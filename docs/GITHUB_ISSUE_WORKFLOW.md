# GitHub Issue Orchestration Workflow

This document explains how to use AI Scrum Master with GitHub issues for distributed agent workflows.

## Overview

AI Scrum Master can work with GitHub issues to:
1. Analyze existing projects and create issues
2. Fetch issues labeled as `ready-for-dev`
3. Implement features based on issue descriptions
4. Create PRs with comprehensive review checklists
5. Link PRs back to issues

## Quick Start

### 1. Setup a GitHub Repository

Use the setup script to prepare any local repository for AI Scrum Master:

```bash
# Basic usage (auto-detects repo name from directory)
python setup_github_repo.py ~/path/to/repo

# With custom name and description
python setup_github_repo.py ~/path/to/repo \
  --name my-project \
  --description "My awesome project"

# Create private repository
python setup_github_repo.py ~/path/to/repo --private
```

**What it does:**
- ✓ Initializes git if needed
- ✓ Creates GitHub repository
- ✓ Pushes code to GitHub
- ✓ Enables issues
- ✓ Creates workflow labels:
  - `ready-for-dev` - Ready for AI agent
  - `in-progress` - Currently being worked on
  - `needs-review` - Needs human review
  - `enhancement` - New feature
  - `bug` - Bug fix
  - `approved` - Approved by Product Owner

### 2. Create Issues

**Option A: Manually create issues on GitHub**

```bash
cd ~/path/to/repo
gh issue create \
  --title "Add dark mode" \
  --body "Implement dark mode theme toggle" \
  --label "ready-for-dev,enhancement"
```

**Option B: Use analysis scripts**

For projects that need feature enhancements, use specialized analysis scripts:

```bash
# Example: AI Calculator enhancements
python analyze_ai_calc.py

# Creates detailed issues with:
# - Clear requirements and constraints
# - Implementation guidelines
# - Testing checklists
# - Priority and complexity ratings
```

### 3. Run AI Scrum Master on Issues

**Single Issue Mode:**

```bash
# Work on a specific issue
python test_single_agent_github.py --issue 1

# With verbose output
python test_single_agent_github.py --issue 1 --verbose
```

**Auto-fetch Mode:**

```bash
# Automatically fetch and work on first ready-for-dev issue
python test_single_agent_github.py
```

## Workflow Stages

### Stage 1: Issue Created
- Issue is created with label `ready-for-dev`
- Contains clear description of feature/bug
- Includes acceptance criteria

### Stage 2: Agent Picks Up Work
- AI Scrum Master fetches issue
- Marks issue as `in-progress`
- Adds comment: "🤖 AI Scrum Master is now working on this feature..."

### Stage 3: Implementation
- All 4 agents run in sequence:
  1. **Architect** - Implements the feature
  2. **Security** - Reviews and hardens code
  3. **Tester** - Creates and runs tests
  4. **Product Owner** - Reviews and approves

### Stage 4: PR Created
- Feature branch is created
- PR is opened with:
  - Summary of changes
  - Human review checklist
  - Agent metrics (cost, duration)
  - Files changed
- PR is linked back to issue
- Issue updated to `needs-review`

### Stage 5: Human Review
Human reviewer:
1. Reviews code changes
2. Completes review checklist
3. Tests manually
4. Approves or requests changes
5. Merges to staging (not main)

### Stage 6: Production Release
After staging validation:
1. Merge staging → main
2. Close the issue
3. Deploy to production

## Labels and Their Meaning

| Label | Color | Meaning | Who Sets It |
|-------|-------|---------|-------------|
| `ready-for-dev` | Green | Ready for AI agent to work on | Human or analysis script |
| `in-progress` | Yellow | AI agent currently working | AI Scrum Master |
| `needs-review` | Red | Awaiting human review | AI Scrum Master |
| `enhancement` | Blue | New feature request | Human |
| `bug` | Red | Bug to fix | Human |
| `approved` | Green | Approved by PO | AI Scrum Master |

## Example Workflows

### Example 1: Add New Feature

```bash
# 1. Setup repository (if not already done)
python setup_github_repo.py ~/my-project

# 2. Create issue
cd ~/my-project
gh issue create \
  --title "Add user authentication" \
  --body "Implement JWT-based authentication system" \
  --label "ready-for-dev,enhancement"

# 3. Let AI implement it
python test_single_agent_github.py --issue 1 --verbose

# 4. Review the PR created by AI
# 5. Merge to staging and test
# 6. Merge staging to main
```

### Example 2: Fix Bug

```bash
# 1. Create bug issue
gh issue create \
  --title "Fix login redirect loop" \
  --body "Users get stuck in redirect loop after login" \
  --label "ready-for-dev,bug"

# 2. AI fixes it
python test_single_agent_github.py --issue 2

# 3. Review and merge
```

### Example 3: Multiple Features (Distributed)

For large projects with multiple features:

```bash
# 1. Analyze project and create issues
python analyze_ai_calc.py  # Creates issues #1 and #2

# 2. Work on issues in parallel (future: multiple agents)
# For now, run sequentially:
python test_single_agent_github.py --issue 1
python test_single_agent_github.py --issue 2

# 3. Review both PRs
# 4. Merge to staging and test integration
# 5. Merge to main
```

## Scripts Reference

### setup_github_repo.py

**Purpose**: Initialize a local repository on GitHub with all necessary labels

**Usage**:
```bash
python setup_github_repo.py <repo_path> [OPTIONS]
```

**Options**:
- `--name NAME` - Repository name (default: directory name)
- `--description DESC` - Repository description
- `--private` - Create private repository (default: public)

**Example**:
```bash
python setup_github_repo.py ~/my-app \
  --name my-awesome-app \
  --description "My awesome application"
```

### test_single_agent_github.py

**Purpose**: Run AI Scrum Master on a GitHub issue

**Usage**:
```bash
python test_single_agent_github.py [OPTIONS]
```

**Options**:
- `--issue NUMBER` - Specific issue number to work on
- `--verbose, -v` - Stream Claude Code output in real-time

**Example**:
```bash
# Auto-fetch first ready issue
python test_single_agent_github.py

# Work on specific issue with verbose output
python test_single_agent_github.py --issue 5 --verbose
```

### analyze_ai_calc.py

**Purpose**: Analyze ai-calc-2 project and create enhancement issues

**Usage**:
```bash
python analyze_ai_calc.py
```

**What it does**:
- Sets up GitHub repository if needed
- Creates Issue #1: Scientific calculator features
- Creates Issue #2: Custom color themes
- Both issues include detailed specifications

## Best Practices

### Issue Writing

**Good Issue:**
```markdown
## Title
Add dark mode toggle

## Description
Implement a dark mode theme that users can toggle between light and dark.

## Requirements
- Toggle button in settings
- Persist preference to localStorage
- Smooth transition animation

## Constraints
- Do not change existing layout
- Maintain accessibility (WCAG AA)

## Acceptance Criteria
- [ ] Toggle button works
- [ ] Preference persists across sessions
- [ ] All text remains readable in both modes
```

**Bad Issue:**
```markdown
make it dark
```

### PR Review Checklist

When reviewing AI-generated PRs, always check:

1. **Functionality**
   - Feature works as described
   - No breaking changes
   - Edge cases handled

2. **Code Quality**
   - Follows project conventions
   - No test artifacts (temp files, debug logs)
   - Clear comments

3. **Security**
   - Input validation present
   - No XSS/injection vulnerabilities
   - No sensitive data exposed

4. **Testing**
   - Tests pass
   - Coverage is adequate
   - Manual testing completed

### Staging First

**Always merge to staging before main:**

```bash
# ✓ Good
PR: feature-branch → staging
(test on staging)
PR: staging → main

# ✗ Bad
PR: feature-branch → main (dangerous!)
```

## Troubleshooting

### "Could not resolve to a Repository"

**Problem**: Repository doesn't exist on GitHub

**Solution**:
```bash
python setup_github_repo.py ~/path/to/repo
```

### "Label 'ready-for-dev' not found"

**Problem**: Labels haven't been created

**Solution**:
```bash
cd ~/path/to/repo
python setup_github_repo.py .  # Re-run setup
```

### "No issues found with label 'ready-for-dev'"

**Problem**: No issues are ready for development

**Solution**:
```bash
# Create an issue with the label
gh issue create \
  --title "Your feature" \
  --body "Description" \
  --label "ready-for-dev"
```

### "GitHub CLI not authenticated"

**Problem**: gh CLI needs authentication

**Solution**:
```bash
gh auth login
# Follow the prompts
```

## Future Enhancements

Planned features for distributed agent workflows:

1. **Multiple Agents in Parallel**
   - Multiple agents work on different issues simultaneously
   - Conflict resolution for overlapping changes

2. **Issue Dependencies**
   - Track dependencies between issues
   - Ensure prerequisites completed first

3. **Auto-prioritization**
   - AI analyzes issues and suggests priority order
   - Considers complexity, dependencies, value

4. **Progress Dashboard**
   - Web dashboard showing all agents and their progress
   - Real-time updates on what each agent is doing

5. **Distributed Architecture**
   - Multiple machines running agents
   - Centralized orchestrator managing work queue
   - Load balancing across agents

## See Also

- [Setup GitHub Integration](SETUP_GITHUB_INTEGRATION.md) - Initial GitHub setup guide
- [Production Deployment Workflow](PRODUCTION_DEPLOYMENT_WORKFLOW.md) - Full CI/CD pipeline
- [Analysis Mode](ANALYSIS_MODE.md) - Analysis-only mode documentation
