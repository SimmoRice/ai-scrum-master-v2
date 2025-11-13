# Orchestrator Service

The orchestrator coordinates distributed AI Scrum Master workers, managing work distribution and monitoring progress.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Orchestrator Service                    │
│                                                          │
│  ┌──────────────┐  ┌─────────────┐  ┌────────────────┐ │
│  │   FastAPI    │  │   GitHub    │  │    Worker      │ │
│  │     API      │  │   Client    │  │   Manager      │ │
│  └──────┬───────┘  └──────┬──────┘  └────────┬───────┘ │
│         │                 │                   │         │
│         │                 │                   │         │
│         ▼                 ▼                   ▼         │
│  ┌──────────────────────────────────────────────────┐   │
│  │             Work Queue Manager                    │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
      [Worker 1]      [Worker 2]  ...  [Worker 5]
```

## Components

### 1. server.py
Main FastAPI application that provides:
- `/health` - Health check endpoint
- `/work/next` - Workers request next task
- `/work/complete` - Workers report completion
- `/work/failed` - Workers report failures
- `/workers` - List all workers
- `/queue` - View work queue status

### 2. github_client.py
GitHub API client for:
- Fetching issues with specific labels
- Adding/removing labels
- Creating comments
- Closing issues

### 3. work_queue.py
Work queue manager:
- Tracks pending/in-progress/completed tasks
- Prevents duplicate work
- Handles retries (up to 2 attempts)
- File-level locking (future)

### 4. worker_manager.py
Worker health monitoring:
- SSH connectivity checks
- Service status monitoring
- Worker activity tracking
- Log retrieval

### 5. worker_client.py
Worker-side client that:
- Polls orchestrator for work
- Executes AI Scrum Master workflows
- Reports results back

## Installation

### On Orchestrator Container

```bash
# Install dependencies
pip install -r orchestrator/requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."
export GITHUB_REPO="owner/repo"
export WORKER_IPS="10.0.0.11,10.0.0.12,10.0.0.13,10.0.0.14,10.0.0.15"
export WORKER_SSH_KEY="/root/.ssh/id_orchestrator"

# Run orchestrator
python orchestrator/server.py
```

### On Worker Containers

```bash
# Set environment variables
export WORKER_ID="worker-1"
export ORCHESTRATOR_URL="http://10.0.0.10:8000"
export ANTHROPIC_API_KEY="sk-ant-..."
export WORKSPACE_DIR="/opt/ai-scrum-master/workspace"

# Run worker client
python orchestrator/worker_client.py
```

## Configuration

### Environment Variables

#### Orchestrator
- `ORCHESTRATOR_HOST` - Bind address (default: 0.0.0.0)
- `ORCHESTRATOR_PORT` - Port number (default: 8000)
- `GITHUB_TOKEN` - GitHub personal access token (required)
- `GITHUB_REPO` - Repository in format "owner/repo" (required)
- `GITHUB_ISSUE_LABELS` - Label to filter issues (default: "ai-ready")
- `GITHUB_POLL_INTERVAL` - Seconds between GitHub polls (default: 60)
- `WORKER_IPS` - Comma-separated worker IPs
- `WORKER_SSH_KEY` - Path to SSH private key
- `WORKER_SSH_USER` - SSH username (default: root)
- `WORKER_HEALTH_CHECK_INTERVAL` - Seconds between health checks (default: 30)
- `LOG_LEVEL` - Logging level (default: INFO)

#### Worker
- `WORKER_ID` - Unique worker identifier (required)
- `ORCHESTRATOR_URL` - Orchestrator API URL (required)
- `ANTHROPIC_API_KEY` - Anthropic API key (required)
- `WORKSPACE_DIR` - Workspace directory (default: /opt/ai-scrum-master/workspace)
- `WORKER_POLL_INTERVAL` - Seconds between work requests (default: 30)
- `LOG_LEVEL` - Logging level (default: INFO)

## API Reference

### GET /health
Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "workers": {
    "total": 5,
    "available": 4
  },
  "queue": {
    "pending": 10,
    "in_progress": 4,
    "completed": 25
  },
  "github_connected": true
}
```

### GET /work/next?worker_id=worker-1
Request next work item

**Response (work available):**
```json
{
  "work_available": true,
  "issue_number": 123,
  "title": "Add user authentication",
  "body": "Implement JWT-based authentication...",
  "labels": ["ai-ready", "priority:high"],
  "branch_name": "ai-feature/issue-123",
  "repository": "owner/repo"
}
```

**Response (no work):**
```json
{
  "work_available": false
}
```

### POST /work/complete
Report work completion

**Request:**
```json
{
  "worker_id": "worker-1",
  "issue_number": 123,
  "pr_url": "https://github.com/owner/repo/pull/124",
  "success": true
}
```

### POST /work/failed
Report work failure

**Request:**
```json
{
  "worker_id": "worker-1",
  "issue_number": 123,
  "error": "Product Owner rejected after 3 revisions"
}
```

### GET /workers
List all workers

**Response:**
```json
{
  "workers": [
    {
      "id": "worker-1",
      "ip": "10.0.0.11",
      "status": "busy",
      "current_task": 123,
      "last_seen": "2025-11-13T12:00:00",
      "health": "healthy"
    }
  ]
}
```

### GET /queue
View work queue status

**Response:**
```json
{
  "pending": [...],
  "in_progress": [...],
  "completed": [...]
}
```

## Workflow

1. **GitHub Polling:**
   - Orchestrator polls GitHub every 60s for issues labeled "ai-ready"
   - New issues are added to work queue
   - Issue labeled "ai-in-progress"

2. **Work Assignment:**
   - Worker requests work via `/work/next`
   - Orchestrator assigns first pending issue
   - Issue marked as "in_progress"

3. **Execution:**
   - Worker creates isolated workspace
   - Runs AI Scrum Master workflow
   - Reports result to orchestrator

4. **Completion:**
   - If successful: Create PR, label "ai-completed"
   - If failed: Release for retry (max 2 attempts)
   - If max retries: Label "ai-failed", add comment

## Monitoring

### View Orchestrator Logs
```bash
# On orchestrator container
journalctl -u ai-scrum-orchestrator -f
```

### View Worker Logs
```bash
# On worker container
journalctl -u ai-scrum-worker -f
```

### Check Status via API
```bash
# Health check
curl http://10.0.0.10:8000/health

# Worker status
curl http://10.0.0.10:8000/workers

# Queue status
curl http://10.0.0.10:8000/queue
```

## Development

### Run Locally
```bash
# Terminal 1: Start orchestrator
python orchestrator/server.py

# Terminal 2: Start worker (simulate)
WORKER_ID="worker-local" \
ORCHESTRATOR_URL="http://localhost:8000" \
python orchestrator/worker_client.py
```

### Testing
```bash
# Create test issue
gh issue create \
  --title "[Test] Simple function" \
  --body "Create a hello world function" \
  --label "ai-ready"

# Monitor execution
curl http://localhost:8000/queue
```

## Troubleshooting

### Orchestrator won't start
```bash
# Check logs
journalctl -u ai-scrum-orchestrator -xe

# Verify environment variables
systemctl show ai-scrum-orchestrator --property=Environment
```

### Worker can't connect
```bash
# Test connectivity
curl http://10.0.0.10:8000/health

# Check worker logs
journalctl -u ai-scrum-worker -n 50
```

### No work being assigned
```bash
# Check GitHub connection
curl http://10.0.0.10:8000/health | jq .github_connected

# Verify issue labels
gh issue list --label "ai-ready"
```

## Performance Tuning

### Adjust Poll Intervals
```bash
# Faster GitHub polling (30s instead of 60s)
export GITHUB_POLL_INTERVAL=30

# More frequent health checks (15s instead of 30s)
export WORKER_HEALTH_CHECK_INTERVAL=15
```

### Scale Workers
Simply add more worker IPs:
```bash
export WORKER_IPS="10.0.0.11,10.0.0.12,10.0.0.13,10.0.0.14,10.0.0.15,10.0.0.16"
```

## Security

- SSH keys used for worker communication
- GitHub token requires minimal permissions: `repo`, `issues`
- Anthropic API keys stored securely in `.env`
- All communication over private network

## Future Enhancements

- [ ] File-level locking to prevent conflicts
- [ ] Redis backend for shared state
- [ ] Web dashboard UI
- [ ] Prometheus metrics export
- [ ] Grafana dashboards
- [ ] Slack/Discord notifications
- [ ] Auto-scaling workers
- [ ] Cost tracking per feature
