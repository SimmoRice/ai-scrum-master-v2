# GitHub Integration Setup Guide

## Quick Start (5 minutes)

### Prerequisites
- Git repository (local or pushed to GitHub)
- GitHub CLI installed

### Step 1: Install GitHub CLI

```bash
# macOS
brew install gh

# Linux (Ubuntu/Debian)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

### Step 2: Authenticate with GitHub

```bash
gh auth login
```

Follow the prompts:
- Choose **GitHub.com**
- Choose **HTTPS**
- Authenticate via **browser**

### Step 3: Push Your Repository (if not already on GitHub)

```bash
# Create a new repository on GitHub (via browser or CLI)
gh repo create ai-scrum-master-v2 --public --source=. --remote=origin --push

# Or connect to existing repository
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
git push origin staging
```

### Step 4: Test GitHub Integration

```bash
# Verify gh CLI works
gh auth status

# Test PR creation (optional - will create a test PR)
git checkout -b test-branch
echo "test" > test.txt
git add test.txt
git commit -m "Test commit"
git push -u origin test-branch
gh pr create --title "Test PR" --body "Testing GitHub integration" --base staging
```

---

## Configuration

### Enable/Disable GitHub Integration

Edit `config.py`:

```python
# GitHub Integration (v2.2)
GITHUB_CONFIG = {
    "enabled": True,  # Set to False to disable
    "auto_create_pr": True,
    "pr_target_branch": "staging",
    "include_review_checklist": True,
    "link_pr_to_issue": True,
    "require_manual_review": True,
}
```

---

## Workflow Overview

1. **Run AI Scrum Master**: `./run.sh "your user story"`
2. **Agents complete work**: Architect → Security → Tester → PO
3. **PO approves**: Workflow creates PR automatically
4. **You review PR**: Check code changes, complete checklist
5. **Merge to staging**: After your approval
6. **Test on staging**: Manual UAT testing
7. **Merge to main**: Production deployment

---

## What Gets Created Automatically

### Pull Request
- **Target branch**: `staging` (not `main`)
- **Title**: "Feature: {user story}"
- **Body**: Includes:
  - Link to original issue (if applicable)
  - Comprehensive review checklist
  - AI agent metrics (cost, duration)
  - List of changed files
  - Next steps

### GitHub Actions CI
- Runs automatically on every PR
- Tests, linting, security audit
- Checks for test artifacts
- Comments results on PR

---

## GitHub Actions Workflows

Three workflows are included:

### 1. `ai-scrum-ci.yml` - Continuous Integration
**Triggers**: Pull request to `staging` or `main`

**Actions**:
- Install dependencies (if package.json exists)
- Run tests
- Run linting
- Security audit (npm audit)
- Check for test artifacts
- Comment results on PR

### 2. `deploy-staging.yml` - Staging Deployment
**Triggers**: Push to `staging` branch

**Actions**:
- Build project
- Prepare deployment (currently local instructions)
- Update linked GitHub issue with "in-staging" label
- Add comment with staging deployment info

**Note**: Deploy step includes instructions for Proxmox deployment (customize for your setup)

### 3. `deploy-production.yml` - Production Deployment
**Triggers**: Push to `main` branch

**Actions**:
- Build project
- Create release tag (`release-YYYY.MM.DD-HHMM`)
- Prepare deployment (currently local instructions)
- Close linked GitHub issue with "deployed" label
- Add success comment

**Note**: Deploy step includes instructions for Proxmox deployment (customize for your setup)

---

## Customizing for Proxmox Deployment

Edit `.github/workflows/deploy-staging.yml` and `.github/workflows/deploy-production.yml`:

### Example: Deploy to Proxmox via SCP

```yaml
- name: Deploy to staging
  run: |
    # Build the project
    if [ -f package.json ]; then
      npm run build
    fi

    # Package files
    tar -czf staging-$(date +%Y%m%d-%H%M%S).tar.gz dist/

    # Transfer to Proxmox staging server
    scp staging-*.tar.gz ${{ secrets.PROXMOX_USER }}@${{ secrets.PROXMOX_STAGING_HOST }}:/path/to/staging/

    # Extract on remote server
    ssh ${{ secrets.PROXMOX_USER }}@${{ secrets.PROXMOX_STAGING_HOST }} \
      "cd /path/to/staging && tar -xzf staging-*.tar.gz"

    # Restart service if needed
    ssh ${{ secrets.PROXMOX_USER }}@${{ secrets.PROXMOX_STAGING_HOST }} \
      "systemctl restart your-app"
```

### Required GitHub Secrets

Add these in GitHub Settings → Secrets:
- `PROXMOX_USER`: SSH username for Proxmox
- `PROXMOX_STAGING_HOST`: Staging server hostname/IP
- `PROXMOX_PRODUCTION_HOST`: Production server hostname/IP

---

## Issue-Driven Development (Optional)

You can drive development from GitHub Issues:

### 1. Create Feature Request Issue
Use the template: `.github/ISSUE_TEMPLATE/feature_request.md`

### 2. Label Issue as Ready
Add label: `ready-for-dev`

### 3. AI Scrum Master Picks It Up
```python
# Future enhancement - automatic issue queue processing
from github_integration import GitHubIntegration

github = GitHubIntegration(GITHUB_CONFIG)
issues = github.get_ready_issues(label='ready-for-dev')

for issue in issues:
    github.mark_issue_in_progress(issue['number'])
    result = orchestrator.process_user_story(issue['body'])
    # PR will be linked back to issue automatically
```

---

## Troubleshooting

### PR creation fails: "not authenticated"
```bash
gh auth login
gh auth status  # Verify authentication
```

### PR creation fails: "already exists"
You already have a PR for this branch. Either:
- Close the existing PR: `gh pr close <number>`
- Use a different branch name

### GitHub Actions not running
- Ensure workflows are pushed to GitHub
- Check repository Settings → Actions (must be enabled)
- Verify workflow files are in `.github/workflows/`

### Cannot push to GitHub
```bash
# Check remote
git remote -v

# Add remote if missing
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Push branches
git push -u origin main
git push -u origin staging
```

---

## Next Steps

After setup:

1. ✅ Run a test workflow
2. ✅ Verify PR is created
3. ✅ Review the PR checklist
4. ✅ Test merging to staging
5. ✅ Customize deployment workflows for your Proxmox setup
6. ✅ Set up Slack notifications (future enhancement)
7. ✅ Set up PostgreSQL metrics (future enhancement)

---

## Security Considerations

- **GitHub CLI authentication**: Uses OAuth (more secure than personal access tokens)
- **No auto-merge**: Human review required before merging
- **Branch protection**: Configure in GitHub Settings → Branches
- **Secret management**: Use GitHub Secrets for sensitive data (Proxmox credentials)
- **Audit logs**: GitHub maintains complete audit trail of all actions

---

## Benefits of This Setup

✅ **Traceability**: Every feature tracked from issue → PR → deployment

✅ **Quality Gates**: Automated tests + human review

✅ **Safe Deployments**: Staging environment before production

✅ **Clear Process**: Everyone knows the workflow

✅ **Audit Trail**: Complete history in GitHub

✅ **Team Collaboration**: PRs enable code review and discussion

✅ **Rollback Safety**: Git history + release tags enable easy rollbacks
