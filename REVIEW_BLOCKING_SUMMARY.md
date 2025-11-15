# PR Review & Queue Blocking Implementation Summary

## Problem Solved

You identified a critical workflow bottleneck: **workers can continue picking up new issues even when there are unapproved PRs**, leading to:

1. **Cascading bugs**: PR #1 has a bug, PRs #2-5 build on that buggy code
2. **Wasted work**: Workers continue while waiting for review
3. **Review overload**: Too many PRs to review at once
4. **No feedback loop**: Workers don't learn from review comments

## Solution Implemented

### 1. **PR Review Tracker** ([orchestrator_service/pr_review_tracker.py](orchestrator_service/pr_review_tracker.py))

A comprehensive tracking system that:
- Tracks all pending PRs awaiting review
- Blocks queue when thresholds are exceeded
- Supports dependency tracking for parallel independent work
- Provides detailed status and blocking reasons

**Key Features:**
```python
PRReviewTracker(
    max_pending_prs=5,              # Max PRs before blocking
    block_on_changes_requested=True, # Block when changes requested
    allow_parallel_independent=True  # Allow independent features
)
```

### 2. **Orchestrator Integration** ([orchestrator_service/server.py](orchestrator_service/server.py))

Updated orchestrator to:
- Initialize PR tracker on startup with configurable settings
- Check if queue is blocked before assigning work to workers
- Register new PRs when workers complete tasks
- Update PR status via API endpoints
- Include PR review status in health endpoint

**New API Endpoints:**
- `GET /pr-review/status` - Get tracker status and pending PRs
- `POST /pr-review/approved/{issue_number}` - Mark PR approved
- `POST /pr-review/changes-requested/{issue_number}` - Mark changes requested
- `POST /pr-review/merged/{issue_number}` - Mark PR merged

### 3. **Review Script Integration** ([review_prs.py](review_prs.py))

Updated review script to:
- Notify orchestrator when PRs are approved
- Notify orchestrator when changes are requested
- Notify orchestrator when PRs are merged
- Automatically unblock queue when you approve/merge PRs

### 4. **Configuration Options**

Environment variables for orchestrator (`.env`):
```bash
# Maximum pending PRs before blocking queue (default: 5)
MAX_PENDING_PRS=5

# Block all work when changes requested on any PR (default: true)
BLOCK_ON_CHANGES_REQUESTED=true

# Allow work on independent issues while PRs pending (default: true)
ALLOW_PARALLEL_INDEPENDENT=true

# Orchestrator URL for review script notifications
ORCHESTRATOR_URL=http://192.168.100.200:8000
```

## How It Works

### Blocking Scenario 1: Too Many Pending PRs

```
Workers create 5 PRs → Queue BLOCKED
You approve/merge 2 → Queue UNBLOCKED (3/5)
Workers resume processing
```

### Blocking Scenario 2: Changes Requested

```
Worker creates PR → You request changes → Queue IMMEDIATELY BLOCKED
Worker sees comment → Fixes code → Updates PR
You approve → Queue UNBLOCKED
```

### Parallel Independent Work

```
PR #1 pending (Add auth feature)
Issue #2 (Fix typo) → CAN PROCEED (independent)
Issue #3 (Add logout) → BLOCKED (depends on #1)
```

## Configuration Strategies

### Conservative (Production)
```bash
MAX_PENDING_PRS=3
BLOCK_ON_CHANGES_REQUESTED=true
ALLOW_PARALLEL_INDEPENDENT=false
```
Maximum safety, sequential processing

### Balanced (Default)
```bash
MAX_PENDING_PRS=5
BLOCK_ON_CHANGES_REQUESTED=true
ALLOW_PARALLEL_INDEPENDENT=true
```
Good safety with reasonable throughput

### Aggressive (Prototyping)
```bash
MAX_PENDING_PRS=10
BLOCK_ON_CHANGES_REQUESTED=false
ALLOW_PARALLEL_INDEPENDENT=true
```
Maximum throughput, more review burden

## Monitoring

### Check Queue Status
```bash
curl http://192.168.100.200:8000/health | jq '.pr_review'
```

Output:
```json
{
  "pending_prs": 3,
  "changes_requested": 0,
  "approved": 2,
  "queue_blocked": false,
  "blocking_reason": null
}
```

### Check Detailed PR Status
```bash
curl http://192.168.100.200:8000/pr-review/status | jq
```

### Worker Experience When Blocked
```json
{
  "work_available": false,
  "blocked": true,
  "reason": "Too many pending PRs: #1, #2, #3, #4, #5. Review and merge before proceeding (max: 5)."
}
```

## Documentation Created

1. **[QUEUE_BLOCKING_STRATEGY.md](docs/QUEUE_BLOCKING_STRATEGY.md)**
   - Comprehensive guide to queue blocking
   - Configuration strategies
   - Workflow examples
   - API reference
   - Troubleshooting

2. **Updated [GETTING_STARTED.md](docs/GETTING_STARTED.md)**
   - Added queue management section
   - Explained workflow with blocking
   - Configuration examples

3. **Updated [PR_REVIEW_WORKFLOW.md](docs/PR_REVIEW_WORKFLOW.md)**
   - Already included review labels and workflow
   - Now integrates with queue blocking

## Benefits

✅ **Prevents cascading bugs** - Issues caught before more code builds on them
✅ **Manageable review workload** - Never more than N PRs pending
✅ **Immediate feedback** - Workers pause when issues found
✅ **Parallel efficiency** - Independent features proceed in parallel
✅ **Full visibility** - Monitor queue and PR status in real-time
✅ **Flexible configuration** - Tune for your workflow
✅ **Automatic orchestration** - review_prs.py handles everything

## Usage Examples

### Typical Workflow

```bash
# 1. Workers create PRs until threshold reached
# (5 PRs created, queue blocks)

# 2. Check what's blocking
curl http://192.168.100.200:8000/health | jq '.pr_review'

# 3. Review pending PRs
python review_prs.py --all --list

# 4. Approve and merge
python review_prs.py --repo owner/repo --approve 1,2,3 --merge

# 5. Queue unblocks, workers resume
```

### Handling Issues

```bash
# Request changes (blocks queue)
python review_prs.py --repo owner/repo --request-changes 5 \
  --comment "Add error handling for edge cases"

# Queue now blocked until issue #5 is fixed
# Worker will see comment, fix, and update PR

# After fixing, approve to unblock
python review_prs.py --repo owner/repo --approve 5 --merge
```

## Files Changed/Created

### New Files
- `orchestrator_service/pr_review_tracker.py` - PR tracking system
- `docs/QUEUE_BLOCKING_STRATEGY.md` - Comprehensive documentation
- `REVIEW_BLOCKING_SUMMARY.md` - This file

### Modified Files
- `orchestrator_service/server.py` - Integrated PR tracker
- `review_prs.py` - Added orchestrator notifications
- `docs/GETTING_STARTED.md` - Added queue management docs
- `setup_repo_labels.py` - Already had review labels
- `worker/distributed_worker.py` - Already adds needs-review label

## Deployment

### Update Orchestrator

```bash
# On Proxmox host
ssh root@proxmox-host
cd /root/ai-scrum-master-v2

# Pull latest code
git pull

# Update orchestrator container
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    git pull

    # Optional: Configure thresholds
    echo 'MAX_PENDING_PRS=5' >> .env
    echo 'BLOCK_ON_CHANGES_REQUESTED=true' >> .env
    echo 'ALLOW_PARALLEL_INDEPENDENT=true' >> .env
"

# Restart orchestrator
pct exec 200 -- systemctl restart ai-orchestrator

# Verify
curl http://192.168.100.200:8000/health | jq '.pr_review'
```

### Update Local Review Script

```bash
# On your local machine
cd ~/Development/repos/ai-scrum-master-v2
git pull

# Optional: Set custom orchestrator URL
echo 'ORCHESTRATOR_URL=http://192.168.100.200:8000' >> .env

# Install requests library if needed
pip install requests
```

## Next Steps

1. **Deploy to Proxmox** - Update orchestrator and restart service
2. **Test with small project** - Create a few issues, watch queue blocking
3. **Tune configuration** - Adjust MAX_PENDING_PRS based on your review capacity
4. **Monitor in production** - Watch `/health` endpoint during real work

## Support

- Full documentation: [docs/QUEUE_BLOCKING_STRATEGY.md](docs/QUEUE_BLOCKING_STRATEGY.md)
- Review workflow: [docs/PR_REVIEW_WORKFLOW.md](docs/PR_REVIEW_WORKFLOW.md)
- Getting started: [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)
