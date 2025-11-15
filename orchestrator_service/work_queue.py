"""
Work Queue Manager

Manages the queue of issues to be worked on, tracks assignments,
and prevents conflicts
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class WorkItem:
    """Represents a work item (GitHub issue) in the queue"""
    issue_number: int
    title: str
    body: str
    labels: List[str]
    repository: str
    branch_name: str
    status: str = "pending"  # pending, in_progress, completed, failed
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0


class WorkQueue:
    """Manages work queue for distributed workers"""

    def __init__(self):
        self.items: Dict[int, WorkItem] = {}  # issue_number -> WorkItem
        self.file_locks: Dict[str, int] = {}  # file_path -> issue_number

    def add_work_item(
        self,
        issue_number: int,
        title: str,
        body: str,
        labels: List[str],
        repository: str,
    ) -> bool:
        """
        Add work item to queue

        Args:
            issue_number: GitHub issue number
            title: Issue title
            body: Issue body
            labels: Issue labels
            repository: Repository name (owner/repo)

        Returns:
            True if added, False if already exists
        """
        if issue_number in self.items:
            logger.debug(f"Issue #{issue_number} already in queue")
            return False

        branch_name = f"ai-feature/issue-{issue_number}"

        item = WorkItem(
            issue_number=issue_number,
            title=title,
            body=body,
            labels=labels,
            repository=repository,
            branch_name=branch_name,
        )

        self.items[issue_number] = item
        logger.info(f"Added issue #{issue_number} to work queue: {title}")
        return True

    def get_next_work(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        Get next available work item for worker

        Args:
            worker_id: Identifier for requesting worker

        Returns:
            Work item dict or None if no work available
        """
        # Find first pending item
        for item in self.items.values():
            if item.status == "pending":
                # Assign to worker
                item.status = "in_progress"
                item.assigned_to = worker_id
                item.assigned_at = datetime.now()

                logger.info(f"Assigned issue #{item.issue_number} to {worker_id}")

                return {
                    "issue_number": item.issue_number,
                    "title": item.title,
                    "body": item.body,
                    "labels": item.labels,
                    "branch_name": item.branch_name,
                    "repository": item.repository,
                }

        # No work available
        return None

    def mark_complete(
        self,
        issue_number: int,
        worker_id: str,
        success: bool,
        pr_url: Optional[str] = None,
        error: Optional[str] = None,
    ) -> bool:
        """
        Mark work item as complete

        Args:
            issue_number: Issue number
            worker_id: Worker that completed the work
            success: Whether work was successful
            pr_url: Pull request URL (if successful)
            error: Error message (if failed)

        Returns:
            True if successful
        """
        if issue_number not in self.items:
            logger.error(f"Issue #{issue_number} not found in queue")
            return False

        item = self.items[issue_number]

        if item.assigned_to != worker_id:
            logger.warning(
                f"Worker {worker_id} tried to complete issue #{issue_number} "
                f"but it's assigned to {item.assigned_to}"
            )
            return False

        item.status = "completed" if success else "failed"
        item.completed_at = datetime.now()
        item.pr_url = pr_url
        item.error = error

        logger.info(
            f"Issue #{issue_number} marked as {item.status} by {worker_id}"
        )
        return True

    def mark_failed(
        self,
        issue_number: int,
        worker_id: str,
        error: str,
    ) -> bool:
        """
        Mark work item as failed and release for retry

        Args:
            issue_number: Issue number
            worker_id: Worker that failed
            error: Error message

        Returns:
            True if successful
        """
        if issue_number not in self.items:
            logger.error(f"Issue #{issue_number} not found in queue")
            return False

        item = self.items[issue_number]

        if item.assigned_to != worker_id:
            logger.warning(
                f"Worker {worker_id} tried to fail issue #{issue_number} "
                f"but it's assigned to {item.assigned_to}"
            )
            return False

        item.retry_count += 1

        # If retry count exceeds limit, mark as permanently failed
        MAX_RETRIES = 2
        if item.retry_count >= MAX_RETRIES:
            item.status = "failed"
            item.completed_at = datetime.now()
            item.error = f"Max retries exceeded. Last error: {error}"
            logger.warning(
                f"Issue #{issue_number} permanently failed after {item.retry_count} retries"
            )
        else:
            # Release for retry
            item.status = "pending"
            item.assigned_to = None
            item.assigned_at = None
            item.error = f"Retry {item.retry_count}: {error}"
            logger.info(
                f"Issue #{issue_number} released for retry ({item.retry_count}/{MAX_RETRIES})"
            )

        return True

    def release_work(
        self,
        issue_number: int,
        worker_id: str,
    ) -> bool:
        """
        Release work item back to queue without marking as failed
        (e.g., for clarification)

        Args:
            issue_number: Issue number
            worker_id: Worker releasing the work

        Returns:
            True if successful
        """
        if issue_number not in self.items:
            logger.error(f"Issue #{issue_number} not found in queue")
            return False

        item = self.items[issue_number]

        if item.assigned_to != worker_id:
            logger.warning(
                f"Worker {worker_id} tried to release issue #{issue_number} "
                f"but it's assigned to {item.assigned_to}"
            )
            return False

        # Remove from queue entirely (needs clarification)
        # Orchestrator will re-add it only if it gets ai-ready label again
        del self.items[issue_number]

        logger.info(
            f"Issue #{issue_number} removed from queue by {worker_id} (needs clarification)"
        )

        return True

    def has_issue(self, issue_number: int) -> bool:
        """Check if issue is already in queue"""
        return issue_number in self.items

    def pending_count(self) -> int:
        """Get count of pending items"""
        return sum(1 for item in self.items.values() if item.status == "pending")

    def in_progress_count(self) -> int:
        """Get count of in-progress items"""
        return sum(1 for item in self.items.values() if item.status == "in_progress")

    def completed_count(self) -> int:
        """Get count of completed items"""
        return sum(1 for item in self.items.values() if item.status == "completed")

    def get_pending_items(self) -> List[Dict[str, Any]]:
        """Get list of pending work items"""
        return [
            {
                "issue_number": item.issue_number,
                "title": item.title,
                "labels": item.labels,
            }
            for item in self.items.values()
            if item.status == "pending"
        ]

    def get_in_progress_items(self) -> List[Dict[str, Any]]:
        """Get list of in-progress work items"""
        return [
            {
                "issue_number": item.issue_number,
                "title": item.title,
                "assigned_to": item.assigned_to,
                "assigned_at": item.assigned_at.isoformat() if item.assigned_at else None,
            }
            for item in self.items.values()
            if item.status == "in_progress"
        ]

    def get_completed_items(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get list of recently completed work items"""
        completed = [
            item for item in self.items.values()
            if item.status in ("completed", "failed")
        ]

        # Sort by completion time (most recent first)
        completed.sort(
            key=lambda x: x.completed_at if x.completed_at else datetime.min,
            reverse=True
        )

        return [
            {
                "issue_number": item.issue_number,
                "title": item.title,
                "status": item.status,
                "assigned_to": item.assigned_to,
                "pr_url": item.pr_url,
                "error": item.error,
                "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            }
            for item in completed[:limit]
        ]
