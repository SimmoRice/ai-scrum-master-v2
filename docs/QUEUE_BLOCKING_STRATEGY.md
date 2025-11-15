# Queue Blocking Strategy: Preventing Cascading Bugs

This document explains how the AI Scrum Cluster prevents cascading bugs and review overload through intelligent queue management.

## The Problem

Without queue management, workers can create several issues:

1. **Cascading Bugs**: Worker creates PR #1 with a bug, then PRs #2-5 build on that buggy code
2. **Wasted Work**: Workers continue processing while you review, potentially creating more buggy code
3. **Review Overload**: You get overwhelmed with many PRs to review at once
4. **No Feedback Loop**: Workers don't learn from review comments on earlier PRs

## The Solution: PR Review Tracker

The orchestrator includes a **PR Review Tracker** that:
- Tracks all pending PRs awaiting review
- Blocks new work when thresholds are exceeded
- Allows parallel work on independent features
- Integrates with review workflow

## How It Works

### 1. PR Lifecycle Tracking

Every PR created by workers is tracked through these states:

```
Worker Creates PR
        ↓
  [needs-review] ← Tracked as "pending PR"
        ↓
   Human Review
        ↓
    ┌───┴───┐
    ↓       ↓
[approved]  [changes-requested] ← Blocks ALL work
    ↓
  Merged ← Removed from tracking
```

### 2. Queue Blocking Rules

The queue is blocked when:

**Rule 1: Changes Requested** (Default: BLOCKS)
- ANY PR has `changes-requested` label
- **Why**: Indicates systemic issue that needs addressing
- **Unblocks when**: Changes are addressed and PR is re-approved or closed

**Rule 2: Too Many Pending PRs** (Default: 5)
- Number of PRs with `needs-review` exceeds threshold
- **Why**: Prevents review overload
- **Unblocks when**: PRs are reviewed/approved/merged

### 3. Parallel Independent Work (Optional)

When enabled (default: ON), workers can continue on **independent** features:

```
Issue #1: "Add user authentication" → PR pending review
Issue #2: "Fix typo in docs"      → Can proceed (independent)
Issue #3: "Add logout button"      → BLOCKED (depends on #1)
```

Dependencies are extracted from issue descriptions:
```markdown
**Dependencies:** #1, #5
```

### 4. Worker Experience

When a worker requests work from a blocked queue:

```json
{
  "work_available": false,
  "blocked": true,
  "reason": "Changes requested on PRs: #12. Address feedback before proceeding."
}
```

Worker logs:
```
INFO: Queue blocked: Changes requested on PRs: #12. Address feedback before proceeding.
INFO: Waiting 30s before retry...
```

## Configuration

Configure in orchestrator `.env`:

```bash
# Maximum pending PRs before blocking queue (default: 5)
MAX_PENDING_PRS=5

# Block all work when changes requested (default: true)
BLOCK_ON_CHANGES_REQUESTED=true

# Allow parallel work on independent issues (default: true)
ALLOW_PARALLEL_INDEPENDENT=true
```

### Configuration Strategies

#### 🔒 **Conservative (Recommended for Critical Projects)**
```bash
MAX_PENDING_PRS=3
BLOCK_ON_CHANGES_REQUESTED=true
ALLOW_PARALLEL_INDEPENDENT=false
```
- Maximum safety
- Review 3 PRs, then next 3 workers start
- Any issue blocks everything
- Best for: Production code, security-critical features

#### ⚖️ **Balanced (Default)**
```bash
MAX_PENDING_PRS=5
BLOCK_ON_CHANGES_REQUESTED=true
ALLOW_PARALLEL_INDEPENDENT=true
```
- Good safety with reasonable throughput
- Independent features can proceed
- Critical issues still block everything
- Best for: Most projects

#### 🚀 **Aggressive (High Throughput)**
```bash
MAX_PENDING_PRS=10
BLOCK_ON_CHANGES_REQUESTED=false
ALLOW_PARALLEL_INDEPENDENT=true
```
- Maximum throughput
- More PRs to review
- Issues don't block (just label them)
- Best for: Experimental projects, rapid prototyping

#### 🎯 **Review Batch Mode**
```bash
MAX_PENDING_PRS=10
BLOCK_ON_CHANGES_REQUESTED=true
ALLOW_PARALLEL_INDEPENDENT=false
```
- Workers create 10 PRs, then stop
- You review all 10 at once
- Next batch starts after review
- Best for: Scheduled review sessions

## Monitoring Queue Status

### Check Health Endpoint

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

### Detailed PR Status

```bash
curl http://192.168.100.200:8000/pr-review/status | jq
```

Output:
```json
{
  "pending_prs": 3,
  "changes_requested": 0,
  "approved": 2,
  "queue_blocked": false,
  "blocking_reason": null,
  "config": {
    "max_pending_prs": 5,
    "block_on_changes_requested": true,
    "allow_parallel_independent": true
  },
  "pending_pr_details": [
    {
      "issue_number": 12,
      "pr_url": "https://github.com/owner/repo/pull/12",
      "repository": "owner/repo",
      "created_at": "2025-01-15T10:30:00",
      "worker_id": "worker-1",
      "dependencies": [],
      "age_seconds": 1800
    }
  ]
}
```

## Workflow Examples

### Example 1: Normal Workflow

```bash
# 1. Workers create 5 PRs (max threshold)
Worker-1: Created PR #1 → Pending
Worker-2: Created PR #2 → Pending
Worker-3: Created PR #3 → Pending
Worker-4: Created PR #4 → Pending
Worker-5: Created PR #5 → Pending

# 2. Queue is now BLOCKED (5/5 pending)
Worker-1: Queue blocked - 5 PRs pending review
Worker-2: Queue blocked - 5 PRs pending review

# 3. You review and approve 2 PRs
$ python review_prs.py --repo owner/repo --approve 1,2 --merge

# 4. Queue UNBLOCKED (3/5 pending)
Worker-1: Assigned issue #6
Worker-2: Assigned issue #7
```

### Example 2: Changes Requested

```bash
# 1. Worker creates PR, you request changes
Worker-1: Created PR #10
$ python review_prs.py --repo owner/repo --request-changes 10 \
  --comment "Add error handling"

# 2. Queue BLOCKED immediately
Worker-1: Queue blocked - Changes requested on PR #10
Worker-2: Queue blocked - Changes requested on PR #10

# 3. Worker addresses feedback
# (Manual intervention: worker sees comment, fixes code, updates PR)

# 4. You approve the changes
$ python review_prs.py --repo owner/repo --approve 10

# 5. Queue UNBLOCKED
Worker-1: Assigned issue #11
```

### Example 3: Parallel Independent Work

```bash
# 1. Worker creates PR for feature A
Worker-1: Created PR #5 (Add authentication)
# Queue: 1 pending PR

# 2. Another worker gets independent work
Worker-2: Assigned issue #6 (Fix typo in README)
# No dependencies on #5, can proceed

# 3. Third worker tries dependent work
Worker-3: Checking issue #7 (Add logout - depends on #5)
Worker-3: Cannot proceed - dependency #5 not merged
# Waits for next available work

# 4. You merge #5
$ python review_prs.py --repo owner/repo --approve 5 --merge

# 5. Dependent work now available
Worker-3: Assigned issue #7 (logout now OK)
```

## Integration with Review Script

The [review_prs.py](../review_prs.py) script automatically notifies the orchestrator:

```bash
# When you approve
$ python review_prs.py --repo owner/repo --approve 12
# ↓ Calls: POST http://orchestrator:8000/pr-review/approved/12
# ↓ Result: PR removed from pending, queue may unblock

# When you request changes
$ python review_prs.py --repo owner/repo --request-changes 12 --comment "..."
# ↓ Calls: POST http://orchestrator:8000/pr-review/changes-requested/12
# ↓ Result: Queue BLOCKED

# When you merge
$ python review_prs.py --repo owner/repo --approve 12 --merge
# ↓ Calls: POST http://orchestrator:8000/pr-review/merged/12
# ↓ Result: PR fully removed from tracking
```

## API Endpoints

The orchestrator exposes these endpoints for PR tracking:

### `GET /pr-review/status`
Get current PR tracker status and pending PR details

### `POST /pr-review/approved/{issue_number}`
Notify that a PR was approved (called by review script)

### `POST /pr-review/changes-requested/{issue_number}`
Notify that changes were requested (called by review script)

### `POST /pr-review/merged/{issue_number}`
Notify that a PR was merged (called by review script)

## Best Practices

### 1. Review Promptly
- Workers wait when queue is blocked
- Quick reviews = higher throughput
- Set up notifications for new PRs

### 2. Use Changes Requested Wisely
- Minor issues: Approve with comment, fix in next PR
- Major issues: Request changes to block queue
- Systemic issues: Request changes to prevent cascading

### 3. Tune Thresholds
- Start conservative (MAX_PENDING_PRS=3)
- Increase as you get comfortable
- Monitor your review capacity

### 4. Leverage Dependencies
- Workers should specify dependencies in issues
- Orchestrator respects dependency order
- Independent work proceeds in parallel

### 5. Monitor Queue Health
```bash
# Add to your monitoring dashboard
watch -n 30 'curl -s http://192.168.100.200:8000/health | jq ".pr_review"'
```

## Troubleshooting

### Queue Stuck Blocked

**Check what's blocking:**
```bash
curl http://192.168.100.200:8000/health | jq '.pr_review.blocking_reason'
```

**Common causes:**
1. PR has `changes-requested` label → Review and approve or close
2. Too many pending PRs → Review and merge some
3. Stale PR tracking → Restart orchestrator to reset

### Workers Not Picking Up Work

**Check if blocked:**
```bash
curl http://192.168.100.200:8000/health | jq '.pr_review.queue_blocked'
```

If `true`, review pending PRs to unblock.

### PRs Not Tracked

**Verify orchestrator received completion:**
```bash
# Check orchestrator logs
./view_logs.sh orchestrator | grep "Registered PR for review"
```

If missing, worker may have failed to report completion.

## Summary

The queue blocking strategy ensures:
✅ No cascading bugs from unreviewed code
✅ Manageable review workload
✅ Workers get feedback before continuing
✅ Independent features can proceed in parallel
✅ Full visibility into pending work

This creates a sustainable, high-quality development workflow where AI and humans work together effectively.
