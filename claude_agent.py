"""
ClaudeCodeAgent - Wrapper for Claude Code CLI

This class manages individual Claude Code instances, running them as subprocesses
with specific system prompts and working directories.
"""
import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from config import CLAUDE_CLI_CONFIG


class ClaudeCodeAgent:
    """
    Wrapper for controlling Claude Code via CLI

    Each agent instance represents a specialized AI (Architect, Security, Tester, or PO)
    that can execute tasks in a specific workspace and git branch.
    """

    def __init__(
        self,
        role: str,
        workspace: Path,
        system_prompt: str,
        allowed_tools: Optional[str] = None,
        verbose: bool = False
    ):
        """
        Initialize a Claude Code agent

        Args:
            role: Agent role (e.g., "Architect", "Security", "Tester", "ProductOwner")
            workspace: Working directory for the agent
            system_prompt: System prompt defining agent's personality and instructions
            allowed_tools: Comma-separated list of allowed tools (default from config)
            verbose: If True, stream Claude Code output in real-time
        """
        self.role = role
        self.workspace = Path(workspace)
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools or CLAUDE_CLI_CONFIG["allowed_tools"]
        self.timeout = CLAUDE_CLI_CONFIG["timeout"]
        self.verbose = verbose

        # Ensure workspace exists
        self.workspace.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_log_output(output: str) -> str:
        """
        Sanitize log output to prevent sensitive data leakage

        Security: Removes API keys, tokens, passwords, and other sensitive data

        Args:
            output: Raw log output

        Returns:
            Sanitized output
        """
        # Security: Redact common sensitive patterns
        patterns = [
            (r'ANTHROPIC_API_KEY[=:]\s*["\']?([a-zA-Z0-9_-]+)["\']?', 'ANTHROPIC_API_KEY=***REDACTED***'),
            (r'API_KEY[=:]\s*["\']?([a-zA-Z0-9_-]+)["\']?', 'API_KEY=***REDACTED***'),
            (r'TOKEN[=:]\s*["\']?([a-zA-Z0-9_-]+)["\']?', 'TOKEN=***REDACTED***'),
            (r'PASSWORD[=:]\s*["\']?([^\s"\']+)["\']?', 'PASSWORD=***REDACTED***'),
            (r'SECRET[=:]\s*["\']?([a-zA-Z0-9_-]+)["\']?', 'SECRET=***REDACTED***'),
            (r'sk-[a-zA-Z0-9]{32,}', '***REDACTED_API_KEY***'),  # Anthropic API key pattern
            (r'ghp_[a-zA-Z0-9]{36,}', '***REDACTED_GITHUB_TOKEN***'),  # GitHub token
        ]

        sanitized = output
        for pattern, replacement in patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    def execute_task(
        self,
        task: str,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using Claude Code

        Args:
            task: The task description/prompt
            timeout: Optional timeout in seconds (default: from config)

        Returns:
            Dictionary with execution results:
            {
                'success': bool,
                'result': str,  # Claude's response message
                'output': dict,  # Full JSON output from Claude Code
                'session_id': str,
                'cost_usd': float,
                'num_turns': int,
                'duration_ms': int,
                'error': str  # Only present if failed
            }
        """
        timeout = timeout or self.timeout

        # Build command
        cmd = [
            "claude",
            "-p", task,
            "--output-format", "json",
            "--system-prompt", self.system_prompt,
            "--allowedTools", self.allowed_tools
        ]

        print(f"\n{'='*60}")
        print(f"🤖 {self.role} Agent Starting")
        print(f"{'='*60}")
        print(f"Task: {task[:100]}{'...' if len(task) > 100 else ''}")
        print(f"Workspace: {self.workspace}")
        print(f"Timeout: {timeout}s")
        print(f"{'='*60}")
        print(f"⏳ Running Claude Code (this may take 30-120 seconds)...")
        print(f"💭 {self.role} is thinking and working...")
        print()

        try:
            import time
            import threading
            start_time = time.time()

            # Create stop event before defining the function that uses it
            stop_progress = threading.Event()

            # Progress monitoring function
            def show_progress():
                """Show periodic heartbeat messages during long-running tasks"""
                interval = 30  # Show message every 30 seconds
                while not stop_progress.is_set():
                    time.sleep(interval)
                    if not stop_progress.is_set():
                        elapsed = time.time() - start_time
                        minutes = int(elapsed // 60)
                        seconds = int(elapsed % 60)
                        print(f"⏳ Still running... {minutes}m {seconds}s elapsed (max {timeout}s)")

            # Start progress monitoring in background
            progress_thread = threading.Thread(target=show_progress, daemon=True)
            progress_thread.start()

            try:
                # Execute Claude Code as subprocess
                if self.verbose:
                    # Verbose mode: Stream output in real-time
                    print(f"\n{'─'*60}")
                    print(f"📡 VERBOSE MODE: Streaming Claude Code output...")
                    print(f"{'─'*60}\n")

                    # Use Popen to stream output line by line
                    process = subprocess.Popen(
                        cmd,
                        cwd=str(self.workspace),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1  # Line buffered
                    )

                    # Collect output while streaming
                    stdout_lines = []
                    stderr_lines = []

                    import select
                    import sys

                    # Stream output in real-time
                    while True:
                        # Check if process has finished
                        return_code = process.poll()

                        # Read stdout
                        if process.stdout:
                            line = process.stdout.readline()
                            if line:
                                stdout_lines.append(line)
                                # Print to terminal (sanitize first for security)
                                sanitized_line = self._sanitize_log_output(line)
                                print(sanitized_line, end='', flush=True)

                        # Read stderr
                        if process.stderr:
                            err_line = process.stderr.readline()
                            if err_line:
                                stderr_lines.append(err_line)

                        # Break if process finished and no more output
                        if return_code is not None and not line and not err_line:
                            break

                        # Check timeout
                        if time.time() - start_time > timeout:
                            process.kill()
                            raise subprocess.TimeoutExpired(cmd, timeout)

                    # Create result object
                    result = subprocess.CompletedProcess(
                        args=cmd,
                        returncode=return_code,
                        stdout=''.join(stdout_lines),
                        stderr=''.join(stderr_lines)
                    )

                    print(f"\n{'─'*60}")
                    print(f"📡 End of Claude Code output")
                    print(f"{'─'*60}\n")
                else:
                    # Normal mode: Capture output silently
                    result = subprocess.run(
                        cmd,
                        cwd=str(self.workspace),
                        capture_output=True,
                        text=True,
                        timeout=timeout
                    )
            finally:
                # Stop progress monitoring
                stop_progress.set()
                progress_thread.join(timeout=1)

            elapsed = time.time() - start_time
            print(f"✓ Completed in {elapsed:.1f} seconds")

            # Security: Log stderr for debugging but sanitize sensitive data
            if result.stderr:
                import os
                debug_log = Path("logs") / "claude_debug.log"
                debug_log.parent.mkdir(exist_ok=True)

                # Security: Sanitize stderr to prevent sensitive data leakage
                sanitized_stderr = self._sanitize_log_output(result.stderr)

                with open(debug_log, "a") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Agent: {self.role} | Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Return code: {result.returncode}\n")
                    f.write(f"{'='*60}\n")
                    f.write(sanitized_stderr)
                    f.write(f"\n{'='*60}\n\n")

            # Check if execution succeeded
            if result.returncode == 0:
                # Parse JSON output
                try:
                    output = json.loads(result.stdout)

                    # Extract key information
                    return {
                        'success': True,
                        'result': output.get('result', ''),
                        'output': output,
                        'session_id': output.get('session_id', ''),
                        'cost_usd': output.get('total_cost_usd', 0.0),
                        'num_turns': output.get('num_turns', 0),
                        'duration_ms': output.get('duration_ms', 0),
                    }
                except json.JSONDecodeError as e:
                    return {
                        'success': False,
                        'error': f"Failed to parse JSON output: {e}",
                        'raw_stdout': result.stdout,
                        'raw_stderr': result.stderr,
                    }
            else:
                # Execution failed
                # Security: Sanitize error output to prevent information disclosure
                sanitized_stdout = self._sanitize_log_output(result.stdout) if result.stdout else ""
                sanitized_stderr = self._sanitize_log_output(result.stderr) if result.stderr else ""

                return {
                    'success': False,
                    'error': f"Claude Code exited with code {result.returncode}",
                    'raw_stdout': sanitized_stdout[:1000],  # Limit output size
                    'raw_stderr': sanitized_stderr[:1000],  # Limit output size
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Task timed out after {timeout} seconds",
            }

        except Exception as e:
            # Security: Don't expose full exception details
            return {
                'success': False,
                'error': f"Unexpected error during agent execution",
            }

    def print_result(self, result: Dict[str, Any]) -> None:
        """
        Pretty print the execution result

        Args:
            result: Result dictionary from execute_task()
        """
        print(f"\n{'='*60}")
        print(f"📊 {self.role} Result")
        print(f"{'='*60}")

        if result['success']:
            print(f"✅ Success")
            print(f"\n💬 What {self.role} did:")
            # Show response with better formatting
            response = result['result']
            if len(response) > 500:
                print(f"   {response[:500]}...")
                print(f"   ... (truncated, {len(response)} chars total)")
            else:
                print(f"   {response}")

            print(f"\n📊 Stats:")
            print(f"   💰 Cost: ${result['cost_usd']:.4f}")
            print(f"   🔄 Turns: {result['num_turns']}")
            print(f"   ⏱️  Duration: {result['duration_ms']/1000:.1f}s")
        else:
            print(f"❌ Failed")
            print(f"\n⚠️  Error: {result.get('error', 'Unknown error')}")
            # Security: Don't print raw error details that might contain sensitive info
            # Errors are already logged to debug file with sanitization

        print(f"{'='*60}\n")

    def __repr__(self) -> str:
        return f"ClaudeCodeAgent(role='{self.role}', workspace='{self.workspace}')"