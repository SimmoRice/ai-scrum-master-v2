"""
Worker Manager

Manages worker containers, checks health, and monitors status
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Worker:
    """Represents a worker container"""
    id: str
    ip: str
    status: str = "unknown"  # unknown, available, busy, offline
    health: str = "unknown"  # healthy, degraded, unhealthy
    current_task: Optional[int] = None  # Issue number being worked on
    last_seen: Optional[datetime] = None
    last_health_check: Optional[datetime] = None


class WorkerManager:
    """Manages worker containers"""

    def __init__(self, worker_ips: List[str], ssh_key: str, ssh_user: str):
        """
        Initialize worker manager

        Args:
            worker_ips: List of worker IP addresses
            ssh_key: Path to SSH private key for worker access
            ssh_user: SSH username for worker access
        """
        self.ssh_key = Path(ssh_key)
        self.ssh_user = ssh_user
        self.workers: Dict[str, Worker] = {}

        # Initialize workers
        for i, ip in enumerate(worker_ips, 1):
            worker_id = f"worker-{i}"
            self.workers[worker_id] = Worker(
                id=worker_id,
                ip=ip,
            )

        logger.info(f"Initialized {len(self.workers)} workers")

    async def initialize(self):
        """Initialize worker connections"""
        logger.info("Initializing worker connections...")

        # Check SSH connectivity to all workers
        for worker_id, worker in self.workers.items():
            try:
                await self._check_ssh_connectivity(worker)
                worker.status = "available"
                worker.health = "healthy"
                logger.info(f"Worker {worker_id} ({worker.ip}): Connected")
            except Exception as e:
                worker.status = "offline"
                worker.health = "unhealthy"
                logger.error(f"Worker {worker_id} ({worker.ip}): Failed to connect - {e}")

    async def _check_ssh_connectivity(self, worker: Worker) -> bool:
        """
        Check if worker is reachable via SSH

        Args:
            worker: Worker to check

        Returns:
            True if reachable
        """
        cmd = [
            "ssh",
            "-i", str(self.ssh_key),
            "-o", "StrictHostKeyChecking=no",
            "-o", "ConnectTimeout=5",
            f"{self.ssh_user}@{worker.ip}",
            "echo 'ok'"
        ]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)

            if proc.returncode == 0:
                return True
            else:
                raise Exception(f"SSH failed: {stderr.decode()}")

        except asyncio.TimeoutError:
            raise Exception("SSH connection timeout")
        except Exception as e:
            raise Exception(f"SSH error: {e}")

    async def check_worker_health(self, worker: Worker) -> bool:
        """
        Check worker health

        Args:
            worker: Worker to check

        Returns:
            True if healthy
        """
        try:
            # Check if worker service is running
            cmd = [
                "ssh",
                "-i", str(self.ssh_key),
                "-o", "StrictHostKeyChecking=no",
                "-o", "ConnectTimeout=5",
                f"{self.ssh_user}@{worker.ip}",
                "systemctl is-active ai-scrum-worker"
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)

            if proc.returncode == 0 and b"active" in stdout:
                worker.health = "healthy"
                worker.status = "available"
                worker.last_health_check = datetime.now()
                return True
            else:
                worker.health = "degraded"
                logger.warning(f"Worker {worker.id}: Service not running")
                return False

        except asyncio.TimeoutError:
            worker.health = "unhealthy"
            worker.status = "offline"
            logger.error(f"Worker {worker.id}: Health check timeout")
            return False
        except Exception as e:
            worker.health = "unhealthy"
            worker.status = "offline"
            logger.error(f"Worker {worker.id}: Health check failed - {e}")
            return False

    async def check_all_workers(self):
        """Check health of all workers"""
        tasks = []
        for worker in self.workers.values():
            tasks.append(self.check_worker_health(worker))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        healthy = sum(1 for r in results if r is True)
        logger.debug(f"Worker health check: {healthy}/{len(self.workers)} healthy")

    async def update_worker_activity(self, worker_id: str, task_number: Optional[int] = None):
        """
        Update worker activity

        Args:
            worker_id: Worker identifier
            task_number: Issue number being worked on (None if idle)
        """
        if worker_id not in self.workers:
            # Worker not registered, add it dynamically
            # Extract IP from worker_id if possible, otherwise use placeholder
            logger.warning(f"Unknown worker {worker_id} contacted orchestrator")
            return

        worker = self.workers[worker_id]
        worker.last_seen = datetime.now()

        if task_number:
            worker.status = "busy"
            worker.current_task = task_number
        else:
            worker.status = "available"
            worker.current_task = None

    async def get_worker_logs(self, worker_id: str, lines: int = 50) -> str:
        """
        Get worker logs

        Args:
            worker_id: Worker identifier
            lines: Number of log lines to retrieve

        Returns:
            Log content
        """
        if worker_id not in self.workers:
            return f"Worker {worker_id} not found"

        worker = self.workers[worker_id]

        try:
            cmd = [
                "ssh",
                "-i", str(self.ssh_key),
                "-o", "StrictHostKeyChecking=no",
                f"{self.ssh_user}@{worker.ip}",
                f"journalctl -u ai-scrum-worker -n {lines} --no-pager"
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)

            if proc.returncode == 0:
                return stdout.decode()
            else:
                return f"Failed to get logs: {stderr.decode()}"

        except Exception as e:
            return f"Error getting logs: {e}"

    async def restart_worker(self, worker_id: str) -> bool:
        """
        Restart worker service

        Args:
            worker_id: Worker identifier

        Returns:
            True if successful
        """
        if worker_id not in self.workers:
            logger.error(f"Worker {worker_id} not found")
            return False

        worker = self.workers[worker_id]

        try:
            cmd = [
                "ssh",
                "-i", str(self.ssh_key),
                "-o", "StrictHostKeyChecking=no",
                f"{self.ssh_user}@{worker.ip}",
                "systemctl restart ai-scrum-worker"
            ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(proc.communicate(), timeout=30)

            if proc.returncode == 0:
                logger.info(f"Restarted worker {worker_id}")
                return True
            else:
                logger.error(f"Failed to restart worker {worker_id}")
                return False

        except Exception as e:
            logger.error(f"Error restarting worker {worker_id}: {e}")
            return False

    async def shutdown(self):
        """Cleanup on shutdown"""
        logger.info("Shutting down worker manager...")
        # Could send shutdown signals to workers here if needed
