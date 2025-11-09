"""
Configuration for AI Scrum Master
"""
from pathlib import Path

# Version
VERSION = "2.1.0"

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
    "timeout": 600,  # 10 minutes per agent execution (agents can take time to think and commit)
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