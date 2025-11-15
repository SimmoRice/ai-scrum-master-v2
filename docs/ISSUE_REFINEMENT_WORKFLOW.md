# Issue Refinement & Q&A Workflow

This document describes the Sprint Planning Q&A workflow that mimics real Scrum sprint planning meetings where developers ask clarifying questions before starting work.

## Overview

The AI Scrum Master now includes a two-phase approach to issue quality:

1. **Enhanced Issue Creation** - Create detailed user stories upfront with acceptance criteria
2. **Sprint Planning Q&A** - Workers analyze issues and ask questions before coding

This ensures workers have clear requirements and reduces wasted effort on unclear specifications.

## Phase 1: Enhanced Issue Creation

### What Changed

The `create_project_issues.py` script now generates much more detailed user stories by prompting Claude to include:

- **User Story Format**: "As a [role], I want [feature] so that [benefit]"
- **Background/Context**: Why the task is needed
- **Technical Approach**: High-level implementation strategy
- **Key Implementation Details**: Specific technologies, patterns, or approaches
- **Acceptance Criteria**: 3-5 specific, testable criteria
- **Edge Cases**: 2-3 scenarios to consider
- **Technical Notes**: Important considerations, constraints, or gotchas

### Example Issue Body

```markdown
As a developer, I want a properly configured Express.js backend with TypeScript so that we have a solid foundation for the API.

**Background:** This is the foundation of our backend API. We need TypeScript for type safety and better developer experience.

**Technical Approach:**
- Initialize Node.js project with TypeScript
- Configure Express.js with middleware
- Set up project structure (routes, controllers, models)
- Configure environment variables

**Key Details:**
- Use Express 4.x with TypeScript 5.x
- Implement middleware: cors, helmet, express-validator
- Structure: src/routes, src/controllers, src/models, src/middleware
- Use dotenv for configuration

## Acceptance Criteria

1. TypeScript compiles without errors
2. Express server starts on configured port
3. CORS is properly configured for frontend origin
4. Environment variables load from .env file
5. Basic health check endpoint returns 200 OK

## Edge Cases to Consider

- Server fails to start if port is already in use
- Environment variables missing - should show clear error
- Invalid TypeScript configuration - should fail build

## Technical Notes

Use ts-node-dev for development hot reload. Ensure tsconfig.json has strict mode enabled. Configure nodemon to ignore build directory.

---

**Phase:** 1 - Foundation
**Priority:** High
**Complexity:** Medium
**Dependencies:** None
```

### Usage

Create issues with enhanced detail:

```bash
python create_project_issues.py \
    --repo owner/repo-name \
    --project "Build a task management app with React and Node.js"
```

The script now:
- Uses 8000 max tokens (increased from 4000) for detailed responses
- Generates acceptance criteria, edge cases, and technical notes
- Formats issues with clear sections for easy reading

## Phase 2: Sprint Planning Q&A

### How It Works

When a worker picks up an issue labeled `ai-ready`, it goes through a **clarification check** before starting work:

1. **Worker requests work** from orchestrator
2. **Clarification Agent analyzes issue** using Claude
3. **If unclear**:
   - Generates 3-5 specific questions
   - Posts questions as GitHub comment
   - Adds `needs-clarification` label
   - Removes `ai-ready` label
   - Releases work back to queue
4. **If clear**: Proceeds with normal workflow

### Clarification Agent

The `ClarificationAgent` (in `worker/clarification_agent.py`) considers:

- Are requirements clear and unambiguous?
- Are acceptance criteria testable and complete?
- Are edge cases sufficiently covered?
- Is the technical approach feasible?
- Are there missing details about behavior, UI, or data?
- Are dependencies and integrations clear?

### Example Clarification Comment

```markdown
## ❓ Clarification Needed

The acceptance criteria mention "users can filter tasks" but don't specify the filtering options.

### Questions for Product Owner:

1. What fields should be available for filtering (status, priority, assignee, due date)?
2. Should users be able to combine multiple filters?
3. Should filter selections persist across sessions?
4. What should happen when no tasks match the filters?
5. Should there be a "clear all filters" option?

---
**Please answer these questions so development can proceed.**
Once answered, remove the `needs-clarification` label and re-add `ai-ready`.
```

### Worker Workflow

The updated worker flow:

```
1. Request work from orchestrator
2. Check if issue needs clarification ← NEW
   ├─ If YES: Post questions, update labels, release work
   └─ If NO: Continue to step 3
3. Setup isolated workspace
4. Run AI Scrum Master workflow
5. Push to GitHub and create PR
6. Report success to orchestrator
```

### Orchestrator Changes

The orchestrator now:

1. **Filters needs-clarification issues** when polling GitHub
2. **Handles work release** - new `/work/release` endpoint
3. **Doesn't assign** issues with `needs-clarification` label

## Manual Issue Refinement

### Use Case

You may want to refine existing issues before they go to the cluster. The `refine_issues.py` script provides a manual refinement process.

### Usage

**Refine all ai-ready issues:**
```bash
python refine_issues.py --repo owner/repo-name
```

**Refine specific issues:**
```bash
python refine_issues.py --repo owner/repo-name --issues 1,2,3
```

**Dry run (see what would happen):**
```bash
python refine_issues.py --repo owner/repo-name --dry-run
```

### Example Output

```
==============================================================
Issue Refinement Tool
==============================================================
Repository: SimmoRice/taskmaster-app
Fetching all issues with label 'ai-ready'...
Found 5 issues: 1, 2, 3, 4, 5

============================================================
Refining Issue #1
============================================================
Title: Setup Express.js backend with TypeScript
Labels: ai-ready, phase:1-foundation, priority:high

✅ Issue is clear - ready for work

============================================================
Refining Issue #2
============================================================
Title: Implement user authentication
Labels: ai-ready, phase:2-core-features, priority:high

❓ Issue needs clarification
Reason: Authentication method and session management not specified

Questions (4):
  1. Should we use JWT or session-based authentication?
  2. Do we need OAuth integration (Google, GitHub, etc.)?
  3. What password requirements should we enforce?
  4. Should sessions persist across browser restarts?

📝 Posting questions to GitHub...
🏷️  Updating labels...
✅ Issue refined - questions posted

==============================================================
Refinement Summary
==============================================================
Total issues: 5
Clear and ready: 4
Need clarification: 1

Issues needing clarification: 2

Next steps:
1. Review questions posted to these issues
2. Answer questions by editing issue body
3. Remove 'needs-clarification' label
4. Re-add 'ai-ready' label
```

## Answering Clarification Questions

When a worker or refinement script posts questions:

### Option 1: Edit Issue Body (Recommended)

1. Edit the issue on GitHub
2. Add an "Answers" section at the top or after the questions comment
3. Answer each question clearly
4. Remove `needs-clarification` label
5. Add `ai-ready` label back

### Option 2: Reply in Comments

1. Reply to the clarification comment
2. Answer each question
3. Remove `needs-clarification` label
4. Add `ai-ready` label back

**Note:** Workers will see the full issue body + comments when they pick up work, so either method works.

## Labels

### New Label: `needs-clarification`

- **Color:** `#D4C5F9` (purple)
- **Description:** "Issue needs clarification before work can begin"
- **Usage:** Added automatically by workers/refinement script
- **Effect:** Blocks issue from being assigned to workers

### Label Workflow

```
Issue Created
    ↓
[ai-ready] ← Created by create_project_issues.py (Phase 1 only)
    ↓
Worker/Refinement analyzes
    ├─ Clear → [ai-ready, ai-in-progress] → Work proceeds
    └─ Unclear → [needs-clarification] → Wait for answers
                      ↓
                 Human answers questions
                      ↓
                 Remove needs-clarification, add ai-ready
                      ↓
                 Worker picks up → [ai-ready, ai-in-progress]
```

## API Changes

### New Endpoint: `/work/release`

Workers can release work back to queue without marking as failed.

**Request:**
```json
POST /work/release
{
  "worker_id": "worker-01",
  "issue_number": 1
}
```

**Response:**
```json
{
  "status": "released"
}
```

**Effect:**
- Issue removed from worker's assignment
- Status changed back to "pending"
- Retry count NOT incremented (unlike /work/failed)
- Issue stays in queue for reassignment

## Best Practices

### When Creating Issues

1. **Be specific about requirements** - Include examples and edge cases
2. **Add acceptance criteria** - Make them testable
3. **Specify technical constraints** - Preferred libraries, patterns, etc.
4. **Include context** - Explain WHY the feature is needed

### When Answering Questions

1. **Be thorough** - Detailed answers prevent follow-up questions
2. **Update issue body** - Add answers to the original description
3. **Add examples** - Screenshots, mockups, or code examples help
4. **Consider edge cases** - Think through unusual scenarios

### When Refining Issues

1. **Run refinement before deployment** - Catch issues early
2. **Use dry-run first** - See what would change
3. **Batch refinement** - Refine all Phase 1 issues together
4. **Answer quickly** - Don't block the queue for too long

## Disabling Clarification Check

If you want workers to skip the clarification check (not recommended):

Edit `worker/distributed_worker.py` and comment out the clarification check:

```python
# Skip clarification check
# needs_clarification = check_issue_for_clarification(...)
# if needs_clarification:
#     ...
#     continue
```

Or set an environment variable:

```bash
# In worker .env file
SKIP_CLARIFICATION_CHECK=true
```

(Note: This env var support would need to be added to the code)

## Monitoring

### Orchestrator Logs

Watch for clarification activity:

```bash
# On Proxmox
pct exec 200 -- journalctl -u ai-orchestrator -f | grep -i clarification
```

You'll see:
```
Skipping issue SimmoRice/taskmaster-app#2: needs clarification
```

### Worker Logs

Watch for workers posting questions:

```bash
pct exec 201 -- journalctl -u ai-worker -f | grep -i clarification
```

You'll see:
```
❓ Issue #2 needs clarification
   Reason: Authentication method not specified
   Questions: 4
⏸️  Issue #2 needs clarification - questions posted to GitHub
```

### GitHub

Monitor issues with clarification label:

```bash
gh issue list --repo owner/repo-name --label needs-clarification
```

## Troubleshooting

### Questions Not Being Posted

**Symptom:** Worker logs show clarification needed but no GitHub comment appears

**Check:**
1. GitHub token has write permissions (`repo` scope)
2. `gh` CLI is authenticated: `gh auth status`
3. Worker has network access to GitHub

**Fix:**
```bash
# Re-authenticate gh CLI
gh auth login

# Test manually
gh issue comment 1 --repo owner/repo --body "Test"
```

### Issues Stuck in needs-clarification

**Symptom:** Issues have `needs-clarification` label but questions were answered

**Fix:**
```bash
# Manually remove label and re-add ai-ready
gh issue edit ISSUE_NUMBER --repo owner/repo \
    --remove-label needs-clarification \
    --add-label ai-ready
```

### Worker Keeps Asking Same Questions

**Symptom:** Every time issue is released, worker asks same questions

**Cause:** Clarification check runs on every work assignment

**Fix:** Answer questions in issue body, not just comments. Worker sees full issue body each time.

### Too Many Issues Needing Clarification

**Symptom:** Most issues get flagged for clarification

**Solution:**
1. Improve project description when creating issues
2. Add more detail to create_project_issues.py prompt
3. Run `refine_issues.py --dry-run` first to see what's unclear
4. Answer common questions in a "Development Guidelines" document

## Future Enhancements

Potential improvements to the Q&A workflow:

1. **Smart Context** - Remember previous answers for similar questions
2. **Question Templates** - Common questions for different issue types
3. **Auto-Answer** - Use AI to suggest answers based on project context
4. **Interactive Refinement** - CLI tool that asks questions interactively
5. **Clarification Metrics** - Track which issues need most clarification

---

**Created:** 2025-11-15
**Version:** 1.0
**Related Docs:**
- [Creating Project Issues](CREATE_GITHUB_ISSUE.md)
- [GitHub Issue Workflow](GITHUB_ISSUE_WORKFLOW.md)
- [Distributed Architecture](../DISTRIBUTED_ARCHITECTURE.md)
