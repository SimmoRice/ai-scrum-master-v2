#!/usr/bin/env python3
"""
PR Review Tracker for Orchestrator

Tracks pull requests awaiting review and manages queue blocking
to prevent cascading bugs and review overload.
"""

import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PendingPR:
    """Represents a PR awaiting review"""
    issue_number: int
    pr_url: str
    repository: str
    created_at: datetime
    worker_id: str
    dependencies: Set[int]  # Issue numbers this PR depends on


class PRReviewTracker:
    """
    Tracks PRs needing review and manages queue blocking

    This prevents:
    1. Cascading bugs from unreviewed PRs
    2. Review overload from too many pending PRs
    3. Wasted work building on buggy foundations
    """

    def __init__(
        self,
        max_pending_prs: int = 5,
        block_on_changes_requested: bool = True,
        allow_parallel_independent: bool = True
    ):
        """
        Initialize PR review tracker

        Args:
            max_pending_prs: Maximum PRs pending review before blocking queue
            block_on_changes_requested: Block all new work when changes requested
            allow_parallel_independent: Allow work on independent features while PRs pending
        """
        self.max_pending_prs = max_pending_prs
        self.block_on_changes_requested = block_on_changes_requested
        self.allow_parallel_independent = allow_parallel_independent

        # Track PRs by status
        self.pending_prs: Dict[int, PendingPR] = {}  # issue_number -> PendingPR
        self.changes_requested_prs: Set[int] = set()  # issue numbers with changes requested
        self.approved_prs: Set[int] = set()  # issue numbers approved for merge

        # Track dependencies
        self.dependency_graph: Dict[int, Set[int]] = {}  # issue -> dependencies

        logger.info(
            f"PR Review Tracker initialized: "
            f"max_pending={max_pending_prs}, "
            f"block_on_changes={block_on_changes_requested}, "
            f"allow_parallel={allow_parallel_independent}"
        )

    def add_pending_pr(
        self,
        issue_number: int,
        pr_url: str,
        repository: str,
        worker_id: str,
        dependencies: Optional[Set[int]] = None
    ):
        """
        Register a new PR awaiting review

        Args:
            issue_number: GitHub issue number
            pr_url: Pull request URL
            repository: Repository name (owner/repo)
            worker_id: Worker that created the PR
            dependencies: Issue numbers this PR depends on
        """
        pr = PendingPR(
            issue_number=issue_number,
            pr_url=pr_url,
            repository=repository,
            created_at=datetime.now(),
            worker_id=worker_id,
            dependencies=dependencies or set()
        )

        self.pending_prs[issue_number] = pr
        if dependencies:
            self.dependency_graph[issue_number] = dependencies

        logger.info(
            f"Added pending PR: {repository}#{issue_number} "
            f"({len(self.pending_prs)} total pending)"
        )

    def mark_approved(self, issue_number: int):
        """Mark a PR as approved for merge"""
        if issue_number in self.pending_prs:
            del self.pending_prs[issue_number]
            self.approved_prs.add(issue_number)
            logger.info(f"PR #{issue_number} approved and removed from pending")

    def mark_changes_requested(self, issue_number: int):
        """Mark a PR as needing changes"""
        if issue_number in self.pending_prs:
            del self.pending_prs[issue_number]
            self.changes_requested_prs.add(issue_number)
            logger.warning(
                f"PR #{issue_number} needs changes - "
                f"{'BLOCKING queue' if self.block_on_changes_requested else 'not blocking'}"
            )

    def mark_merged(self, issue_number: int):
        """Remove a PR that was merged"""
        self.pending_prs.pop(issue_number, None)
        self.approved_prs.discard(issue_number)
        self.changes_requested_prs.discard(issue_number)
        self.dependency_graph.pop(issue_number, None)
        logger.info(f"PR #{issue_number} merged and cleared from tracking")

    def should_block_queue(self, repository: Optional[str] = None) -> bool:
        """
        Determine if new work should be blocked

        Args:
            repository: Optional specific repository to check

        Returns:
            True if queue should be blocked
        """
        # Block if any PRs have changes requested
        if self.block_on_changes_requested and self.changes_requested_prs:
            return True

        # Block if too many pending PRs
        if repository:
            # Count pending PRs for specific repo
            repo_pending = sum(
                1 for pr in self.pending_prs.values()
                if pr.repository == repository
            )
            if repo_pending >= self.max_pending_prs:
                return True
        else:
            # Count all pending PRs
            if len(self.pending_prs) >= self.max_pending_prs:
                return True

        return False

    def can_work_on_issue(self, issue_number: int, dependencies: Set[int]) -> bool:
        """
        Check if work can proceed on an issue given current PR state

        Args:
            issue_number: Issue to check
            dependencies: Issues this one depends on

        Returns:
            True if work can proceed
        """
        # If queue is fully blocked, no work
        if self.should_block_queue():
            return False

        # If allowing parallel independent work
        if self.allow_parallel_independent:
            # Check if any dependencies have unmerged PRs
            for dep in dependencies:
                if dep in self.pending_prs or dep in self.changes_requested_prs:
                    # Dependency not yet merged
                    return False
            # All dependencies resolved, can work
            return True

        # Not allowing parallel work, block if any PRs pending
        return len(self.pending_prs) == 0

    def get_blocking_reason(self, repository: Optional[str] = None) -> Optional[str]:
        """
        Get human-readable reason why queue is blocked

        Args:
            repository: Optional specific repository

        Returns:
            Blocking reason string or None
        """
        if self.changes_requested_prs:
            issues = ", ".join(f"#{n}" for n in sorted(self.changes_requested_prs))
            return f"Changes requested on PRs: {issues}. Address feedback before proceeding."

        if repository:
            repo_pending = [
                pr for pr in self.pending_prs.values()
                if pr.repository == repository
            ]
            if len(repo_pending) >= self.max_pending_prs:
                issues = ", ".join(f"#{pr.issue_number}" for pr in repo_pending)
                return (
                    f"Too many pending PRs for {repository}: {issues}. "
                    f"Review and merge before proceeding (max: {self.max_pending_prs})."
                )
        else:
            if len(self.pending_prs) >= self.max_pending_prs:
                issues = ", ".join(f"#{n}" for n in sorted(self.pending_prs.keys()))
                return (
                    f"Too many pending PRs: {issues}. "
                    f"Review and merge before proceeding (max: {self.max_pending_prs})."
                )

        return None

    def get_status(self) -> Dict:
        """Get current tracker status"""
        return {
            "pending_prs": len(self.pending_prs),
            "changes_requested": len(self.changes_requested_prs),
            "approved": len(self.approved_prs),
            "queue_blocked": self.should_block_queue(),
            "blocking_reason": self.get_blocking_reason(),
            "config": {
                "max_pending_prs": self.max_pending_prs,
                "block_on_changes_requested": self.block_on_changes_requested,
                "allow_parallel_independent": self.allow_parallel_independent
            }
        }

    def get_pending_pr_details(self) -> List[Dict]:
        """Get details of all pending PRs"""
        return [
            {
                "issue_number": pr.issue_number,
                "pr_url": pr.pr_url,
                "repository": pr.repository,
                "created_at": pr.created_at.isoformat(),
                "worker_id": pr.worker_id,
                "dependencies": list(pr.dependencies),
                "age_seconds": (datetime.now() - pr.created_at).total_seconds()
            }
            for pr in self.pending_prs.values()
        ]
