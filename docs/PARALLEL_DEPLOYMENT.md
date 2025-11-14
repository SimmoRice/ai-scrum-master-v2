# Parallel Agent Deployment Guide

Complete guide for deploying and testing multiple AI Scrum Master agents in parallel.

## Overview

The AI Scrum Master v2 supports parallel deployment of multiple worker instances to process GitHub issues concurrently. This dramatically increases throughput and enables distributed development workflows.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
│  - Issues (labeled: ready-for-dev)                          │
│  - Pull Requests                                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
         ┌────────▼─────────┐
         │  Orchestrator    │  (Optional)
         │    Service       │
         └────────┬─────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┬─────────────┐
    │             │             │             │             │
┌───▼───┐    ┌───▼───┐    ┌───▼───┐    ┌───▼───┐    ┌───▼───┐
│Worker │    │Worker │    │Worker │    │Worker │    │Worker │
│  #1   │    │  #2   │    │  #3   │    │  #4   │    │  #5   │
│       │    │       │    │       │    │       │    │       │
│Issue  │    │Issue  │    │Issue  │    │Issue  │    │Issue  │
│ #123  │    │ #124  │    │ #125  │    │ #126  │    │ #127  │
└───────┘    └───────┘    └───────┘    └───────┘    └───────┘
```

## Features

- ✅ **Parallel Execution**: Run multiple agents simultaneously
- ✅ **Workspace Isolation**: Each worker has isolated workspace
- ✅ **Resource Management**: Prevent conflicts between workers
- ✅ **Load Balancing**: Distribute work across workers
- ✅ **Failure Isolation**: Worker failures don't affect others
- ✅ **Performance Monitoring**: Real-time status and metrics
- ✅ **Scalability**: Supports 1-10+ parallel workers

## Quick Start

### 1. Run Parallel Test

Test parallel deployment with mock issues:

```bash
python3 deploy_parallel_agents.py --workers 3 --mode test --mock-issues 5
```

This will:
- Deploy 3 simulated workers
- Process 5 mock issues
- Show real-time status updates
- Display completion metrics

### 2. Run Test Suite

Comprehensive parallel operation tests:

```bash
# Run all tests
python3 test_parallel_agents.py

# Run specific test
python3 test_parallel_agents.py --test test_concurrent_execution

# Run with more workers
python3 test_parallel_agents.py --workers 5

# Run performance benchmark
python3 test_parallel_agents.py --benchmark
```

### 3. Deploy Local Workers

Deploy workers that process real GitHub issues:

```bash
python3 deploy_parallel_agents.py \
  --workers 3 \
  --mode local \
  --workspace ./parallel_workspace \
  --monitor-duration 300
```

This will:
- Deploy 3 local workers
- Poll GitHub for issues with `ready-for-dev` label
- Process issues concurrently
- Monitor for 5 minutes (300s)

## Deployment Modes

### Local Mode

Workers run as local processes, polling GitHub directly:

```bash
python3 deploy_parallel_agents.py --workers 3 --mode local
```

**Pros:**
- Simple setup
- No external dependencies
- Good for testing

**Cons:**
- Manual coordination required
- Limited scalability

### Distributed Mode

Workers connect to orchestrator service for centralized coordination:

```bash
# Start orchestrator service first
python3 orchestrator_service/server.py

# Deploy workers
python3 deploy_parallel_agents.py \
  --workers 5 \
  --mode distributed \
  --orchestrator-url http://localhost:8000
```

**Pros:**
- Centralized work queue
- Better coordination
- Prevents duplicate work
- Scales to many workers

**Cons:**
- Requires orchestrator service
- More complex setup

### Test Mode

Simulated workers for testing:

```bash
python3 deploy_parallel_agents.py \
  --workers 2 \
  --mode test \
  --mock-issues 5
```

## Test Suite

### Available Tests

1. **test_worker_deployment** - Verify workers deploy correctly
2. **test_workspace_isolation** - Ensure workspace isolation
3. **test_concurrent_execution** - Test parallel task execution
4. **test_resource_contention** - Test resource locking
5. **test_failure_isolation** - Verify failure handling
6. **test_load_balancing** - Check work distribution
7. **test_performance_benchmark** - Benchmark speedup

### Running Tests

```bash
# All tests
python3 test_parallel_agents.py

# Specific test
python3 test_parallel_agents.py --test test_concurrent_execution

# With custom worker count
python3 test_parallel_agents.py --workers 5

# Performance benchmark
python3 test_parallel_agents.py --benchmark
```

### Example Test Output

```
================================================================================
TEST: Concurrent Execution
================================================================================
  ✅ Task 0 completed
  ✅ Task 1 completed
  ✅ Task 2 completed
  ✅ Task 3 completed
  ✅ Task 4 completed
  ✅ Task 5 completed

📊 Execution Statistics:
  Tasks: 6
  Workers: 3
  Duration: 2.24s
  Sequential time: 6.00s
  Speedup: 2.67x

✅ Concurrent execution working (speedup: 2.67x)
```

## Performance Benchmarks

### Speedup vs Worker Count

Based on our benchmark tests (10 tasks, 1s each):

| Workers | Duration | Speedup | Efficiency |
|---------|----------|---------|------------|
| 1       | 10.30s   | 0.97x   | 97.1%      |
| 2       | 5.26s    | 1.90x   | 95.0%      |
| 3       | 4.20s    | 2.38x   | 79.3%      |
| 5       | 2.26s    | 4.43x   | 88.6%      |

### Key Findings

- **Near-linear speedup** up to 3 workers (2.38x speedup)
- **High efficiency** maintained (79-95%)
- **Optimal configuration**: 3-5 workers for most workloads
- **Diminishing returns** beyond 5 workers due to overhead

### Real-World Performance

Typical AI Scrum Master task (simple feature):
- **Sequential**: ~15 minutes/feature
- **3 Workers**: ~5 features/15 minutes = **3x throughput**
- **5 Workers**: ~5 features/15 minutes = **5x throughput**

## Workspace Management

### Isolation

Each worker gets isolated workspace:

```
parallel_workspace/
├── worker-01/
│   ├── issue-123/
│   │   ├── .git/
│   │   └── src/
│   └── issue-125/
├── worker-02/
│   └── issue-124/
└── worker-03/
    └── issue-126/
```

### Cleanup

Workspaces are automatically cleaned up after task completion.

Manual cleanup:

```bash
rm -rf parallel_workspace/
```

## Conflict Prevention

### File-Level Isolation

Workers operate on different issues, preventing merge conflicts:

1. Each issue gets separate branch: `ai-feature/issue-123`
2. Workers create PRs independently
3. GitHub handles merge conflicts during PR review

### Resource Locking

For shared resources (if needed):

```python
import fcntl

with open(shared_file, "r+") as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    try:
        # Critical section
        value = f.read()
        # Process...
        f.write(new_value)
    finally:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

## Monitoring

### Real-Time Status

Workers report status in real-time:

```
================================================================================
PARALLEL WORKERS STATUS - 20:33:32
================================================================================
🔵 worker-01       | Status: working    | Completed:   1 | Cost: $   0.08
🔵 worker-02       | Status: working    | Completed:   1 | Cost: $   0.08
⚪ worker-03       | Status: idle       | Completed:   0 | Cost: $   0.00
================================================================================
```

### Status Indicators

- 🟢 Running - Worker process active
- ⚪ Idle - Waiting for work
- 🔵 Working - Processing issue
- 🔴 Failed - Worker encountered error
- ⚫ Stopped - Worker shut down

### Metrics

Each worker tracks:
- Issues completed
- Total cost ($USD)
- Current task
- Uptime
- Last heartbeat

## Configuration

### Environment Variables

```bash
# Required for all modes
export ANTHROPIC_API_KEY="your-key"

# For distributed mode
export ORCHESTRATOR_URL="http://localhost:8000"
export WORKER_ID="worker-01"

# Optional
export WORKSPACE_DIR="/opt/workspace"
export LOG_LEVEL="INFO"
export GITHUB_TOKEN="ghp_..."
```

### Worker Configuration

Edit [config.py](../config.py):

```python
WORKFLOW_CONFIG = {
    "max_revisions": 3,
    "auto_merge_on_approval": True,
    "max_agent_retries": 2,
    "retry_backoff_seconds": 5,
}
```

## Troubleshooting

### Worker Not Starting

```bash
# Check logs
tail -f logs/worker-01.log

# Verify API key
echo $ANTHROPIC_API_KEY

# Test orchestrator (distributed mode)
curl http://localhost:8000/health
```

### Resource Exhaustion

Reduce worker count or increase system resources:

```bash
# Check CPU/memory
top

# Reduce workers
python3 deploy_parallel_agents.py --workers 2
```

### Merge Conflicts

If workers create conflicting PRs:

1. Review PRs in order
2. Merge one at a time
3. Rebase subsequent PRs
4. Use GitHub's conflict resolution

## Best Practices

### 1. Start Small

Begin with 2-3 workers, scale up gradually:

```bash
# Start conservative
python3 deploy_parallel_agents.py --workers 2
```

### 2. Label Issues Carefully

Use `ready-for-dev` label only for:
- Well-defined requirements
- Independent tasks
- Non-conflicting files

### 3. Monitor Resource Usage

```bash
# Check system resources
htop

# Adjust worker count based on available resources
```

### 4. Review PRs Promptly

Parallel workers create multiple PRs - review and merge regularly to prevent:
- Merge conflicts
- Stale branches
- Confusion

### 5. Use Distributed Mode for Scale

For 5+ workers, use orchestrator service:

```bash
# More efficient coordination
python3 deploy_parallel_agents.py \
  --workers 10 \
  --mode distributed
```

## Future Enhancements

- [ ] Docker containerization
- [ ] Kubernetes deployment
- [ ] Automatic conflict resolution
- [ ] Web dashboard for monitoring
- [ ] Cost optimization algorithms
- [ ] Priority-based scheduling
- [ ] Multi-repository support

## Contributing

See [DISTRIBUTED_ARCHITECTURE.md](../DISTRIBUTED_ARCHITECTURE.md) for architecture details.

## Support

For issues or questions:
- GitHub Issues: [ai-scrum-master-v2/issues](https://github.com/YOUR_ORG/ai-scrum-master-v2/issues)
- Documentation: [docs/](.)

---

**Last Updated**: 2025-11-14
**Version**: 2.4.0
