# AI Scrum Cluster Workflow

This guide shows how to use the distributed AI Scrum Master cluster to build entire projects.

## Quick Start: Build a Calculator App

### Step 1: Create a Calculator Repository

First, create a new GitHub repository for your calculator app:

```bash
gh repo create your-username/calculator-app --public --clone
cd calculator-app
echo "# Calculator App" > README.md
git add README.md
git commit -m "Initial commit"
git push origin main
```

### Step 2: Setup Repository Labels

Setup the required labels for the AI cluster workflow:

```bash
cd ~/Development/repos/ai-scrum-master-v2

# Setup labels for calculator app
python setup_repo_labels.py --repo your-username/calculator-app

# Or setup for all monitored repos at once
python setup_repo_labels.py --all

# Include optional organization labels (priority, complexity, type)
python setup_repo_labels.py --repo your-username/calculator-app --include-optional
```

This creates the required labels:
- `ai-ready` - Issues ready for workers to pick up
- `ai-in-progress` - Currently being worked on
- `ai-completed` - Successfully completed
- `ai-failed` - Worker failed to complete

### Step 3: Configure Cluster for Multi-Repo

Add the calculator repo to your cluster's monitored repositories:

```bash
# On Proxmox host
cd /root/ai-scrum-master-v2/deployment/proxmox
./configure_multi_repo.sh "SimmoRice/ai-scrum-master-v2,your-username/calculator-app"
```

Or manually update the orchestrator's .env:

```bash
# On container 200
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    echo 'GITHUB_REPOS=SimmoRice/ai-scrum-master-v2,your-username/calculator-app' >> .env
"
pct exec 200 -- systemctl restart ai-orchestrator
```

### Step 4: Break Down Project into Issues

Use the `create_project_issues.py` script to automatically break down your project:

```bash
cd ~/Development/repos/ai-scrum-master-v2

# Option 1: One-liner description
python create_project_issues.py \
  --repo your-username/calculator-app \
  --project "Build a web-based calculator with basic arithmetic operations, history, and dark mode"

# Option 2: From detailed description file
cat > calculator_requirements.txt << 'EOF'
Build a modern web-based calculator application with the following features:

Core Features:
- Basic arithmetic operations (+, -, ×, ÷)
- Decimal point support
- Clear and backspace functions
- Keyboard support
- Calculation history (last 10 calculations)
- Dark/light mode toggle

Technical Requirements:
- Use HTML, CSS, and vanilla JavaScript
- Responsive design (mobile-friendly)
- Clean, modern UI
- Local storage for theme preference
- No external dependencies
EOF

python create_project_issues.py \
  --repo your-username/calculator-app \
  --project-file calculator_requirements.txt
```

This will:
1. Use Claude AI to break down the project into individual tasks
2. Create GitHub issues for each task
3. Automatically add the `ai-ready` label
4. The cluster will pick them up within 60 seconds

### Step 5: Monitor Progress

Watch the cluster work on your issues:

```bash
# Check cluster health and queue
curl http://192.168.100.200:8000/health | jq

# Check what workers are doing
curl http://192.168.100.200:8000/workers | jq

# View orchestrator logs
cd /root/ai-scrum-master-v2/deployment/proxmox
./view_logs.sh orchestrator

# View worker logs
./view_logs.sh all
```

Check GitHub issues:
```bash
# List issues being worked on
gh issue list --repo your-username/calculator-app --label ai-in-progress

# List completed issues
gh issue list --repo your-username/calculator-app --label ai-completed --state all
```

### Step 6: Review Pull Requests

As workers complete tasks, they create pull requests:

```bash
# List PRs
gh pr list --repo your-username/calculator-app

# Review a specific PR
gh pr view 1 --repo your-username/calculator-app

# Merge a PR
gh pr merge 1 --repo your-username/calculator-app --squash
```

## Advanced Workflows

### Custom Issue Breakdown

Create your own issues manually if you prefer more control:

```bash
gh issue create \
  --repo your-username/calculator-app \
  --title "Setup project structure" \
  --body "Create HTML, CSS, and JS files with basic boilerplate" \
  --label "ai-ready"
```

### Dependencies Between Tasks

Specify dependencies in issue body:

```bash
gh issue create \
  --repo your-username/calculator-app \
  --title "Implement calculation logic" \
  --body "Add JavaScript functions for arithmetic operations

**Dependencies:** #1 (Setup project structure)
**Priority:** High
**Complexity:** Medium" \
  --label "ai-ready"
```

### Testing Before Deployment

Create issues without `ai-ready` label first, then add it when you're ready:

```bash
# Create without ai-ready
python create_project_issues.py \
  --repo your-username/calculator-app \
  --project "Build calculator" \
  --no-ai-ready

# Review issues on GitHub
# Then add ai-ready label when ready:
gh issue edit 1 --repo your-username/calculator-app --add-label "ai-ready"
```

### Monitor Specific Repository

Check issues for a specific repo:

```bash
# View all issues
gh issue list --repo your-username/calculator-app

# View by label
gh issue list --repo your-username/calculator-app --label ai-ready
gh issue list --repo your-username/calculator-app --label ai-in-progress
gh issue list --repo your-username/calculator-app --label ai-completed
```

## Cluster Configuration

### Add/Remove Repositories

Update monitored repositories:

```bash
# Add more repos
./configure_multi_repo.sh "repo1,repo2,repo3,repo4"

# Check current configuration
curl http://192.168.100.200:8000/health | jq '.github'
```

### Adjust Polling Interval

Change how often orchestrator checks for new issues:

```bash
# On orchestrator container
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    echo 'GITHUB_POLL_INTERVAL=30' >> .env  # Check every 30 seconds
"
pct exec 200 -- systemctl restart ai-orchestrator
```

### Scale Workers

Add more workers for faster processing:

```bash
# Deploy additional worker containers
# Update IDs and IPs as needed
./deploy_lxc_cluster.sh

# Workers automatically register with orchestrator
```

## Troubleshooting

### Issues Not Being Picked Up

1. Check orchestrator is monitoring the repo:
   ```bash
   curl http://192.168.100.200:8000/health | jq '.github'
   ```

2. Verify `ai-ready` label exists and is applied:
   ```bash
   gh label list --repo your-username/calculator-app
   gh issue list --repo your-username/calculator-app --label ai-ready
   ```

3. Check orchestrator logs:
   ```bash
   ./view_logs.sh orchestrator
   ```

### Workers Not Completing Tasks

1. Check worker logs:
   ```bash
   ./view_logs.sh worker1
   ```

2. Verify workers have correct permissions:
   ```bash
   # Check .env on workers has GITHUB_TOKEN
   pct exec 201 -- su - aimaster -c "cat ai-scrum-master-v2/.env | grep GITHUB"
   ```

3. Test worker manually:
   ```bash
   pct exec 201 -- su - aimaster -c "
       cd ai-scrum-master-v2
       source env/bin/activate
       python worker/distributed_worker.py
   "
   ```

## Example: Complete Calculator App Workflow

Here's a complete example from start to finish:

```bash
# 1. Create repository
gh repo create myusername/calculator-app --public --clone
cd calculator-app
echo "# Calculator App" > README.md
git add README.md && git commit -m "Initial" && git push

# 2. Configure cluster
cd ~/ai-scrum-master-v2/deployment/proxmox
./configure_multi_repo.sh "SimmoRice/ai-scrum-master-v2,myusername/calculator-app"

# 3. Create issues
cd ~/ai-scrum-master-v2
python create_project_issues.py \
  --repo myusername/calculator-app \
  --project "Build a modern calculator web app with basic operations, history, and dark mode"

# 4. Watch it work!
watch -n 5 'curl -s http://192.168.100.200:8000/health | jq'

# 5. Review PRs as they come in
gh pr list --repo myusername/calculator-app

# 6. Merge completed work
gh pr merge 1 --repo myusername/calculator-app --squash
```

## Tips

- **Start Small**: Begin with 3-5 simple issues to test the workflow
- **Clear Descriptions**: The better your issue descriptions, the better the AI's implementation
- **Review PRs**: Always review pull requests before merging
- **Use Labels**: Tag issues with priority, complexity, etc. for better organization
- **Monitor Queue**: Keep an eye on the queue to see what's pending vs in-progress
- **Scale as Needed**: Add more workers if you have many issues to process
