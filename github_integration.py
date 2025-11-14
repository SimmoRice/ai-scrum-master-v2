"""
GitHub Integration for AI Scrum Master

Handles:
- Issue queue management
- Pull request creation with review checklists
- Issue status updates
- PR-to-issue linking
"""

import subprocess
import json
import re
from datetime import datetime
from typing import Optional, Dict, List, Any
from utils import validate_issue_number, validate_github_label, sanitize_github_text


class GitHubIntegration:
    """GitHub integration using GitHub CLI (gh)"""

    def __init__(self, config: Dict[str, Any], workspace_dir: Optional[Any] = None):
        """
        Initialize GitHub integration

        Args:
            config: Configuration dict with GitHub settings
            workspace_dir: Optional workspace directory path for git/gh commands
        """
        self.config = config
        self.base_branch = config.get('pr_target_branch', 'staging')
        self.include_checklist = config.get('include_review_checklist', True)
        self.workspace_dir = str(workspace_dir) if workspace_dir else None

    @staticmethod
    def _validate_issue_number(issue_number: int) -> None:
        """
        Validate GitHub issue number to prevent injection

        Security: Ensures issue number is a positive integer
        Now uses shared validation from utils module.

        Args:
            issue_number: Issue number to validate

        Raises:
            ValueError: If issue number is invalid
        """
        if not validate_issue_number(issue_number):
            raise ValueError(f"Security: Invalid issue number: {issue_number}")

    @staticmethod
    def _validate_label(label: str) -> None:
        """
        Validate GitHub label to prevent command injection

        Security: Ensures label contains only safe characters
        Now uses shared validation from utils module.

        Args:
            label: Label to validate

        Raises:
            ValueError: If label contains dangerous characters
        """
        if validate_github_label(label) is None:
            raise ValueError(f"Security: Invalid label format: {label}")

    # _sanitize_text now uses sanitize_github_text from utils module

    def check_gh_cli_installed(self) -> bool:
        """Check if GitHub CLI is installed and authenticated"""
        try:
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_ready_issues(self, label='ready-for-dev', limit=10) -> List[Dict]:
        """
        Get issues labeled as ready for development

        Args:
            label: GitHub label to filter by
            limit: Maximum number of issues to return

        Returns:
            List of issue dicts with number, title, body, labels
        """
        # Security: Validate label to prevent command injection
        self._validate_label(label)

        # Security: Validate limit to prevent abuse
        if not isinstance(limit, int) or limit <= 0 or limit > 100:
            raise ValueError(f"Security: Invalid limit value: {limit}")

        if not self.check_gh_cli_installed():
            print("⚠️  GitHub CLI not installed or not authenticated")
            print("   Install: brew install gh")
            print("   Authenticate: gh auth login")
            return []

        try:
            result = subprocess.run([
                'gh', 'issue', 'list',
                '--label', label,
                '--json', 'number,title,body,labels',
                '--limit', str(limit)
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                # Security: Don't expose full error details
                print(f"⚠️  Failed to fetch issues")
                return []

        except subprocess.TimeoutExpired:
            print("⚠️  GitHub CLI timed out")
            return []
        except json.JSONDecodeError as e:
            # Security: Don't expose full error details
            print(f"⚠️  Failed to parse GitHub response")
            return []

    def mark_issue_in_progress(self, issue_number: int) -> bool:
        """
        Mark issue as in-progress

        Args:
            issue_number: GitHub issue number

        Returns:
            True if successful
        """
        # Security: Validate issue number to prevent command injection
        self._validate_issue_number(issue_number)

        try:
            # Remove ready-for-dev label
            subprocess.run([
                'gh', 'issue', 'edit', str(issue_number),
                '--remove-label', 'ready-for-dev'
            ], capture_output=True, timeout=5)

            # Add in-progress label
            subprocess.run([
                'gh', 'issue', 'edit', str(issue_number),
                '--add-label', 'in-progress'
            ], capture_output=True, timeout=5)

            # Add comment
            subprocess.run([
                'gh', 'issue', 'comment', str(issue_number),
                '--body', '🤖 AI Scrum Master is now working on this feature...'
            ], capture_output=True, timeout=5)

            return True

        except subprocess.TimeoutExpired:
            print(f"⚠️  Timeout updating issue #{issue_number}")
            return False

    def _ensure_base_branch_exists(self) -> str:
        """
        Ensure the base branch exists, creating it from main if needed

        Returns:
            The base branch name to use for PR
        """
        # Check if staging branch exists
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--verify', self.base_branch],
                cwd=self.workspace_dir,
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"✓ Base branch '{self.base_branch}' exists")
                return self.base_branch

        except subprocess.TimeoutExpired:
            pass

        # Staging branch doesn't exist - check if we should create it or use main
        print(f"⚠️  Base branch '{self.base_branch}' doesn't exist")

        # Check if main branch exists
        try:
            main_check = subprocess.run(
                ['git', 'rev-parse', '--verify', 'main'],
                cwd=self.workspace_dir,
                capture_output=True,
                timeout=5
            )

            if main_check.returncode == 0:
                print(f"→ Using 'main' as base branch instead")
                return 'main'

        except subprocess.TimeoutExpired:
            pass

        # Default to main
        print("→ Defaulting to 'main' as base branch")
        return 'main'

    def create_pr(
        self,
        workflow_result: Any,
        issue_number: Optional[int] = None
    ) -> Optional[str]:
        """
        Create pull request with comprehensive review checklist

        Args:
            workflow_result: WorkflowResult object from orchestrator
            issue_number: Optional GitHub issue number to link

        Returns:
            PR URL if successful, None otherwise
        """
        # Security: Validate issue number if provided
        if issue_number is not None:
            self._validate_issue_number(issue_number)

        if not self.check_gh_cli_installed():
            raise Exception(
                "GitHub CLI not installed or authenticated. "
                "Run: gh auth login"
            )

        # Ensure base branch exists and get the actual base to use
        actual_base_branch = self._ensure_base_branch_exists()

        # Generate PR title - sanitize user story
        sanitized_story = sanitize_github_text(workflow_result.user_story, max_length=200)
        pr_title = f"Feature: {sanitized_story[:60]}"
        if len(sanitized_story) > 60:
            pr_title += "..."

        # Generate PR body with checklist (pass actual base branch)
        pr_body = self._generate_pr_body(workflow_result, issue_number, actual_base_branch)

        # Get current branch name (feature branch created by tester)
        try:
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            head_branch = branch_result.stdout.strip()

        except subprocess.TimeoutExpired:
            print("⚠️  Could not determine current branch")
            head_branch = "HEAD"

        # Create PR
        try:
            result = subprocess.run([
                'gh', 'pr', 'create',
                '--title', pr_title,
                '--body', pr_body,
                '--base', actual_base_branch,
                '--head', head_branch,
                '--label', 'needs-review'
            ], cwd=self.workspace_dir, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                pr_url = result.stdout.strip()
                print(f"\n✅ Pull request created: {pr_url}")

                # Link PR back to issue if provided
                if issue_number:
                    self._link_pr_to_issue(issue_number, pr_url)

                return pr_url
            else:
                error_msg = result.stderr
                if "already exists" in error_msg:
                    print(f"⚠️  PR already exists for branch {head_branch}")
                    # Try to get existing PR URL
                    existing_pr = subprocess.run([
                        'gh', 'pr', 'list',
                        '--head', head_branch,
                        '--json', 'url',
                        '--limit', '1'
                    ], cwd=self.workspace_dir, capture_output=True, text=True, timeout=5)

                    if existing_pr.returncode == 0:
                        prs = json.loads(existing_pr.stdout)
                        if prs:
                            return prs[0]['url']

                raise Exception(f"PR creation failed: {error_msg}")

        except subprocess.TimeoutExpired:
            raise Exception("PR creation timed out")

    def _generate_pr_body(
        self,
        workflow_result: Any,
        issue_number: Optional[int],
        base_branch: str = None
    ) -> str:
        """Generate PR body with review checklist"""

        # Use provided base branch or fall back to configured one
        if base_branch is None:
            base_branch = self.base_branch

        # Calculate agent metrics
        architect = workflow_result.agents[0]
        security = workflow_result.agents[1]
        tester = workflow_result.agents[2]
        po = workflow_result.agents[3]

        # Get file changes from git
        try:
            diff_result = subprocess.run(
                ['git', 'diff', '--name-status', base_branch],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=5
            )
            files_changed = diff_result.stdout.strip()
        except subprocess.TimeoutExpired:
            files_changed = "(Could not determine changed files)"

        body = f"""## 🤖 AI-Generated Feature Implementation

{f"**Related Issue:** #{issue_number}" if issue_number else ""}

### What Changed
{workflow_result.user_story}

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
- [ ] Feature works as described{f" in issue #{issue_number}" if issue_number else ""}
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
| Architect | ${architect['cost_usd']:.3f} | {architect['duration_ms']/1000:.1f}s | ✅ |
| Security | ${security['cost_usd']:.3f} | {security['duration_ms']/1000:.1f}s | ✅ |
| Tester | ${tester['cost_usd']:.3f} | {tester['duration_ms']/1000:.1f}s | ✅ |
| Product Owner | ${po['cost_usd']:.3f} | {po['duration_ms']/1000:.1f}s | ✅ APPROVED |

**Total Cost:** ${workflow_result.total_cost:.2f}
**Total Duration:** {workflow_result.total_duration_ms/1000/60:.1f} minutes
**Revisions:** {workflow_result.revision_count}

---

## 📁 Files Changed

```
{files_changed}
```

---

## 🔄 Next Steps

1. ✅ Review code changes above
2. ✅ Complete the checklist
3. ✅ Merge to `{base_branch}` branch{" (NOT main)" if base_branch != "main" else ""}
4. ✅ Test on staging environment
5. ✅ Create production release when ready

---

🤖 Generated by AI Scrum Master v2.2
⚠️  **IMPORTANT:** {"Merge to staging first, then to main after validation" if base_branch != "main" else "Thoroughly test before deploying to production"}
"""
        return body

    def _link_pr_to_issue(self, issue_number: int, pr_url: str) -> None:
        """Link PR back to issue with comment"""
        # Security: Validate issue number
        self._validate_issue_number(issue_number)

        # Security: Sanitize PR URL to prevent injection
        pr_url = sanitize_github_text(pr_url, max_length=500)

        try:
            subprocess.run([
                'gh', 'issue', 'comment', str(issue_number),
                '--body', f"""✅ **Pull request created:** {pr_url}

Please review and test before merging to staging.

**Next Steps:**
1. Review the code changes in the PR
2. Complete the review checklist
3. Test the feature manually
4. Approve and merge to staging
5. Perform UAT on staging environment
"""
            ], capture_output=True, timeout=5)

            # Update label
            subprocess.run([
                'gh', 'issue', 'edit', str(issue_number),
                '--remove-label', 'in-progress',
                '--add-label', 'needs-review'
            ], capture_output=True, timeout=5)

        except subprocess.TimeoutExpired:
            print(f"⚠️  Could not link PR to issue #{issue_number}")

    def get_issue_details(self, issue_number: int) -> Optional[Dict]:
        """
        Get details for a specific issue

        Args:
            issue_number: GitHub issue number

        Returns:
            Issue dict or None
        """
        # Security: Validate issue number to prevent command injection
        self._validate_issue_number(issue_number)

        try:
            result = subprocess.run([
                'gh', 'issue', 'view', str(issue_number),
                '--json', 'number,title,body,labels,state'
            ], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                return None

        except (subprocess.TimeoutExpired, json.JSONDecodeError):
            return None
