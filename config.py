"""
Configuration for AI Scrum Master
"""
import os
import re
from pathlib import Path
from typing import Dict, List

# Version
VERSION = "2.2.1"
AUTHOR = 'AI Scrum Master Team'

# Project paths
PROJECT_ROOT = Path(__file__).parent
WORKSPACE_DIR = PROJECT_ROOT / "workspace"

# Git branch names
MAIN_BRANCH = "main"
ARCHITECT_BRANCH = "architect-branch"
SECURITY_BRANCH = "security-branch"
TESTER_BRANCH = "tester-branch"

# Claude Code CLI settings
CLAUDE_CLI_CONFIG = {
    "timeout": 2400,  # 40 minutes per agent execution (extended for complex tasks like code review)
    "output_format": "json",
    "allowed_tools": "Write,Read,Edit,Bash,Glob,Grep",
}

# Agent roles
AGENT_ROLES = {
    "architect": "Architect",
    "security": "Security",
    "tester": "Tester",
    "product_owner": "ProductOwner",
}

# Workflow settings
WORKFLOW_CONFIG = {
    "max_revisions": 3,  # Maximum number of revision iterations
    "auto_merge_on_approval": False,  # CHANGED: Set to False for distributed worker + PR workflow (v2.2+)
    "require_tests_passing": True,  # Require tests to pass before PO review
    "max_agent_retries": 2,  # Maximum retries per agent on transient failures
    "retry_backoff_seconds": 5,  # Initial backoff time between retries (exponential)
}

# Git user configuration
GIT_CONFIG = {
    "user_name": "AI Scrum Master",
    "user_email": "ai@scrum-master.local",
}

# Logging
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# GitHub Integration (v2.2)
GITHUB_CONFIG = {
    "enabled": False,
    "auto_create_pr": True,           # Create PR automatically after PO approval
    "pr_target_branch": "staging",    # PRs target staging branch (not main)
    "include_review_checklist": True, # Include comprehensive review checklist in PR
    "link_pr_to_issue": True,         # Link PRs back to originating issues
    "require_manual_review": True,    # Always require human review (no auto-merge)
}

# Deployment Configuration
DEPLOYMENT_CONFIG = {
    "development_branch_prefix": "ai-scrum-",
    "staging_branch": "staging",
    "production_branch": "main",
    "auto_deploy_staging": False,  # Will be handled by GitHub Actions
    "auto_deploy_production": False,  # Will be handled by GitHub Actions
}

# UI Protection Configuration (v2.5)
UI_PROTECTION_CONFIG = {
    "enabled": True,                      # Enable UI protection system
    "verify_before_po_review": True,      # Check UI protection before Product Owner review
    "block_on_violation": True,           # Block workflow if protected UI files are modified
    "protected_file_marker": "🔒 UI-PROTECTED",  # Marker in file headers
    "cache_file": ".ui_protection_cache.json",  # Cache file for protected file hashes
}

# Agent Output Cache Configuration
CACHE_CONFIG = {
    "enabled": True,                      # Enable agent output caching
    "ttl_days": 7,                       # Time-to-live in days
    "cache_dir": "logs/cache",           # Directory for cache files
}


def validate_config() -> Dict[str, List[str]]:
    """
    Validate configuration and return errors/warnings

    Returns:
        Dictionary with 'errors' and 'warnings' lists

    Example:
        >>> result = validate_config()
        >>> if result["errors"]:
        ...     print("Configuration errors found!")
    """
    errors = []
    warnings = []

    # Validate paths
    if not PROJECT_ROOT.exists():
        errors.append(f"PROJECT_ROOT does not exist: {PROJECT_ROOT}")

    # Validate branch names
    branch_pattern = re.compile(r'^[a-zA-Z0-9/_.-]+$')
    for branch_name in [MAIN_BRANCH, ARCHITECT_BRANCH, SECURITY_BRANCH, TESTER_BRANCH]:
        if not branch_pattern.match(branch_name):
            errors.append(f"Invalid branch name: {branch_name}")

    # Validate workflow settings
    max_revisions = WORKFLOW_CONFIG.get("max_revisions", 3)
    if not isinstance(max_revisions, int) or max_revisions < 1:
        errors.append(f"max_revisions must be positive integer, got: {max_revisions}")

    if max_revisions > 10:
        warnings.append(f"max_revisions is very high: {max_revisions} (recommended: 3-5)")

    max_retries = WORKFLOW_CONFIG.get("max_agent_retries", 2)
    if not isinstance(max_retries, int) or max_retries < 0:
        errors.append(f"max_agent_retries must be non-negative integer, got: {max_retries}")

    retry_backoff = WORKFLOW_CONFIG.get("retry_backoff_seconds", 5)
    if not isinstance(retry_backoff, (int, float)) or retry_backoff < 0:
        errors.append(f"retry_backoff_seconds must be non-negative number, got: {retry_backoff}")

    # Validate Claude CLI settings
    timeout = CLAUDE_CLI_CONFIG.get("timeout", 2400)
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        errors.append(f"CLAUDE_CLI_CONFIG timeout must be positive number, got: {timeout}")

    if timeout < 60:
        warnings.append(f"Claude CLI timeout is very low: {timeout}s (recommended: 600+)")

    if timeout > 3600:
        warnings.append(f"Claude CLI timeout is very high: {timeout}s (recommended: < 1 hour)")

    # Validate environment
    if not os.getenv("ANTHROPIC_API_KEY"):
        warnings.append("ANTHROPIC_API_KEY environment variable not set")

    # Validate git config
    git_user = GIT_CONFIG.get("user_name")
    if not git_user or not isinstance(git_user, str):
        errors.append("GIT_CONFIG user_name must be a non-empty string")

    git_email = GIT_CONFIG.get("user_email")
    if not git_email or not isinstance(git_email, str):
        errors.append("GIT_CONFIG user_email must be a non-empty string")
    elif "@" not in git_email:
        warnings.append(f"GIT_CONFIG user_email may be invalid: {git_email}")

    # Validate GitHub config
    if GITHUB_CONFIG.get("enabled", False):
        pr_target = GITHUB_CONFIG.get("pr_target_branch")
        if not pr_target or not branch_pattern.match(pr_target):
            errors.append(f"Invalid GitHub pr_target_branch: {pr_target}")

    # Validate deployment config
    staging_branch = DEPLOYMENT_CONFIG.get("staging_branch")
    if not staging_branch or not branch_pattern.match(staging_branch):
        errors.append(f"Invalid staging_branch: {staging_branch}")

    production_branch = DEPLOYMENT_CONFIG.get("production_branch")
    if not production_branch or not branch_pattern.match(production_branch):
        errors.append(f"Invalid production_branch: {production_branch}")

    # Validate UI protection config
    cache_file = UI_PROTECTION_CONFIG.get("cache_file")
    if not cache_file or not isinstance(cache_file, str):
        errors.append("UI_PROTECTION_CONFIG cache_file must be a non-empty string")

    return {"errors": errors, "warnings": warnings}