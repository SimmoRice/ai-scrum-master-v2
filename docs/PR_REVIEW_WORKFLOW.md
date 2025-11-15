# Pull Request Review Workflow

This guide explains the human review process for PRs created by AI workers.

## Overview

All pull requests created by AI workers are automatically labeled with `needs-review` and require human approval before merging. This ensures code quality and gives you full control over what gets merged into your repositories.

## Review Labels

The cluster uses three labels to manage the review workflow:

- 🟠 **needs-review**: PR created by worker, awaiting human review
- 🟢 **approved-for-merge**: Human has approved, ready to merge
- 🔴 **changes-requested**: Human requested changes

## Setup

Ensure review labels are configured in your repository:

```bash
cd ~/Development/repos/ai-scrum-master-v2

# Setup labels for a specific repo
python setup_repo_labels.py --repo owner/repo-name

# Setup labels for all monitored repos
python setup_repo_labels.py --all
```

## Review Workflow

### 1. List PRs Needing Review

```bash
# List PRs for a specific repository
python review_prs.py --repo owner/repo-name --list

# List PRs across all monitored repositories
python review_prs.py --all --list
```

Example output:
```
==========================================
PRs Needing Review
==========================================

📋 owner/calculator-app - 3 PR(s) need review:
================================================================================

#1: Setup project structure
  Author: ai-worker-1
  URL: https://github.com/owner/calculator-app/pull/1
  Created: 2025-01-15T10:30:00Z

#2: Implement calculator logic
  Author: ai-worker-2
  URL: https://github.com/owner/calculator-app/pull/2
  Created: 2025-01-15T10:45:00Z
  Labels: priority: high

#3: Add dark mode toggle
  Author: ai-worker-3
  URL: https://github.com/owner/calculator-app/pull/3
  Created: 2025-01-15T11:00:00Z
```

### 2. Review a PR

#### In Browser
```bash
# Open PR in browser
gh pr view 1 --repo owner/repo-name --web
```

#### Locally
```bash
# Check out the PR locally
gh pr checkout 1 --repo owner/repo-name

# View the changes
gh pr diff 1 --repo owner/repo-name

# Test the changes
cd path/to/repo
# Run tests, check functionality...

# Switch back to main when done
git checkout main
```

### 3. Approve a PR

Once you've reviewed and tested the changes:

```bash
# Simple approval (adds approved-for-merge label)
python review_prs.py --repo owner/repo-name --approve 1

# Approve with a comment
python review_prs.py --repo owner/repo-name --approve 1 \
  --comment "Great work! Tests pass and code looks good."

# Approve and merge immediately
python review_prs.py --repo owner/repo-name --approve 1 --merge

# Approve multiple PRs at once
python review_prs.py --repo owner/repo-name --approve 1,2,3

# Approve and merge all at once
python review_prs.py --repo owner/repo-name --approve 1,2,3 --merge
```

### 4. Request Changes

If the PR needs modifications:

```bash
# Request changes with explanation
python review_prs.py --repo owner/repo-name --request-changes 1 \
  --comment "Please add error handling for invalid input and add unit tests"
```

This will:
- Add a comment to the PR with your feedback
- Add the `changes-requested` label
- Remove the `needs-review` label

The worker will see this feedback in the issue and can retry the implementation.

### 5. Merge Approved PRs

#### Using the Review Script
```bash
# Approve and merge in one command
python review_prs.py --repo owner/repo-name --approve 1 --merge

# Choose merge method
python review_prs.py --repo owner/repo-name --approve 1 --merge --merge-method squash
python review_prs.py --repo owner/repo-name --approve 1 --merge --merge-method merge
python review_prs.py --repo owner/repo-name --approve 1 --merge --merge-method rebase
```

#### Manual Merge
```bash
# Merge directly with GitHub CLI
gh pr merge 1 --repo owner/repo-name --squash
gh pr merge 1 --repo owner/repo-name --merge
gh pr merge 1 --repo owner/repo-name --rebase
```

## Batch Operations

### Review Multiple Repositories

```bash
# List all PRs across all monitored repos
python review_prs.py --all --list
```

### Approve Multiple PRs

```bash
# Approve PRs 1, 2, and 3
python review_prs.py --repo owner/repo-name --approve 1,2,3

# Approve and merge all
python review_prs.py --repo owner/repo-name --approve 1,2,3 --merge
```

## Best Practices

### 1. Review Promptly
- Check for new PRs regularly
- Workers are waiting for your feedback
- Set up GitHub notifications for new PRs

### 2. Test Thoroughly
- Check out PRs locally when possible
- Run tests and verify functionality
- Look for edge cases

### 3. Provide Clear Feedback
- Be specific when requesting changes
- Reference specific files or lines
- Explain why changes are needed

### 4. Use Labels Consistently
- `approved-for-merge`: Only when you're confident it's ready
- `changes-requested`: When modifications are needed
- Workers use these labels to track progress

### 5. Merge Strategy
- **Squash**: Recommended for clean history (default)
- **Merge**: Preserves all commits
- **Rebase**: Linear history without merge commits

## Integration with GitHub

The review workflow integrates seamlessly with GitHub's native PR features:

- **Comments**: Add review comments directly on GitHub
- **Reviews**: Use GitHub's review feature for line-by-line feedback
- **Checks**: CI/CD checks still run on all PRs
- **Branch Protection**: Compatible with branch protection rules

## Automation Options

### Auto-Approve Low-Risk Changes

For repositories where you want to auto-approve certain types of changes:

```bash
# Example: Auto-approve documentation changes
gh pr list --repo owner/repo-name --label needs-review --label type:docs \
  --json number -q '.[] | .number' | \
  xargs -I {} python review_prs.py --repo owner/repo-name --approve {} --merge
```

### Scheduled Review Reminders

Set up a cron job to remind you of pending reviews:

```bash
# Add to crontab: Daily review reminder at 9 AM
0 9 * * * python ~/ai-scrum-master-v2/review_prs.py --all --list | mail -s "PRs Need Review" you@example.com
```

## Troubleshooting

### PR Missing `needs-review` Label

If a PR doesn't have the label:

```bash
# Add it manually
gh pr edit 1 --repo owner/repo-name --add-label needs-review
```

### Can't Approve PR

Ensure you have:
- GitHub CLI authenticated (`gh auth status`)
- Write access to the repository
- PR is not already merged

### Changes Not Applied

If requesting changes didn't work:
- Check GitHub CLI authentication
- Verify you have write access to the repo
- Check that the label exists (`gh label list --repo owner/repo-name`)

## Examples

### Complete Review Session

```bash
# 1. Check what needs review
python review_prs.py --all --list

# 2. Review first PR in browser
gh pr view 1 --repo owner/calculator-app --web

# 3. Test it locally
gh pr checkout 1 --repo owner/calculator-app
cd calculator-app
# Run tests...
python -m pytest
# Test manually...
open index.html

# 4. Looks good, approve and merge
cd ~/ai-scrum-master-v2
python review_prs.py --repo owner/calculator-app --approve 1 --merge

# 5. Next PR needs changes
python review_prs.py --repo owner/calculator-app --request-changes 2 \
  --comment "Add input validation for division by zero"

# 6. Third PR looks good too
python review_prs.py --repo owner/calculator-app --approve 3 --merge
```

### Batch Approval After Testing

```bash
# Review all PRs in browser
gh pr list --repo owner/calculator-app --label needs-review

# Test each one locally
for pr in 1 2 3; do
  gh pr checkout $pr --repo owner/calculator-app
  # Test...
done

# All look good, approve all at once
python review_prs.py --repo owner/calculator-app --approve 1,2,3 --merge
```

## Support

For issues or questions about the review workflow:
- 📖 Documentation: [docs/](../docs/)
- 🐛 Issues: https://github.com/SimmoRice/ai-scrum-master-v2/issues
- 💬 Discussions: GitHub Discussions
