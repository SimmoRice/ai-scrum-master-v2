#!/usr/bin/env python3
"""
PR Review Helper for AI Scrum Cluster

This script helps review PRs created by AI workers and manage the review workflow.

Usage:
    # List PRs needing review
    python review_prs.py --repo owner/repo --list

    # List PRs needing review across all monitored repos
    python review_prs.py --all --list

    # Approve a PR for merging
    python review_prs.py --repo owner/repo --approve 123

    # Request changes on a PR
    python review_prs.py --repo owner/repo --request-changes 123 --comment "Please fix XYZ"

    # Approve and merge a PR
    python review_prs.py --repo owner/repo --approve 123 --merge

    # Bulk approve multiple PRs
    python review_prs.py --repo owner/repo --approve 123,124,125
"""

import subprocess
import sys
import argparse
import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def notify_orchestrator(action: str, pr_number: int) -> bool:
    """
    Notify orchestrator of PR status change

    Args:
        action: approved, changes-requested, or merged
        pr_number: PR number

    Returns:
        True if notification sent successfully
    """
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://192.168.100.200:8000")
    endpoint = f"{orchestrator_url}/pr-review/{action}/{pr_number}"

    try:
        response = requests.post(endpoint, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        # Not critical if notification fails
        print(f"  ⚠️  Could not notify orchestrator: {e}")
        return False


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


def get_monitored_repos() -> List[str]:
    """Get list of repositories being monitored"""
    repos_env = os.getenv("GITHUB_REPOS", "")
    if repos_env:
        return [r.strip() for r in repos_env.split(",") if r.strip()]

    repo_env = os.getenv("GITHUB_REPO", "")
    if repo_env:
        return [repo_env.strip()]

    return []


def list_prs_for_review(repo: str) -> List[Dict]:
    """
    List PRs that need review

    Args:
        repo: Repository in format "owner/repo"

    Returns:
        List of PR dictionaries
    """
    try:
        # Get PRs with needs-review label
        result = subprocess.run(
            [
                "gh", "pr", "list",
                "--repo", repo,
                "--label", "needs-review",
                "--json", "number,title,url,author,createdAt,labels",
                "--limit", "100"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        import json
        prs = json.loads(result.stdout)
        return prs

    except subprocess.CalledProcessError as e:
        print(f"❌ Error listing PRs from {repo}: {e.stderr}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing PR list: {e}")
        return []


def approve_pr(repo: str, pr_number: int, comment: Optional[str] = None) -> bool:
    """
    Approve a PR and mark it as approved-for-merge

    Args:
        repo: Repository in format "owner/repo"
        pr_number: PR number
        comment: Optional review comment

    Returns:
        True if successful
    """
    try:
        # Add review comment if provided
        if comment:
            subprocess.run(
                [
                    "gh", "pr", "comment", str(pr_number),
                    "--repo", repo,
                    "--body", comment
                ],
                capture_output=True,
                check=True
            )

        # Add approved-for-merge label
        subprocess.run(
            [
                "gh", "pr", "edit", str(pr_number),
                "--repo", repo,
                "--add-label", "approved-for-merge"
            ],
            capture_output=True,
            check=True
        )

        # Remove needs-review label
        subprocess.run(
            [
                "gh", "pr", "edit", str(pr_number),
                "--repo", repo,
                "--remove-label", "needs-review"
            ],
            capture_output=True,
            check=True
        )

        # Notify orchestrator
        notify_orchestrator("approved", pr_number)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error approving PR #{pr_number}: {e.stderr.decode()}")
        return False


def request_changes(repo: str, pr_number: int, comment: str) -> bool:
    """
    Request changes on a PR

    Args:
        repo: Repository in format "owner/repo"
        pr_number: PR number
        comment: Changes requested comment

    Returns:
        True if successful
    """
    try:
        # Add comment with changes requested
        full_comment = f"🔄 **Changes Requested**\n\n{comment}"
        subprocess.run(
            [
                "gh", "pr", "comment", str(pr_number),
                "--repo", repo,
                "--body", full_comment
            ],
            capture_output=True,
            check=True
        )

        # Add changes-requested label
        subprocess.run(
            [
                "gh", "pr", "edit", str(pr_number),
                "--repo", repo,
                "--add-label", "changes-requested"
            ],
            capture_output=True,
            check=True
        )

        # Remove needs-review label
        subprocess.run(
            [
                "gh", "pr", "edit", str(pr_number),
                "--repo", repo,
                "--remove-label", "needs-review"
            ],
            capture_output=True,
            check=True
        )

        # Notify orchestrator
        notify_orchestrator("changes-requested", pr_number)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error requesting changes on PR #{pr_number}: {e.stderr.decode()}")
        return False


def merge_pr(repo: str, pr_number: int, method: str = "squash") -> bool:
    """
    Merge a PR

    Args:
        repo: Repository in format "owner/repo"
        pr_number: PR number
        method: Merge method (squash, merge, rebase)

    Returns:
        True if successful
    """
    try:
        cmd = [
            "gh", "pr", "merge", str(pr_number),
            "--repo", repo
        ]

        if method == "squash":
            cmd.append("--squash")
        elif method == "merge":
            cmd.append("--merge")
        elif method == "rebase":
            cmd.append("--rebase")

        subprocess.run(
            cmd,
            capture_output=True,
            check=True
        )

        # Notify orchestrator
        notify_orchestrator("merged", pr_number)

        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error merging PR #{pr_number}: {e.stderr.decode()}")
        return False


def display_prs(repo: str, prs: List[Dict]):
    """Display PRs in a readable format"""
    if not prs:
        print(f"  ✅ No PRs need review for {repo}")
        return

    print(f"\n📋 {repo} - {len(prs)} PR(s) need review:")
    print("=" * 80)

    for pr in prs:
        print(f"\n#{pr['number']}: {pr['title']}")
        print(f"  Author: {pr['author']['login']}")
        print(f"  URL: {pr['url']}")
        print(f"  Created: {pr['createdAt']}")

        # Show other labels
        other_labels = [
            label['name'] for label in pr['labels']
            if label['name'] != 'needs-review'
        ]
        if other_labels:
            print(f"  Labels: {', '.join(other_labels)}")

        print("")


def main():
    parser = argparse.ArgumentParser(
        description="Review PRs created by AI workers"
    )
    parser.add_argument(
        "--repo",
        help="Repository in format 'owner/repo'"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all monitored repositories (from .env)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List PRs that need review"
    )
    parser.add_argument(
        "--approve",
        help="Approve PR(s) for merging (comma-separated PR numbers)"
    )
    parser.add_argument(
        "--request-changes",
        type=int,
        help="Request changes on a PR"
    )
    parser.add_argument(
        "--comment",
        help="Comment to add with approval or change request"
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge PR after approval"
    )
    parser.add_argument(
        "--merge-method",
        choices=["squash", "merge", "rebase"],
        default="squash",
        help="Merge method (default: squash)"
    )

    args = parser.parse_args()

    # Check gh CLI
    if not check_gh_cli():
        sys.exit(1)

    # Determine which repos to process
    repos_to_process = []

    if args.all:
        repos_to_process = get_monitored_repos()
        if not repos_to_process:
            print("❌ No repositories configured in .env")
            print("   Set GITHUB_REPOS or GITHUB_REPO environment variable")
            sys.exit(1)
    elif args.repo:
        repos_to_process = [args.repo]
    else:
        print("❌ Either --repo or --all is required")
        parser.print_help()
        sys.exit(1)

    # List PRs needing review
    if args.list:
        print("==========================================")
        print("PRs Needing Review")
        print("==========================================")

        total_prs = 0
        for repo in repos_to_process:
            prs = list_prs_for_review(repo)
            total_prs += len(prs)
            display_prs(repo, prs)

        print("\n==========================================")
        print(f"Total: {total_prs} PR(s) need review")
        print("==========================================")
        print("\nNext steps:")
        print("  • Review PRs in browser: gh pr view <number> --repo <repo> --web")
        print("  • Approve: python review_prs.py --repo <repo> --approve <number>")
        print("  • Request changes: python review_prs.py --repo <repo> --request-changes <number> --comment \"...\"")
        print("")

    # Approve PR(s)
    elif args.approve:
        if len(repos_to_process) > 1:
            print("❌ Cannot approve PRs for multiple repos at once")
            print("   Use --repo to specify a single repository")
            sys.exit(1)

        repo = repos_to_process[0]
        pr_numbers = [int(n.strip()) for n in args.approve.split(",")]

        print("==========================================")
        print(f"Approving PRs for {repo}")
        print("==========================================")

        for pr_number in pr_numbers:
            print(f"\n✅ Approving PR #{pr_number}...")

            if approve_pr(repo, pr_number, args.comment):
                print(f"  ✅ Approved PR #{pr_number}")

                if args.merge:
                    print(f"  🔀 Merging PR #{pr_number}...")
                    if merge_pr(repo, pr_number, args.merge_method):
                        print(f"  ✅ Merged PR #{pr_number}")
                    else:
                        print(f"  ❌ Failed to merge PR #{pr_number}")
            else:
                print(f"  ❌ Failed to approve PR #{pr_number}")

        print("\n==========================================")
        print("Review complete")
        print("==========================================")

    # Request changes
    elif args.request_changes:
        if len(repos_to_process) > 1:
            print("❌ Cannot request changes for multiple repos at once")
            print("   Use --repo to specify a single repository")
            sys.exit(1)

        if not args.comment:
            print("❌ --comment is required when requesting changes")
            sys.exit(1)

        repo = repos_to_process[0]
        pr_number = args.request_changes

        print("==========================================")
        print(f"Requesting Changes on PR #{pr_number}")
        print("==========================================")

        if request_changes(repo, pr_number, args.comment):
            print(f"\n✅ Changes requested on PR #{pr_number}")
            print(f"   Comment: {args.comment}")
        else:
            print(f"\n❌ Failed to request changes on PR #{pr_number}")

        print("\n==========================================")

    else:
        print("❌ No action specified")
        print("   Use --list to see PRs, --approve to approve, or --request-changes")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
