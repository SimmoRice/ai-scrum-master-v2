# Quick Fix Guide - Get Cluster Working NOW

## TL;DR - Run These Commands

### On Proxmox Host

```bash
ssh root@YOUR_PROXMOX_IP
cd /root/ai-scrum-master-v2/deployment/proxmox

# 1. Check current status
./check_tokens.sh

# 2. Update code on all containers
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && git pull origin main"
for id in 201 202 203 204 205; do
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git pull origin main"
done

# 3. Fix GitHub tokens (replace with your token)
./fix_github_tokens.sh ghp_YOUR_TOKEN_HERE

# 4. Fix workspace paths (already done by fix_github_tokens.sh, but here for reference)
for id in 201 202 203 204 205; do
    pct exec $id -- systemctl stop ai-worker
    pct exec $id -- sed -i 's|Environment=WORKSPACE_DIR=/home/aimaster/workspace|Environment=WORKSPACE_DIR=/opt/ai-scrum-master/workspace|' /etc/systemd/system/ai-worker.service
    pct exec $id -- mkdir -p /opt/ai-scrum-master/workspace
    pct exec $id -- chown -R aimaster:aimaster /opt/ai-scrum-master
    pct exec $id -- systemctl daemon-reload
    pct exec $id -- systemctl start ai-worker
done

# 5. Verify services
curl http://192.168.100.200:8000/health | jq '.pr_review'
```

### Back on Local Machine

```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Development/repos/ai-scrum-master-v2

# Reset all failed issues
gh issue list --repo SimmoRice/taskmaster-app --label ai-failed --json number --jq '.[].number' | while read num; do
    gh issue edit $num --repo SimmoRice/taskmaster-app --remove-label ai-failed --add-label ai-ready
done

# Watch for PRs
watch -n 10 'gh pr list --repo SimmoRice/taskmaster-app'
```

## What Each Fix Does

### Fix 1: Code Update (a296b43)
**Problem:** Workers initialized empty repos instead of cloning from GitHub
**Fix:** Added repository cloning functionality
**Impact:** Workers can now work on external repositories

### Fix 2: GitHub Token
**Problem:** Token may be invalid, expired, or missing `repo` scope
**Fix:** Validates and updates token on all containers
**Impact:** Workers can clone, push, and create PRs

### Fix 3: Workspace Path
**Problem:** Workers using `/home/aimaster/workspace` (blocked for security)
**Fix:** Updates to `/opt/ai-scrum-master/workspace`
**Impact:** Workers can create workspaces without security errors

## Expected Timeline

- **Minute 0:** Deploy fixes
- **Minute 1-2:** Workers start picking up issues
- **Minute 5-10:** First repository clones complete
- **Minute 10-30:** First PRs created
- **Minute 30+:** Queue blocking kicks in (after 5 PRs by default)

## Success Indicators

✅ **Orchestrator logs show:**
```
Detected new issue #1
Added to queue
Assigned issue #1 to worker-01
```

✅ **Worker logs show:**
```
🚀 Starting workflow for issue #1
🔧 Cloning repository: https://github.com/SimmoRice/taskmaster-app.git
✅ Repository cloned to /opt/ai-scrum-master/workspace/issue-1
✨ Workflow completed: APPROVED
📤 Creating pull request
✅ Issue #1 completed: https://github.com/SimmoRice/taskmaster-app/pull/1
```

✅ **GitHub shows:**
- Issues moving from `ai-ready` → `ai-in-progress` → `ai-completed`
- Pull requests with `needs-review` label
- Code changes in PRs

## If Something's Still Wrong

### Workers Still Failing?

```bash
# Check worker logs for errors
pct exec 201 -- journalctl -u ai-worker -n 100 --no-pager

# Common errors and fixes:
# - "git checkout main failed" → Code update needed
# - "403 Forbidden" → Token issue
# - "Security: Workspace path" → Workspace path issue
# - "No module named 'requests'" → pip install requests
```

### Token Issues?

```bash
# Test token locally first
curl -H "Authorization: token ghp_YOUR_TOKEN" https://api.github.com/user

# Should return your user info, not 401/403
```

### Orchestrator Not Assigning Work?

```bash
# Check multi-repo config
curl http://192.168.100.200:8000/health | jq '.github.repositories'

# Should show: ["SimmoRice/ai-scrum-master-v2", "SimmoRice/taskmaster-app"]

# If not, fix it:
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    sed -i '/^GITHUB_REPOS=/d' .env
    echo 'GITHUB_REPOS=SimmoRice/ai-scrum-master-v2,SimmoRice/taskmaster-app' >> .env
"
pct exec 200 -- systemctl restart ai-orchestrator
```

## Monitoring Commands

```bash
# Watch orchestrator
pct exec 200 -- journalctl -u ai-orchestrator -f

# Watch a worker
pct exec 201 -- journalctl -u ai-worker -f

# Watch queue status
watch -n 5 'curl -s http://192.168.100.200:8000/health | jq ".pr_review"'

# Watch GitHub PRs
watch -n 10 'gh pr list --repo SimmoRice/taskmaster-app'
```

## Review PRs When Ready

```bash
# List PRs needing review
python review_prs.py --repo SimmoRice/taskmaster-app --list

# Approve and merge
python review_prs.py --repo SimmoRice/taskmaster-app --approve 1,2,3 --merge

# Request changes
python review_prs.py --repo SimmoRice/taskmaster-app --request-changes 4 \
    --comment "Please add error handling for edge cases"
```

## Files You Need

All fix scripts are in the repo root:
- `check_tokens.sh` - Check token status on all containers
- `fix_github_tokens.sh` - Update tokens everywhere
- `DEPLOYMENT_CHECKLIST.md` - Detailed step-by-step guide
- `URGENT_UPDATE.md` - Quick deployment instructions

## Still Stuck?

1. Check [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) for detailed steps
2. Review orchestrator logs: `pct exec 200 -- journalctl -u ai-orchestrator -n 100`
3. Review worker logs: `pct exec 201 -- journalctl -u ai-worker -n 100`
4. Verify GitHub token scopes at https://github.com/settings/tokens

---

**Key Commit:** a296b43 - FIX: Clone GitHub repositories instead of initializing empty repos
