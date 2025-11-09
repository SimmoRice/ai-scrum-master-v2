# Working with External Projects

AI Scrum Master v2.2 can now work on **external projects** separate from its own repository.

---

## Quick Start

### Basic Usage

```bash
# Work on an external project
./run.sh --workspace /path/to/your/project "user story here"

# Example: Add feature to existing calculator app
./run.sh --workspace ../my-calculator-app "add dark mode toggle"
```

---

## Use Cases

### 1. Keep Tool Separate from Projects

**Before (Mixed):**
```
ai-scrum-master-v2/
├── orchestrator.py          # Tool code
├── workspace/
│   ├── calculator.html      # Project code (MIXED!)
│   └── calculator.js
```

**After (Clean Separation):**
```
ai-scrum-master-v2/          # Tool repository
├── orchestrator.py
└── (clean, no project files)

my-calculator-app/           # Project repository
├── calculator.html
├── calculator.js
└── .github/workflows/       # Project-specific CI/CD
```

### 2. Work on Multiple Projects

```bash
# Project A
./run.sh --workspace ~/projects/calculator-app "add export feature"

# Project B
./run.sh --workspace ~/projects/todo-app "add user authentication"

# Project C
./run.sh --workspace ~/projects/blog-platform "implement comments"
```

Each project maintains its own:
- Git history
- GitHub repository
- CI/CD workflows
- Dependencies

### 3. Collaborate on Team Projects

```bash
# Clone team's repository
cd ~/projects
git clone https://github.com/team/our-app.git
cd our-app
git checkout -b feature/new-feature

# Work on it with AI Scrum Master
cd ~/ai-scrum-master-v2
./run.sh --workspace ~/projects/our-app "implement new feature from issue #123"

# AI creates commits in team repo
cd ~/projects/our-app
git push origin feature/new-feature

# Create PR in team's repository
gh pr create --base main
```

---

## How It Works

### 1. **AI Scrum Master Changes Directory**
```bash
./run.sh --workspace /path/to/project "task"
```

The orchestrator:
- Changes to your project directory
- Initializes git (if needed)
- Creates feature branches in YOUR project
- Commits to YOUR project's git history
- Creates PRs in YOUR project's repository

### 2. **Logs Stay in AI Scrum Master**
```
ai-scrum-master-v2/
└── logs/
    ├── workflow_20251109_123456.json
    └── workflow_20251109_123456.log
```

Workflow logs are still stored in AI Scrum Master's directory, not the project.

### 3. **GitHub Integration Works Too**

If you have GitHub enabled (`GITHUB_CONFIG["enabled"] = True`):

```bash
# Work on external project
./run.sh --workspace ~/projects/my-app "add feature"

# AI creates PR in my-app repository (not ai-scrum-master!)
# PR URL: https://github.com/yourname/my-app/pull/123
```

The PR is created in **your project's repository**, not AI Scrum Master's.

---

## Complete Example Workflows

### Example 1: New Feature on Existing Project

```bash
# You have an existing calculator app
cd ~/projects/calculator-app
git status  # On branch: main

# Use AI Scrum Master to add a feature
cd ~/ai-scrum-master-v2
./run.sh --workspace ~/projects/calculator-app \
  "Add a scientific mode with functions: sin, cos, tan, log, sqrt"

# What happens:
# 1. AI creates feature branch in calculator-app
# 2. Architect implements the feature
# 3. Security reviews code
# 4. Tester writes and runs tests
# 5. PO approves
# 6. (Optional) PR created in calculator-app repo
# 7. All commits are in calculator-app's git history

# Check the results
cd ~/projects/calculator-app
git log --oneline -5
git branch
```

### Example 2: Work on GitHub Project

```bash
# Clone a GitHub project (or use existing)
git clone https://github.com/myteam/our-app.git ~/projects/our-app

# Work on it
./run.sh --workspace ~/projects/our-app \
  "Implement feature from GitHub issue #42"

# AI creates PR in our-app repository
# Review and merge through GitHub
```

### Example 3: Multiple Sequential Tasks

```bash
# Task 1: Authentication
./run.sh --workspace ~/projects/my-app \
  "Add user authentication with JWT"

# Task 2: Authorization (builds on previous work)
./run.sh --workspace ~/projects/my-app \
  "Add role-based authorization (admin, user, guest)"

# Task 3: Password reset
./run.sh --workspace ~/projects/my-app \
  "Implement password reset flow with email"

# All changes are in my-app's git history
cd ~/projects/my-app
git log --oneline -10
```

---

## Requirements

### Project Must Have:
1. **Directory exists** (will be created if it doesn't exist)
2. **Write permissions** for AI Scrum Master
3. **Git repository** (will be initialized if needed)

### Project Can Have:
- Existing code (AI will work with it)
- Existing git history (AI will add to it)
- GitHub remote (AI will push/create PRs)
- CI/CD workflows (will run on AI's changes)

---

## Path Specifications

### Relative Paths
```bash
# Relative to AI Scrum Master directory
./run.sh --workspace ../my-app "task"
./run.sh --workspace ../../projects/app "task"
./run.sh --workspace workspace "task"  # Use internal workspace
```

### Absolute Paths
```bash
# Full path
./run.sh --workspace /Users/simon/projects/my-app "task"
./run.sh --workspace ~/projects/my-app "task"
```

### Path Resolution
Paths are automatically resolved to absolute paths, so:
```bash
./run.sh --workspace ../my-app "task"
# Becomes: /Users/simon/projects/my-app
```

---

## GitHub Integration Behavior

### When `GITHUB_CONFIG["enabled"] = True`

**Internal Workspace:**
```bash
./run.sh "task"
# PR created in: ai-scrum-master-v2 repository
```

**External Workspace:**
```bash
./run.sh --workspace ~/projects/my-app "task"
# PR created in: my-app repository (if it has GitHub remote)
```

### GitHub Remote Detection

AI Scrum Master uses `gh` CLI, which automatically detects the remote:
```bash
cd ~/projects/my-app
git remote -v
# origin  https://github.com/user/my-app.git

# When AI creates PR, it goes to user/my-app
```

---

## Best Practices

### 1. **One Project Per Repository**
Keep AI Scrum Master separate from all projects.

```
Good:
  ~/ai-scrum-master-v2/        (tool)
  ~/projects/calculator-app/   (project 1)
  ~/projects/todo-app/         (project 2)

Bad:
  ~/ai-scrum-master-v2/
    └── workspace/
        ├── calculator-app/    (mixed with tool)
        └── todo-app/
```

### 2. **Use Branches**
Let AI create feature branches in your project:
```bash
cd ~/projects/my-app
git checkout main
git pull origin main

./run.sh --workspace ~/projects/my-app "add feature"
# AI creates: architect-branch, security-branch, tester-branch
```

### 3. **Review Before Merging**
Always review AI's changes before merging to main:
```bash
cd ~/projects/my-app
git log --oneline tester-branch
git diff main..tester-branch
```

### 4. **Use GitHub PRs**
Enable GitHub integration for best workflow:
```python
# config.py
GITHUB_CONFIG = {
    "enabled": True,  # Enable PR creation
}
```

```bash
./run.sh --workspace ~/projects/my-app "feature"
# PR created automatically for review
```

---

## Troubleshooting

### Error: "Workspace directory not found"
```bash
./run.sh --workspace /bad/path "task"
# ❌ Error: Workspace directory not found: /bad/path
```

**Solution:** Ensure directory exists:
```bash
mkdir -p ~/projects/my-app
./run.sh --workspace ~/projects/my-app "task"
```

### Error: "Permission denied"
**Solution:** Ensure you have write permissions:
```bash
ls -la ~/projects/my-app
chmod u+w ~/projects/my-app
```

### Git Not Initialized
**Solution:** AI Scrum Master will initialize git automatically:
```bash
# Even if directory is empty, AI will:
# 1. Initialize git
# 2. Create initial commit
# 3. Start working
```

### Wrong Repository for PR
If PR is created in wrong repo:
```bash
cd ~/projects/my-app
git remote -v  # Check remote

# Set correct remote if needed
git remote set-url origin https://github.com/user/correct-repo.git
```

---

## Comparison: Internal vs External Workspace

| Feature | Internal Workspace | External Workspace |
|---------|-------------------|-------------------|
| **Command** | `./run.sh "task"` | `./run.sh --workspace /path "task"` |
| **Location** | `ai-scrum-master-v2/workspace/` | Any directory |
| **Git History** | Mixed with tool | Clean project history |
| **GitHub Repo** | ai-scrum-master-v2 | Your project repo |
| **PRs Created In** | Tool repo | Project repo |
| **CI/CD** | Tool's workflows | Project's workflows |
| **Logs** | `ai-scrum-master-v2/logs/` | `ai-scrum-master-v2/logs/` |
| **Use Case** | Testing, demos | Real projects |

---

## Summary

**External workspace support gives you:**

✅ **Clean separation** - Tool and projects in different repos

✅ **Flexibility** - Work on any project, anywhere

✅ **Team collaboration** - Work on shared repositories

✅ **Proper git history** - Each project has its own clean history

✅ **Correct CI/CD** - PRs and Actions run in project repos

✅ **Multiple projects** - Easily switch between projects

**Simple command:**
```bash
./run.sh --workspace /path/to/project "what to build"
```

That's it! 🚀
