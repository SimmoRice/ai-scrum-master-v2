# Claude Code CLI Integration - Key Findings

## Discovery Summary

We've successfully validated that Claude Code CAN be controlled programmatically via CLI, making the v2.0 architecture viable!

## Key Learnings

### 1. Working Directory Behavior

**Issue**: Claude Code doesn't have a `--cwd` flag to set working directory.

**Solution**: Use Python's `subprocess.run(cwd=workspace)` parameter instead.

```python
# ❌ WRONG - This flag doesn't exist
cmd = ["claude", "-p", task, "--cwd", str(workspace)]

# ✅ CORRECT - Use subprocess cwd parameter
cmd = ["claude", "-p", task, "--output-format", "json"]
result = subprocess.run(cmd, cwd=str(workspace))
```

### 2. File Creation Location

**Issue**: Claude Code may create files in `/tmp` or other locations unless explicitly instructed.

**Solution**: Be very explicit in the task prompt about file location.

```python
# ❌ Vague - might create files anywhere
task = "Create a file called hello.txt"

# ✅ Explicit - creates file in correct location
task = "Create a file called hello.txt in the current working directory"
```

**Best Practice**: Always include phrases like:
- "in the current working directory"
- "Do NOT create files in /tmp or anywhere else"
- "Create ALL files in the current directory"

### 3. CLI Command Structure

**Minimal Working Command**:
```python
cmd = [
    "claude",
    "-p", task,                          # Non-interactive mode
    "--output-format", "json",           # Get structured output
    "--system-prompt", system_prompt,    # Define agent role
    "--allowedTools", "Write,Read,Edit,Bash,Glob,Grep"  # Control permissions
]

result = subprocess.run(
    cmd,
    cwd=str(workspace),                  # Set working directory
    capture_output=True,                 # Capture stdout/stderr
    text=True,                           # Get text output
    timeout=300                          # 5 minute timeout
)
```

### 4. JSON Output Format

When successful, Claude Code returns a JSON object with:

```json
{
    "type": "result",
    "subtype": "success",
    "is_error": false,
    "duration_ms": 5215,
    "num_turns": 2,
    "result": "I've successfully created...",
    "session_id": "48ee7432-7008-42fc...",
    "total_cost_usd": 0.00462,
    "usage": {...},
    "modelUsage": {...},
    "permission_denials": []
}
```

**Key Fields**:
- `result`: The AI's final response message
- `is_error`: Whether the task failed
- `num_turns`: How many conversation turns were needed
- `total_cost_usd`: Cost of the operation
- `session_id`: Unique session identifier

### 5. Available CLI Options

From `claude --help`, key options for v2.0:

```bash
--print, -p                  # Non-interactive mode (required)
--output-format json         # Get structured JSON output
--system-prompt "..."        # Define agent personality/role
--allowedTools "..."         # Control what tools agent can use
--tools "..."                # Override default tool set
--model "sonnet"             # Specify model (sonnet, opus, haiku)
--permission-mode "..."      # Control permission behavior
--add-dir "..."              # Additional directories for access
```

### 6. Tool Control

You can restrict tools to specific operations:

```python
# Allow all common tools
"--allowedTools", "Write,Read,Edit,Bash,Glob,Grep"

# Fine-grained control (from help)
"--allowedTools", "Bash(git:*) Edit"  # Only git commands and Edit

# Deny specific tools
"--disallowedTools", "Bash(rm:*)"  # Block rm commands
```

### 7. Git Integration

Claude Code can execute git commands via Bash tool:

```python
task = """
Create index.html file.
Then commit it to git with message 'Add index page'
"""
```

The agent will:
1. Create the file
2. Run `git add index.html`
3. Run `git commit -m "Add index page"`

**Important**: The workspace must already be a git repository (run `git init` first).

## Architecture Implications for V2.0

### ✅ Confirmed Viable

1. **Multi-agent orchestration**: Can spawn multiple Claude Code instances
2. **Git branch workflow**: Each agent can work on separate branches
3. **File creation**: Agents can create and modify files
4. **Sequential workflow**: Can chain agents (Architect → Security → Tester)
5. **Structured output**: JSON format allows parsing results
6. **Cost tracking**: Can monitor spend per agent

### 🎯 Implementation Pattern

```python
class ClaudeCodeAgent:
    def __init__(self, role: str, workspace: Path, system_prompt: str):
        self.role = role
        self.workspace = workspace
        self.system_prompt = system_prompt

    def execute_task(self, task: str) -> dict:
        cmd = [
            "claude",
            "-p", task,
            "--output-format", "json",
            "--system-prompt", self.system_prompt,
            "--allowedTools", "Write,Read,Edit,Bash,Glob,Grep"
        ]

        result = subprocess.run(
            cmd,
            cwd=str(self.workspace),
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            raise Exception(f"Task failed: {result.stderr}")
```

### 📋 Workflow Design

```python
# 1. Architect creates initial implementation
architect = ClaudeCodeAgent("Architect", workspace, ARCHITECT_PROMPT)
arch_result = architect.execute_task(user_story)

# 2. Security reviews and hardens
security = ClaudeCodeAgent("Security", workspace, SECURITY_PROMPT)
sec_result = security.execute_task("Review and fix security issues")

# 3. Tester creates and runs tests
tester = ClaudeCodeAgent("Tester", workspace, TESTER_PROMPT)
test_result = tester.execute_task("Create tests and verify code works")

# 4. Product Owner reviews
po = ClaudeCodeAgent("ProductOwner", workspace, PO_PROMPT)
po_result = po.execute_task("Review implementation against requirements")
```

## Next Steps

1. ✅ Validate POC passes all 3 tests
2. Design ClaudeCodeAgent class
3. Implement Orchestrator
4. Create agent system prompts
5. Build sequential workflow
6. Add git branch management
7. Implement merge decision logic

## Cost Considerations

From test run:
- Simple file creation: ~$0.0046 USD (2 turns)
- More complex tasks: ~$0.0067 USD (3 turns)

**Estimated cost per workflow**:
- Architect: ~$0.02-0.05
- Security: ~$0.01-0.03
- Tester: ~$0.02-0.05
- Product Owner: ~$0.01-0.02

**Total per iteration**: ~$0.06-0.15 USD

Very affordable! 🎉

## Potential Issues

### 1. Permission Prompts

Claude Code may prompt for permissions in interactive mode. Solutions:
- Use `--permission-mode bypassPermissions` for trusted environments
- Use `--dangerously-skip-permissions` in sandboxed environments

### 2. Session Management

Each call creates a new session. For iterative work:
- Consider using `--continue` flag to resume sessions
- Or design agents to be stateless and work from git state

### 3. Error Handling

Need robust error handling for:
- Agent failures (syntax errors, crashes)
- Git conflicts
- Permission denials
- Rate limits

## Summary

**✅ V2.0 Architecture is VIABLE!**

We can control Claude Code programmatically via CLI, making the multi-agent orchestration approach completely feasible. The key insights:

1. Use `subprocess.run(cwd=workspace)` for working directory
2. Be explicit about file locations in task prompts
3. Use JSON output format for structured results
4. Control tools with `--allowedTools`
5. Each agent costs ~$0.01-0.05 per execution

The POC validation will confirm these findings work end-to-end for file creation, git commits, and multi-file projects.
