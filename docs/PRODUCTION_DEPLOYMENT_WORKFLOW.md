# Production Deployment Workflow - AI Scrum Master v2.2

## Overview

This document describes the complete workflow from feature request (GitHub Issue) → Development → Testing → Staging → Production, with human checkpoints at critical moments.

---

## The Complete Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. BACKLOG (GitHub Issues)                                      │
│    - Feature requests tagged with labels                        │
│    - Pre-loaded with prompts, rules, design guidelines          │
│    - Prioritized and ready for development                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. SELECTION                                                     │
│    - Human or automated process selects issues to build          │
│    - Marks issue with "in-progress" label                       │
│    - AI Scrum Master picks up the issue                         │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. AI DEVELOPMENT                                                │
│    - Architect builds feature                                    │
│    - Security reviews and hardens                                │
│    - Tester writes and runs tests                               │
│    - Product Owner validates against requirements               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. PULL REQUEST CREATION                                         │
│    - PR created automatically with detailed description          │
│    - Includes AI metrics, changed files, test results           │
│    - Contains HUMAN REVIEW CHECKLIST                            │
│    - Links back to original issue                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. AUTOMATED CI/CD TESTS                                         │
│    - Unit tests run                                              │
│    - Integration tests run                                       │
│    - Security scans (npm audit, OWASP checks)                   │
│    - Linting and code quality checks                            │
│    - Build verification                                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 6. HUMAN REVIEW & TESTING ⚠️ CHECKPOINT                         │
│    - Review code changes                                         │
│    - Complete manual testing checklist                           │
│    - Verify no breaking changes                                 │
│    - Check for unintended side effects                          │
│    - Approve or request changes                                 │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 7. MERGE TO STAGING                                              │
│    - PR merged to 'staging' branch                              │
│    - Deploys to staging environment automatically               │
│    - Issue marked as "in-staging"                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 8. STAGING VALIDATION ⚠️ CHECKPOINT                             │
│    - QA team tests on staging environment                        │
│    - User acceptance testing (UAT)                              │
│    - Performance testing                                         │
│    - Final approval before production                           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ 9. PRODUCTION DEPLOYMENT                                         │
│    - Create release branch from staging                          │
│    - Deploy to production environment                            │
│    - Monitor for errors/issues                                  │
│    - Issue closed and marked "deployed"                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. GitHub Issues as Backlog

### Issue Template for Features

Create `.github/ISSUE_TEMPLATE/feature_request.md`:

```markdown
---
name: Feature Request
about: Request a new feature to be built by AI Scrum Master
title: '[FEATURE] '
labels: ['feature-request', 'needs-triage']
assignees: ''
---

## Feature Description
<!-- Clear, concise description of what you want built -->

## User Story
As a [type of user], I want [goal] so that [benefit].

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Design Guidelines
<!-- Specific design requirements, UI/UX considerations -->

## Technical Constraints
<!-- Technology stack, performance requirements, security requirements -->

## Project Scope
<!-- Which part of the system this affects -->
- [ ] Frontend
- [ ] Backend
- [ ] Database
- [ ] API
- [ ] Infrastructure

## Priority
- [ ] Critical (do immediately)
- [ ] High (do soon)
- [ ] Medium (normal queue)
- [ ] Low (nice to have)

## Additional Context
<!-- Screenshots, mockups, links to related issues -->
```

### Issue Labels

```
feature-request     # New feature to build
ready-for-dev       # Approved and ready to be picked up
in-progress         # AI Scrum Master is working on it
needs-review        # PR created, waiting for human review
in-staging          # Merged to staging, being tested
deployed            # Deployed to production
blocked             # Cannot proceed (needs more info)
```

---

## 2. Automated Issue Selection

### Option A: Manual Selection
Human adds `ready-for-dev` label to issues they want built.

### Option B: Automated Queue
AI Scrum Master runs periodically and picks up issues:

```python
# New module: issue_queue.py
import subprocess
import json

def get_ready_issues():
    """Get issues labeled 'ready-for-dev'"""
    result = subprocess.run([
        'gh', 'issue', 'list',
        '--label', 'ready-for-dev',
        '--json', 'number,title,body,labels',
        '--limit', '10'
    ], capture_output=True, text=True)

    return json.loads(result.stdout)

def mark_issue_in_progress(issue_number):
    """Mark issue as in-progress"""
    subprocess.run([
        'gh', 'issue', 'edit', str(issue_number),
        '--remove-label', 'ready-for-dev',
        '--add-label', 'in-progress'
    ])

    # Add comment
    subprocess.run([
        'gh', 'issue', 'comment', str(issue_number),
        '--body', '🤖 AI Scrum Master is now working on this feature...'
    ])

def link_pr_to_issue(issue_number, pr_url):
    """Link PR back to original issue"""
    subprocess.run([
        'gh', 'issue', 'comment', str(issue_number),
        '--body', f'✅ Pull request created: {pr_url}\n\nPlease review and test before merging.'
    ])
```

---

## 3. AI Development (Existing Workflow)

This is what we already have working! No changes needed here.

---

## 4. PR Creation with Human Review Checklist

### Enhanced PR Template

```python
def create_pr_with_checklist(workflow_result, issue_number=None):
    """Create PR with comprehensive human review checklist"""

    pr_body = f"""## 🤖 AI-Generated Feature Implementation

{f"**Related Issue:** #{issue_number}" if issue_number else ""}

### What Changed
{generate_change_summary(workflow_result)}

---

## ⚠️ HUMAN REVIEW CHECKLIST

Before merging, please verify:

### Code Quality
- [ ] Code follows project style guidelines
- [ ] No test artifacts left behind (test.html, temp.js, etc.)
- [ ] No unnecessary files renamed or deleted
- [ ] Comments are clear and helpful
- [ ] Error handling is appropriate

### Functionality
- [ ] Feature works as described in the issue
- [ ] No breaking changes to existing features
- [ ] Edge cases are handled properly
- [ ] User experience is intuitive

### Security
- [ ] No XSS vulnerabilities
- [ ] No SQL injection risks
- [ ] Input validation is present
- [ ] Authentication/authorization works correctly
- [ ] No sensitive data exposed

### Testing
- [ ] All automated tests pass ✓
- [ ] Manual testing completed
- [ ] Tested on multiple browsers (if frontend)
- [ ] Tested edge cases manually
- [ ] Performance is acceptable

### Documentation
- [ ] README updated if needed
- [ ] API documentation updated if needed
- [ ] User-facing changes documented

---

## 📊 AI Agent Metrics

| Agent | Cost | Duration | Status |
|-------|------|----------|--------|
| Architect | ${workflow_result.architect_result['cost_usd']:.3f} | {workflow_result.architect_result['duration_ms']/1000:.1f}s | ✅ |
| Security | ${workflow_result.security_result['cost_usd']:.3f} | {workflow_result.security_result['duration_ms']/1000:.1f}s | ✅ |
| Tester | ${workflow_result.tester_result['cost_usd']:.3f} | {workflow_result.tester_result['duration_ms']/1000:.1f}s | ✅ |
| Product Owner | ${workflow_result.po_result['cost_usd']:.3f} | {workflow_result.po_result['duration_ms']/1000:.1f}s | ✅ APPROVED |

**Total Cost:** ${workflow_result.total_cost:.2f}
**Total Duration:** {workflow_result.total_duration_ms/1000/60:.1f} minutes

---

## 📁 Files Changed

{list_changed_files_with_context(workflow_result)}

---

## 🧪 Test Results

{format_test_results(workflow_result)}

---

## 🔄 Next Steps

1. ✅ Review code changes above
2. ✅ Complete the checklist
3. ✅ Merge to `staging` branch (NOT main)
4. ✅ Test on staging environment
5. ✅ Create production release when ready

---

🤖 Generated by AI Scrum Master v2.2
⚠️  **IMPORTANT:** Merge to `staging` first, then to `main` after validation
"""

    # Create PR targeting staging branch
    result = subprocess.run([
        'gh', 'pr', 'create',
        '--title', f"Feature: {workflow_result.user_story[:60]}",
        '--body', pr_body,
        '--base', 'staging',  # NOT main!
        '--head', TESTER_BRANCH,
        '--label', 'needs-review'
    ], capture_output=True, text=True)

    return result.stdout.strip()
```

---

## 5. Automated CI/CD Tests

### GitHub Actions Workflow

Create `.github/workflows/ai-scrum-ci.yml`:

```yaml
name: AI Scrum Master CI

on:
  pull_request:
    branches: [staging, main]

jobs:
  test:
    runs-on: ubuntu-latest
    name: Automated Tests & Security Checks

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: |
          if [ -f package.json ]; then
            npm ci
          fi

      - name: Run unit tests
        run: |
          if [ -f package.json ] && npm run test --dry-run 2>/dev/null; then
            npm test
          else
            echo "No tests configured, skipping"
          fi

      - name: Run linting
        run: |
          if [ -f package.json ] && npm run lint --dry-run 2>/dev/null; then
            npm run lint
          else
            echo "No linting configured, skipping"
          fi

      - name: Security audit
        run: |
          if [ -f package.json ]; then
            npm audit --audit-level=high || echo "⚠️ Security vulnerabilities found"
          fi

      - name: Build verification
        run: |
          if [ -f package.json ] && npm run build --dry-run 2>/dev/null; then
            npm run build
          else
            echo "No build script, skipping"
          fi

      - name: Check for test artifacts
        run: |
          # Fail if suspicious files found
          if find . -name "test.html" -o -name "temp.*" -o -name "debug.*" | grep -q .; then
            echo "❌ Test artifacts found! Please clean up:"
            find . -name "test.html" -o -name "temp.*" -o -name "debug.*"
            exit 1
          fi
          echo "✅ No test artifacts found"

      - name: Comment test results
        if: always()
        uses: actions/github-script@v6
        with:
          script: |
            const status = '${{ job.status }}' === 'success' ? '✅' : '❌';
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `${status} Automated CI checks completed. Status: **${{ job.status }}**`
            })
```

---

## 6. Human Review Process

### Reviewer Checklist (in PR)

The PR body contains a comprehensive checklist. Reviewers should:

1. **Read the code changes** - Understand what was modified
2. **Check out the branch locally** - Test it yourself
   ```bash
   gh pr checkout <number>
   npm install
   npm test
   # Test manually in browser
   ```
3. **Complete the checklist** - Check off each item
4. **Approve or request changes** - Use GitHub's review feature

### Branch Protection Rules

Configure in GitHub Settings → Branches → `staging`:

```yaml
Branch protection rules for 'staging':
- Require pull request reviews before merging
- Require status checks to pass before merging
  - Required checks: AI Scrum Master CI / test
- Require branches to be up to date before merging
- Do not allow bypassing the above settings
```

---

## 7. Staging Deployment

### Automatic Deployment on Merge to Staging

Create `.github/workflows/deploy-staging.yml`:

```yaml
name: Deploy to Staging

on:
  push:
    branches: [staging]

jobs:
  deploy:
    runs-on: ubuntu-latest
    name: Deploy to Staging Environment

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Deploy to staging
        run: |
          # This depends on your hosting platform
          # Examples:

          # Option 1: Netlify
          # npx netlify-cli deploy --prod --dir=dist --site=${{ secrets.NETLIFY_STAGING_SITE_ID }}

          # Option 2: Vercel
          # npx vercel --prod --token=${{ secrets.VERCEL_TOKEN }}

          # Option 3: AWS S3
          # aws s3 sync ./dist s3://staging-bucket --delete

          # Option 4: Simple server
          # scp -r ./dist/* user@staging-server:/var/www/html/

          echo "Deployed to staging!"

      - name: Update issue status
        uses: actions/github-script@v6
        with:
          script: |
            // Find related issue and update label
            const { data: prs } = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'closed',
              sort: 'updated',
              direction: 'desc',
              per_page: 1
            });

            if (prs.length > 0) {
              const pr = prs[0];
              // Extract issue number from PR body
              const issueMatch = pr.body.match(/#(\d+)/);
              if (issueMatch) {
                const issueNumber = parseInt(issueMatch[1]);
                await github.rest.issues.update({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issueNumber,
                  labels: ['in-staging']
                });
                await github.rest.issues.createComment({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issueNumber,
                  body: '🚀 Feature deployed to staging environment for testing!'
                });
              }
            }
```

---

## 8. Staging Validation

### Manual Testing on Staging

1. **Access staging environment** (e.g., https://staging.yourapp.com)
2. **Perform UAT** (User Acceptance Testing):
   - Test the new feature end-to-end
   - Verify existing features still work
   - Check on different browsers/devices
   - Test edge cases
   - Performance testing
3. **Document results** in GitHub issue
4. **Approve for production** if everything passes

### Approval Process

Create a new PR: `staging` → `main`

```bash
# After staging validation passes:
gh pr create \
  --title "Release: [Feature Name] to Production" \
  --body "Staging validation complete. Ready for production deployment." \
  --base main \
  --head staging \
  --label "ready-for-production"
```

---

## 9. Production Deployment

### Production Deployment Workflow

Create `.github/workflows/deploy-production.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    name: Deploy to Production Environment

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Create release tag
        run: |
          VERSION=$(date +%Y.%m.%d-%H%M)
          git tag "release-$VERSION"
          git push origin "release-$VERSION"

      - name: Deploy to production
        run: |
          # Your production deployment commands
          echo "Deploying to production!"

      - name: Monitor for errors
        run: |
          # Set up monitoring, alerting, etc.
          echo "Production deployment complete!"

      - name: Close related issues
        uses: actions/github-script@v6
        with:
          script: |
            // Find and close related issues
            const { data: prs } = await github.rest.pulls.list({
              owner: context.repo.owner,
              repo: context.repo.repo,
              state: 'closed',
              base: 'main',
              sort: 'updated',
              direction: 'desc',
              per_page: 5
            });

            for (const pr of prs) {
              const issueMatch = pr.body.match(/#(\d+)/);
              if (issueMatch) {
                const issueNumber = parseInt(issueMatch[1]);
                await github.rest.issues.update({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issueNumber,
                  state: 'closed',
                  labels: ['deployed']
                });
                await github.rest.issues.createComment({
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  issue_number: issueNumber,
                  body: '🎉 Feature successfully deployed to production!'
                });
              }
            }
```

---

## Branch Strategy

```
main (production)
  ↑
  └── staging (pre-production)
        ↑
        └── feature branches (AI development)
              - ai-scrum-20251109-210556
              - ai-scrum-20251109-215432
              - etc.
```

### Branch Rules:

1. **Feature branches** → created by AI Scrum Master for each issue
2. **Staging branch** → PRs target this first
3. **Main branch** → only receives merges from staging after validation

---

## Configuration

```python
# config.py

DEPLOYMENT_CONFIG = {
    # Branch strategy
    "development_branch_prefix": "ai-scrum-",
    "staging_branch": "staging",
    "production_branch": "main",

    # PR configuration
    "pr_target_branch": "staging",  # PRs go to staging first
    "require_human_review": True,
    "include_review_checklist": True,

    # Deployment
    "auto_deploy_staging": True,   # Deploy to staging on merge
    "auto_deploy_production": True, # Deploy to prod on merge to main

    # Issue tracking
    "link_pr_to_issue": True,
    "auto_close_issues": True,
    "update_issue_labels": True,
}
```

---

## Initial Setup Steps

### 1. Create Staging Branch

```bash
git checkout -b staging
git push -u origin staging
```

### 2. Configure Branch Protection

```bash
# Protect staging branch
gh api repos/{owner}/{repo}/branches/staging/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}'

# Protect main branch
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":1}'
```

### 3. Create Issue Templates

```bash
mkdir -p .github/ISSUE_TEMPLATE
# Copy feature_request.md from examples
```

### 4. Create GitHub Actions Workflows

```bash
mkdir -p .github/workflows
# Copy workflow files from examples
```

### 5. Test the Pipeline

```bash
# 1. Create a test issue
gh issue create \
  --title "[FEATURE] Test feature for pipeline" \
  --body "Test the new deployment pipeline" \
  --label "feature-request,ready-for-dev"

# 2. Run AI Scrum Master
./run.sh --from-issues

# 3. Review the PR created
# 4. Merge to staging
# 5. Test on staging
# 6. Create PR to main
# 7. Deploy to production
```

---

## Summary: What You Get

✅ **Issue-Driven Development** - Features start as GitHub issues with clear requirements

✅ **Automated Development** - AI Scrum Master builds features from issues

✅ **Automated Testing** - CI runs tests, security scans, quality checks

✅ **Human Safety Checkpoints** - Humans review code and test before each stage

✅ **Staging Environment** - Safe place to test before production

✅ **Traceability** - Issues → PRs → Commits → Deployments all linked

✅ **Rollback Safety** - Tagged releases, separate branches, clear deployment history

✅ **Team Coordination** - Clear process for multiple developers/teams

---

## Questions to Answer

1. **Hosting Platform**: Where will you deploy? (Netlify, Vercel, AWS, custom server?)
2. **Staging Environment**: Do you already have a staging environment, or should we set one up?
3. **Issue Selection**: Manual (human picks issues) or automated (AI picks from queue)?
4. **Review Requirements**: How many human approvers needed before staging? Before production?
5. **Deployment Timing**: Deploy immediately on merge, or scheduled (e.g., nightly)?

---

This gives you a **production-ready deployment pipeline** with AI automation where it helps and human oversight where it matters.
