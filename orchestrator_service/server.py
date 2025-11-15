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

from orchestrator_service.github_client import GitHubClient
from orchestrator_service.multi_repo_manager import MultiRepoManager
from orchestrator_service.work_queue import WorkQueue
from orchestrator_service.worker_manager import WorkerManager
from orchestrator_service.simple_worker_tracker import SimpleWorkerTracker
from orchestrator_service.pr_review_tracker import PRReviewTracker

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
multi_repo_manager: Optional[MultiRepoManager] = None
work_queue: Optional[WorkQueue] = None
worker_manager: Optional[WorkerManager] = None
worker_tracker: Optional[SimpleWorkerTracker] = None
pr_tracker: Optional[PRReviewTracker] = None


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
    global github_client, multi_repo_manager, work_queue, worker_manager, worker_tracker, pr_tracker

    logger.info("Starting AI Scrum Master Orchestrator...")

    # Validate environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.error("GITHUB_TOKEN not set - GitHub integration disabled")
        github_client = None
        multi_repo_manager = None
    else:
        # Check for multi-repo configuration first
        github_repos = os.getenv("GITHUB_REPOS", "").split(",")
        github_repos = [repo.strip() for repo in github_repos if repo.strip()]

        if github_repos:
            # Multi-repo mode
            multi_repo_manager = MultiRepoManager(github_token, github_repos)
            github_client = None
            logger.info(f"Multi-repo mode: monitoring {len(github_repos)} repositories")
        else:
            # Single-repo mode (backward compatibility)
            github_repo = os.getenv("GITHUB_REPO")
            if not github_repo:
                logger.error("Neither GITHUB_REPOS nor GITHUB_REPO is set")
                raise RuntimeError("GITHUB_REPOS or GITHUB_REPO environment variable required")

            github_client = GitHubClient(github_token, github_repo)
            multi_repo_manager = None
            logger.info(f"Single-repo mode: {github_repo}")

    # Initialize work queue
    work_queue = WorkQueue()
    logger.info("Work queue initialized")

    # Initialize PR review tracker
    max_pending_prs = int(os.getenv("MAX_PENDING_PRS", "5"))
    block_on_changes = os.getenv("BLOCK_ON_CHANGES_REQUESTED", "true").lower() == "true"
    allow_parallel = os.getenv("ALLOW_PARALLEL_INDEPENDENT", "true").lower() == "true"

    pr_tracker = PRReviewTracker(
        max_pending_prs=max_pending_prs,
        block_on_changes_requested=block_on_changes,
        allow_parallel_independent=allow_parallel
    )
    logger.info("PR review tracker initialized")

    # Initialize worker manager or tracker
    worker_ips = os.getenv("WORKER_IPS", "").split(",")
    worker_ips = [ip.strip() for ip in worker_ips if ip.strip()]

    if not worker_ips:
        logger.info("No worker IPs configured - using dynamic worker tracker")
        worker_manager = None
        worker_tracker = SimpleWorkerTracker(timeout_minutes=5)
    else:
        ssh_key = os.getenv("WORKER_SSH_KEY", "/root/.ssh/id_orchestrator")
        ssh_user = os.getenv("WORKER_SSH_USER", "root")

        worker_manager = WorkerManager(worker_ips, ssh_key, ssh_user)
        await worker_manager.initialize()
        logger.info(f"Worker manager initialized with {len(worker_ips)} workers")
        worker_tracker = None

    # Start background tasks
    if github_client or multi_repo_manager:
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
    if worker_manager:
        worker_count = len(worker_manager.workers)
        active_workers = sum(1 for w in worker_manager.workers.values() if w.status == "available")
    elif worker_tracker:
        worker_count = worker_tracker.get_worker_count()
        active_workers = worker_tracker.get_available_worker_count()
    else:
        worker_count = 0
        active_workers = 0

    # Get repository info
    if multi_repo_manager:
        repos = multi_repo_manager.get_repositories()
        github_info = {
            "connected": True,
            "mode": "multi-repo",
            "repositories": repos,
            "count": len(repos)
        }
    elif github_client:
        github_info = {
            "connected": True,
            "mode": "single-repo",
            "repository": github_client.repo
        }
    else:
        github_info = {"connected": False}

    # Get PR tracker status
    pr_review_info = {}
    if pr_tracker:
        pr_status = pr_tracker.get_status()
        pr_review_info = {
            "pending_prs": pr_status["pending_prs"],
            "changes_requested": pr_status["changes_requested"],
            "approved": pr_status["approved"],
            "queue_blocked": pr_status["queue_blocked"],
            "blocking_reason": pr_status["blocking_reason"]
        }

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
        "github": github_info,
        "pr_review": pr_review_info,
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

    # Update worker activity tracking
    if worker_manager:
        await worker_manager.update_worker_activity(worker_id)
    elif worker_tracker:
        worker_tracker.update_activity(worker_id)

    # Check if queue is blocked by pending PRs
    if pr_tracker and pr_tracker.should_block_queue():
        blocking_reason = pr_tracker.get_blocking_reason()
        logger.info(f"Queue blocked for {worker_id}: {blocking_reason}")
        return {
            "work_available": False,
            "blocked": True,
            "reason": blocking_reason
        }

    # Get next work item
    work_item = work_queue.get_next_work(worker_id)

    if not work_item:
        return {"work_available": False, "blocked": False}

    # Update tracker with task assignment
    if worker_tracker:
        worker_tracker.update_activity(worker_id, work_item["issue_number"])

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

    # Get work item to find repository
    work_item = work_queue.items.get(result.issue_number)
    repo = work_item.repository if work_item else None

    # Mark work as complete in queue
    work_queue.mark_complete(
        result.issue_number,
        result.worker_id,
        result.success,
        pr_url=result.pr_url if result.success else None,
        error=result.error
    )

    # Update GitHub issue and register PR for review
    if result.success and repo:
        try:
            comment = (
                f"✅ Implementation completed!\n\n"
                f"Pull Request: {result.pr_url}\n\n"
                f"Completed by: {result.worker_id}\n\n"
                f"⚠️ This PR requires human review before merging."
            )

            if multi_repo_manager:
                await multi_repo_manager.add_issue_comment(repo, result.issue_number, comment)
                await multi_repo_manager.add_issue_label(repo, result.issue_number, "ai-completed")
                await multi_repo_manager.remove_issue_label(repo, result.issue_number, "ai-in-progress")
            elif github_client:
                await github_client.add_issue_comment(result.issue_number, comment)
                await github_client.add_issue_label(result.issue_number, "ai-completed")
                await github_client.remove_issue_label(result.issue_number, "ai-in-progress")

            # Register PR with review tracker
            if pr_tracker:
                # Extract dependencies from work item (if available)
                dependencies = set()
                if work_item and hasattr(work_item, 'dependencies'):
                    dependencies = work_item.dependencies

                pr_tracker.add_pending_pr(
                    issue_number=result.issue_number,
                    pr_url=result.pr_url,
                    repository=repo,
                    worker_id=result.worker_id,
                    dependencies=dependencies
                )
                logger.info(f"Registered PR for review tracking: {repo}#{result.issue_number}")

        except Exception as e:
            logger.error(f"Failed to update GitHub issue {repo}#{result.issue_number}: {e}")

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

    # Get work item to find repository
    work_item = work_queue.items.get(result.issue_number)
    repo = work_item.repository if work_item else None

    # Mark work as failed in queue
    work_queue.mark_failed(result.issue_number, result.worker_id, result.error)

    # Update GitHub issue
    if repo:
        try:
            comment = (
                f"❌ Implementation failed\n\n"
                f"Error: {result.error}\n\n"
                f"Worker: {result.worker_id}\n\n"
                f"This issue has been released for retry."
            )

            if multi_repo_manager:
                await multi_repo_manager.add_issue_comment(repo, result.issue_number, comment)
                await multi_repo_manager.remove_issue_label(repo, result.issue_number, "ai-in-progress")
                await multi_repo_manager.add_issue_label(repo, result.issue_number, "ai-failed")
            elif github_client:
                await github_client.add_issue_comment(result.issue_number, comment)
                await github_client.remove_issue_label(result.issue_number, "ai-in-progress")
                await github_client.add_issue_label(result.issue_number, "ai-failed")

        except Exception as e:
            logger.error(f"Failed to update GitHub issue {repo}#{result.issue_number}: {e}")

    return {"status": "acknowledged"}


@app.get("/workers")
async def list_workers():
    """List all workers and their status"""
    workers = []

    if worker_manager:
        for worker_id, worker in worker_manager.workers.items():
            workers.append({
                "id": worker_id,
                "ip": worker.ip,
                "status": worker.status,
                "current_task": worker.current_task,
                "last_seen": worker.last_seen.isoformat() if worker.last_seen else None,
                "health": worker.health,
            })
    elif worker_tracker:
        active_workers = worker_tracker.get_active_workers()
        for worker_id, worker in active_workers.items():
            workers.append({
                "id": worker_id,
                "status": "busy" if worker.current_task else "available",
                "current_task": worker.current_task,
                "last_seen": worker.last_seen.isoformat(),
                "first_seen": worker.first_seen.isoformat(),
                "total_tasks": worker.total_tasks,
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


@app.get("/pr-review/status")
async def pr_review_status():
    """Get PR review tracker status"""
    if not pr_tracker:
        raise HTTPException(status_code=503, detail="PR tracker not initialized")

    status = pr_tracker.get_status()
    pending_details = pr_tracker.get_pending_pr_details()

    return {
        **status,
        "pending_pr_details": pending_details
    }


@app.post("/pr-review/approved/{issue_number}")
async def pr_approved(issue_number: int):
    """
    Notify that a PR was approved

    This can be called by review_prs.py script or GitHub webhook
    """
    if not pr_tracker:
        raise HTTPException(status_code=503, detail="PR tracker not initialized")

    pr_tracker.mark_approved(issue_number)
    logger.info(f"PR #{issue_number} marked as approved")

    return {"status": "acknowledged", "message": f"PR #{issue_number} approved"}


@app.post("/pr-review/changes-requested/{issue_number}")
async def pr_changes_requested(issue_number: int):
    """
    Notify that changes were requested on a PR

    This can be called by review_prs.py script or GitHub webhook
    """
    if not pr_tracker:
        raise HTTPException(status_code=503, detail="PR tracker not initialized")

    pr_tracker.mark_changes_requested(issue_number)
    logger.warning(f"Changes requested on PR #{issue_number}")

    return {"status": "acknowledged", "message": f"Changes requested on PR #{issue_number}"}


@app.post("/pr-review/merged/{issue_number}")
async def pr_merged(issue_number: int):
    """
    Notify that a PR was merged

    This can be called by review_prs.py script or GitHub webhook
    """
    if not pr_tracker:
        raise HTTPException(status_code=503, detail="PR tracker not initialized")

    pr_tracker.mark_merged(issue_number)
    logger.info(f"PR #{issue_number} marked as merged")

    return {"status": "acknowledged", "message": f"PR #{issue_number} merged"}


# Background Tasks

async def poll_github_issues():
    """Background task: Poll GitHub for new issues"""
    if not github_client and not multi_repo_manager:
        return

    poll_interval = int(os.getenv("GITHUB_POLL_INTERVAL", "60"))
    logger.info(f"Starting GitHub polling (interval: {poll_interval}s)")

    while True:
        try:
            label = os.getenv("GITHUB_ISSUE_LABELS", "ai-ready")

            # Fetch issues from all repositories
            if multi_repo_manager:
                issues = await multi_repo_manager.fetch_all_issues(labels=[label], state="open")
            else:
                # Single-repo mode (backward compatibility)
                issues = await github_client.fetch_issues(labels=[label], state="open")
                # Add repository info for single-repo mode
                for issue in issues:
                    issue["repository"] = github_client.repo

            # Add new issues to work queue
            for issue in issues:
                repo = issue.get("repository")
                issue_number = issue["number"]

                # Create unique identifier for issue (repo + issue number)
                issue_key = f"{repo}#{issue_number}"

                # Skip if already in queue
                if work_queue.has_issue(issue_number):
                    continue

                # Add to queue
                work_queue.add_work_item(
                    issue_number=issue_number,
                    title=issue["title"],
                    body=issue["body"],
                    labels=issue["labels"],
                    repository=repo,
                )

                # Update issue labels
                if multi_repo_manager:
                    await multi_repo_manager.add_issue_label(repo, issue_number, "ai-in-progress")
                else:
                    await github_client.add_issue_label(issue_number, "ai-in-progress")

                logger.info(f"Added issue {repo}#{issue_number} to work queue: {issue['title']}")

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
