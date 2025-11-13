"""
Orchestrator Client

Simple HTTP client library for workers to communicate with orchestrator.
As described in DISTRIBUTED_ARCHITECTURE.md
"""

import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """Client for communicating with orchestrator service"""

    def __init__(self, orchestrator_url: str, timeout: int = 30):
        """
        Initialize orchestrator client

        Args:
            orchestrator_url: Base URL of orchestrator API
            timeout: Request timeout in seconds
        """
        self.base_url = orchestrator_url.rstrip("/")
        self.timeout = timeout
        self.worker_id = None

        logger.info(f"Orchestrator client initialized: {self.base_url}")

    def set_worker_id(self, worker_id: str):
        """Set worker ID for this client"""
        self.worker_id = worker_id

    def get_next_work(self) -> Optional[Dict[str, Any]]:
        """
        Request next work item from orchestrator

        Returns:
            Work item dict or None if no work available
        """
        if not self.worker_id:
            raise ValueError("Worker ID not set. Call set_worker_id() first.")

        try:
            response = requests.get(
                f"{self.base_url}/work/next",
                params={"worker_id": self.worker_id},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("work_available"):
                logger.info(f"Received work: Issue #{data['issue_number']}")
                return data
            else:
                logger.debug("No work available")
                return None

        except requests.Timeout:
            logger.error("Request to orchestrator timed out")
            return None
        except requests.RequestException as e:
            logger.error(f"Failed to get work from orchestrator: {e}")
            return None

    def mark_complete(
        self,
        issue_number: int,
        pr_url: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> bool:
        """
        Report work completion to orchestrator

        Args:
            issue_number: GitHub issue number
            pr_url: Pull request URL
            success: Whether work was successful
            error: Error message if failed

        Returns:
            True if successfully reported
        """
        if not self.worker_id:
            raise ValueError("Worker ID not set. Call set_worker_id() first.")

        try:
            response = requests.post(
                f"{self.base_url}/work/complete",
                json={
                    "worker_id": self.worker_id,
                    "issue_number": issue_number,
                    "pr_url": pr_url,
                    "success": success,
                    "error": error,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"Reported completion for issue #{issue_number}")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to report completion: {e}")
            return False

    def mark_failed(self, issue_number: int, error: str) -> bool:
        """
        Report work failure to orchestrator

        Args:
            issue_number: GitHub issue number
            error: Error message

        Returns:
            True if successfully reported
        """
        if not self.worker_id:
            raise ValueError("Worker ID not set. Call set_worker_id() first.")

        try:
            response = requests.post(
                f"{self.base_url}/work/failed",
                json={
                    "worker_id": self.worker_id,
                    "issue_number": issue_number,
                    "error": error,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            logger.info(f"Reported failure for issue #{issue_number}")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to report failure: {e}")
            return False

    def health_check(self) -> Optional[Dict[str, Any]]:
        """
        Check orchestrator health

        Returns:
            Health status dict or None if unreachable
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return None
