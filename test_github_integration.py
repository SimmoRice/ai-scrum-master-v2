"""
Test suite for github_integration.py

Tests GitHub integration with mocking to avoid actual GitHub API calls.
Covers happy paths, edge cases, error handling, and security validations.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from github_integration import GitHubIntegration


class TestGitHubIntegrationInitialization:
    """Test GitHub integration initialization"""

    def test_init_with_config(self):
        """Test initialization with configuration"""
        config = {
            "enabled": True,
            "pr_target_branch": "staging",
            "include_review_checklist": True
        }

        github = GitHubIntegration(config)

        assert github.config == config
        assert github.base_branch == "staging"
        assert github.include_checklist is True

    def test_init_with_default_values(self):
        """Test initialization with minimal config"""
        config = {}

        github = GitHubIntegration(config)

        # Should use defaults
        assert github.base_branch == "staging"
        assert github.include_checklist is True


class TestSecurityValidations:
    """Test security validation methods"""

    def test_validate_issue_number_accepts_valid(self):
        """Test that valid issue numbers are accepted"""
        valid_numbers = [1, 42, 100, 9999]

        for num in valid_numbers:
            # Should not raise exception
            GitHubIntegration._validate_issue_number(num)

    def test_validate_issue_number_rejects_negative(self):
        """Security: Test that negative issue numbers are rejected"""
        with pytest.raises(ValueError, match="Security"):
            GitHubIntegration._validate_issue_number(-1)

    def test_validate_issue_number_rejects_zero(self):
        """Security: Test that zero is rejected"""
        with pytest.raises(ValueError, match="Security"):
            GitHubIntegration._validate_issue_number(0)

    def test_validate_issue_number_rejects_non_integer(self):
        """Security: Test that non-integers are rejected"""
        invalid_values = ["42", 42.5, None, [], {}]

        for value in invalid_values:
            with pytest.raises(ValueError, match="Security"):
                GitHubIntegration._validate_issue_number(value)

    def test_validate_label_accepts_valid(self):
        """Test that valid labels are accepted"""
        valid_labels = [
            "ready-for-dev",
            "in-progress",
            "bug",
            "feature_request",
            "v1-0-0"
        ]

        for label in valid_labels:
            # Should not raise exception
            GitHubIntegration._validate_label(label)

    def test_validate_label_rejects_special_chars(self):
        """Security: Test that labels with special characters are rejected"""
        invalid_labels = [
            "label;rm -rf /",
            "label&whoami",
            "label|cat /etc/passwd",
            "label$HOME",
            "label`whoami`",
            "label<script>",
            "label with spaces",
        ]

        for label in invalid_labels:
            with pytest.raises(ValueError, match="Security"):
                GitHubIntegration._validate_label(label)

    def test_validate_label_rejects_too_long(self):
        """Security: Test that overly long labels are rejected"""
        long_label = "a" * 100

        with pytest.raises(ValueError, match="Security"):
            GitHubIntegration._validate_label(long_label)

    def test_sanitize_text_removes_null_bytes(self):
        """Security: Test that null bytes are removed"""
        text = "Test\0text\0with\0nulls"
        sanitized = GitHubIntegration._sanitize_text(text)

        assert "\0" not in sanitized

    def test_sanitize_text_removes_control_chars(self):
        """Security: Test that control characters are removed"""
        text = "Test\x01\x02\x03text"
        sanitized = GitHubIntegration._sanitize_text(text)

        assert "\x01" not in sanitized
        assert "\x02" not in sanitized
        assert "\x03" not in sanitized

    def test_sanitize_text_limits_length(self):
        """Security: Test that text is length-limited"""
        long_text = "A" * 20000
        sanitized = GitHubIntegration._sanitize_text(long_text, max_length=5000)

        assert len(sanitized) <= 5100  # 5000 + truncation message

    def test_sanitize_text_preserves_newlines_and_tabs(self):
        """Test that newlines and tabs are preserved"""
        text = "Line 1\nLine 2\tTabbed"
        sanitized = GitHubIntegration._sanitize_text(text)

        assert "\n" in sanitized
        assert "\t" in sanitized


class TestGitHubCliCheck:
    """Test GitHub CLI availability checking"""

    @patch('github_integration.subprocess.run')
    def test_check_gh_cli_installed_success(self, mock_run):
        """Test checking when gh CLI is installed and authenticated"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = github.check_gh_cli_installed()

        assert result is True
        mock_run.assert_called_once()

    @patch('github_integration.subprocess.run')
    def test_check_gh_cli_not_authenticated(self, mock_run):
        """Test checking when gh CLI is not authenticated"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        result = github.check_gh_cli_installed()

        assert result is False

    @patch('github_integration.subprocess.run')
    def test_check_gh_cli_not_installed(self, mock_run):
        """Test checking when gh CLI is not installed"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_run.side_effect = FileNotFoundError()

        result = github.check_gh_cli_installed()

        assert result is False

    @patch('github_integration.subprocess.run')
    def test_check_gh_cli_timeout(self, mock_run):
        """Test handling of timeout when checking gh CLI"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("gh", 5)

        result = github.check_gh_cli_installed()

        assert result is False


class TestGetReadyIssues:
    """Test getting ready issues from GitHub"""

    @patch('github_integration.GitHubIntegration.check_gh_cli_installed')
    @patch('github_integration.subprocess.run')
    def test_get_ready_issues_success(self, mock_run, mock_check):
        """Test successfully getting ready issues"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_check.return_value = True

        issues_data = [
            {
                "number": 1,
                "title": "Feature 1",
                "body": "Description 1",
                "labels": [{"name": "ready-for-dev"}]
            },
            {
                "number": 2,
                "title": "Feature 2",
                "body": "Description 2",
                "labels": [{"name": "ready-for-dev"}]
            }
        ]

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(issues_data)
        mock_run.return_value = mock_result

        issues = github.get_ready_issues()

        assert len(issues) == 2
        assert issues[0]["number"] == 1
        assert issues[1]["number"] == 2

    @patch('github_integration.GitHubIntegration.check_gh_cli_installed')
    def test_get_ready_issues_gh_not_installed(self, mock_check):
        """Test getting issues when gh CLI is not installed"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_check.return_value = False

        issues = github.get_ready_issues()

        assert issues == []

    @patch('github_integration.GitHubIntegration.check_gh_cli_installed')
    @patch('github_integration.subprocess.run')
    def test_get_ready_issues_command_fails(self, mock_run, mock_check):
        """Test handling of command failure"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_check.return_value = True

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Error"
        mock_run.return_value = mock_result

        issues = github.get_ready_issues()

        assert issues == []

    @patch('github_integration.GitHubIntegration.check_gh_cli_installed')
    @patch('github_integration.subprocess.run')
    def test_get_ready_issues_invalid_json(self, mock_run, mock_check):
        """Test handling of invalid JSON response"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_check.return_value = True

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Not valid JSON"
        mock_run.return_value = mock_result

        issues = github.get_ready_issues()

        assert issues == []

    @patch('github_integration.GitHubIntegration.check_gh_cli_installed')
    @patch('github_integration.subprocess.run')
    def test_get_ready_issues_custom_label(self, mock_run, mock_check):
        """Test getting issues with custom label"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_check.return_value = True

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([])
        mock_run.return_value = mock_result

        github.get_ready_issues(label="custom-label", limit=5)

        # Check that custom label was passed
        call_args = mock_run.call_args[0][0]
        assert "custom-label" in call_args

    def test_get_ready_issues_validates_limit(self):
        """Security: Test that limit parameter is validated"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        # Invalid limits
        with pytest.raises(ValueError, match="Security"):
            github.get_ready_issues(limit=-1)

        with pytest.raises(ValueError, match="Security"):
            github.get_ready_issues(limit=0)

        with pytest.raises(ValueError, match="Security"):
            github.get_ready_issues(limit=1000)


class TestMarkIssueInProgress:
    """Test marking issues as in-progress"""

    @patch('github_integration.subprocess.run')
    def test_mark_issue_in_progress_success(self, mock_run):
        """Test successfully marking issue in progress"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = github.mark_issue_in_progress(42)

        assert result is True
        # Should make multiple subprocess calls
        assert mock_run.call_count >= 2

    @patch('github_integration.subprocess.run')
    def test_mark_issue_in_progress_timeout(self, mock_run):
        """Test handling of timeout"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("gh", 5)

        result = github.mark_issue_in_progress(42)

        assert result is False

    def test_mark_issue_in_progress_validates_issue_number(self):
        """Security: Test that issue number is validated"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        with pytest.raises(ValueError, match="Security"):
            github.mark_issue_in_progress(-1)

        with pytest.raises(ValueError, match="Security"):
            github.mark_issue_in_progress(0)


class TestCreatePullRequest:
    """Test pull request creation"""

    @patch('github_integration.GitHubIntegration.check_gh_cli_installed')
    @patch('github_integration.subprocess.run')
    def test_create_pr_success(self, mock_run, mock_check):
        """Test successful PR creation"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_check.return_value = True

        # Mock workflow result
        workflow_result = Mock()
        workflow_result.user_story = "Add new feature"
        workflow_result.total_cost = 0.15
        workflow_result.total_duration_ms = 120000
        workflow_result.revision_count = 0
        workflow_result.agents = [
            {"cost_usd": 0.05, "duration_ms": 30000},  # Architect
            {"cost_usd": 0.03, "duration_ms": 20000},  # Security
            {"cost_usd": 0.04, "duration_ms": 40000},  # Tester
            {"cost_usd": 0.03, "duration_ms": 30000},  # PO
        ]

        # Mock subprocess calls
        mock_results = [
            Mock(returncode=0, stdout="feature-branch"),  # git branch --show-current
            Mock(returncode=0, stdout="M\tfile.py\nA\ttest.py"),  # git diff
            Mock(returncode=0, stdout="https://github.com/user/repo/pull/1"),  # gh pr create
        ]
        mock_run.side_effect = mock_results

        pr_url = github.create_pr(workflow_result)

        assert pr_url == "https://github.com/user/repo/pull/1"

    @patch('github_integration.GitHubIntegration.check_gh_cli_installed')
    def test_create_pr_gh_not_installed(self, mock_check):
        """Test PR creation when gh CLI not installed"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_check.return_value = False

        workflow_result = Mock()

        with pytest.raises(Exception, match="GitHub CLI not installed"):
            github.create_pr(workflow_result)

    @patch('github_integration.GitHubIntegration.check_gh_cli_installed')
    @patch('github_integration.GitHubIntegration._link_pr_to_issue')
    @patch('github_integration.subprocess.run')
    def test_create_pr_with_issue_number(self, mock_run, mock_link, mock_check):
        """Test PR creation with linked issue"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_check.return_value = True

        workflow_result = Mock()
        workflow_result.user_story = "Add new feature"
        workflow_result.total_cost = 0.15
        workflow_result.total_duration_ms = 120000
        workflow_result.revision_count = 0
        workflow_result.agents = [
            {"cost_usd": 0.05, "duration_ms": 30000},
            {"cost_usd": 0.03, "duration_ms": 20000},
            {"cost_usd": 0.04, "duration_ms": 40000},
            {"cost_usd": 0.03, "duration_ms": 30000},
        ]

        mock_results = [
            Mock(returncode=0, stdout="feature-branch"),
            Mock(returncode=0, stdout="M\tfile.py"),
            Mock(returncode=0, stdout="https://github.com/user/repo/pull/1"),
        ]
        mock_run.side_effect = mock_results

        pr_url = github.create_pr(workflow_result, issue_number=42)

        assert pr_url is not None
        # Should link PR to issue
        mock_link.assert_called_once_with(42, "https://github.com/user/repo/pull/1")

    @patch('github_integration.GitHubIntegration.check_gh_cli_installed')
    @patch('github_integration.subprocess.run')
    def test_create_pr_sanitizes_user_story(self, mock_run, mock_check):
        """Security: Test that user story is sanitized"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_check.return_value = True

        workflow_result = Mock()
        workflow_result.user_story = "Story\x00with\x01control\x02chars"
        workflow_result.total_cost = 0.15
        workflow_result.total_duration_ms = 120000
        workflow_result.revision_count = 0
        workflow_result.agents = [
            {"cost_usd": 0.05, "duration_ms": 30000},
            {"cost_usd": 0.03, "duration_ms": 20000},
            {"cost_usd": 0.04, "duration_ms": 40000},
            {"cost_usd": 0.03, "duration_ms": 30000},
        ]

        mock_results = [
            Mock(returncode=0, stdout="feature-branch"),
            Mock(returncode=0, stdout="M\tfile.py"),
            Mock(returncode=0, stdout="https://github.com/user/repo/pull/1"),
        ]
        mock_run.side_effect = mock_results

        pr_url = github.create_pr(workflow_result)

        # Should not raise exception
        assert pr_url is not None

    def test_create_pr_validates_issue_number(self):
        """Security: Test that issue number is validated"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        workflow_result = Mock()

        with pytest.raises(ValueError, match="Security"):
            github.create_pr(workflow_result, issue_number=-1)


class TestGeneratePRBody:
    """Test PR body generation"""

    def test_generate_pr_body_includes_checklist(self):
        """Test that PR body includes review checklist"""
        config = {"enabled": True, "pr_target_branch": "staging"}
        github = GitHubIntegration(config)

        workflow_result = Mock()
        workflow_result.user_story = "Add feature"
        workflow_result.total_cost = 0.15
        workflow_result.total_duration_ms = 120000
        workflow_result.revision_count = 0
        workflow_result.agents = [
            {"cost_usd": 0.05, "duration_ms": 30000},
            {"cost_usd": 0.03, "duration_ms": 20000},
            {"cost_usd": 0.04, "duration_ms": 40000},
            {"cost_usd": 0.03, "duration_ms": 30000},
        ]

        with patch('github_integration.subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="M\tfile.py")
            body = github._generate_pr_body(workflow_result, None)

        # Check for checklist items
        assert "HUMAN REVIEW CHECKLIST" in body
        assert "Code Quality" in body
        assert "Security" in body
        assert "Testing" in body
        assert "Documentation" in body

    def test_generate_pr_body_includes_metrics(self):
        """Test that PR body includes agent metrics"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        workflow_result = Mock()
        workflow_result.user_story = "Add feature"
        workflow_result.total_cost = 0.15
        workflow_result.total_duration_ms = 120000
        workflow_result.revision_count = 0
        workflow_result.agents = [
            {"cost_usd": 0.05, "duration_ms": 30000},
            {"cost_usd": 0.03, "duration_ms": 20000},
            {"cost_usd": 0.04, "duration_ms": 40000},
            {"cost_usd": 0.03, "duration_ms": 30000},
        ]

        with patch('github_integration.subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="M\tfile.py")
            body = github._generate_pr_body(workflow_result, None)

        # Check for metrics
        assert "AI Agent Metrics" in body
        assert "$0.15" in body

    def test_generate_pr_body_includes_issue_link(self):
        """Test that PR body includes issue link"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        workflow_result = Mock()
        workflow_result.user_story = "Add feature"
        workflow_result.total_cost = 0.15
        workflow_result.total_duration_ms = 120000
        workflow_result.revision_count = 0
        workflow_result.agents = [
            {"cost_usd": 0.05, "duration_ms": 30000},
            {"cost_usd": 0.03, "duration_ms": 20000},
            {"cost_usd": 0.04, "duration_ms": 40000},
            {"cost_usd": 0.03, "duration_ms": 30000},
        ]

        with patch('github_integration.subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="M\tfile.py")
            body = github._generate_pr_body(workflow_result, issue_number=42)

        assert "#42" in body


class TestGetIssueDetails:
    """Test getting issue details"""

    @patch('github_integration.subprocess.run')
    def test_get_issue_details_success(self, mock_run):
        """Test successfully getting issue details"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        issue_data = {
            "number": 42,
            "title": "Feature request",
            "body": "Description",
            "labels": [{"name": "ready-for-dev"}],
            "state": "open"
        }

        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(issue_data)
        mock_run.return_value = mock_result

        issue = github.get_issue_details(42)

        assert issue is not None
        assert issue["number"] == 42
        assert issue["title"] == "Feature request"

    @patch('github_integration.subprocess.run')
    def test_get_issue_details_not_found(self, mock_run):
        """Test handling of non-existent issue"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        issue = github.get_issue_details(999)

        assert issue is None

    def test_get_issue_details_validates_issue_number(self):
        """Security: Test that issue number is validated"""
        config = {"enabled": True}
        github = GitHubIntegration(config)

        with pytest.raises(ValueError, match="Security"):
            github.get_issue_details(-1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
