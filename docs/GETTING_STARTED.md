# Getting Started: Build Your First App with AI Scrum Cluster

This guide will walk you through building a complete application using your distributed AI Scrum Master cluster.

## Prerequisites

- ✅ Proxmox cluster deployed (containers 200-205)
- ✅ All services running (`./status_cluster.sh` shows all green)
- ✅ GitHub CLI installed locally (`gh --version`)
- ✅ Python environment with required packages

## Example: Build a Calculator Web App

Let's build a fully functional calculator web application from scratch.

### Step 1: Create the Repository

```bash
# Create a new GitHub repository
gh repo create YourUsername/calculator-app --public --clone
cd calculator-app

# Initialize with README
echo "# Calculator App

A modern web-based calculator application built by AI.

## Features
- Basic arithmetic operations
- Calculation history
- Dark/Light mode
- Responsive design
" > README.md

git add README.md
git commit -m "Initial commit"
git push origin main
```

### Step 2: Setup Repository for AI Cluster

This one command does everything needed:

```bash
cd ~/Development/repos/ai-scrum-master-v2

# Setup labels and enable issues
python setup_repo_labels.py --repo YourUsername/calculator-app --include-optional
```

This will:
- ✅ Enable issues on the repository (if disabled)
- ✅ Create required AI labels (`ai-ready`, `ai-in-progress`, `ai-completed`, `ai-failed`)
- ✅ Create optional organization labels (`priority:*`, `complexity:*`, `type:*`)

### Step 3: Configure Cluster to Monitor the Repository

On your Proxmox host:

```bash
ssh root@your-proxmox-host
cd /root/ai-scrum-master-v2/deployment/proxmox

# Add calculator app to monitored repos
./configure_multi_repo.sh "SimmoRice/ai-scrum-master-v2,YourUsername/calculator-app"

# Verify configuration
curl http://192.168.100.200:8000/health | jq '.github'
```

You should see:
```json
{
  "github": {
    "connected": true,
    "mode": "multi-repo",
    "repositories": [
      "SimmoRice/ai-scrum-master-v2",
      "YourUsername/calculator-app"
    ],
    "count": 2
  }
}
```

### Step 4: Generate Project Issues

Back on your local machine:

```bash
cd ~/Development/repos/ai-scrum-master-v2

# Let AI break down the project
python create_project_issues.py \
  --repo YourUsername/calculator-app \
  --project "Build a modern web-based calculator application with:
- Basic arithmetic operations (+, -, ×, ÷)
- Clear and backspace functionality
- Decimal point support
- Calculation history (last 10 calculations)
- Dark/Light mode toggle
- Responsive design for mobile
- Keyboard support
- Local storage for theme preference
Use vanilla HTML, CSS, and JavaScript (no frameworks)"
```

The script will:
1. 🤖 Use Claude AI to analyze the project
2. 📝 Break it into 5-10 concrete tasks
3. ✅ Create GitHub issues for each task
4. 🏷️ Add `ai-ready` label to each issue

Example output:
```
==========================================
Creating Project Issues
==========================================
Repository: YourUsername/calculator-app
Project: Build a modern web-based calculator...

🤖 Using Claude to break down project into tasks...
   Found 8 tasks

📝 Creating GitHub issues...

1/8: Setup project structure and HTML layout
  ✅ Created: Setup project structure and HTML layout
     https://github.com/YourUsername/calculator-app/issues/1

2/8: Implement basic calculator CSS styling
  ✅ Created: Implement basic calculator CSS styling
     https://github.com/YourUsername/calculator-app/issues/2

...

==========================================
✅ Created 8/8 issues
==========================================
```

### Step 5: Watch the Cluster Work

The orchestrator will pick up issues within 60 seconds. Monitor progress:

```bash
# Watch cluster health (updates every 5 seconds)
watch -n 5 'curl -s http://192.168.100.200:8000/health | jq'

# Check what workers are doing
curl http://192.168.100.200:8000/workers | jq

# Check the work queue
curl http://192.168.100.200:8000/queue | jq
```

View GitHub issues:
```bash
# List issues in progress
gh issue list --repo YourUsername/calculator-app --label ai-in-progress

# List all issues
gh issue list --repo YourUsername/calculator-app
```

View logs on Proxmox:
```bash
# On Proxmox host
cd /root/ai-scrum-master-v2/deployment/proxmox

# Orchestrator logs
./view_logs.sh orchestrator

# All workers (last 50 lines each)
./view_logs.sh all

# Specific worker
./view_logs.sh worker1
```

### Step 6: Review and Merge Pull Requests

As workers complete tasks, they'll create pull requests with the `needs-review` label:

#### Review Workflow

PRs go through a human review process:
- 🟠 **needs-review**: PR created by worker, awaiting human review
- 🟢 **approved-for-merge**: Human approved, ready to merge
- 🔴 **changes-requested**: Human requested changes

#### List PRs Needing Review

```bash
# Use the review helper script
cd ~/Development/repos/ai-scrum-master-v2

# List all PRs needing review
python review_prs.py --repo YourUsername/calculator-app --list

# Or check all monitored repos
python review_prs.py --all --list
```

#### Review a PR

```bash
# View PR in browser
gh pr view 1 --repo YourUsername/calculator-app --web

# Or check it locally
gh pr checkout 1 --repo YourUsername/calculator-app
# Test it...

# View the diff
gh pr diff 1 --repo YourUsername/calculator-app
```

#### Approve and Merge

```bash
# Approve a PR (adds 'approved-for-merge' label)
python review_prs.py --repo YourUsername/calculator-app --approve 1

# Approve and merge in one step
python review_prs.py --repo YourUsername/calculator-app --approve 1 --merge

# Approve with a comment
python review_prs.py --repo YourUsername/calculator-app --approve 1 --comment "Great work!"

# Approve multiple PRs at once
python review_prs.py --repo YourUsername/calculator-app --approve 1,2,3
```

#### Request Changes

```bash
# Request changes (adds 'changes-requested' label)
python review_prs.py --repo YourUsername/calculator-app --request-changes 1 \
  --comment "Please add error handling for edge cases"
```

#### Manual Merge (Alternative)

You can also merge manually using GitHub CLI:

```bash
# Merge a PR directly (squash commits for clean history)
gh pr merge 1 --repo YourUsername/calculator-app --squash
```

### Step 7: Test the Application

Once all PRs are merged:

```bash
# Clone/pull latest
cd ~/Development
git clone https://github.com/YourUsername/calculator-app
cd calculator-app

# Open in browser
open index.html

# Or use a simple HTTP server
python3 -m http.server 8080
# Visit http://localhost:8080
```

## What Just Happened?

1. 📋 You created a repository and described what you want built
2. 🤖 Claude AI broke down the project into concrete tasks
3. 📝 Issues were created with `ai-ready` label
4. 👀 The orchestrator detected new issues (polls every 60s)
5. 📋 Issues were added to the work queue
6. 👷 Workers picked up issues and worked on them in parallel
7. 💻 Each worker:
   - Cloned the repository
   - Read the issue description
   - Implemented the feature
   - Tested it (when possible)
   - Created a pull request with `needs-review` label
   - Updated the GitHub issue
8. 🛑 **Queue Management**: Once 5 PRs are pending (configurable), workers pause for review
   - Prevents cascading bugs from unreviewed code
   - Prevents review overload
   - Independent features can still proceed in parallel
9. 👀 You reviewed PRs using the review helper script
10. ✅ You approved and merged the PRs, unblocking the queue
11. 🔄 Workers resumed processing remaining issues
12. 🎉 Your calculator app is complete!

**Note**: The cluster uses intelligent queue blocking to ensure code quality. See [Queue Blocking Strategy](QUEUE_BLOCKING_STRATEGY.md) for details.

## Cluster Workflow Summary

```
┌─────────────────┐
│  Create Repo    │
│  & Describe     │
│  Project        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Setup Labels   │  ← python setup_repo_labels.py
│  Enable Issues  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Configure      │  ← ./configure_multi_repo.sh
│  Cluster        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Generate       │  ← python create_project_issues.py
│  Issues (AI)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Orchestrator   │  ← Polls for ai-ready issues
│  Detects Issues │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Queue Issues   │  ← Work queue managed by orchestrator
│  for Workers    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Workers Pick   │  ← 5 workers poll for work every 30s
│  Up Tasks       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Implement      │  ← Each worker:
│  Features       │     • Clones repo
│                 │     • Implements feature
│                 │     • Creates PR with needs-review label
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Human Review   │  ← python review_prs.py --list
│  PRs            │     • Review code changes
└────────┬────────┘     • Test functionality
         │
         ▼
┌─────────────────┐
│  Approve or     │  ← Approve: adds approved-for-merge label
│  Request        │     Request changes: adds changes-requested label
│  Changes        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Merge PRs      │  ← python review_prs.py --approve N --merge
│                 │     OR gh pr merge N --squash
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Complete App   │  ✅
└─────────────────┘
```

## Tips for Success

### Writing Good Project Descriptions

Be specific about:
- **Features**: What functionality do you want?
- **Technology**: What stack/languages to use?
- **Constraints**: Mobile-friendly? No frameworks? Specific design?
- **Quality**: Testing? Documentation? Code style?

**Good example:**
```
Build a todo list web app with:
- Add/delete/edit todos
- Mark as complete
- Filter by status (all/active/completed)
- Local storage persistence
- Responsive design
- Use vanilla JavaScript (ES6+)
- Clean, modern UI with CSS Grid
```

**Less helpful:**
```
Make a todo app
```

### Organizing Issues

Use optional labels for better tracking:

```bash
# Add labels when creating issues
gh issue edit 1 --repo YourUsername/calculator-app \
  --add-label "priority: high" \
  --add-label "complexity: simple"
```

### Managing Queue and Reviews

The cluster intelligently blocks new work to prevent review overload:

```bash
# Check if queue is blocked
curl http://192.168.100.200:8000/health | jq '.pr_review'

# See why queue is blocked
{
  "pending_prs": 5,
  "queue_blocked": true,
  "blocking_reason": "Too many pending PRs: #1, #2, #3, #4, #5..."
}

# Review and approve to unblock
python review_prs.py --repo YourUsername/calculator-app --list
python review_prs.py --repo YourUsername/calculator-app --approve 1,2,3 --merge
```

**Configuration** (in orchestrator `.env`):
```bash
# Max PRs before blocking (default: 5)
MAX_PENDING_PRS=5

# Block when changes requested (default: true)
BLOCK_ON_CHANGES_REQUESTED=true

# Allow parallel independent work (default: true)
ALLOW_PARALLEL_INDEPENDENT=true
```

See [Queue Blocking Strategy](QUEUE_BLOCKING_STRATEGY.md) for full details.

### Handling Failed Issues

If a worker fails (check logs):

```bash
# View failed issues
gh issue list --repo YourUsername/calculator-app --label ai-failed

# Worker will add a comment explaining the failure
gh issue view 5 --repo YourUsername/calculator-app

# Options:
# 1. Add more details to the issue description
# 2. Remove ai-failed, add ai-ready to retry
# 3. Implement it manually
```

### Scaling the Cluster

Need faster processing?

```bash
# On Proxmox host
cd /root/ai-scrum-master-v2/deployment/proxmox

# Deploy more workers (update IDs as needed)
# Edit deploy_lxc_cluster.sh to add workers 206, 207, etc.
```

## Next Steps

- 📖 Read [CLUSTER_WORKFLOW.md](CLUSTER_WORKFLOW.md) for advanced workflows
- 🔧 Customize worker behavior by editing worker configuration
- 📊 Build dashboards to monitor cluster performance
- 🚀 Scale up to build multiple projects simultaneously

## Troubleshooting

### Issues Not Being Picked Up

```bash
# 1. Check orchestrator is running
curl http://192.168.100.200:8000/health

# 2. Verify repo is being monitored
curl http://192.168.100.200:8000/health | jq '.github.repositories'

# 3. Check issue has ai-ready label
gh issue view 1 --repo YourUsername/calculator-app --json labels

# 4. Check orchestrator logs
./view_logs.sh orchestrator
```

### Workers Not Completing Tasks

```bash
# 1. Check worker logs
./view_logs.sh worker1

# 2. Verify workers are registered
curl http://192.168.100.200:8000/workers | jq

# 3. Check worker has correct permissions
pct exec 201 -- su - aimaster -c "cat ai-scrum-master-v2/.env | grep GITHUB"
```

### Pull Requests Not Being Created

Check worker logs for errors:
```bash
./view_logs.sh worker1 | grep -i error
```

Common issues:
- Missing GITHUB_TOKEN
- Insufficient permissions on token
- Repository not cloneable
- Git configuration issues

## Support

- 📖 Documentation: [docs/](../docs/)
- 🐛 Issues: https://github.com/SimmoRice/ai-scrum-master-v2/issues
- 💬 Discussions: GitHub Discussions

Happy building! 🚀
