#!/usr/bin/env python3
"""
Worker Client

This script runs on worker containers and:
1. Polls orchestrator for work
2. Executes AI Scrum Master workflow
3. Reports results back to orchestrator
"""

import os
import sys
import time
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator import Orchestrator

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class WorkerClient:
    """Worker client that polls for and executes work"""

    def __init__(self, worker_id: str, orchestrator_url: str, workspace_dir: Path):
        self.worker_id = worker_id
        self.orchestrator_url = orchestrator_url.rstrip("/")
        self.workspace_dir = workspace_dir
        self.poll_interval = int(os.getenv("WORKER_POLL_INTERVAL", "30"))

        logger.info(f"Worker {worker_id} initialized")
        logger.info(f"Orchestrator: {orchestrator_url}")
        logger.info(f"Workspace: {workspace_dir}")

    def run(self):
        """Main worker loop"""
        logger.info(f"Worker {self.worker_id} starting...")

        while True:
            try:
                # Request work from orchestrator
                work = self._request_work()

                if not work or not work.get("work_available"):
                    logger.debug("No work available, waiting...")
                    time.sleep(self.poll_interval)
                    continue

                # Execute work
                self._execute_work(work)

            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                time.sleep(self.poll_interval)

    def _request_work(self) -> dict:
        """Request next work item from orchestrator"""
        try:
            response = requests.get(
                f"{self.orchestrator_url}/work/next",
                params={"worker_id": self.worker_id},
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"Failed to request work: {e}")
            return {}

    def _execute_work(self, work: dict):
        """
        Execute work item

        Args:
            work: Work item from orchestrator
        """
        issue_number = work["issue_number"]
        title = work["title"]
        body = work["body"]
        branch_name = work["branch_name"]

        logger.info(f"Starting work on issue #{issue_number}: {title}")

        try:
            # Create isolated workspace for this issue
            issue_workspace = self.workspace_dir / f"issue-{issue_number}"
            issue_workspace.mkdir(parents=True, exist_ok=True)

            # Initialize orchestrator (AI Scrum Master)
            orchestrator = Orchestrator(workspace_dir=issue_workspace)

            # Execute workflow
            result = orchestrator.process_user_story(body)

            if result.approved:
                # Success - push and create PR
                pr_url = self._create_pull_request(
                    issue_workspace,
                    issue_number,
                    title,
                    branch_name,
                    work["repository"]
                )

                # Report success
                self._report_complete(issue_number, pr_url, success=True)

                logger.info(f"Completed issue #{issue_number}: {pr_url}")
            else:
                # Failed - PO rejected
                error = f"Product Owner rejected after {result.revision_count} revisions"
                self._report_complete(issue_number, None, success=False, error=error)

                logger.warning(f"Issue #{issue_number} rejected: {error}")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to execute issue #{issue_number}: {error_msg}", exc_info=True)

            # Report failure
            self._report_failed(issue_number, error_msg)

        finally:
            # Cleanup workspace
            self._cleanup_workspace(issue_workspace)

    def _create_pull_request(
        self,
        workspace: Path,
        issue_number: int,
        title: str,
        branch_name: str,
        repository: str,
    ) -> str:
        """
        Create pull request on GitHub

        Args:
            workspace: Workspace directory
            issue_number: Issue number
            title: Issue title
            branch_name: Branch name
            repository: Repository (owner/repo)

        Returns:
            PR URL
        """
        # TODO: Implement actual GitHub PR creation
        # For now, return placeholder
        return f"https://github.com/{repository}/pull/{issue_number}"

    def _report_complete(
        self,
        issue_number: int,
        pr_url: str,
        success: bool,
        error: str = None
    ):
        """Report work completion to orchestrator"""
        try:
            response = requests.post(
                f"{self.orchestrator_url}/work/complete",
                json={
                    "worker_id": self.worker_id,
                    "issue_number": issue_number,
                    "pr_url": pr_url,
                    "success": success,
                    "error": error,
                },
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"Reported completion for issue #{issue_number}")

        except requests.RequestException as e:
            logger.error(f"Failed to report completion: {e}")

    def _report_failed(self, issue_number: int, error: str):
        """Report work failure to orchestrator"""
        try:
            response = requests.post(
                f"{self.orchestrator_url}/work/failed",
                json={
                    "worker_id": self.worker_id,
                    "issue_number": issue_number,
                    "error": error,
                },
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"Reported failure for issue #{issue_number}")

        except requests.RequestException as e:
            logger.error(f"Failed to report failure: {e}")

    def _cleanup_workspace(self, workspace: Path):
        """Clean up workspace after work completion"""
        try:
            import shutil
            if workspace.exists():
                shutil.rmtree(workspace)
                logger.debug(f"Cleaned up workspace: {workspace}")
        except Exception as e:
            logger.warning(f"Failed to cleanup workspace {workspace}: {e}")


if __name__ == "__main__":
    # Get configuration from environment
    worker_id = os.getenv("WORKER_ID")
    orchestrator_url = os.getenv("ORCHESTRATOR_URL")
    workspace_dir = Path(os.getenv("WORKSPACE_DIR", "/opt/ai-scrum-master/workspace"))

    if not worker_id:
        logger.error("WORKER_ID environment variable not set")
        sys.exit(1)

    if not orchestrator_url:
        logger.error("ORCHESTRATOR_URL environment variable not set")
        sys.exit(1)

    # Create and run worker
    worker = WorkerClient(worker_id, orchestrator_url, workspace_dir)
    worker.run()
