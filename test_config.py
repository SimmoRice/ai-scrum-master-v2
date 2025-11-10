"""
Test suite for config.py

Tests configuration values, constants, and validation.
Covers happy paths, edge cases, and security validations.
"""
import pytest
from pathlib import Path
from config import (
    VERSION,
    AUTHOR,
    PROJECT_ROOT,
    WORKSPACE_DIR,
    MAIN_BRANCH,
    ARCHITECT_BRANCH,
    SECURITY_BRANCH,
    TESTER_BRANCH,
    CLAUDE_CLI_CONFIG,
    AGENT_ROLES,
    WORKFLOW_CONFIG,
    GIT_CONFIG,
    LOGGING_CONFIG,
    GITHUB_CONFIG,
    DEPLOYMENT_CONFIG
)


class TestVersionAndMetadata:
    """Test version and metadata constants"""

    def test_version_exists(self):
        """Test that VERSION constant is defined"""
        assert VERSION is not None
        assert isinstance(VERSION, str)
        assert len(VERSION) > 0

    def test_version_format(self):
        """Test that VERSION follows semantic versioning"""
        # Should be in format X.Y.Z
        parts = VERSION.split('.')
        assert len(parts) >= 2, "Version should have at least major.minor"
        # Each part should be numeric
        for part in parts:
            assert part.isdigit() or part[0].isdigit(), f"Version part '{part}' should start with a digit"

    def test_author_exists(self):
        """Test that AUTHOR constant is defined"""
        assert AUTHOR is not None
        assert isinstance(AUTHOR, str)
        assert len(AUTHOR) > 0

    def test_author_value(self):
        """Test that AUTHOR has the expected value"""
        assert AUTHOR == 'AI Scrum Master Team'


class TestProjectPaths:
    """Test project path configurations"""

    def test_project_root_exists(self):
        """Test that PROJECT_ROOT is defined and valid"""
        assert PROJECT_ROOT is not None
        assert isinstance(PROJECT_ROOT, Path)

    def test_project_root_is_absolute(self):
        """Test that PROJECT_ROOT is an absolute path"""
        assert PROJECT_ROOT.is_absolute()

    def test_workspace_dir_exists(self):
        """Test that WORKSPACE_DIR is defined"""
        assert WORKSPACE_DIR is not None
        assert isinstance(WORKSPACE_DIR, Path)

    def test_workspace_dir_under_project_root(self):
        """Test that WORKSPACE_DIR is under PROJECT_ROOT"""
        # Workspace should be a subdirectory of project root
        assert str(WORKSPACE_DIR).startswith(str(PROJECT_ROOT))

    def test_workspace_dir_name(self):
        """Test that WORKSPACE_DIR has the correct name"""
        assert WORKSPACE_DIR.name == "workspace"


class TestGitBranchNames:
    """Test git branch name configurations"""

    def test_main_branch_name(self):
        """Test that MAIN_BRANCH is defined correctly"""
        assert MAIN_BRANCH == "main"
        assert isinstance(MAIN_BRANCH, str)

    def test_architect_branch_name(self):
        """Test that ARCHITECT_BRANCH is defined correctly"""
        assert ARCHITECT_BRANCH == "architect-branch"
        assert isinstance(ARCHITECT_BRANCH, str)

    def test_security_branch_name(self):
        """Test that SECURITY_BRANCH is defined correctly"""
        assert SECURITY_BRANCH == "security-branch"
        assert isinstance(SECURITY_BRANCH, str)

    def test_tester_branch_name(self):
        """Test that TESTER_BRANCH is defined correctly"""
        assert TESTER_BRANCH == "tester-branch"
        assert isinstance(TESTER_BRANCH, str)

    def test_all_branch_names_unique(self):
        """Test that all branch names are unique"""
        branches = [MAIN_BRANCH, ARCHITECT_BRANCH, SECURITY_BRANCH, TESTER_BRANCH]
        assert len(branches) == len(set(branches)), "Branch names must be unique"

    def test_branch_names_no_special_chars(self):
        """Security: Test that branch names don't contain dangerous characters"""
        dangerous_chars = [';', '&', '|', '$', '`', '(', ')', '<', '>', '\n', '\r']
        branches = [MAIN_BRANCH, ARCHITECT_BRANCH, SECURITY_BRANCH, TESTER_BRANCH]

        for branch in branches:
            for char in dangerous_chars:
                assert char not in branch, f"Branch name '{branch}' contains dangerous character: {char}"


class TestClaudeCliConfig:
    """Test Claude CLI configuration"""

    def test_claude_cli_config_exists(self):
        """Test that CLAUDE_CLI_CONFIG is defined"""
        assert CLAUDE_CLI_CONFIG is not None
        assert isinstance(CLAUDE_CLI_CONFIG, dict)

    def test_claude_cli_timeout(self):
        """Test that timeout is set and reasonable"""
        assert "timeout" in CLAUDE_CLI_CONFIG
        timeout = CLAUDE_CLI_CONFIG["timeout"]
        assert isinstance(timeout, int)
        assert timeout > 0, "Timeout must be positive"
        assert timeout <= 3600, "Timeout should not exceed 1 hour"

    def test_claude_cli_output_format(self):
        """Test that output format is set to JSON"""
        assert "output_format" in CLAUDE_CLI_CONFIG
        assert CLAUDE_CLI_CONFIG["output_format"] == "json"

    def test_claude_cli_allowed_tools(self):
        """Test that allowed tools are defined"""
        assert "allowed_tools" in CLAUDE_CLI_CONFIG
        tools = CLAUDE_CLI_CONFIG["allowed_tools"]
        assert isinstance(tools, str)
        # Should contain common tools
        assert "Read" in tools or "Write" in tools or "Bash" in tools


class TestAgentRoles:
    """Test agent role configurations"""

    def test_agent_roles_exists(self):
        """Test that AGENT_ROLES is defined"""
        assert AGENT_ROLES is not None
        assert isinstance(AGENT_ROLES, dict)

    def test_all_agent_roles_present(self):
        """Test that all required agent roles are defined"""
        required_roles = ["architect", "security", "tester", "product_owner"]
        for role in required_roles:
            assert role in AGENT_ROLES, f"Missing agent role: {role}"

    def test_agent_role_values(self):
        """Test that agent role values are strings"""
        for key, value in AGENT_ROLES.items():
            assert isinstance(value, str)
            assert len(value) > 0


class TestWorkflowConfig:
    """Test workflow configuration"""

    def test_workflow_config_exists(self):
        """Test that WORKFLOW_CONFIG is defined"""
        assert WORKFLOW_CONFIG is not None
        assert isinstance(WORKFLOW_CONFIG, dict)

    def test_max_revisions(self):
        """Test that max_revisions is set and reasonable"""
        assert "max_revisions" in WORKFLOW_CONFIG
        max_rev = WORKFLOW_CONFIG["max_revisions"]
        assert isinstance(max_rev, int)
        assert max_rev >= 0
        assert max_rev <= 10, "Max revisions should be reasonable"

    def test_auto_merge_setting(self):
        """Test that auto_merge_on_approval is a boolean"""
        assert "auto_merge_on_approval" in WORKFLOW_CONFIG
        assert isinstance(WORKFLOW_CONFIG["auto_merge_on_approval"], bool)

    def test_require_tests_passing(self):
        """Test that require_tests_passing is a boolean"""
        assert "require_tests_passing" in WORKFLOW_CONFIG
        assert isinstance(WORKFLOW_CONFIG["require_tests_passing"], bool)

    def test_max_agent_retries(self):
        """Test that max_agent_retries is reasonable"""
        assert "max_agent_retries" in WORKFLOW_CONFIG
        retries = WORKFLOW_CONFIG["max_agent_retries"]
        assert isinstance(retries, int)
        assert retries >= 0
        assert retries <= 5, "Too many retries could cause long delays"

    def test_retry_backoff_seconds(self):
        """Test that retry_backoff_seconds is reasonable"""
        assert "retry_backoff_seconds" in WORKFLOW_CONFIG
        backoff = WORKFLOW_CONFIG["retry_backoff_seconds"]
        assert isinstance(backoff, int)
        assert backoff > 0
        assert backoff <= 60, "Backoff should be reasonable"


class TestGitConfig:
    """Test git configuration"""

    def test_git_config_exists(self):
        """Test that GIT_CONFIG is defined"""
        assert GIT_CONFIG is not None
        assert isinstance(GIT_CONFIG, dict)

    def test_git_user_name(self):
        """Test that git user name is defined"""
        assert "user_name" in GIT_CONFIG
        user_name = GIT_CONFIG["user_name"]
        assert isinstance(user_name, str)
        assert len(user_name) > 0

    def test_git_user_email(self):
        """Test that git user email is defined"""
        assert "user_email" in GIT_CONFIG
        user_email = GIT_CONFIG["user_email"]
        assert isinstance(user_email, str)
        assert len(user_email) > 0
        # Basic email format check
        assert "@" in user_email

    def test_git_email_no_injection(self):
        """Security: Test that git email doesn't contain dangerous characters"""
        email = GIT_CONFIG["user_email"]
        dangerous_chars = [';', '&', '|', '$', '`', '\n', '\r']
        for char in dangerous_chars:
            assert char not in email, f"Git email contains dangerous character: {char}"


class TestLoggingConfig:
    """Test logging configuration"""

    def test_logging_config_exists(self):
        """Test that LOGGING_CONFIG is defined"""
        assert LOGGING_CONFIG is not None
        assert isinstance(LOGGING_CONFIG, dict)

    def test_logging_level(self):
        """Test that logging level is defined"""
        assert "level" in LOGGING_CONFIG
        level = LOGGING_CONFIG["level"]
        assert level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_logging_format(self):
        """Test that logging format is defined"""
        assert "format" in LOGGING_CONFIG
        log_format = LOGGING_CONFIG["format"]
        assert isinstance(log_format, str)
        assert len(log_format) > 0


class TestGitHubConfig:
    """Test GitHub integration configuration"""

    def test_github_config_exists(self):
        """Test that GITHUB_CONFIG is defined"""
        assert GITHUB_CONFIG is not None
        assert isinstance(GITHUB_CONFIG, dict)

    def test_github_enabled_flag(self):
        """Test that enabled flag is a boolean"""
        assert "enabled" in GITHUB_CONFIG
        assert isinstance(GITHUB_CONFIG["enabled"], bool)

    def test_github_auto_create_pr(self):
        """Test that auto_create_pr is a boolean"""
        assert "auto_create_pr" in GITHUB_CONFIG
        assert isinstance(GITHUB_CONFIG["auto_create_pr"], bool)

    def test_github_pr_target_branch(self):
        """Test that PR target branch is defined"""
        assert "pr_target_branch" in GITHUB_CONFIG
        target = GITHUB_CONFIG["pr_target_branch"]
        assert isinstance(target, str)
        assert len(target) > 0

    def test_github_checklist_flag(self):
        """Test that include_review_checklist is a boolean"""
        assert "include_review_checklist" in GITHUB_CONFIG
        assert isinstance(GITHUB_CONFIG["include_review_checklist"], bool)

    def test_github_link_pr_to_issue(self):
        """Test that link_pr_to_issue is a boolean"""
        assert "link_pr_to_issue" in GITHUB_CONFIG
        assert isinstance(GITHUB_CONFIG["link_pr_to_issue"], bool)

    def test_github_require_manual_review(self):
        """Test that require_manual_review is a boolean"""
        assert "require_manual_review" in GITHUB_CONFIG
        assert isinstance(GITHUB_CONFIG["require_manual_review"], bool)


class TestDeploymentConfig:
    """Test deployment configuration"""

    def test_deployment_config_exists(self):
        """Test that DEPLOYMENT_CONFIG is defined"""
        assert DEPLOYMENT_CONFIG is not None
        assert isinstance(DEPLOYMENT_CONFIG, dict)

    def test_development_branch_prefix(self):
        """Test that development branch prefix is defined"""
        assert "development_branch_prefix" in DEPLOYMENT_CONFIG
        prefix = DEPLOYMENT_CONFIG["development_branch_prefix"]
        assert isinstance(prefix, str)
        assert len(prefix) > 0

    def test_staging_branch(self):
        """Test that staging branch is defined"""
        assert "staging_branch" in DEPLOYMENT_CONFIG
        staging = DEPLOYMENT_CONFIG["staging_branch"]
        assert isinstance(staging, str)
        assert len(staging) > 0

    def test_production_branch(self):
        """Test that production branch is defined"""
        assert "production_branch" in DEPLOYMENT_CONFIG
        production = DEPLOYMENT_CONFIG["production_branch"]
        assert isinstance(production, str)
        assert len(production) > 0

    def test_auto_deploy_flags(self):
        """Test that auto deploy flags are booleans"""
        assert "auto_deploy_staging" in DEPLOYMENT_CONFIG
        assert isinstance(DEPLOYMENT_CONFIG["auto_deploy_staging"], bool)

        assert "auto_deploy_production" in DEPLOYMENT_CONFIG
        assert isinstance(DEPLOYMENT_CONFIG["auto_deploy_production"], bool)

    def test_deployment_branches_unique(self):
        """Test that deployment branches are unique"""
        staging = DEPLOYMENT_CONFIG["staging_branch"]
        production = DEPLOYMENT_CONFIG["production_branch"]
        assert staging != production, "Staging and production branches must be different"


class TestSecurityValidations:
    """Security-focused tests for configuration"""

    def test_no_hardcoded_secrets(self):
        """Security: Ensure no hardcoded secrets in config values"""
        sensitive_patterns = ["password", "token", "key", "secret"]

        # Check all config dictionaries
        configs = [
            CLAUDE_CLI_CONFIG,
            AGENT_ROLES,
            WORKFLOW_CONFIG,
            GIT_CONFIG,
            LOGGING_CONFIG,
            GITHUB_CONFIG,
            DEPLOYMENT_CONFIG
        ]

        for config in configs:
            for key, value in config.items():
                if isinstance(value, str):
                    value_lower = value.lower()
                    # Check if it looks like a real secret (long random string)
                    if len(value) > 20 and not any(word in value_lower for word in ["scrum", "ai", "local", "branch"]):
                        # This might be a secret, check patterns
                        for pattern in sensitive_patterns:
                            if pattern in key.lower():
                                assert not value.startswith("sk-"), "Potential API key found"
                                assert not value.startswith("ghp_"), "Potential GitHub token found"

    def test_paths_not_absolute_to_system_dirs(self):
        """Security: Ensure paths don't point to system directories"""
        system_dirs = ['/etc', '/var', '/usr', '/bin', '/sbin', '/root']

        paths = [PROJECT_ROOT, WORKSPACE_DIR]
        for path in paths:
            path_str = str(path)
            for sys_dir in system_dirs:
                assert not path_str.startswith(sys_dir), f"Path should not be in system directory: {sys_dir}"

    def test_no_path_traversal_in_branches(self):
        """Security: Ensure branch names don't contain path traversal"""
        branches = [MAIN_BRANCH, ARCHITECT_BRANCH, SECURITY_BRANCH, TESTER_BRANCH]

        for branch in branches:
            assert ".." not in branch, "Branch name should not contain .."
            assert not branch.startswith("/"), "Branch name should not start with /"
            assert not branch.startswith("\\"), "Branch name should not start with \\"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_config_values_handled(self):
        """Test that no config values are empty strings"""
        configs = [
            CLAUDE_CLI_CONFIG,
            AGENT_ROLES,
            WORKFLOW_CONFIG,
            GIT_CONFIG,
            LOGGING_CONFIG,
            GITHUB_CONFIG,
            DEPLOYMENT_CONFIG
        ]

        for config in configs:
            for key, value in config.items():
                if isinstance(value, str):
                    assert len(value) > 0, f"Config value for '{key}' should not be empty"

    def test_numeric_configs_not_negative(self):
        """Test that numeric config values are not negative where inappropriate"""
        assert WORKFLOW_CONFIG["max_revisions"] >= 0
        assert WORKFLOW_CONFIG["max_agent_retries"] >= 0
        assert WORKFLOW_CONFIG["retry_backoff_seconds"] > 0
        assert CLAUDE_CLI_CONFIG["timeout"] > 0

    def test_config_types_consistent(self):
        """Test that config values have consistent types"""
        # All timeouts should be integers
        assert isinstance(CLAUDE_CLI_CONFIG["timeout"], int)
        assert isinstance(WORKFLOW_CONFIG["retry_backoff_seconds"], int)

        # All boolean flags should be booleans
        assert isinstance(WORKFLOW_CONFIG["auto_merge_on_approval"], bool)
        assert isinstance(WORKFLOW_CONFIG["require_tests_passing"], bool)
        assert isinstance(GITHUB_CONFIG["enabled"], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
