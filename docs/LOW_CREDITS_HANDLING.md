# Low Credits Handling

## Overview

The AI Scrum Master system now gracefully handles situations where Anthropic API credits are too low, preventing system failures and providing clear recovery instructions.

## How It Works

### Detection

When Claude Code makes an API call and receives a "credit balance is too low" error:

1. **claude_agent.py** catches the error in the JSON output
2. **CreditChecker.is_low_credit_error()** identifies the error type
3. **InsufficientCreditsError** exception is raised

### Worker Response

When a worker encounters insufficient credits:

```
💳 Critical: Anthropic API credits too low - pausing worker

Anthropic API credit balance is too low.
Please add credits at https://console.anthropic.com/settings/billing

⏸️  Worker paused for 5 minutes - waiting for credits to be added
```

The worker:
1. **Releases** the work item back to the orchestrator queue (doesn't mark as failed)
2. **Pauses** for 5 minutes to avoid rapid retry spam
3. **Automatically resumes** and tries again after the pause
4. **Continues pausing** until credits are added

### Recovery

Once you add credits to your Anthropic account:

1. Workers automatically detect the next time they try to work
2. Work resumes normally
3. No manual intervention required
4. No issues lost or marked as failed

## User Actions

### When You See Low Credit Warnings

1. **Go to** https://console.anthropic.com/settings/billing
2. **Add credits** to your account (minimum $10 recommended)
3. **Wait** for workers to automatically resume (within 5 minutes)

### Checking Worker Status

```bash
# View worker logs to see credit status
./deployment/proxmox/view_worker_status.sh

# Check for credit errors specifically
pct exec 201 -- su - aimaster -c "journalctl -u ai-worker -n 100 | grep -i credit"
```

### Monitoring Credit Usage

Workers log cost per workflow to help you track usage:

```bash
# Check workflow costs
pct exec 201 -- su - aimaster -c "cat ai-scrum-master-v2/logs/workflow_*.log | grep 'Total Cost'"
```

## Technical Details

### Error Detection

The system detects these error patterns (case-insensitive):
- `"credit balance is too low"`
- `"insufficient credits"`
- `"credit limit exceeded"`
- `"balance too low"`

### Pause Behavior

**Why 5 minutes?**
- Prevents overwhelming the API with retries
- Gives you time to add credits
- Balances between responsiveness and system load

**Configurable?**
Yes, edit `worker/distributed_worker.py` line 153:
```python
time.sleep(300)  # 5 minutes = 300 seconds
```

### Exception Hierarchy

```
Exception
└── InsufficientCreditsError  (custom, in credit_checker.py)
    └── Raised by: CreditChecker.handle_low_credit_error()
    └── Caught by: DistributedWorker.run()
```

## Files Modified

- **credit_checker.py** (new) - Credit detection and error handling
- **claude_agent.py** - Detect credit errors in Claude Code output
- **worker/distributed_worker.py** - Catch and handle credit errors gracefully

## Best Practices

### For Production

1. **Monitor credits proactively** using Anthropic console
2. **Set up billing alerts** if available
3. **Maintain buffer** of at least $50 for uninterrupted operation
4. **Check logs regularly** for cost trends

### Cost Estimation

Typical costs per issue (Phase 1 tasks):
- **Architect**: $0.30-0.40
- **Security**: $0.40-0.50
- **Tester**: $0.20-0.30
- **PO**: $0.10-0.15
- **Total per issue**: ~$1.00-1.50

For 5 workers processing 50 issues: ~$50-75

### Emergency Procedures

If workers are paused and you need immediate resumption:

```bash
# Add credits first, then restart workers for immediate retry
./deployment/proxmox/restart_workers.sh
```

## Troubleshooting

### Workers Still Failing After Adding Credits

1. Check if credits actually added:
   - Visit https://console.anthropic.com/settings/billing
   - Verify balance is > $1.00

2. Check API key is correct:
   ```bash
   pct exec 201 -- su - aimaster -c "grep ANTHROPIC_API_KEY /home/aimaster/ai-scrum-master-v2/.env"
   ```

3. Restart workers to clear any cached state:
   ```bash
   ./deployment/proxmox/restart_workers.sh
   ```

### False Positive Credit Errors

If you see credit errors but have sufficient balance:
1. Check Anthropic API status: https://status.anthropic.com
2. Verify API key permissions in console
3. Check for rate limiting (different error pattern)

## Future Enhancements

Potential improvements:
- [ ] Proactive credit balance checking before starting work
- [ ] Email/Slack notifications when credits low
- [ ] Automatic credit top-up integration
- [ ] Cost prediction based on issue complexity
- [ ] Per-worker cost tracking and budgets
