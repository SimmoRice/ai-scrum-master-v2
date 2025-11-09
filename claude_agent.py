"""
ClaudeCodeAgent - Wrapper for Claude Code CLI

This class manages individual Claude Code instances, running them as subprocesses
with specific system prompts and working directories.
"""
import subprocess
import json
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
        allowed_tools: Optional[str] = None
    ):
        """
        Initialize a Claude Code agent

        Args:
            role: Agent role (e.g., "Architect", "Security", "Tester", "ProductOwner")
            workspace: Working directory for the agent
            system_prompt: System prompt defining agent's personality and instructions
            allowed_tools: Comma-separated list of allowed tools (default from config)
        """
        self.role = role
        self.workspace = Path(workspace)
        self.system_prompt = system_prompt
        self.allowed_tools = allowed_tools or CLAUDE_CLI_CONFIG["allowed_tools"]
        self.timeout = CLAUDE_CLI_CONFIG["timeout"]

        # Ensure workspace exists
        self.workspace.mkdir(parents=True, exist_ok=True)

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
            start_time = time.time()

            # Execute Claude Code as subprocess
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace),
                capture_output=True,
                text=True,
                timeout=timeout
            )

            elapsed = time.time() - start_time
            print(f"✓ Completed in {elapsed:.1f} seconds")

            # Log stderr for debugging (even on success)
            if result.stderr:
                import os
                debug_log = Path("logs") / "claude_debug.log"
                debug_log.parent.mkdir(exist_ok=True)
                with open(debug_log, "a") as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Agent: {self.role} | Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Return code: {result.returncode}\n")
                    f.write(f"{'='*60}\n")
                    f.write(result.stderr)
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
                return {
                    'success': False,
                    'error': f"Claude Code exited with code {result.returncode}",
                    'raw_stdout': result.stdout,
                    'raw_stderr': result.stderr,
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f"Task timed out after {timeout} seconds",
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
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
            if 'raw_stderr' in result and result['raw_stderr']:
                print(f"\n📋 Details:")
                print(f"   {result['raw_stderr'][:500]}")

        print(f"{'='*60}\n")

    def __repr__(self) -> str:
        return f"ClaudeCodeAgent(role='{self.role}', workspace='{self.workspace}')"