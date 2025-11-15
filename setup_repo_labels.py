#!/usr/bin/env python3
"""
Setup GitHub Repository Labels for AI Scrum Cluster

This script creates the necessary labels in a GitHub repository
for the AI Scrum Master cluster workflow.

Usage:
    python setup_repo_labels.py --repo owner/repo-name
    python setup_repo_labels.py --repo owner/repo-name --reset
    python setup_repo_labels.py --all  # Setup labels for all monitored repos
"""

import subprocess
import sys
import argparse
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Define standard labels for AI Scrum cluster
CLUSTER_LABELS = [
    {
        "name": "ai-ready",
        "description": "Issue is ready to be picked up by AI workers",
        "color": "0E8A16"  # Green
    },
    {
        "name": "ai-in-progress",
        "description": "Issue is currently being worked on by an AI worker",
        "color": "FBCA04"  # Yellow
    },
    {
        "name": "ai-completed",
        "description": "Issue has been completed by an AI worker",
        "color": "5319E7"  # Purple
    },
    {
        "name": "ai-failed",
        "description": "AI worker failed to complete this issue",
        "color": "D93F0B"  # Red
    },
    {
        "name": "ai-blocked",
        "description": "Issue is blocked and cannot be worked on",
        "color": "B60205"  # Dark red
    }
]

# Optional labels for organization
OPTIONAL_LABELS = [
    {
        "name": "priority: high",
        "description": "High priority task",
        "color": "D93F0B"
    },
    {
        "name": "priority: medium",
        "description": "Medium priority task",
        "color": "FBCA04"
    },
    {
        "name": "priority: low",
        "description": "Low priority task",
        "color": "0E8A16"
    },
    {
        "name": "complexity: simple",
        "description": "Simple task, quick to implement",
        "color": "C5DEF5"
    },
    {
        "name": "complexity: medium",
        "description": "Medium complexity task",
        "color": "5319E7"
    },
    {
        "name": "complexity: complex",
        "description": "Complex task requiring significant work",
        "color": "B60205"
    },
    {
        "name": "type: feature",
        "description": "New feature or enhancement",
        "color": "84B6EB"
    },
    {
        "name": "type: bug",
        "description": "Bug fix",
        "color": "D73A4A"
    },
    {
        "name": "type: refactor",
        "description": "Code refactoring",
        "color": "BFDADC"
    },
    {
        "name": "type: docs",
        "description": "Documentation update",
        "color": "0075CA"
    }
]


def check_gh_cli():
    """Check if GitHub CLI is installed"""
    try:
        subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ GitHub CLI (gh) is not installed")
        print("   Install: https://cli.github.com/")
        return False


def get_existing_labels(repo: str) -> List[str]:
    """Get list of existing labels in repository"""
    try:
        result = subprocess.run(
            ["gh", "label", "list", "--repo", repo, "--limit", "1000"],
            capture_output=True,
            text=True,
            check=True
        )

        # Parse label names from output (format: "NAME\tDESCRIPTION\tCOLOR")
        labels = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                if parts:
                    labels.append(parts[0])

        return labels
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting labels from {repo}: {e.stderr}")
        return []


def create_label(repo: str, label: Dict) -> bool:
    """Create a single label"""
    try:
        subprocess.run(
            [
                "gh", "label", "create",
                label["name"],
                "--repo", repo,
                "--description", label["description"],
                "--color", label["color"],
                "--force"  # Update if exists
            ],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        # Ignore "already exists" errors
        if "already exists" not in e.stderr.decode():
            print(f"  ❌ Failed to create label '{label['name']}': {e.stderr.decode()}")
            return False
        return True


def delete_label(repo: str, label_name: str) -> bool:
    """Delete a label"""
    try:
        subprocess.run(
            ["gh", "label", "delete", label_name, "--repo", repo, "--yes"],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def enable_issues(repo: str) -> bool:
    """
    Enable issues for a repository

    Args:
        repo: Repository in format "owner/repo"

    Returns:
        True if successful or already enabled
    """
    try:
        # Use gh api to enable issues
        subprocess.run(
            [
                "gh", "api",
                f"repos/{repo}",
                "-X", "PATCH",
                "-f", "has_issues=true"
            ],
            capture_output=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ⚠️  Could not enable issues: {e.stderr.decode()}")
        return False


def check_issues_enabled(repo: str) -> bool:
    """
    Check if issues are enabled for a repository

    Args:
        repo: Repository in format "owner/repo"

    Returns:
        True if issues are enabled
    """
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}", "--jq", ".has_issues"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip() == "true"
    except subprocess.CalledProcessError:
        return False


def setup_labels(repo: str, include_optional: bool = False, reset: bool = False):
    """
    Setup labels for a repository

    Args:
        repo: Repository in format "owner/repo"
        include_optional: Include optional organizational labels
        reset: Delete existing AI labels before creating
    """
    print(f"\n📋 Setting up labels for {repo}")

    # Check if issues are enabled
    print("  🔍 Checking if issues are enabled...")
    if not check_issues_enabled(repo):
        print("  ⚙️  Issues are disabled, enabling...")
        if enable_issues(repo):
            print("  ✅ Issues enabled")
        else:
            print("  ❌ Failed to enable issues - you may need to enable manually")
            print(f"     Go to: https://github.com/{repo}/settings")
            return
    else:
        print("  ✅ Issues are already enabled")

    # Get existing labels
    existing = get_existing_labels(repo)

    # Reset if requested
    if reset:
        print("  🗑️  Removing existing AI labels...")
        for label in CLUSTER_LABELS:
            if label["name"] in existing:
                if delete_label(repo, label["name"]):
                    print(f"    ✅ Deleted: {label['name']}")

    # Create cluster labels
    print("  ✨ Creating AI cluster labels...")
    labels_to_create = CLUSTER_LABELS.copy()
    if include_optional:
        labels_to_create.extend(OPTIONAL_LABELS)

    created = 0
    updated = 0

    for label in labels_to_create:
        was_existing = label["name"] in existing
        if create_label(repo, label):
            if was_existing:
                updated += 1
                print(f"    ♻️  Updated: {label['name']}")
            else:
                created += 1
                print(f"    ✅ Created: {label['name']}")

    print(f"\n  Summary: {created} created, {updated} updated")


def get_monitored_repos() -> List[str]:
    """
    Get list of repositories being monitored by the orchestrator

    Returns:
        List of repository names in format "owner/repo"
    """
    repos_env = os.getenv("GITHUB_REPOS", "")
    if repos_env:
        return [r.strip() for r in repos_env.split(",") if r.strip()]

    repo_env = os.getenv("GITHUB_REPO", "")
    if repo_env:
        return [repo_env.strip()]

    return []


def main():
    parser = argparse.ArgumentParser(
        description="Setup GitHub labels for AI Scrum cluster"
    )
    parser.add_argument(
        "--repo",
        help="Repository in format 'owner/repo'"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Setup labels for all monitored repositories (from .env)"
    )
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Include optional organizational labels (priority, complexity, type)"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing AI labels before creating"
    )
    parser.add_argument(
        "--list-monitored",
        action="store_true",
        help="List repositories being monitored by orchestrator"
    )

    args = parser.parse_args()

    # Check gh CLI
    if not check_gh_cli():
        sys.exit(1)

    # List monitored repos
    if args.list_monitored:
        repos = get_monitored_repos()
        if repos:
            print("Monitored repositories:")
            for repo in repos:
                print(f"  • {repo}")
        else:
            print("No repositories configured in .env")
            print("Set GITHUB_REPOS or GITHUB_REPO environment variable")
        sys.exit(0)

    # Determine which repos to setup
    repos_to_setup = []

    if args.all:
        repos_to_setup = get_monitored_repos()
        if not repos_to_setup:
            print("❌ No repositories configured in .env")
            print("   Set GITHUB_REPOS or GITHUB_REPO environment variable")
            sys.exit(1)
    elif args.repo:
        repos_to_setup = [args.repo]
    else:
        print("❌ Either --repo or --all is required")
        parser.print_help()
        sys.exit(1)

    # Setup labels
    print("==========================================")
    print("GitHub Label Setup for AI Scrum Cluster")
    print("==========================================")

    for repo in repos_to_setup:
        setup_labels(repo, args.include_optional, args.reset)

    print("\n==========================================")
    print(f"✅ Label setup complete for {len(repos_to_setup)} repository/repositories")
    print("==========================================")
    print("\nRequired labels created:")
    for label in CLUSTER_LABELS:
        print(f"  • {label['name']}: {label['description']}")

    if args.include_optional:
        print("\nOptional labels created:")
        for label in OPTIONAL_LABELS:
            print(f"  • {label['name']}: {label['description']}")

    print("\nYou can now:")
    print(f"  1. Create issues with 'ai-ready' label")
    print(f"  2. Use create_project_issues.py to generate issues")
    print(f"  3. The cluster will automatically pick up ai-ready issues")
    print("")


if __name__ == "__main__":
    main()
