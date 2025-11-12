"""
Configuration for AI Scrum Master
"""
from pathlib import Path

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
    "auto_merge_on_approval": True,  # Automatically merge when PO approves
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