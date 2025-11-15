# Immediate Fix Steps - You're Currently in Python!

## Current Problem
You're in a Python interpreter (>>>), but you need to run bash commands on your Proxmox host.

## STEP 1: Exit Python Interpreter

In your terminal, type one of these:
```
exit()
```
OR press `Ctrl+D`

## STEP 2: Verify You're in Bash

You should see a bash prompt like:
```
root@proxmox:~#
```

## STEP 3: Transfer the Fix Script to Proxmox

On your **local machine** (Mac), run:
```bash
cd ~/Library/Mobile\ Documents/com~apple~CloudDocs/Development/repos/ai-scrum-master-v2
scp fix_deployment.sh root@your-proxmox-host:/root/
```

## STEP 4: Run the Fix Script on Proxmox

SSH to Proxmox (if not already there):
```bash
ssh root@your-proxmox-host
```

Make script executable and run:
```bash
chmod +x /root/fix_deployment.sh
/root/fix_deployment.sh
```

## OR: Manual Fix (If Script Doesn't Work)

### Fix 1: Update Workspace Directory on Workers
```bash
for id in 201 202 203 204 205; do
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^WORKSPACE_DIR=/d' .env && echo 'WORKSPACE_DIR=/opt/ai-scrum-master/workspace' >> .env"
done
```

### Fix 2: Configure Multi-Repo Mode
```bash
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^GITHUB_REPOS=/d' .env && echo 'GITHUB_REPOS=SimmoRice/ai-scrum-master-v2,SimmoRice/taskmaster-app' >> .env && sed -i '/^GITHUB_REPO=/d' .env"
```

### Fix 3: Update GitHub Token

First, create a new token at: https://github.com/settings/tokens/new
- Description: AI Scrum Master Cluster
- Scopes: Check "repo" (full control)

Then update on orchestrator:
```bash
# Replace YOUR_TOKEN_HERE with actual token
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^GITHUB_TOKEN=/d' .env && echo 'GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE' >> .env"
```

### Fix 4: Restart Services
```bash
# Restart orchestrator
pct exec 200 -- systemctl restart ai-orchestrator
sleep 5

# Restart workers
for id in 201 202 203 204 205; do
    pct exec $id -- systemctl restart ai-worker
done
sleep 10
```

### Fix 5: Verify
```bash
# Check orchestrator health
curl http://192.168.100.200:8000/health | jq '.pr_review'

# Check workers
curl http://192.168.100.200:8000/workers | jq '.workers | length'

# Check logs
cd /root/ai-scrum-master-v2/deployment/proxmox
./view_logs.sh orchestrator | tail -50
```

## What These Fixes Do

1. **Workspace Directory**: Sets correct path `/opt/ai-scrum-master/workspace` so workers can clone repos safely
2. **Multi-Repo Mode**: Configures orchestrator to monitor both `ai-scrum-master-v2` AND `taskmaster-app`
3. **GitHub Token**: Updates token with proper permissions to access both repositories
4. **Service Restart**: Applies all configuration changes

## Expected Results After Fix

✅ No more "Security: Workspace path cannot be in system directory" errors
✅ No more "403 Forbidden" GitHub API errors
✅ Orchestrator monitors both repositories
✅ Workers can pick up issues from taskmaster-app
✅ PRs get created successfully

## Monitoring Commands

```bash
# Watch queue status
watch -n 5 'curl -s http://192.168.100.200:8000/health | jq ".pr_review"'

# View orchestrator logs
cd /root/ai-scrum-master-v2/deployment/proxmox
./view_logs.sh orchestrator

# View worker logs
./view_logs.sh worker1

# List PRs needing review
python ~/Development/repos/ai-scrum-master-v2/review_prs.py --repo SimmoRice/taskmaster-app --list
```
