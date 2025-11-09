# MCP Integration Plan for AI Scrum Master v2.2

## Overview
Model Context Protocol (MCP) servers will extend AI Scrum Master's capabilities beyond file operations to interact with external services.

## Selected MCPs

### 1. PostgreSQL MCP (Highest Priority)
**Use Case:** Persistent workflow analytics and metrics

**Integration Point:** Orchestrator level (not agents)
- Store every workflow execution
- Track costs, duration, success rates over time
- Query historical data for insights

**Implementation:**
```python
# New module: database.py
class WorkflowDatabase:
    def __init__(self, mcp_client):
        self.mcp = mcp_client

    def store_workflow(self, workflow_result):
        """Store complete workflow in database"""

    def get_metrics(self, days=30):
        """Get workflow metrics for last N days"""

    def get_cost_trends(self):
        """Analyze cost trends over time"""
```

**Benefits:**
- Better than JSON logs for querying
- Track success/failure patterns
- Cost analysis and forecasting
- Identify which types of tasks are most expensive

**Questions:**
- Local PostgreSQL or hosted (Supabase)?
- Schema design for workflows/agents/metrics?
- Migration from JSON logs?

---

### 2. GitHub MCP (Medium Priority)
**Use Case:** Automated PR creation and issue management

**Integration Point:** Orchestrator, after PO approval
- Create PR when PO approves
- Add issue when PO rejects with feedback
- Link commits to issues

**Implementation:**
```python
# In orchestrator.py, after PO approves:
if WORKFLOW_CONFIG['auto_create_pr'] and github_mcp:
    pr_url = github_mcp.create_pr(
        title=f"Feature: {user_story[:50]}",
        body=f"""
        ## Summary
        {result.po_decision}

        ## Metrics
        - Cost: ${result.total_cost:.2f}
        - Duration: {result.total_duration_ms/1000:.1f}s
        - Revisions: {result.revision_count}

        ## Agents
        - Architect: ${result.architect_result['cost_usd']:.2f}
        - Security: ${result.security_result['cost_usd']:.2f}
        - Tester: ${result.tester_result['cost_usd']:.2f}
        """,
        base="main",
        head=TESTER_BRANCH
    )
    print(f"✅ Created PR: {pr_url}")
```

**Benefits:**
- Seamless integration with GitHub workflow
- Automatic PR creation saves manual steps
- Better traceability (commits → PRs → issues)
- Team visibility

**Questions:**
- Should this be optional (config flag)?
- PR creation for all approvals or only certain types?
- Should agents have direct GitHub access or just orchestrator?

---

### 3. Slack MCP (Lower Priority)
**Use Case:** Team notifications and monitoring

**Integration Point:** Orchestrator level, notifications
- Notify when workflow starts
- Alert on completion (success/failure)
- Post metrics summary
- Alert on errors/failures

**Implementation:**
```python
# New module: notifications.py
class SlackNotifier:
    def __init__(self, mcp_client, channel):
        self.mcp = mcp_client
        self.channel = channel

    def workflow_started(self, user_story):
        """Notify workflow has started"""

    def workflow_completed(self, result):
        """Post completion summary"""

    def workflow_failed(self, result, error):
        """Alert on failure"""
```

**Example Message:**
```
🎉 Workflow Completed!

Story: Add dark mode toggle to calculator
Status: ✅ APPROVED
Cost: $1.23
Duration: 12.4 minutes

Architect: $0.59 (210s)
Security: $0.60 (190s)
Tester: $0.45 (340s)
PO: $0.05 (45s)
```

**Benefits:**
- Real-time visibility for team
- Async monitoring (no need to watch CLI)
- Historical record in Slack
- Good for multi-team coordination

**Questions:**
- Which events to notify? (start, complete, error, all?)
- Different channels for different workflows?
- Throttling/rate limiting?

---

## Architecture Considerations

### Where to Integrate MCPs?

**✅ Orchestrator Level (Recommended)**
```
Orchestrator
├── Database MCP (stores all data)
├── GitHub MCP (creates PRs after approval)
└── Slack MCP (sends notifications)
    │
    └── Agents (remain MCP-free)
        ├── Architect
        ├── Security
        ├── Tester
        └── Product Owner
```

**Why?**
- Agents focus on code generation (single responsibility)
- Orchestrator handles workflow coordination and external integration
- Cleaner separation of concerns
- Easier to test and maintain

**❌ Agent Level (Not Recommended)**
- Agents become more complex
- Harder to coordinate (which agent posts to Slack?)
- Potential for duplicate notifications
- Violates single responsibility principle

### Exception: Agent-Specific MCPs

Some MCPs might make sense for specific agents:
- **Puppeteer MCP** → Tester agent (for E2E testing)
- **Brave Search MCP** → Architect agent (for API documentation lookup)

---

## Implementation Plan

### Phase 1: PostgreSQL MCP (v2.2)
1. Install and configure PostgreSQL MCP
2. Design database schema
3. Create `database.py` module
4. Integrate in orchestrator
5. Migrate existing JSON log data
6. Add metrics queries/reports

**Estimated effort:** 4-6 hours

### Phase 2: GitHub MCP (v2.3)
1. Install and configure GitHub MCP
2. Add GitHub integration to orchestrator
3. Add config flag for auto-PR creation
4. Test PR creation workflow
5. Add issue creation for rejections

**Estimated effort:** 2-3 hours

### Phase 3: Slack MCP (v2.4)
1. Install and configure Slack MCP
2. Create `notifications.py` module
3. Add notification hooks in orchestrator
4. Configure notification preferences
5. Test message formatting

**Estimated effort:** 2-3 hours

---

## Configuration Structure

```python
# config.py additions
MCP_CONFIG = {
    "enabled": True,
    "postgres": {
        "enabled": True,
        "host": "localhost",
        "database": "ai_scrum_master",
        "schema": "public"
    },
    "github": {
        "enabled": True,
        "auto_create_pr": True,
        "create_issues_on_reject": True,
        "repository": "owner/repo"
    },
    "slack": {
        "enabled": True,
        "channel": "#ai-scrum-master",
        "notify_on": ["start", "complete", "error"],
        "mention_on_error": ["@devops-team"]
    }
}
```

---

## Open Questions

1. **PostgreSQL:**
   - Local or hosted database?
   - Backup/retention strategy?
   - Export format (CSV, JSON)?

2. **GitHub:**
   - Auto-merge PRs after creation?
   - Require manual review?
   - PR template customization?

3. **Slack:**
   - Notification frequency limits?
   - Thread vs new message for updates?
   - DM vs channel for errors?

4. **General:**
   - MCP failure handling (continue without or abort)?
   - Rate limiting strategies?
   - Cost tracking for MCP calls?

---

## Success Metrics

After implementing MCPs, we should see:
- **Database:** Query workflow data in <1s, generate reports easily
- **GitHub:** 100% of approved workflows have PRs automatically
- **Slack:** Team receives notifications within 30s of completion
- **Overall:** <5% overhead on total workflow time

---

## Next Steps

1. ✅ Document MCP integration plan (this file)
2. ⏳ Test current v2.1 workflow (in progress)
3. ⏳ Commit v2.1 changes
4. ⬜ Install PostgreSQL MCP
5. ⬜ Design database schema
6. ⬜ Implement Phase 1 (Database)
7. ⬜ Test and iterate
