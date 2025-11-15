# URGENT: Critical Fix for Repository Cloning

## What Was Fixed

All issues were failing with `git checkout main` errors because workers were **initializing empty repositories** instead of **cloning from GitHub**.

The fix:
✅ Workers now clone the actual GitHub repository
✅ Git operations work correctly (checkout, branch, push, PR)
✅ External repositories (like taskmaster-app) now work properly

## IMPORTANT: GitHub Token Check

You mentioned token issues. Before deploying, ensure your GitHub token has:
- ✅ `repo` scope (full control)
- ✅ Access to both `ai-scrum-master-v2` AND `taskmaster-app` repositories

### Quick Token Fix (If Needed)

If you need to update tokens:

```bash
# On Proxmox host
ssh root@your-proxmox-host
cd /root/ai-scrum-master-v2/deployment/proxmox

# Run the token fix script
./fix_github_tokens.sh YOUR_GITHUB_TOKEN
```

This will:
- ✅ Validate token is working
- ✅ Check token scopes
- ✅ Update orchestrator token
- ✅ Update all worker tokens (both .env and systemd)
- ✅ Restart services
- ✅ Test GitHub access

## Deploy This Fix NOW

### Step 1: Update Code on Proxmox

On your Proxmox host:

```bash
# Update orchestrator (container 200)
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && git pull origin main"

# Update all workers (containers 201-205)
for id in 201 202 203 204 205; do
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git pull origin main"
done
```

### Step 2: Restart Services

```bash
# Restart orchestrator
pct exec 200 -- systemctl restart ai-orchestrator
sleep 5

# Restart all workers
for id in 201 202 203 204 205; do
    pct exec $id -- systemctl restart ai-worker
    sleep 2
done
```

### Step 3: Clear Failed Issues and Retry

All the taskmaster-app issues are marked as `ai-failed`. We need to reset them:

```bash
# On your local machine
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Development/repos/ai-scrum-master-v2

# List all failed issues
gh issue list --repo SimmoRice/taskmaster-app --label ai-failed

# Reset each failed issue (replace NUMBER with actual issue numbers)
gh issue edit NUMBER --repo SimmoRice/taskmaster-app --remove-label ai-failed --add-label ai-ready

# Or reset all at once (if you have jq installed)
gh issue list --repo SimmoRice/taskmaster-app --label ai-failed --json number --jq '.[].number' | while read num; do
    echo "Resetting issue #$num..."
    gh issue edit $num --repo SimmoRice/taskmaster-app --remove-label ai-failed --add-label ai-ready
done
```

### Step 4: Verify It's Working

```bash
# Watch orchestrator logs for new work
pct exec 200 -- journalctl -u ai-orchestrator -f

# In another terminal, watch worker logs
pct exec 201 -- journalctl -u ai-worker -f

# You should see:
# ✅ "Cloning repository: https://github.com/SimmoRice/taskmaster-app.git"
# ✅ "Repository cloned to /opt/ai-scrum-master/workspace/issue-N"
# ✅ No more "git checkout main" errors
```

## What Changed

**Before:**
```python
# Worker created empty workspace
orchestrator = AIScrumOrchestrator(workspace_dir=workspace)
# This initialized a NEW empty git repo ❌
```

**After:**
```python
# Worker passes repository URL
repo_url = f"https://github.com/{repository}.git"
orchestrator = AIScrumOrchestrator(
    workspace_dir=workspace,
    repository_url=repo_url  # ✅ Clones the actual repo
)
```

## Commit Details

- Commit: `a296b43`
- Files changed:
  - `git_manager.py` - Added `clone_repository()` method
  - `orchestrator.py` - Added `repository_url` parameter
  - `worker/distributed_worker.py` - Pass repo URL to orchestrator

## Verification Commands

After deploying, verify workers can clone repos:

```bash
# Check a worker log for successful clone
pct exec 201 -- journalctl -u ai-worker -n 100 --no-pager | grep -i "clon"

# Should see something like:
# "🔧 Cloning repository: https://github.com/SimmoRice/taskmaster-app.git"
# "✅ Repository cloned to /opt/ai-scrum-master/workspace/issue-1"
```

## Next Steps After Fix

1. Deploy the update (commands above)
2. Reset failed issues to `ai-ready`
3. Monitor workers picking up issues
4. Watch for successful PRs being created
5. Test the PR review workflow

The queue blocking system is already deployed, so once PRs start getting created, you can test the approval workflow!
