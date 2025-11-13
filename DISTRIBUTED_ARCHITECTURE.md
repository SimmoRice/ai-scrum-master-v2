# Distributed AI Scrum Master Architecture

## Vision: Scalable Multi-Container Development System

A distributed system where multiple AI Scrum Master instances work in parallel on different features/issues, coordinated through GitHub as the source of truth.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Repository                         │
│  - Issues (Features, Bugs, Tasks)                           │
│  - Pull Requests                                             │
│  - Branch Protection Rules                                   │
│  - CI/CD Workflows                                           │
└─────────────────┬───────────────────────────────────────────┘
                  │
         ┌────────▼─────────┐
         │  Orchestrator    │  ← Assigns work, monitors progress
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
└───┬───┘    └───┬───┘    └───┬───┘    └───┬───┘    └───┬───┘
    │            │            │            │            │
    └────────────┴────────────┴────────────┴────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   GitHub Actions   │
                    │  CI/CD Pipeline    │
                    │  - Run tests       │
                    │  - Code quality    │
                    │  - Auto-merge      │
                    └────────────────────┘
```

## Component Design

### 1. Orchestrator Service

**Responsibilities:**
- Poll GitHub for new issues (based on labels: `ai-ready`, `priority:high`)
- Assign issues to available workers
- Monitor worker health and progress
- Handle merge conflicts and failures
- Provide dashboard for monitoring

**API Endpoints:**
```python
# orchestrator/api.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/work/next")
async def get_next_work_item(worker_id: str):
    """Worker requests next issue to work on"""
    issue = fetch_next_github_issue()
    claim_issue(issue.number, worker_id)
    return {
        "issue_number": issue.number,
        "title": issue.title,
        "body": issue.body,
        "labels": issue.labels,
        "branch_name": f"ai-feature/issue-{issue.number}"
    }

@app.post("/work/complete")
async def mark_work_complete(worker_id: str, issue_number: int, pr_url: str):
    """Worker reports completion"""
    update_issue_status(issue_number, "completed")
    trigger_ci_pipeline(pr_url)
    return {"status": "success"}

@app.post("/work/failed")
async def mark_work_failed(worker_id: str, issue_number: int, error: str):
    """Worker reports failure"""
    add_issue_comment(issue_number, f"Failed: {error}")
    release_issue(issue_number)  # Make available for retry
    return {"status": "acknowledged"}
```

### 2. Worker Container

**Lifecycle:**
```python
# worker/main.py
import requests
from orchestrator_client import OrchestratorClient
from ai_scrum_master import Orchestrator

class DistributedWorker:
    def __init__(self, worker_id: str, orchestrator_url: str):
        self.worker_id = worker_id
        self.client = OrchestratorClient(orchestrator_url)

    def run(self):
        """Main worker loop"""
        while True:
            # 1. Request work from orchestrator
            work_item = self.client.get_next_work()
            if not work_item:
                time.sleep(30)  # Wait before checking again
                continue

            try:
                # 2. Setup isolated workspace
                workspace = self.setup_workspace(work_item)

                # 3. Run AI Scrum Master workflow
                result = self.execute_workflow(work_item, workspace)

                if result.approved:
                    # 4. Push to GitHub and create PR
                    pr_url = self.create_pull_request(work_item, workspace)

                    # 5. Report success
                    self.client.mark_complete(work_item.issue_number, pr_url)
                else:
                    # Workflow not approved - report failure
                    self.client.mark_failed(
                        work_item.issue_number,
                        f"PO rejected after {result.revision_count} revisions"
                    )

            except Exception as e:
                # Report failure to orchestrator
                self.client.mark_failed(work_item.issue_number, str(e))

            finally:
                # Cleanup workspace
                self.cleanup_workspace(workspace)

    def execute_workflow(self, work_item, workspace):
        """Run AI Scrum Master on the issue"""
        orchestrator = Orchestrator(workspace_dir=workspace)

        # Convert GitHub issue to user story
        user_story = self.format_user_story(work_item)

        # Execute workflow
        return orchestrator.process_user_story(user_story)

    def create_pull_request(self, work_item, workspace):
        """Push branch and create PR on GitHub"""
        # Push feature branch
        self.git_push(workspace, work_item.branch_name)

        # Create PR via GitHub API
        pr = self.github.create_pull_request(
            title=f"[AI] {work_item.title}",
            head=work_item.branch_name,
            base="main",
            body=f"""
            Automated implementation of issue #{work_item.issue_number}

            ## Changes
            {self.get_commit_summary(workspace)}

            ## Testing
            - All tests passing (194 tests)
            - Security review completed
            - Code coverage: 70%+

            **Generated by AI Scrum Master**
            Closes #{work_item.issue_number}
            """
        )
        return pr.html_url
```

### 3. GitHub Integration

**Issue Labeling System:**
```
Labels:
- `ai-ready` - Issue is ready for AI implementation
- `priority:critical` - Work on this first
- `priority:high` - High priority
- `priority:medium` - Medium priority
- `priority:low` - Low priority
- `type:feature` - New feature
- `type:bug` - Bug fix
- `type:refactor` - Code refactoring
- `complexity:small` - < 2 hour estimated
- `complexity:medium` - 2-8 hour estimated
- `complexity:large` - > 8 hour estimated
- `ai-in-progress` - Currently being worked on
- `ai-completed` - AI implementation complete
- `ai-failed` - AI implementation failed (needs human)
```

**GitHub Actions Workflow:**
```yaml
# .github/workflows/ai-pr-validation.yml
name: AI PR Validation

on:
  pull_request:
    branches: [ main ]
    types: [ opened, synchronize ]

jobs:
  validate-ai-pr:
    runs-on: ubuntu-latest
    if: startsWith(github.head_ref, 'ai-feature/')

    steps:
      - uses: actions/checkout@v3

      - name: Run Tests
        run: |
          npm install
          npm test

      - name: Check Coverage
        run: |
          npm run test:coverage
          # Require 70%+ coverage

      - name: Security Scan
        uses: snyk/actions/node@master

      - name: Auto-merge if tests pass
        if: success()
        uses: pascalgn/automerge-action@v0.15.6
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          MERGE_LABELS: "ai-ready,auto-merge"
```

## Preventing Merge Conflicts

### Strategy 1: File-Level Locking
```python
# orchestrator/conflict_prevention.py
class WorkAssigner:
    def __init__(self):
        self.file_locks = {}  # {file_path: worker_id}

    def can_assign_issue(self, issue: Issue) -> bool:
        """Check if issue can be assigned without conflicts"""
        estimated_files = self.estimate_affected_files(issue)

        for file_path in estimated_files:
            if file_path in self.file_locks:
                return False  # File is being worked on

        return True

    def assign_issue(self, issue: Issue, worker_id: str):
        """Assign issue and lock estimated files"""
        estimated_files = self.estimate_affected_files(issue)

        for file_path in estimated_files:
            self.file_locks[file_path] = worker_id
```

### Strategy 2: Feature Branch Isolation
- Each worker creates isolated feature branch
- Workers pull latest `main` at start
- If merge conflict on PR creation:
  - Orchestrator assigns "merge conflict resolution" task
  - Worker rebases and resolves
  - Re-runs tests

### Strategy 3: Microfeatures
- Break down large features into small, isolated tasks
- Each issue should modify 3-5 files maximum
- Use GitHub Projects to track dependencies

## Scaling Considerations

### Performance Optimization

**Current Metrics (1 instance):**
- Simple feature: ~10-15 minutes
- Complex feature: ~30-60 minutes
- Cost per feature: ~$5-15

**With 5 Parallel Workers:**
- Throughput: 5x increase
- Can complete 100+ features per day
- Cost remains same (parallelization doesn't increase per-feature cost)

### Resource Requirements

**Per Worker Container:**
```yaml
resources:
  limits:
    memory: 4Gi
    cpu: "2"
  requests:
    memory: 2Gi
    cpu: "1"
```

**Total for 5 Workers + Orchestrator:**
- Memory: ~20-25 GB
- CPU: 10-12 cores
- Disk: 100 GB (for workspaces and cache)

### Cost Analysis

**With 5 Parallel Workers:**
- Infrastructure: ~$100-200/month (AWS/GCP)
- Claude API: $0.10-0.30 per feature
- 100 features/day = $10-30/day in API costs

**ROI:**
- Human developer: $500-1000/day
- AI system: $13-30/day
- **Savings: ~95%** (assuming similar output quality)

## Implementation Phases

### Phase 1: Orchestrator Service (Week 1-2)
- [ ] Create FastAPI orchestrator service
- [ ] GitHub API integration (issue fetching, PR creation)
- [ ] Work queue management
- [ ] Worker health monitoring
- [ ] Basic web dashboard

### Phase 2: Worker Containerization (Week 2-3)
- [ ] Dockerize ai-scrum-master
- [ ] Create worker loop (pull work, execute, report)
- [ ] Implement workspace isolation
- [ ] Add failure recovery
- [ ] Test with 2 parallel workers

### Phase 3: Conflict Prevention (Week 3-4)
- [ ] File-level locking system
- [ ] Merge conflict detection
- [ ] Automatic rebase on conflicts
- [ ] Issue dependency tracking

### Phase 4: CI/CD Integration (Week 4-5)
- [ ] GitHub Actions workflows
- [ ] Automated testing pipeline
- [ ] Auto-merge on success
- [ ] Notification system (Slack/Discord)

### Phase 5: Scaling & Monitoring (Week 5-6)
- [ ] Scale to 5 parallel workers
- [ ] Performance monitoring (Prometheus/Grafana)
- [ ] Cost tracking per feature
- [ ] Load balancing and optimization

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Merge conflicts | High | File locking, small issues, auto-rebase |
| API rate limits | High | Request queuing, exponential backoff |
| Worker failures | Medium | Health checks, automatic restart, work reassignment |
| Inconsistent code style | Medium | Pre-commit hooks, ESLint/Prettier enforcement |
| Cost overruns | Medium | Budget limits, per-worker cost tracking |
| Quality degradation | High | Mandatory PR reviews for complex features, human oversight |

## Next Steps

1. **Validate Architecture**: Review with team
2. **Build Orchestrator Prototype**: Simple FastAPI service
3. **Test with 2 Workers**: Prove parallel execution works
4. **Implement Conflict Prevention**: Ensure stability
5. **Scale to 5 Workers**: Full production deployment

## Questions to Resolve

- Should we use Docker or LXC for containers?
- What's the maximum parallelization before conflicts become unmanageable?
- Should PO reviews require human approval for critical features?
- How do we handle issues that span multiple areas (need coordination)?
- Database per worker or shared database?
