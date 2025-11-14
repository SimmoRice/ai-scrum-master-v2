#!/usr/bin/env python3
"""
Test GitHub Issue Orchestration with Single Agent

This script demonstrates how a single agent can:
1. Fetch an issue from GitHub (labeled 'ready-for-dev')
2. Work on the issue
3. Create a PR when complete

Usage:
    python test_single_agent_github.py [--repo REPO] [--issue NUMBER]
"""

import sys
from pathlib import Path
from github_integration import GitHubIntegration
from orchestrator import Orchestrator
from config import GITHUB_CONFIG
import argparse


def test_single_agent_github_workflow(repo_path: str = None, issue_number: int = None, verbose: bool = False):
    """
    Test workflow: GitHub Issue → Single Agent → PR

    Args:
        repo_path: Path to local repository (e.g., '~/Development/repos/ai-calc-2')
        issue_number: Specific issue number to work on (optional)
        verbose: Stream Claude Code output in real-time
    """
    print("="*60)
    print("🧪 TESTING: Single Agent GitHub Orchestration")
    print("="*60)

    # Determine workspace - if repo_path provided, use it; otherwise use current repo
    if repo_path:
        workspace = Path(repo_path).expanduser().resolve()
        if not workspace.exists():
            print(f"\n❌ Repository path does not exist: {workspace}")
            return False
        print(f"\n📁 Target repository: {workspace}")
    else:
        workspace = Path.cwd()
        print(f"\n📁 Using current repository: {workspace}")

    # Initialize GitHub integration with workspace directory
    github = GitHubIntegration(GITHUB_CONFIG, workspace_dir=workspace)

    # Check if gh CLI is installed
    if not github.check_gh_cli_installed():
        print("\n❌ GitHub CLI not installed or not authenticated")
        print("   Install: brew install gh")
        print("   Authenticate: gh auth login")
        return False

    # Get issue to work on - need to run gh commands in the target repo directory
    import subprocess
    if issue_number:
        print(f"\n📋 Fetching issue #{issue_number} from {workspace.name}...")
        try:
            result = subprocess.run([
                'gh', 'issue', 'view', str(issue_number),
                '--json', 'number,title,body,labels,state'
            ], cwd=workspace, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                import json
                issue = json.loads(result.stdout)
            else:
                print(f"❌ Could not find issue #{issue_number}")
                return False
        except Exception as e:
            print(f"❌ Error fetching issue: {e}")
            return False
    else:
        print(f"\n📋 Fetching ready-for-dev issues from {workspace.name}...")
        try:
            result = subprocess.run([
                'gh', 'issue', 'list',
                '--label', 'ready-for-dev',
                '--json', 'number,title,body,labels',
                '--limit', '1'
            ], cwd=workspace, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                import json
                issues = json.loads(result.stdout)
                if not issues:
                    print("❌ No issues found with label 'ready-for-dev'")
                    print(f"\nTo create issues in {workspace.name}:")
                    print(f"  cd {workspace}")
                    print("  gh issue create --title 'Feature' --body 'Description' --label 'ready-for-dev'")
                    return False
                issue = issues[0]
            else:
                print("❌ Failed to fetch issues")
                return False
        except Exception as e:
            print(f"❌ Error fetching issues: {e}")
            return False

    # Display issue details
    print(f"\n✅ Found issue to work on:")
    print(f"   #{issue['number']}: {issue['title']}")
    print(f"   Labels: {', '.join([l['name'] for l in issue.get('labels', [])])}")

    # Extract user story from issue
    user_story = f"{issue['title']}\n\n{issue.get('body', '')}"

    print(f"\n📝 User Story:")
    print(f"   {user_story[:200]}{'...' if len(user_story) > 200 else ''}")

    # Mark issue as in-progress
    print(f"\n🏷️  Marking issue #{issue['number']} as in-progress...")
    try:
        subprocess.run([
            'gh', 'issue', 'edit', str(issue['number']),
            '--remove-label', 'ready-for-dev'
        ], cwd=workspace, capture_output=True, timeout=5)

        subprocess.run([
            'gh', 'issue', 'edit', str(issue['number']),
            '--add-label', 'in-progress'
        ], cwd=workspace, capture_output=True, timeout=5)

        subprocess.run([
            'gh', 'issue', 'comment', str(issue['number']),
            '--body', '🤖 AI Scrum Master is now working on this feature...'
        ], cwd=workspace, capture_output=True, timeout=5)
    except Exception as e:
        print(f"⚠️  Could not update issue labels: {e}")

    print(f"\n📁 Working in: {workspace}")

    # Initialize orchestrator for this workspace with GitHub integration
    print(f"\n🤖 Initializing AI Scrum Master...")
    orchestrator = Orchestrator(workspace_dir=workspace, verbose=verbose, github=github)

    # Process the user story
    print(f"\n🚀 Starting workflow...")
    print("="*60)

    try:
        result = orchestrator.process_user_story(user_story)

        # Print summary
        print("\n" + "="*60)
        print("📈 WORKFLOW SUMMARY")
        print("="*60)
        print(f"Status: {'✅ APPROVED' if result.approved else '❌ NOT APPROVED'}")
        print(f"Revisions: {result.revision_count}")
        print(f"Total Cost: ${result.total_cost:.4f}")

        if result.errors:
            print(f"\nErrors:")
            for error in result.errors:
                print(f"  - {error}")

        print("="*60 + "\n")

        if result.approved:
            # Create pull request
            print(f"\n📤 Creating pull request...")
            pr_url = github.create_pr(result, issue_number=issue['number'])

            if pr_url:
                print(f"\n✅ SUCCESS!")
                print(f"\n📝 Next steps:")
                print(f"   1. Review the PR: {pr_url}")
                print(f"   2. Complete the review checklist")
                print(f"   3. Test the feature manually")
                print(f"   4. Merge to staging when ready")
                return True
            else:
                print(f"\n⚠️  PR creation failed")
                return False
        else:
            print(f"\n⚠️  Workflow not approved. Check errors above.")
            return False

    except KeyboardInterrupt:
        print("\n⚠️  Workflow interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Test GitHub issue orchestration with single agent'
    )
    parser.add_argument(
        '--repo',
        help='Path to local repository (e.g., ~/Development/repos/ai-calc-2)',
        default=None
    )
    parser.add_argument(
        '--issue',
        type=int,
        help='Specific issue number to work on',
        default=None
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Stream Claude Code output in real-time'
    )

    args = parser.parse_args()

    # Run test
    success = test_single_agent_github_workflow(
        repo_path=args.repo,
        issue_number=args.issue,
        verbose=args.verbose
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
