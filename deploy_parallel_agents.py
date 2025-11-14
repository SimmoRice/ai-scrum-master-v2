#!/usr/bin/env python3
"""
Parallel Agent Deployment Script

Deploys and manages multiple AI Scrum Master worker instances for parallel execution.
Supports local multi-process testing and distributed deployment scenarios.

Usage:
    # Deploy 3 parallel agents locally
    python deploy_parallel_agents.py --workers 3 --mode local

    # Deploy with orchestrator service
    python deploy_parallel_agents.py --workers 5 --mode distributed --orchestrator-url http://localhost:8000

    # Test parallel execution with mock issues
    python deploy_parallel_agents.py --workers 2 --mode test --mock-issues 5
"""

import os
import sys
import time
import signal
import argparse
import logging
import subprocess
import multiprocessing
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import Orchestrator
from github_integration import GitHubIntegration
from config import GITHUB_CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class WorkerStatus:
    """Status of a worker instance"""
    worker_id: str
    pid: Optional[int]
    status: str  # running, idle, working, failed, stopped
    current_issue: Optional[int] = None
    issues_completed: int = 0
    total_cost: float = 0.0
    start_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None


class ParallelAgentManager:
    """
    Manages multiple parallel AI Scrum Master workers

    Responsibilities:
    - Start/stop workers
    - Monitor worker health
    - Load balancing
    - Aggregate metrics
    """

    def __init__(
        self,
        num_workers: int,
        mode: str = "local",
        orchestrator_url: Optional[str] = None,
        workspace_base: Optional[Path] = None
    ):
        """
        Initialize parallel agent manager

        Args:
            num_workers: Number of parallel workers to deploy
            mode: Deployment mode (local, distributed, test)
            orchestrator_url: Orchestrator service URL (for distributed mode)
            workspace_base: Base directory for worker workspaces
        """
        self.num_workers = num_workers
        self.mode = mode
        self.orchestrator_url = orchestrator_url
        self.workspace_base = workspace_base or Path("./parallel_workspace")
        self.workspace_base.mkdir(parents=True, exist_ok=True)

        self.workers: Dict[str, WorkerStatus] = {}
        self.processes: Dict[str, multiprocessing.Process] = {}
        self.shutdown_event = multiprocessing.Event()

        logger.info(f"Parallel Agent Manager initialized")
        logger.info(f"  Mode: {mode}")
        logger.info(f"  Workers: {num_workers}")
        logger.info(f"  Workspace: {self.workspace_base}")

    def deploy_workers(self):
        """Deploy all worker instances"""
        logger.info(f"Deploying {self.num_workers} workers...")

        for i in range(self.num_workers):
            worker_id = f"worker-{i+1:02d}"
            worker_workspace = self.workspace_base / worker_id
            worker_workspace.mkdir(parents=True, exist_ok=True)

            # Create worker status
            self.workers[worker_id] = WorkerStatus(
                worker_id=worker_id,
                pid=None,
                status="starting",
                start_time=datetime.now()
            )

            if self.mode == "local":
                # Local multi-process mode
                process = multiprocessing.Process(
                    target=self._run_local_worker,
                    args=(worker_id, worker_workspace),
                    name=worker_id
                )
                process.start()
                self.processes[worker_id] = process
                self.workers[worker_id].pid = process.pid
                self.workers[worker_id].status = "idle"

                logger.info(f"  ✅ Started {worker_id} (PID: {process.pid})")

            elif self.mode == "distributed":
                # Distributed mode - launch worker connecting to orchestrator
                if not self.orchestrator_url:
                    raise ValueError("orchestrator_url required for distributed mode")

                process = multiprocessing.Process(
                    target=self._run_distributed_worker,
                    args=(worker_id, worker_workspace, self.orchestrator_url),
                    name=worker_id
                )
                process.start()
                self.processes[worker_id] = process
                self.workers[worker_id].pid = process.pid
                self.workers[worker_id].status = "idle"

                logger.info(f"  ✅ Started {worker_id} (PID: {process.pid})")

            elif self.mode == "test":
                # Test mode - simulate workers
                logger.info(f"  ✅ Simulated {worker_id}")
                self.workers[worker_id].status = "idle"

        logger.info(f"✅ All {self.num_workers} workers deployed")

    def _run_local_worker(self, worker_id: str, workspace: Path):
        """
        Run a local worker in its own process

        This worker polls for GitHub issues with 'ready-for-dev' label
        and processes them independently.
        """
        logger.info(f"[{worker_id}] Starting local worker...")

        # Setup signal handlers
        signal.signal(signal.SIGTERM, lambda s, f: sys.exit(0))
        signal.signal(signal.SIGINT, lambda s, f: sys.exit(0))

        try:
            while not self.shutdown_event.is_set():
                # Check for available work
                issue = self._fetch_next_issue(worker_id)

                if not issue:
                    # No work available - wait
                    time.sleep(10)
                    continue

                # Process issue
                logger.info(f"[{worker_id}] Processing issue #{issue['number']}: {issue['title']}")

                try:
                    # Create isolated workspace for this issue
                    issue_workspace = workspace / f"issue-{issue['number']}"
                    issue_workspace.mkdir(parents=True, exist_ok=True)

                    # Initialize orchestrator
                    orchestrator = Orchestrator(workspace_dir=issue_workspace, verbose=False)

                    # Execute workflow
                    user_story = f"{issue['title']}\n\n{issue.get('body', '')}"
                    result = orchestrator.process_user_story(user_story)

                    if result.approved:
                        logger.info(f"[{worker_id}] ✅ Issue #{issue['number']} approved (cost: ${result.total_cost:.4f})")
                        # Mark complete (in real implementation, create PR)
                    else:
                        logger.warning(f"[{worker_id}] ❌ Issue #{issue['number']} not approved")

                except Exception as e:
                    logger.error(f"[{worker_id}] Error processing issue #{issue['number']}: {e}", exc_info=True)

        except KeyboardInterrupt:
            logger.info(f"[{worker_id}] Shutting down...")

    def _run_distributed_worker(self, worker_id: str, workspace: Path, orchestrator_url: str):
        """
        Run a distributed worker connecting to orchestrator service
        """
        from worker.distributed_worker import DistributedWorker

        logger.info(f"[{worker_id}] Starting distributed worker...")
        logger.info(f"[{worker_id}] Orchestrator: {orchestrator_url}")

        # Set environment for this worker
        os.environ["WORKER_ID"] = worker_id
        os.environ["ORCHESTRATOR_URL"] = orchestrator_url
        os.environ["WORKSPACE_DIR"] = str(workspace)

        try:
            worker = DistributedWorker(worker_id, orchestrator_url)
            worker.run()
        except KeyboardInterrupt:
            logger.info(f"[{worker_id}] Shutting down...")

    def _fetch_next_issue(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch next available issue for worker (simple implementation)

        In production, this would use orchestrator service or distributed lock
        """
        # This is a simplified implementation for local testing
        # Real implementation would use orchestrator service
        return None

    def monitor_workers(self, duration: int = 60):
        """
        Monitor worker status for specified duration

        Args:
            duration: Monitoring duration in seconds (0 = infinite)
        """
        logger.info(f"Monitoring workers for {duration}s...")

        start_time = time.time()

        try:
            while True:
                # Check if duration exceeded
                if duration > 0 and (time.time() - start_time) > duration:
                    break

                # Print status
                self._print_status()

                # Check worker health
                for worker_id, process in self.processes.items():
                    if not process.is_alive():
                        logger.warning(f"Worker {worker_id} died unexpectedly!")
                        self.workers[worker_id].status = "failed"

                time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Monitoring interrupted")

    def _print_status(self):
        """Print current status of all workers"""
        print("\n" + "="*80)
        print(f"PARALLEL WORKERS STATUS - {datetime.now().strftime('%H:%M:%S')}")
        print("="*80)

        for worker_id, status in self.workers.items():
            status_symbol = {
                "running": "🟢",
                "idle": "⚪",
                "working": "🔵",
                "failed": "🔴",
                "stopped": "⚫"
            }.get(status.status, "❓")

            print(f"{status_symbol} {worker_id:15s} | "
                  f"Status: {status.status:10s} | "
                  f"Completed: {status.issues_completed:3d} | "
                  f"Cost: ${status.total_cost:7.2f}")

        print("="*80 + "\n")

    def shutdown(self):
        """Gracefully shutdown all workers"""
        logger.info("Shutting down all workers...")

        self.shutdown_event.set()

        # Terminate all processes
        for worker_id, process in self.processes.items():
            if process.is_alive():
                logger.info(f"  Stopping {worker_id}...")
                process.terminate()
                process.join(timeout=5)

                if process.is_alive():
                    logger.warning(f"  Force killing {worker_id}...")
                    process.kill()
                    process.join()

        logger.info("✅ All workers stopped")

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        total_completed = sum(w.issues_completed for w in self.workers.values())
        total_cost = sum(w.total_cost for w in self.workers.values())
        active_workers = sum(1 for w in self.workers.values() if w.status in ["idle", "working"])

        return {
            "total_workers": self.num_workers,
            "active_workers": active_workers,
            "total_issues_completed": total_completed,
            "total_cost": total_cost,
            "average_cost_per_issue": total_cost / total_completed if total_completed > 0 else 0
        }


def run_parallel_test(num_workers: int, num_issues: int):
    """
    Run a parallel test with mock issues

    Args:
        num_workers: Number of parallel workers
        num_issues: Number of mock issues to process
    """
    logger.info(f"Running parallel test: {num_workers} workers, {num_issues} issues")

    print("\n" + "="*80)
    print("PARALLEL AGENT TEST")
    print("="*80)
    print(f"Workers: {num_workers}")
    print(f"Mock Issues: {num_issues}")
    print("="*80 + "\n")

    # Create mock issues
    mock_issues = [
        {
            "number": i + 1,
            "title": f"Test Feature #{i + 1}",
            "body": f"Implement test feature number {i + 1}",
            "labels": ["ready-for-dev", "test"]
        }
        for i in range(num_issues)
    ]

    # Initialize manager
    manager = ParallelAgentManager(
        num_workers=num_workers,
        mode="test"
    )

    try:
        # Deploy workers
        manager.deploy_workers()

        # Simulate processing
        print("\n🚀 Simulating parallel execution...\n")

        for i in range(10):  # 10 second simulation
            time.sleep(1)

            # Simulate some workers completing issues
            for worker in manager.workers.values():
                if i % 3 == 0 and len(mock_issues) > 0:
                    issue = mock_issues.pop(0)
                    worker.issues_completed += 1
                    worker.total_cost += 0.08  # Mock cost
                    worker.status = "working"
                else:
                    worker.status = "idle"

            manager._print_status()

        # Print summary
        summary = manager.get_summary()
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(f"Workers: {summary['total_workers']}")
        print(f"Issues Completed: {summary['total_issues_completed']}")
        print(f"Total Cost: ${summary['total_cost']:.4f}")
        print(f"Avg Cost/Issue: ${summary['average_cost_per_issue']:.4f}")
        print("="*80 + "\n")

    finally:
        manager.shutdown()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Deploy and manage parallel AI Scrum Master workers"
    )

    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=3,
        help="Number of parallel workers to deploy (default: 3)"
    )

    parser.add_argument(
        "--mode", "-m",
        choices=["local", "distributed", "test"],
        default="local",
        help="Deployment mode (default: local)"
    )

    parser.add_argument(
        "--orchestrator-url",
        help="Orchestrator service URL (required for distributed mode)"
    )

    parser.add_argument(
        "--workspace",
        help="Base workspace directory for workers"
    )

    parser.add_argument(
        "--monitor-duration",
        type=int,
        default=0,
        help="Duration to monitor workers in seconds (0 = infinite)"
    )

    parser.add_argument(
        "--mock-issues",
        type=int,
        help="Number of mock issues to create for testing"
    )

    args = parser.parse_args()

    # Validate
    if args.mode == "distributed" and not args.orchestrator_url:
        parser.error("--orchestrator-url required for distributed mode")

    # Run test mode if mock issues specified
    if args.mock_issues:
        run_parallel_test(args.workers, args.mock_issues)
        return

    # Deploy workers
    manager = ParallelAgentManager(
        num_workers=args.workers,
        mode=args.mode,
        orchestrator_url=args.orchestrator_url,
        workspace_base=Path(args.workspace) if args.workspace else None
    )

    try:
        manager.deploy_workers()

        # Monitor
        if args.monitor_duration >= 0:
            manager.monitor_workers(args.monitor_duration)

        # Print summary
        summary = manager.get_summary()
        print("\n" + "="*80)
        print("DEPLOYMENT SUMMARY")
        print("="*80)
        print(f"Workers: {summary['total_workers']} ({summary['active_workers']} active)")
        print(f"Issues Completed: {summary['total_issues_completed']}")
        print(f"Total Cost: ${summary['total_cost']:.4f}")
        print("="*80 + "\n")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    finally:
        manager.shutdown()


if __name__ == "__main__":
    main()
