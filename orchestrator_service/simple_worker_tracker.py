"""
Simple Worker Tracker

Tracks workers dynamically without SSH - workers self-register by calling /work/next
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TrackedWorker:
    """Represents a self-registered worker"""
    worker_id: str
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    current_task: Optional[int] = None
    total_tasks: int = 0


class SimpleWorkerTracker:
    """Tracks workers that self-register via API calls"""

    def __init__(self, timeout_minutes: int = 5):
        """
        Initialize worker tracker

        Args:
            timeout_minutes: Minutes before considering worker offline
        """
        self.workers: Dict[str, TrackedWorker] = {}
        self.timeout = timedelta(minutes=timeout_minutes)
        logger.info(f"Worker tracker initialized (timeout: {timeout_minutes}m)")

    def update_activity(self, worker_id: str, task_number: Optional[int] = None):
        """
        Update worker activity (auto-registers if new)

        Args:
            worker_id: Worker identifier
            task_number: Issue number being worked on (None if idle)
        """
        now = datetime.now()

        if worker_id not in self.workers:
            # Auto-register new worker
            self.workers[worker_id] = TrackedWorker(
                worker_id=worker_id,
                first_seen=now,
                last_seen=now,
            )
            logger.info(f"New worker registered: {worker_id}")

        worker = self.workers[worker_id]
        worker.last_seen = now

        if task_number:
            if worker.current_task != task_number:
                worker.current_task = task_number
                worker.total_tasks += 1
        else:
            worker.current_task = None

    def get_active_workers(self) -> Dict[str, TrackedWorker]:
        """
        Get all active workers (seen within timeout period)

        Returns:
            Dict of active workers
        """
        now = datetime.now()
        active = {}

        for worker_id, worker in self.workers.items():
            if now - worker.last_seen < self.timeout:
                active[worker_id] = worker

        return active

    def get_worker_count(self) -> int:
        """Get count of active workers"""
        return len(self.get_active_workers())

    def get_available_worker_count(self) -> int:
        """Get count of active workers with no current task"""
        active = self.get_active_workers()
        return sum(1 for w in active.values() if w.current_task is None)

    def get_all_workers(self) -> Dict[str, TrackedWorker]:
        """Get all workers ever seen"""
        return self.workers.copy()

    def cleanup_stale_workers(self, days: int = 7):
        """
        Remove workers not seen in specified days

        Args:
            days: Number of days to keep inactive workers
        """
        now = datetime.now()
        cutoff = timedelta(days=days)

        stale = [
            worker_id for worker_id, worker in self.workers.items()
            if now - worker.last_seen > cutoff
        ]

        for worker_id in stale:
            del self.workers[worker_id]
            logger.info(f"Removed stale worker: {worker_id}")

        return len(stale)