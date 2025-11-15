# Deploy Queue Blocking Update to Proxmox Cluster

This guide walks you through deploying the new PR review and queue blocking features to your Proxmox cluster.

## What's Being Deployed

- ✅ PR Review Tracker system
- ✅ Intelligent queue blocking
- ✅ Enhanced orchestrator with new API endpoints
- ✅ Updated worker with needs-review label
- ✅ Review labels in setup script
- ✅ Comprehensive documentation

## Prerequisites

- Proxmox cluster running (containers 200-205)
- SSH access to Proxmox host
- All workers and orchestrator currently running

## Deployment Steps

### Step 1: Update Orchestrator (Container 200)

```bash
# SSH to Proxmox host
ssh root@your-proxmox-host

# Enter orchestrator container
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2

    # Pull latest code
    git pull origin main

    # Install new dependencies (requests for review_prs.py)
    source env/bin/activate
    pip install requests

    # Configure queue blocking (optional - these are defaults)
    echo '' >> .env
    echo '# Queue Blocking Configuration' >> .env
    echo 'MAX_PENDING_PRS=5' >> .env
    echo 'BLOCK_ON_CHANGES_REQUESTED=true' >> .env
    echo 'ALLOW_PARALLEL_INDEPENDENT=true' >> .env
    echo 'ORCHESTRATOR_URL=http://192.168.100.200:8000' >> .env
"

# Restart orchestrator to load new code
pct exec 200 -- systemctl restart ai-orchestrator

# Wait for restart
sleep 5

# Verify orchestrator is running with new features
curl http://192.168.100.200:8000/health | jq '.pr_review'
```

Expected output:
```json
{
  "pending_prs": 0,
  "changes_requested": 0,
  "approved": 0,
  "queue_blocked": false,
  "blocking_reason": null
}
```

### Step 2: Update Workers (Containers 201-205)

```bash
# Update all workers
for id in 201 202 203 204 205; do
    echo "Updating worker container $id..."
    pct exec $id -- su - aimaster -c "
        cd ai-scrum-master-v2
        git pull origin main
    "

    # Restart worker service
    pct exec $id -- systemctl restart ai-worker

    echo "Worker $id updated"
done

# Wait for all workers to restart
sleep 10

# Verify workers are registered
curl http://192.168.100.200:8000/workers | jq '.workers | length'
```

Expected output: `5` (all workers registered)

### Step 3: Update Local Review Script

On your **local machine** (not Proxmox):

```bash
cd ~/Development/repos/ai-scrum-master-v2

# Pull latest code
git pull origin main

# Install requests library
pip install requests

# Optional: Configure custom orchestrator URL
echo 'ORCHESTRATOR_URL=http://192.168.100.200:8000' >> .env

# Test the review script
python review_prs.py --help
```

### Step 4: Setup Labels for Existing Repositories

Update all your monitored repositories with the new review labels:

```bash
cd ~/Development/repos/ai-scrum-master-v2

# Setup labels for all monitored repos
python setup_repo_labels.py --all

# Or setup for specific repos
python setup_repo_labels.py --repo YOUR_USERNAME/repo-name
```

This adds the new labels:
- `needs-review` (orange)
- `approved-for-merge` (green)
- `changes-requested` (red)

### Step 5: Verify Deployment

Run these checks to ensure everything is working:

```bash
# 1. Check orchestrator health
curl http://192.168.100.200:8000/health | jq

# Should see pr_review section in response

# 2. Check new PR review endpoint
curl http://192.168.100.200:8000/pr-review/status | jq

# Should return tracker status

# 3. Check all workers are active
curl http://192.168.100.200:8000/workers | jq

# Should see 5 workers

# 4. Test review script (on local machine)
python review_prs.py --all --list

# Should connect to orchestrator successfully
```

## Configuration Options

You can tune the queue blocking behavior by editing orchestrator's `.env`:

```bash
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    nano .env
"
```

### Conservative (Production)
```bash
MAX_PENDING_PRS=3              # Block after 3 PRs
BLOCK_ON_CHANGES_REQUESTED=true # Always block when changes requested
ALLOW_PARALLEL_INDEPENDENT=false # No parallel work, sequential only
```

### Balanced (Default - Recommended)
```bash
MAX_PENDING_PRS=5              # Block after 5 PRs
BLOCK_ON_CHANGES_REQUESTED=true # Always block when changes requested
ALLOW_PARALLEL_INDEPENDENT=true # Allow independent features in parallel
```

### Aggressive (High Throughput)
```bash
MAX_PENDING_PRS=10             # Block after 10 PRs
BLOCK_ON_CHANGES_REQUESTED=false # Don't auto-block on changes
ALLOW_PARALLEL_INDEPENDENT=true # Allow independent features in parallel
```

After changing configuration:
```bash
pct exec 200 -- systemctl restart ai-orchestrator
```

## Testing the Deployment

### Quick Test

Create a test repository with a few issues:

```bash
# On local machine
cd ~/Development/repos/ai-scrum-master-v2

# Run the automated test
./test_queue_blocking.sh YOUR_USERNAME/test-queue-blocking
```

This will:
1. Create a test repository
2. Setup labels
3. Generate ~20 test issues
4. Show you monitoring commands

### Watch Queue Blocking in Action

```bash
# Terminal 1: Watch queue status
watch -n 5 'curl -s http://192.168.100.200:8000/health | jq ".pr_review"'

# Terminal 2: Watch workers
watch -n 5 'curl -s http://192.168.100.200:8000/workers | jq'

# Terminal 3: Watch PRs needing review
watch -n 10 'python review_prs.py --all --list'
```

### Test Queue Blocking

```bash
# Wait for workers to create PRs
# Once you hit MAX_PENDING_PRS, queue should block

# Check blocking status
curl http://192.168.100.200:8000/health | jq '.pr_review'

# Should show:
# {
#   "queue_blocked": true,
#   "blocking_reason": "Too many pending PRs: #1, #2, #3..."
# }

# Approve some PRs to unblock
python review_prs.py --repo YOUR_USERNAME/test-repo --approve 1,2 --merge

# Queue should unblock
```

## Rollback (If Needed)

If you encounter issues and need to rollback:

```bash
# On Proxmox host

# Rollback orchestrator
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    git checkout 9219184  # Previous commit before queue blocking
"
pct exec 200 -- systemctl restart ai-orchestrator

# Rollback workers
for id in 201 202 203 204 205; do
    pct exec $id -- su - aimaster -c "
        cd ai-scrum-master-v2
        git checkout 9219184
    "
    pct exec $id -- systemctl restart ai-worker
done
```

## Troubleshooting

### Orchestrator won't start

```bash
# Check logs
pct exec 200 -- journalctl -u ai-orchestrator -n 50

# Common issues:
# - Missing GITHUB_TOKEN in .env
# - Python import errors (missing dependencies)
```

### PR tracker not working

```bash
# Check if pr_review appears in health endpoint
curl http://192.168.100.200:8000/health | jq '.pr_review'

# If missing, check orchestrator logs
pct exec 200 -- journalctl -u ai-orchestrator -f | grep -i "pr"
```

### Review script can't connect to orchestrator

```bash
# Test connection
curl http://192.168.100.200:8000/health

# If fails:
# 1. Check orchestrator is running
# 2. Check firewall allows port 8000
# 3. Verify ORCHESTRATOR_URL in .env
```

### Queue not blocking

```bash
# Check configuration
curl http://192.168.100.200:8000/pr-review/status | jq '.config'

# Verify MAX_PENDING_PRS is set correctly
pct exec 200 -- su - aimaster -c "cat ai-scrum-master-v2/.env | grep MAX_PENDING"
```

## Post-Deployment Checklist

- [ ] Orchestrator running with pr_review in health check
- [ ] All 5 workers registered and active
- [ ] New API endpoint `/pr-review/status` accessible
- [ ] Local review script can connect to orchestrator
- [ ] All monitored repos have new review labels
- [ ] Test repository successfully blocks queue
- [ ] Review workflow tested (approve/request changes/merge)

## Documentation

After deployment, these docs are available:

- **[QUEUE_BLOCKING_STRATEGY.md](docs/QUEUE_BLOCKING_STRATEGY.md)** - How queue blocking works
- **[PR_REVIEW_WORKFLOW.md](docs/PR_REVIEW_WORKFLOW.md)** - How to review PRs
- **[GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Complete workflow guide
- **[REVIEW_BLOCKING_SUMMARY.md](REVIEW_BLOCKING_SUMMARY.md)** - Quick reference

## Support

If you encounter issues:

1. Check orchestrator logs: `pct exec 200 -- journalctl -u ai-orchestrator -n 100`
2. Check worker logs: `pct exec 201 -- journalctl -u ai-worker -n 100`
3. Verify configuration: `curl http://192.168.100.200:8000/pr-review/status`
4. Review documentation in `docs/` folder

## Next Steps

Once deployed and tested:

1. Run the comprehensive test: `./test_queue_blocking.sh YOUR_USERNAME/taskmaster-app`
2. Monitor queue blocking with real projects
3. Tune MAX_PENDING_PRS based on your review capacity
4. Set up monitoring dashboards for PR status

Happy deploying! 🚀
