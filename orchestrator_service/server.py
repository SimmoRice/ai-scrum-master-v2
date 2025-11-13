#!/usr/bin/env python3
"""
Orchestrator Service for Distributed AI Scrum Master

This service:
1. Polls GitHub for issues labeled 'ai-ready'
2. Assigns issues to available workers
3. Monitors worker health and progress
4. Manages work queue and prevents conflicts
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator.github_client import GitHubClient
from orchestrator.work_queue import WorkQueue
from orchestrator.worker_manager import WorkerManager

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Scrum Master Orchestrator",
    description="Distributed work orchestration for AI Scrum Master",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
github_client: Optional[GitHubClient] = None
work_queue: Optional[WorkQueue] = None
worker_manager: Optional[WorkerManager] = None


# Pydantic models
class WorkRequest(BaseModel):
    worker_id: str


class WorkComplete(BaseModel):
    worker_id: str
    issue_number: int
    pr_url: str
    success: bool
    error: Optional[str] = None


class WorkFailed(BaseModel):
    worker_id: str
    issue_number: int
    error: str


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global github_client, work_queue, worker_manager

    logger.info("Starting AI Scrum Master Orchestrator...")

    # Validate environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN not set - GitHub integration disabled")
        github_client = None
    else:
        github_repo = os.getenv("GITHUB_REPO")
        if not github_repo:
            logger.error("GITHUB_REPO not set")
            raise RuntimeError("GITHUB_REPO environment variable required")

        github_client = GitHubClient(github_token, github_repo)
        logger.info(f"GitHub client initialized for {github_repo}")

    # Initialize work queue
    work_queue = WorkQueue()
    logger.info("Work queue initialized")

    # Initialize worker manager
    worker_ips = os.getenv("WORKER_IPS", "").split(",")
    worker_ips = [ip.strip() for ip in worker_ips if ip.strip()]

    if not worker_ips:
        logger.warning("No worker IPs configured - running in standalone mode")
        worker_manager = None
    else:
        ssh_key = os.getenv("WORKER_SSH_KEY", "/root/.ssh/id_orchestrator")
        ssh_user = os.getenv("WORKER_SSH_USER", "root")

        worker_manager = WorkerManager(worker_ips, ssh_key, ssh_user)
        await worker_manager.initialize()
        logger.info(f"Worker manager initialized with {len(worker_ips)} workers")

    # Start background tasks
    if github_client:
        asyncio.create_task(poll_github_issues())

    if worker_manager:
        asyncio.create_task(health_check_workers())

    logger.info("Orchestrator startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down orchestrator...")

    if worker_manager:
        await worker_manager.shutdown()


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Scrum Master Orchestrator",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    worker_count = len(worker_manager.workers) if worker_manager else 0
    active_workers = sum(1 for w in (worker_manager.workers.values() if worker_manager else []) if w.status == "available")

    return {
        "status": "healthy",
        "workers": {
            "total": worker_count,
            "available": active_workers,
        },
        "queue": {
            "pending": work_queue.pending_count() if work_queue else 0,
            "in_progress": work_queue.in_progress_count() if work_queue else 0,
            "completed": work_queue.completed_count() if work_queue else 0,
        },
        "github_connected": github_client is not None,
    }


@app.get("/work/next")
async def get_next_work(worker_id: str):
    """
    Worker requests next work item

    Args:
        worker_id: Identifier for the requesting worker

    Returns:
        Work item or None if no work available
    """
    if not work_queue:
        raise HTTPException(status_code=503, detail="Work queue not initialized")

    if worker_manager:
        # Update worker last seen
        await worker_manager.update_worker_activity(worker_id)

    # Get next work item
    work_item = work_queue.get_next_work(worker_id)

    if not work_item:
        return {"work_available": False}

    logger.info(f"Assigned issue #{work_item['issue_number']} to {worker_id}")

    return {
        "work_available": True,
        "issue_number": work_item["issue_number"],
        "title": work_item["title"],
        "body": work_item["body"],
        "labels": work_item["labels"],
        "branch_name": work_item["branch_name"],
        "repository": work_item["repository"],
    }


@app.post("/work/complete")
async def mark_work_complete(result: WorkComplete):
    """
    Worker reports work completion

    Args:
        result: Work completion details
    """
    if not work_queue:
        raise HTTPException(status_code=503, detail="Work queue not initialized")

    logger.info(
        f"Worker {result.worker_id} completed issue #{result.issue_number}: "
        f"{'success' if result.success else 'failed'}"
    )

    # Mark work as complete in queue
    work_queue.mark_complete(
        result.issue_number,
        result.worker_id,
        result.success,
        pr_url=result.pr_url if result.success else None,
        error=result.error
    )

    # Update GitHub issue
    if github_client and result.success:
        try:
            await github_client.add_issue_comment(
                result.issue_number,
                f"✅ Implementation completed!\n\nPull Request: {result.pr_url}\n\n"
                f"Completed by: {result.worker_id}"
            )
            await github_client.add_issue_label(result.issue_number, "ai-completed")
            await github_client.remove_issue_label(result.issue_number, "ai-in-progress")
        except Exception as e:
            logger.error(f"Failed to update GitHub issue #{result.issue_number}: {e}")

    return {"status": "acknowledged"}


@app.post("/work/failed")
async def mark_work_failed(result: WorkFailed):
    """
    Worker reports work failure

    Args:
        result: Work failure details
    """
    if not work_queue:
        raise HTTPException(status_code=503, detail="Work queue not initialized")

    logger.warning(
        f"Worker {result.worker_id} failed issue #{result.issue_number}: {result.error}"
    )

    # Mark work as failed in queue
    work_queue.mark_failed(result.issue_number, result.worker_id, result.error)

    # Update GitHub issue
    if github_client:
        try:
            await github_client.add_issue_comment(
                result.issue_number,
                f"❌ Implementation failed\n\nError: {result.error}\n\n"
                f"Worker: {result.worker_id}\n\n"
                f"This issue has been released for retry."
            )
            await github_client.remove_issue_label(result.issue_number, "ai-in-progress")
            await github_client.add_issue_label(result.issue_number, "ai-failed")
        except Exception as e:
            logger.error(f"Failed to update GitHub issue #{result.issue_number}: {e}")

    return {"status": "acknowledged"}


@app.get("/workers")
async def list_workers():
    """List all workers and their status"""
    if not worker_manager:
        return {"workers": []}

    workers = []
    for worker_id, worker in worker_manager.workers.items():
        workers.append({
            "id": worker_id,
            "ip": worker.ip,
            "status": worker.status,
            "current_task": worker.current_task,
            "last_seen": worker.last_seen.isoformat() if worker.last_seen else None,
            "health": worker.health,
        })

    return {"workers": workers}


@app.get("/queue")
async def queue_status():
    """Get work queue status"""
    if not work_queue:
        raise HTTPException(status_code=503, detail="Work queue not initialized")

    return {
        "pending": work_queue.get_pending_items(),
        "in_progress": work_queue.get_in_progress_items(),
        "completed": work_queue.get_completed_items(limit=10),
    }


# Background Tasks

async def poll_github_issues():
    """Background task: Poll GitHub for new issues"""
    if not github_client:
        return

    poll_interval = int(os.getenv("GITHUB_POLL_INTERVAL", "60"))
    logger.info(f"Starting GitHub polling (interval: {poll_interval}s)")

    while True:
        try:
            # Fetch issues with 'ai-ready' label
            label = os.getenv("GITHUB_ISSUE_LABELS", "ai-ready")
            issues = await github_client.fetch_issues(labels=[label], state="open")

            # Add new issues to work queue
            for issue in issues:
                # Skip if already in queue
                if work_queue.has_issue(issue["number"]):
                    continue

                # Add to queue
                work_queue.add_work_item(
                    issue_number=issue["number"],
                    title=issue["title"],
                    body=issue["body"],
                    labels=issue["labels"],
                    repository=github_client.repo,
                )

                # Update issue labels
                await github_client.add_issue_label(issue["number"], "ai-in-progress")

                logger.info(f"Added issue #{issue['number']} to work queue: {issue['title']}")

        except Exception as e:
            logger.error(f"Error polling GitHub issues: {e}")

        await asyncio.sleep(poll_interval)


async def health_check_workers():
    """Background task: Check worker health"""
    if not worker_manager:
        return

    check_interval = int(os.getenv("WORKER_HEALTH_CHECK_INTERVAL", "30"))
    logger.info(f"Starting worker health checks (interval: {check_interval}s)")

    while True:
        try:
            await worker_manager.check_all_workers()
        except Exception as e:
            logger.error(f"Error checking worker health: {e}")

        await asyncio.sleep(check_interval)


# Main entry point

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("ORCHESTRATOR_HOST", "0.0.0.0")
    port = int(os.getenv("ORCHESTRATOR_PORT", "8000"))

    logger.info(f"Starting orchestrator on {host}:{port}")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
