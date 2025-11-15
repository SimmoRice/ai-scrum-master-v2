#!/usr/bin/env python3
"""
Issue Refinement Tool

Run this on existing issues to analyze them for clarity and post
clarifying questions if needed. This is like running a sprint
planning meeting to refine issues before they go to ai-ready.

Usage:
    # Refine all ai-ready issues in a repository
    python refine_issues.py --repo owner/repo-name

    # Refine specific issues
    python refine_issues.py --repo owner/repo-name --issues 1,2,3

    # Dry run (show what would be done, don't modify issues)
    python refine_issues.py --repo owner/repo-name --dry-run
"""

import argparse
import subprocess
import json
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
from worker.clarification_agent import ClarificationAgent

load_dotenv()


def get_issue(repo: str, issue_number: int) -> Dict[str, Any]:
    """
    Fetch issue details from GitHub

    Args:
        repo: Repository in format "owner/repo"
        issue_number: Issue number

    Returns:
        Issue dict with title, body, labels
    """
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number), "--repo", repo, "--json", "title,body,labels"],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        print(f"❌ Failed to fetch issue #{issue_number}: {result.stderr}")
        return None

    issue_data = json.loads(result.stdout)

    # Extract label names
    labels = [label["name"] for label in issue_data.get("labels", [])]

    return {
        "number": issue_number,
        "title": issue_data["title"],
        "body": issue_data["body"],
        "labels": labels
    }


def get_all_issues(repo: str, label: str = "ai-ready") -> List[int]:
    """
    Get all issues with a specific label

    Args:
        repo: Repository in format "owner/repo"
        label: Label to filter by

    Returns:
        List of issue numbers
    """
    result = subprocess.run(
        ["gh", "issue", "list", "--repo", repo, "--label", label, "--json", "number", "--jq", ".[].number"],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        print(f"❌ Failed to list issues: {result.stderr}")
        return []

    if not result.stdout.strip():
        return []

    return [int(num) for num in result.stdout.strip().split('\n')]


def refine_issue(repo: str, issue_number: int, dry_run: bool = False) -> bool:
    """
    Refine a single issue

    Args:
        repo: Repository in format "owner/repo"
        issue_number: Issue number
        dry_run: If True, don't modify the issue

    Returns:
        True if issue needs clarification, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Refining Issue #{issue_number}")
    print(f"{'='*60}")

    # Fetch issue
    issue = get_issue(repo, issue_number)
    if not issue:
        return False

    print(f"Title: {issue['title']}")
    print(f"Labels: {', '.join(issue['labels'])}")

    # Skip if already needs clarification
    if "needs-clarification" in issue["labels"]:
        print("⏭️  Already marked as needs-clarification")
        return False

    # Analyze issue
    agent = ClarificationAgent()
    result = agent.analyze_issue(issue)

    if result["needs_clarification"]:
        print(f"\n❓ Issue needs clarification")
        print(f"Reason: {result['reasoning']}")
        print(f"\nQuestions ({len(result['questions'])}):")
        for i, q in enumerate(result['questions'], 1):
            print(f"  {i}. {q}")

        if dry_run:
            print("\n[DRY RUN] Would post questions to GitHub and update labels")
            return True

        # Post questions to GitHub
        print("\n📝 Posting questions to GitHub...")
        agent.post_questions_to_github(
            repo,
            issue_number,
            result["questions"],
            result["reasoning"]
        )

        # Update labels
        print("🏷️  Updating labels...")
        agent.add_clarification_label(repo, issue_number)

        print("✅ Issue refined - questions posted")
        return True
    else:
        print(f"\n✅ Issue is clear - ready for work")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Refine GitHub issues by analyzing clarity and posting questions"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in format 'owner/repo'"
    )
    parser.add_argument(
        "--issues",
        help="Comma-separated issue numbers (if not specified, refines all ai-ready issues)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without modifying issues"
    )
    parser.add_argument(
        "--label",
        default="ai-ready",
        help="Label to filter issues by (default: ai-ready)"
    )

    args = parser.parse_args()

    print("="*60)
    print("Issue Refinement Tool")
    print("="*60)
    print(f"Repository: {args.repo}")
    if args.dry_run:
        print("Mode: DRY RUN (no changes will be made)")
    print()

    # Get issue numbers
    if args.issues:
        issue_numbers = [int(n.strip()) for n in args.issues.split(',')]
        print(f"Refining specific issues: {', '.join(map(str, issue_numbers))}")
    else:
        print(f"Fetching all issues with label '{args.label}'...")
        issue_numbers = get_all_issues(args.repo, args.label)
        if not issue_numbers:
            print(f"No issues found with label '{args.label}'")
            return
        print(f"Found {len(issue_numbers)} issues: {', '.join(map(str, issue_numbers))}")

    # Refine each issue
    needs_clarification = []
    clear_issues = []

    for issue_number in issue_numbers:
        if refine_issue(args.repo, issue_number, args.dry_run):
            needs_clarification.append(issue_number)
        else:
            clear_issues.append(issue_number)

    # Summary
    print("\n" + "="*60)
    print("Refinement Summary")
    print("="*60)
    print(f"Total issues: {len(issue_numbers)}")
    print(f"Clear and ready: {len(clear_issues)}")
    print(f"Need clarification: {len(needs_clarification)}")

    if needs_clarification:
        print(f"\nIssues needing clarification: {', '.join(map(str, needs_clarification))}")
        print("\nNext steps:")
        print("1. Review questions posted to these issues")
        print("2. Answer questions by editing issue body")
        print("3. Remove 'needs-clarification' label")
        print("4. Re-add 'ai-ready' label")

    if clear_issues:
        print(f"\nIssues ready for work: {', '.join(map(str, clear_issues))}")

    print()


if __name__ == "__main__":
    main()
