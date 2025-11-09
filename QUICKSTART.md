# Quick Start Guide - AI Scrum Master v2.0

## Installation

```bash
# 1. Clone or navigate to the repository
cd ai-scrum-master-v2

# 2. Run setup script
./setup.sh

# 3. Edit .env file with your Anthropic API key
nano .env  # or use your favorite editor

# Add your key:
ANTHROPIC_API_KEY=sk-ant-...
```

## First Run

```bash
python3 main.py
```

You should see:
```
╔═══════════════════════════════════════════════════════════╗
║              AI SCRUM MASTER v2.0                         ║
║          Claude Code Multi-Agent System                   ║
╚═══════════════════════════════════════════════════════════╝

✅ AI Scrum Master v2.0 ready!
Type 'help' for available commands

>
```

## Basic Usage

### Create a Task

**Simple (one-line):**
```bash
> task Build a simple calculator web app with HTML, CSS, and JavaScript
```

**Multi-line (paste complex requirements):**
```bash
> task Build a REST API for todos
...
... Requirements:
... - GET /todos - List all todos
... - POST /todos - Create new todo
... - PUT /todos/:id - Update todo
... - DELETE /todos/:id - Delete todo
... - Use Express.js and SQLite
...
... (press Enter TWICE on empty lines to submit)
```

**Backslash continuation:**
```bash
> task Create user authentication with \
... JWT tokens and bcrypt hashing
```

This will:
1. 🏗️ **Architect** creates the implementation
2. 🔒 **Security** reviews and hardens the code
3. 🧪 **Tester** creates and runs tests
4. 👔 **Product Owner** reviews and decides

### Product Owner Decisions

The PO can make three decisions:

- **✅ APPROVE**: Code is good, merges to main automatically
- **🔄 REVISE**: Requests specific improvements (up to 3 revisions)
- **❌ REJECT**: Fundamental issues, start over

### Check Status

```bash
> status
```

Shows:
- Current git branch
- Recent commits on all branches
- Workspace location

### Get Help

```bash
> help
```

### Exit

```bash
> quit
```

## Example Session

```
> task Create a REST API endpoint for user registration with email validation

🏗️  PHASE 1: ARCHITECT
════════════════════════════════════════════════════════════
Task: Create a REST API endpoint for user registration...
Workspace: /path/to/workspace
════════════════════════════════════════════════════════════

✅ Architect created files:
   - server.js
   - routes/register.js
   - utils/validation.js

🔒 PHASE 2: SECURITY
════════════════════════════════════════════════════════════
✅ Security added:
   - Input sanitization
   - Email validation
   - Password hashing (bcrypt)
   - Rate limiting

🧪 PHASE 3: TESTER
════════════════════════════════════════════════════════════
✅ Tester created:
   - test_register.js
   - All 12 tests passing

👔 PHASE 4: PRODUCT OWNER REVIEW
════════════════════════════════════════════════════════════
DECISION: APPROVE

✅ Product Owner APPROVED the implementation!
🔀 Merging approved work to main branch...
✅ Successfully merged to main!

📈 WORKFLOW SUMMARY
════════════════════════════════════════════════════════════
Status: ✅ APPROVED
Revisions: 0
Total Cost: $0.0834
════════════════════════════════════════════════════════════

🎉 Task completed and merged to main!
```

## Workspace Structure

After running a task, your workspace will contain:

```
workspace/
├── README.md                # Auto-generated
├── [your implementation files]
├── [test files]
└── .git/                    # Git repository
    ├── main                 # Approved, merged code
    ├── architect-branch     # Architect's work
    ├── security-branch      # Security's additions
    └── tester-branch        # Tests added
```

## Tips

### Writing Good User Stories

✅ **Good**:
```
Build a todo list API with:
- GET /todos - List all todos
- POST /todos - Create new todo
- PUT /todos/:id - Update todo
- DELETE /todos/:id - Delete todo
- Use Express.js and SQLite
```

❌ **Too Vague**:
```
Make a website
```

### Cost Management

- Each full workflow costs ~$0.06-0.15
- Revisions add ~$0.05-0.10 each
- Simple tasks: 1-2 minutes
- Complex tasks: 5-10 minutes

### Git Branches

The system uses a sequential branch workflow:

```
main
 │
 ├─── architect-branch      (Architect creates code)
 │     │
 │     └─── security-branch (Security hardens code)
 │           │
 │           └─── tester-branch (Tester adds tests)
```

After PO approval, branches merge back:
```
tester → security → architect → main
```

### Troubleshooting

**"claude command not found"**
- Install Claude Code from https://claude.com/code

**"Failed to initialize"**
- Check your `ANTHROPIC_API_KEY` in `.env`
- Verify Claude Code is installed: `claude --version`

**"Permission denied"**
- Make sure you have write access to the workspace directory
- Check git is configured: `git config --global user.name "Your Name"`

**Agent timeout**
- Default timeout is 5 minutes
- Complex tasks may take longer
- Check `config.py` to adjust timeout

## Advanced Usage

### Custom Workspace

```python
from orchestrator import Orchestrator

orch = Orchestrator(workspace_dir="/path/to/custom/workspace")
result = orch.process_user_story("Build a feature...")
```

### Programmatic Access

```python
from orchestrator import Orchestrator

orch = Orchestrator()

result = orch.process_user_story("""
Create a user authentication system with:
- JWT tokens
- Password hashing with bcrypt
- Login and logout endpoints
""")

if result.approved:
    print(f"Success! Cost: ${result.total_cost:.2f}")
else:
    print(f"Failed. Errors: {result.errors}")
```

## Next Steps

1. Try the example tasks in the [README](README.md)
2. Read the [Architecture Overview](README.md#architecture)
3. Review the [POC Findings](CLAUDE_CODE_CLI_FINDINGS.md)
4. Check out the [agent prompts](agents/) to understand how each agent thinks

## Support

- Issues: Create an issue in the repository
- Documentation: See [README.md](README.md)
- POC Details: See [CLAUDE_CODE_CLI_FINDINGS.md](CLAUDE_CODE_CLI_FINDINGS.md)

---

**Happy coding with your AI team! 🚀**
