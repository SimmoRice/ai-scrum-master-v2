#!/usr/bin/env python3
"""
Setup GitHub Repository for AI Scrum Master

This script handles the complete GitHub repository setup:
1. Create GitHub repository
2. Push local code to GitHub
3. Enable issues
4. Create necessary labels

Usage:
    python setup_github_repo.py <repo_path> [--name REPO_NAME] [--description DESC]
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_command(cmd, cwd=None, timeout=30):
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def check_git_cli():
    """Check if git is installed"""
    success, _, _ = run_command(['git', '--version'])
    return success


def check_gh_cli():
    """Check if GitHub CLI is installed and authenticated"""
    if not run_command(['gh', '--version'])[0]:
        return False, "GitHub CLI not installed"

    success, _, stderr = run_command(['gh', 'auth', 'status'])
    if not success:
        return False, "GitHub CLI not authenticated"

    return True, "OK"


def check_if_git_repo(repo_path):
    """Check if directory is already a git repository"""
    git_dir = repo_path / ".git"
    return git_dir.exists()


def init_git_repo(repo_path):
    """Initialize git repository if not already initialized"""
    if check_if_git_repo(repo_path):
        print("  ✓ Already a git repository")
        return True

    success, _, stderr = run_command(['git', 'init'], cwd=repo_path)
    if success:
        print("  ✓ Initialized git repository")
        return True
    else:
        print(f"  ✗ Failed to initialize git: {stderr}")
        return False


def check_git_remote(repo_path):
    """Check if git remote 'origin' exists"""
    success, stdout, _ = run_command(
        ['git', 'remote', 'get-url', 'origin'],
        cwd=repo_path
    )
    return success, stdout.strip() if success else None


def create_github_repo(repo_path, repo_name, description, public=True):
    """Create GitHub repository and push code"""
    # Check if remote already exists
    has_remote, remote_url = check_git_remote(repo_path)
    if has_remote:
        print(f"  ✓ Repository already has remote: {remote_url}")
        return True, remote_url

    # Check if there are any commits
    success, stdout, _ = run_command(
        ['git', 'rev-parse', 'HEAD'],
        cwd=repo_path
    )

    if not success:
        # No commits yet - create initial commit
        print("  → Creating initial commit...")
        run_command(['git', 'add', '.'], cwd=repo_path)
        success, _, stderr = run_command(
            ['git', 'commit', '-m', 'Initial commit'],
            cwd=repo_path
        )
        if not success:
            print(f"  ⚠️  Warning: Could not create initial commit: {stderr}")

    # Create GitHub repository
    visibility = '--public' if public else '--private'
    cmd = [
        'gh', 'repo', 'create', repo_name,
        visibility,
        '--source=.',
        '--remote=origin',
        '--description', description,
        '--push'
    ]

    success, stdout, stderr = run_command(cmd, cwd=repo_path, timeout=60)

    if success:
        # Extract URL from output
        repo_url = stdout.strip().split('\n')[0]
        print(f"  ✓ Created repository: {repo_url}")
        return True, repo_url
    else:
        print(f"  ✗ Failed to create repository: {stderr}")
        return False, None


def enable_issues(repo_path):
    """Enable issues on the GitHub repository"""
    success, _, stderr = run_command(
        ['gh', 'repo', 'edit', '--enable-issues'],
        cwd=repo_path
    )

    if success:
        print("  ✓ Enabled issues")
        return True
    else:
        print(f"  ⚠️  Could not enable issues: {stderr}")
        return False


def create_labels(repo_path):
    """Create standard labels for AI Scrum Master workflow"""
    labels = [
        {
            'name': 'ready-for-dev',
            'description': 'Ready for development by AI agent',
            'color': '0E8A16'  # Green
        },
        {
            'name': 'in-progress',
            'description': 'Currently being worked on by AI agent',
            'color': 'FBCA04'  # Yellow
        },
        {
            'name': 'needs-review',
            'description': 'Needs human review',
            'color': 'D93F0B'  # Red
        },
        {
            'name': 'enhancement',
            'description': 'New feature or request',
            'color': 'A2EEEF'  # Light blue
        },
        {
            'name': 'bug',
            'description': 'Something is not working',
            'color': 'D73A4A'  # Red
        },
        {
            'name': 'approved',
            'description': 'Approved by Product Owner',
            'color': '0E8A16'  # Green
        }
    ]

    created_count = 0
    for label in labels:
        cmd = [
            'gh', 'label', 'create', label['name'],
            '--description', label['description'],
            '--color', label['color']
        ]

        success, _, stderr = run_command(cmd, cwd=repo_path)

        if success:
            print(f"  ✓ Created label: {label['name']}")
            created_count += 1
        elif 'already exists' in stderr.lower():
            print(f"  ✓ Label already exists: {label['name']}")
            created_count += 1
        else:
            print(f"  ✗ Failed to create label '{label['name']}': {stderr}")

    return created_count > 0


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Setup GitHub repository for AI Scrum Master'
    )
    parser.add_argument(
        'repo_path',
        type=str,
        help='Path to the local repository'
    )
    parser.add_argument(
        '--name',
        type=str,
        help='Repository name (defaults to directory name)',
        default=None
    )
    parser.add_argument(
        '--description',
        type=str,
        help='Repository description',
        default='AI-generated project'
    )
    parser.add_argument(
        '--private',
        action='store_true',
        help='Create private repository (default: public)'
    )

    args = parser.parse_args()

    # Resolve repository path
    repo_path = Path(args.repo_path).expanduser().resolve()

    if not repo_path.exists():
        print(f"❌ Error: Repository path does not exist: {repo_path}")
        return 1

    # Determine repository name
    repo_name = args.name or repo_path.name

    print("="*60)
    print("🔧 GitHub Repository Setup")
    print("="*60)
    print(f"Repository: {repo_name}")
    print(f"Path: {repo_path}")
    print(f"Description: {args.description}")
    print(f"Visibility: {'Private' if args.private else 'Public'}")
    print("="*60)

    # Check prerequisites
    print("\n📋 Checking prerequisites...")

    if not check_git_cli():
        print("❌ Git is not installed")
        print("   Install: https://git-scm.com/downloads")
        return 1
    print("  ✓ Git installed")

    gh_ok, gh_msg = check_gh_cli()
    if not gh_ok:
        print(f"❌ {gh_msg}")
        if "not installed" in gh_msg:
            print("   Install: brew install gh")
        else:
            print("   Authenticate: gh auth login")
        return 1
    print("  ✓ GitHub CLI installed and authenticated")

    # Step 1: Initialize git repository
    print("\n📦 Step 1: Initialize Git Repository")
    if not init_git_repo(repo_path):
        return 1

    # Step 2: Create GitHub repository and push
    print("\n🚀 Step 2: Create GitHub Repository")
    success, repo_url = create_github_repo(
        repo_path,
        repo_name,
        args.description,
        public=not args.private
    )
    if not success:
        return 1

    # Step 3: Enable issues
    print("\n📋 Step 3: Enable Issues")
    enable_issues(repo_path)

    # Step 4: Create labels
    print("\n🏷️  Step 4: Create Labels")
    create_labels(repo_path)

    # Summary
    print("\n" + "="*60)
    print("✅ GitHub Repository Setup Complete!")
    print("="*60)
    print(f"Repository URL: {repo_url}")
    print()
    print("Next steps:")
    print("  1. Create issues with 'ready-for-dev' label")
    print("  2. Run: python test_single_agent_github.py")
    print("="*60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
