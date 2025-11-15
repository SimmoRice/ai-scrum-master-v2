# Complete Deployment Checklist

Run these steps in order to deploy all fixes and get the cluster working.

## Prerequisites

- [ ] SSH access to Proxmox host
- [ ] GitHub token with `repo` scope
- [ ] Access to both repositories: ai-scrum-master-v2 and taskmaster-app

## Step 1: Check Current Status

On Proxmox host:

```bash
ssh root@your-proxmox-host
cd /root/ai-scrum-master-v2/deployment/proxmox

# Run check script
./check_tokens.sh
```

**Expected Issues:**
- ❌ Token may be invalid or have wrong scopes
- ❌ Workspace paths may be wrong
- ❌ Code version may be outdated

## Step 2: Update Code

```bash
# Update orchestrator
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && git pull origin main"

# Update all workers
for id in 201 202 203 204 205; do
    echo "Updating worker $id..."
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git pull origin main"
done
```

**Verify:**
```bash
# Check orchestrator version
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && git log --oneline -1"

# Should show: a296b43 FIX: Clone GitHub repositories instead of initializing empty repos
```

## Step 3: Fix GitHub Tokens

```bash
# On Proxmox host
ssh root@your-proxmox-host
cd /root/ai-scrum-master-v2/deployment/proxmox

# Replace YOUR_TOKEN with your actual GitHub token
./fix_github_tokens.sh ghp_YOUR_TOKEN_HERE
```

**This script will:**
- ✅ Validate your token
- ✅ Check token scopes
- ✅ Update orchestrator .env
- ✅ Update all worker .env files
- ✅ Update all worker systemd services
- ✅ Restart all services
- ✅ Test GitHub access

## Step 4: Fix Workspace Paths

```bash
# Fix workspace directories on all workers
for id in 201 202 203 204 205; do
    echo "=== Fixing Worker $id ==="

    # Stop service
    pct exec $id -- systemctl stop ai-worker

    # Update .env
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^WORKSPACE_DIR=/d' .env && echo 'WORKSPACE_DIR=/opt/ai-scrum-master/workspace' >> .env"

    # Update systemd service
    pct exec $id -- sed -i 's|Environment=WORKSPACE_DIR=/home/aimaster/workspace|Environment=WORKSPACE_DIR=/opt/ai-scrum-master/workspace|' /etc/systemd/system/ai-worker.service

    # Create workspace directory
    pct exec $id -- mkdir -p /opt/ai-scrum-master/workspace
    pct exec $id -- chown -R aimaster:aimaster /opt/ai-scrum-master

    # Reload and restart
    pct exec $id -- systemctl daemon-reload
    pct exec $id -- systemctl start ai-worker

    sleep 2

    # Verify
    echo "Checking workspace path:"
    pct exec $id -- journalctl -u ai-worker --since "5 seconds ago" --no-pager | grep "Workspace:" | tail -1
    echo ""
done
```

**Verify:**
Should see: `INFO - Workspace: /opt/ai-scrum-master/workspace` (NOT /home/aimaster/workspace)

## Step 5: Verify All Services Running

```bash
# Check orchestrator
echo "Orchestrator:"
pct exec 200 -- systemctl status ai-orchestrator --no-pager | head -5

# Check workers
for id in 201 202 203 204 205; do
    echo "Worker $id:"
    pct exec $id -- systemctl status ai-worker --no-pager | head -3
done

# Check orchestrator health endpoint
curl http://192.168.100.200:8000/health | jq '.'
```

**Expected:**
- ✅ Orchestrator: active (running)
- ✅ All workers: active (running)
- ✅ Health endpoint returns JSON with pr_review section

## Step 6: Reset Failed Issues

On your **local machine**:

```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Development/repos/ai-scrum-master-v2

# List failed issues
gh issue list --repo SimmoRice/taskmaster-app --label ai-failed

# Reset all failed issues to ai-ready
gh issue list --repo SimmoRice/taskmaster-app --label ai-failed --json number --jq '.[].number' | while read num; do
    echo "Resetting issue #$num..."
    gh issue edit $num --repo SimmoRice/taskmaster-app \
        --remove-label ai-failed \
        --add-label ai-ready
done
```

**Verify:**
```bash
# Check that issues are now ai-ready
gh issue list --repo SimmoRice/taskmaster-app --label ai-ready
```

## Step 7: Monitor System

Open 3 terminals:

**Terminal 1: Orchestrator logs**
```bash
ssh root@your-proxmox-host
pct exec 200 -- journalctl -u ai-orchestrator -f
```

**Terminal 2: Worker logs**
```bash
ssh root@your-proxmox-host
pct exec 201 -- journalctl -u ai-worker -f
```

**Terminal 3: Queue status**
```bash
ssh root@your-proxmox-host
watch -n 5 'curl -s http://192.168.100.200:8000/health | jq ".pr_review"'
```

## Step 8: Watch for Success

You should see:

**In orchestrator logs:**
- ✅ `"Detected new issue #N"`
- ✅ `"Added to queue"`
- ✅ `"Assigned issue #N to worker-01"`

**In worker logs:**
- ✅ `"🚀 Starting workflow for issue #N"`
- ✅ `"🔧 Cloning repository: https://github.com/SimmoRice/taskmaster-app.git"`
- ✅ `"✅ Repository cloned to /opt/ai-scrum-master/workspace/issue-N"`
- ✅ `"✨ Workflow completed: APPROVED"`
- ✅ `"📤 Creating pull request"`
- ✅ `"✅ Issue #N completed: https://github.com/SimmoRice/taskmaster-app/pull/N"`

**On GitHub:**
- ✅ PRs appearing with `needs-review` label
- ✅ Issues moving from `ai-ready` to `ai-in-progress` to `ai-completed`

## Step 9: Test PR Review Workflow

Once you have a few PRs:

```bash
# List PRs needing review
python review_prs.py --repo SimmoRice/taskmaster-app --list

# Approve and merge a PR
python review_prs.py --repo SimmoRice/taskmaster-app --approve 1 --merge

# Request changes on a PR
python review_prs.py --repo SimmoRice/taskmaster-app --request-changes 2 \
    --comment "Please add error handling"
```

**Expected:**
- ✅ Queue blocks when MAX_PENDING_PRS reached (default: 5)
- ✅ Queue blocks immediately when changes requested
- ✅ Queue unblocks after approving/merging PRs

## Troubleshooting

### Issue: Workers not picking up tasks

**Check:**
```bash
# Orchestrator health
curl http://192.168.100.200:8000/health | jq '.github'

# Should show both repositories
# "repositories": ["SimmoRice/ai-scrum-master-v2", "SimmoRice/taskmaster-app"]
```

**Fix:**
```bash
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    sed -i '/^GITHUB_REPOS=/d' .env
    echo 'GITHUB_REPOS=SimmoRice/ai-scrum-master-v2,SimmoRice/taskmaster-app' >> .env
"
pct exec 200 -- systemctl restart ai-orchestrator
```

### Issue: Git clone failures

**Check worker logs:**
```bash
pct exec 201 -- journalctl -u ai-worker -n 50 --no-pager | grep -i "clone\|error"
```

**Common causes:**
- ❌ Invalid GitHub token
- ❌ Token missing `repo` scope
- ❌ Token doesn't have access to repository

**Fix:**
```bash
# Generate new token at https://github.com/settings/tokens/new
# Make sure to select "repo" scope
# Then run:
/root/fix_github_tokens.sh ghp_NEW_TOKEN
```

### Issue: Workspace permission errors

**Check:**
```bash
pct exec 201 -- ls -la /opt/ai-scrum-master/
```

**Fix:**
```bash
for id in 201 202 203 204 205; do
    pct exec $id -- chown -R aimaster:aimaster /opt/ai-scrum-master
done
```

## Success Criteria

- [ ] Orchestrator running and healthy
- [ ] All 5 workers running
- [ ] Workers can clone repositories
- [ ] Workers successfully complete tasks
- [ ] PRs created with `needs-review` label
- [ ] PR review workflow functional
- [ ] Queue blocking works at threshold
- [ ] Queue blocks when changes requested

## Next Steps After Success

1. Monitor cluster performance
2. Test queue blocking with real PRs
3. Tune MAX_PENDING_PRS based on review capacity
4. Scale workers if needed (add more containers)
5. Set up monitoring dashboards

---

**Generated:** 2025-11-15
**Commit:** a296b43 (repository cloning fix)
