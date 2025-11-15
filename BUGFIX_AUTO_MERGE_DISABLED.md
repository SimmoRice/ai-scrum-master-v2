# Bug Fix: Disable Auto-Merge for Distributed Worker Architecture

## Problem

Workflows were completing successfully and being approved by the Product Owner, but:
- ❌ No pull requests were being created on GitHub
- ❌ Issues were being labeled as `ai-failed`
- ❌ Changes were being merged directly to main branch
- ❌ No opportunity for human review before merging

### Observed Behavior

```
2025-11-15 21:33:08 - ✅ Workflow completed: APPROVED
2025-11-15 21:33:08 - ✅ Merged to main branch  ← PROBLEM!
```

The orchestrator was merging changes directly to main, and then the worker tried to create a PR afterward, which failed because there was nothing left to create a PR for.

## Root Cause

**Configuration conflict between v2.1 (standalone) and v2.2 (distributed) architecture:**

```python
# config.py line 41
WORKFLOW_CONFIG = {
    "auto_merge_on_approval": True,  # Legacy setting from v2.1
    ...
}
```

### Architecture Differences

**v2.1 (Standalone):**
- Orchestrator runs workflows locally
- `auto_merge_on_approval: True` makes sense
- Changes merge directly to main after approval
- No PR workflow

**v2.2+ (Distributed Workers):**
- Workers run workflows in isolated workspaces
- Workers should create PRs for human review
- PRs should be merged manually or via GitHub auto-merge
- `auto_merge_on_approval: True` conflicts with PR workflow

### What Was Happening

1. ✅ Worker runs workflow → approved by PO
2. ❌ Orchestrator sees `auto_merge_on_approval: True`
3. ❌ Orchestrator merges tester-branch → main
4. ❌ Worker tries to create PR from already-merged branch
5. ❌ PR creation fails (nothing to create PR for)
6. ❌ Worker marks issue as failed
7. ❌ Issue gets `ai-failed` label

## The Fix

Changed `auto_merge_on_approval` from `True` to `False`:

```python
# config.py line 41
WORKFLOW_CONFIG = {
    "auto_merge_on_approval": False,  # Disabled for distributed worker + PR workflow
    ...
}
```

## Impact

### Before (Broken):
```
Workflow → Approve → Auto-merge to main → Try to create PR → Fail → ai-failed label
```
- ❌ No PRs created
- ❌ No human review opportunity
- ❌ Changes pushed directly to main
- ❌ Issues marked as failed

### After (Fixed):
```
Workflow → Approve → Create PR → Human reviews → Merge PR
```
- ✅ PRs created on GitHub
- ✅ Human review before merge
- ✅ Proper branch workflow
- ✅ Issues marked as completed

## Expected Workflow (Post-Fix)

1. Worker picks up issue labeled `ai-ready`
2. Worker runs AI Scrum Master workflow
3. Product Owner approves the work
4. Worker creates feature branch (`ai-feature/issue-X`)
5. Worker pushes branch to GitHub
6. Worker creates pull request via GitHub API
7. **Human reviews PR**
8. **Human merges PR** (or GitHub auto-merge if configured)
9. Issue automatically closed via "Closes #X" in PR body

## Deployment

### For Existing Deployments

This change requires **restarting all services** to load the new configuration:

```bash
# Update code on all containers
./deployment/proxmox/update_cluster.sh

# Restart all services
./deployment/proxmox/restart_cluster.sh
```

### Configuration Verification

After deployment, verify the setting is applied:

```bash
# Check orchestrator configuration
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && grep -A 5 'WORKFLOW_CONFIG' config.py"
```

Should show:
```python
WORKFLOW_CONFIG = {
    "max_revisions": 3,
    "auto_merge_on_approval": False,  # This should be False
    ...
}
```

## Related Configuration

### GitHub Auto-Merge (Separate Feature)

If you want **automatic merging** after PR approval, configure GitHub's auto-merge feature:

1. Go to repository Settings → General
2. Enable "Allow auto-merge"
3. Enable required status checks if desired
4. On each PR, click "Enable auto-merge"

This is **separate** from `auto_merge_on_approval` and happens **after** PR creation.

### Manual Merge (Recommended)

For production deployments, we recommend:
- `auto_merge_on_approval: False` (in config.py)
- Human review of each PR
- Manual merge after review
- This ensures quality control and oversight

## Testing

After deployment, test the full workflow:

1. Create a test issue on GitHub
2. Label it with `ai-ready`
3. Wait for workflow to complete (~10-15 minutes)
4. Verify:
   - ✅ Issue labeled `ai-in-progress` during execution
   - ✅ Issue labeled `ai-completed` after success
   - ✅ Pull request created on GitHub
   - ✅ Branch `ai-feature/issue-X` exists
   - ✅ PR description mentions the issue number
   - ✅ No auto-merge to main

## Migration Notes

If you have **existing approved workflows** that were auto-merged to main:
- They're already on main (no action needed)
- Future workflows will create PRs instead
- No data loss or corruption

If you have **failed issues** due to this bug:
1. Remove `ai-failed` label
2. Add `ai-ready` label
3. Workflow will retry with correct behavior

## Related Files

- `config.py` (line 41) - Configuration change
- `orchestrator.py` (lines 274-280) - Auto-merge logic
- `worker/distributed_worker.py` (lines 121-126) - PR creation logic

## Future Improvements

Consider making this configuration **dynamic** or **environment-specific**:

```python
# Example: Environment-based configuration
import os

WORKFLOW_CONFIG = {
    "auto_merge_on_approval": os.getenv("AUTO_MERGE", "false").lower() == "true",
    ...
}
```

This would allow different behavior in different environments without code changes.
