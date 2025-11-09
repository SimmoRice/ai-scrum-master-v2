# AI Scrum Master v2.1 - Claude Code Edition

**Multi-Agent Development System powered by Claude Code CLI**

## What's New in v2.1?

**Critical Bug Fixes:**
- Fixed revision loop - Architect now properly iterates on existing code instead of starting from scratch
- Added comprehensive logging system for complete workflow visibility
- Added validation gates to catch agent failures early

See [CHANGELOG.md](CHANGELOG.md) for complete details.

## What's New in v2.0?

V2.0 is a complete architectural redesign that replaces the Anthropic API-based agents with **multiple instances of Claude Code**, each working independently on separate git branches.

### Key Improvements

✅ **Real Development Environment** - Each agent has full filesystem, git, and command-line access
✅ **No Code Extraction Issues** - Claude Code creates files directly, no parsing needed
✅ **True Testing** - Tester can actually run tests and verify code works
✅ **Git Branch Workflow** - Clean separation with automatic branch management
✅ **Iterative Refinement** - Product Owner can request revisions until satisfied
✅ **Cost Efficient** - ~$0.06-0.15 per full workflow iteration

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR                            │
│              (Python Subprocess Manager)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌──────────────────────────────────────┐
        │         Sequential Workflow          │
        └──────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   ARCHITECT  │───▶│   SECURITY   │───▶│    TESTER    │
│              │    │              │    │              │
│ Claude Code  │    │ Claude Code  │    │ Claude Code  │
│ Instance #1  │    │ Instance #2  │    │ Instance #3  │
│              │    │              │    │              │
│ Branch:      │    │ Branch:      │    │ Branch:      │
│ architect    │    │ security     │    │ tester       │
└──────────────┘    └──────────────┘    └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │ PRODUCT OWNER│
                    │              │
                    │ Claude Code  │
                    │ Instance #4  │
                    │              │
                    │ Reviews &    │
                    │ Decides      │
                    └──────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
          ✅ MERGE TO MAIN        🔄 REQUEST REVISION
```

## Git Branch Strategy

```
main
 │
 ├─── architect-branch
 │     └─── security-branch
 │           └─── tester-branch
```

- **Architect** branches from `main`, implements the feature
- **Security** branches from `architect-branch`, adds security hardening
- **Tester** branches from `security-branch`, adds tests and validates
- **Product Owner** reviews final result on `tester-branch`
- If approved: Merge tester → security → architect → main
- If revision needed: Restart from architect with feedback

## How It Works

### 1. User Creates Task

```bash
> task Build a user authentication system with JWT tokens
```

### 2. Orchestrator Launches Sequential Workflow

```python
# Architect implements
architect = ClaudeCodeAgent("Architect", workspace, ARCHITECT_PROMPT)
arch_result = architect.execute_task(user_story, branch="architect-branch")

# Security reviews and hardens
security = ClaudeCodeAgent("Security", workspace, SECURITY_PROMPT)
sec_result = security.execute_task("Review and fix security issues", branch="security-branch")

# Tester creates and runs tests
tester = ClaudeCodeAgent("Tester", workspace, TESTER_PROMPT)
test_result = tester.execute_task("Create tests and verify", branch="tester-branch")

# Product Owner reviews
po = ClaudeCodeAgent("ProductOwner", workspace, PO_PROMPT)
decision = po.review_implementation(user_story, test_result)
```

### 3. Product Owner Makes Decision

- ✅ **APPROVED**: Merge branches to main, task complete
- 🔄 **REVISE**: Provide feedback, restart with architect
- ❌ **REJECT**: Explain why, start fresh

## Technical Implementation

### ClaudeCodeAgent Class

```python
class ClaudeCodeAgent:
    """Wrapper for Claude Code CLI subprocess"""

    def __init__(self, role: str, workspace: Path, system_prompt: str):
        self.role = role
        self.workspace = workspace
        self.system_prompt = system_prompt

    def execute_task(self, task: str, branch: str = None) -> dict:
        """Execute task on specified git branch"""
        # Checkout branch
        # Run claude -p with JSON output
        # Parse and return result
```

### Orchestrator

```python
class Orchestrator:
    """Manages sequential AI workflow"""

    def process_user_story(self, story: str) -> WorkflowResult:
        """Run full Architect → Security → Tester → PO workflow"""
```

## POC Validation

✅ **Proof-of-concept completed successfully!**

All 3 tests passed:
- ✅ Simple file creation
- ✅ HTML file + git commit
- ✅ Multi-file project (calculator with 3 files)

See [poc_claude_code_cli.py](../ai-scrum-master/poc_claude_code_cli.py) for details.

## Cost Analysis

Based on POC testing:

| Agent | Avg Cost | Turns |
|-------|----------|-------|
| Architect | $0.02-0.05 | 3-5 |
| Security | $0.01-0.03 | 2-3 |
| Tester | $0.02-0.05 | 3-5 |
| Product Owner | $0.01-0.02 | 1-2 |

**Total per iteration**: ~$0.06-0.15

Very affordable for high-quality multi-agent development! 🎉

## Project Structure

```
ai-scrum-master-v2/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── orchestrator.py          # Main orchestration logic
├── claude_agent.py          # ClaudeCodeAgent wrapper
├── agents/
│   ├── __init__.py
│   ├── architect_prompt.py  # Architect system prompt
│   ├── security_prompt.py   # Security system prompt
│   ├── tester_prompt.py     # Tester system prompt
│   └── po_prompt.py         # Product Owner prompt
├── git_manager.py           # Git branch operations
├── config.py                # Configuration
├── main.py                  # CLI interface
├── workspace/               # Working directory for agents
└── tests/
    └── test_orchestrator.py

```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your Anthropic API key
# (Claude Code uses this automatically)

# Run the CLI
python main.py

# Create a task
> task Build a REST API for todo items with CRUD operations

# Watch the agents work!
```

## Differences from v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Agent Type | Anthropic API | Claude Code CLI |
| File Creation | Extracted from text | Direct file writes |
| Testing | Simulated | Actually runs tests |
| Git Access | Python subprocess | Native via Bash tool |
| Iteration | Manual | Product Owner driven |
| Cost per workflow | ~$0.10-0.20 | ~$0.06-0.15 |
| Code quality | Good | Excellent |

## Status

🚧 **IN DEVELOPMENT** 🚧

- [x] POC validation
- [x] Architecture design
- [ ] ClaudeCodeAgent implementation
- [ ] Orchestrator implementation
- [ ] Git branch management
- [ ] Agent prompts
- [ ] CLI interface
- [ ] Testing

## Contributing

This is a personal project, but suggestions welcome via issues!

## License

MIT

---

**Built with Claude Code and lots of ☕**