# Bugfix: Credit Exception Not Propagating to Worker

## Issue

Issues were being marked as `ai-failed` with error "PO rejected after 0 revisions" when the REAL cause was Anthropic API credit exhaustion.

## Root Cause

The `InsufficientCreditsError` exception was being raised in `claude_agent.py` but not being caught and re-raised in `orchestrator.py`, causing it to be treated as a generic agent failure instead of a credit error.

**Flow of the bug:**
1. ✅ `claude_agent.py` detects "Credit balance is too low" in Claude Code output
2. ✅ `CreditChecker.handle_low_credit_error()` raises `InsufficientCreditsError`
3. ❌ `orchestrator.py` doesn't have try/except for this exception
4. ❌ Exception gets lost, treated as generic agent failure
5. ❌ Worker marks issue as failed instead of pausing

## Evidence

From worker logs (`claude_errors.log`):
```
Agent: Architect | Time: 2025-11-15 13:12:31
Return code: 1
STDOUT: {"type":"result","subtype":"success","is_error":true,...,"result":"Credit balance is too low"...}
```

The credit error was detected but not handled properly.

## Fix

Added exception handling in `orchestrator.py` to catch and re-raise `InsufficientCreditsError`:

```python
# Import added
from credit_checker import InsufficientCreditsError

# In _execute_agent_with_retry() method:
try:
    agent_result = agent.execute_task(task)
except InsufficientCreditsError:
    # Re-raise credit errors immediately - don't retry, let worker handle it
    raise
```

Now the exception properly propagates to `distributed_worker.py` which:
- Releases work back to queue (doesn't mark as failed)
- Pauses worker for 5 minutes
- Automatically retries after credits added

## Files Modified

- `orchestrator.py` - Added import and exception handling

## Testing

After deploying this fix:
1. Monitor worker logs for credit errors
2. Verify workers pause instead of failing issues
3. Verify issues are released back to queue (not marked failed)
4. Add credits and confirm workers auto-resume

## Related Documentation

- [docs/LOW_CREDITS_HANDLING.md](docs/LOW_CREDITS_HANDLING.md) - Credit handling system docs
- [credit_checker.py](credit_checker.py) - Credit detection logic
- [worker/distributed_worker.py](worker/distributed_worker.py) - Worker credit handling
