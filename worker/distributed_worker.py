#!/usr/bin/env python3
"""
Distributed Worker Implementation

As described in DISTRIBUTED_ARCHITECTURE.md, this worker:
1. Polls orchestrator for work
2. Creates isolated workspace per issue
3. Executes full AI Scrum Master workflow
4. Pushes to GitHub and creates PR
5. Reports results back
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestrator_client import OrchestratorClient
from orchestrator import Orchestrator as AIScrumOrchestrator

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class DistributedWorker:
    """
    Distributed worker for AI Scrum Master

    Implements the worker lifecycle described in DISTRIBUTED_ARCHITECTURE.md
    """

    def __init__(self, worker_id: str, orchestrator_url: str):
        """
        Initialize distributed worker

        Args:
            worker_id: Unique worker identifier
            orchestrator_url: Orchestrator API endpoint
        """
        self.worker_id = worker_id
        self.client = OrchestratorClient(orchestrator_url)
        self.workspace_base = Path(os.getenv("WORKSPACE_DIR", "/opt/ai-scrum-master/workspace"))
        self.workspace_base.mkdir(parents=True, exist_ok=True)

        # GitHub configuration
        self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set - PR creation will fail")

        logger.info(f"Worker {worker_id} initialized")
        logger.info(f"Orchestrator: {orchestrator_url}")
        logger.info(f"Workspace: {self.workspace_base}")

    def run(self):
        """Main worker loop"""
        logger.info(f"Worker {self.worker_id} starting...")

        while True:
            try:
                # 1. Request work from orchestrator
                work_item = self.client.get_next_work()
                if not work_item:
                    time.sleep(30)  # Wait before checking again
                    continue

                try:
                    # 2. Setup isolated workspace
                    workspace = self.setup_workspace(work_item)

                    # 3. Run AI Scrum Master workflow
                    result = self.execute_workflow(work_item, workspace)

                    if result.approved:
                        # 4. Push to GitHub and create PR
                        pr_url = self.create_pull_request(work_item, workspace)

                        # 5. Report success
                        self.client.mark_complete(work_item["issue_number"], pr_url)

                        logger.info(
                            f"✅ Issue #{work_item['issue_number']} completed: {pr_url}"
                        )
                    else:
                        # Workflow not approved - report failure
                        error = f"PO rejected after {result.revision_count} revisions"
                        self.client.mark_failed(work_item["issue_number"], error)

                        logger.warning(
                            f"❌ Issue #{work_item['issue_number']} rejected: {error}"
                        )

                except Exception as e:
                    # Report failure to orchestrator
                    error_msg = str(e)
                    logger.error(
                        f"💥 Issue #{work_item['issue_number']} failed: {error_msg}",
                        exc_info=True
                    )
                    self.client.mark_failed(work_item["issue_number"], error_msg)

                finally:
                    # Cleanup workspace
                    self.cleanup_workspace(workspace)

            except KeyboardInterrupt:
                logger.info("Worker shutting down...")
                break
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
                time.sleep(30)

    def setup_workspace(self, work_item: Dict[str, Any]) -> Path:
        """
        Setup isolated workspace for issue

        Args:
            work_item: Work item from orchestrator

        Returns:
            Workspace directory path
        """
        issue_number = work_item["issue_number"]
        workspace = self.workspace_base / f"issue-{issue_number}"

        # Clean up if exists
        if workspace.exists():
            import shutil
            shutil.rmtree(workspace)

        workspace.mkdir(parents=True)

        logger.info(f"📁 Created workspace: {workspace}")
        return workspace

    def execute_workflow(
        self,
        work_item: Dict[str, Any],
        workspace: Path
    ) -> Any:
        """
        Execute AI Scrum Master workflow

        Args:
            work_item: Work item details
            workspace: Isolated workspace directory

        Returns:
            WorkflowResult
        """
        issue_number = work_item["issue_number"]
        title = work_item["title"]
        body = work_item["body"]

        logger.info(f"🚀 Starting workflow for issue #{issue_number}: {title}")

        # Initialize AI Scrum Master orchestrator
        orchestrator = AIScrumOrchestrator(workspace_dir=workspace)

        # Convert GitHub issue to user story
        user_story = self.format_user_story(work_item)

        # Execute workflow
        result = orchestrator.process_user_story(user_story)

        logger.info(
            f"✨ Workflow completed: "
            f"{'APPROVED' if result.approved else 'REJECTED'} "
            f"({result.revision_count} revisions, ${result.total_cost:.2f})"
        )

        return result

    def format_user_story(self, work_item: Dict[str, Any]) -> str:
        """
        Format GitHub issue as user story

        Args:
            work_item: Work item details

        Returns:
            Formatted user story
        """
        title = work_item["title"]
        body = work_item["body"]
        labels = work_item.get("labels", [])

        # Add context from labels
        context = ""
        if "priority:critical" in labels or "priority:high" in labels:
            context += "\n⚠️ HIGH PRIORITY - Complete with urgency\n"

        if "complexity:small" in labels:
            context += "\n💡 This should be a small, focused change\n"
        elif "complexity:large" in labels:
            context += "\n🏗️ This is a complex feature requiring careful implementation\n"

        return f"""# {title}

{context}

{body}

---
GitHub Issue #{work_item['issue_number']}
Repository: {work_item['repository']}
"""

    def create_pull_request(
        self,
        work_item: Dict[str, Any],
        workspace: Path
    ) -> str:
        """
        Push branch and create PR on GitHub

        Args:
            work_item: Work item details
            workspace: Workspace directory

        Returns:
            PR URL
        """
        issue_number = work_item["issue_number"]
        branch_name = work_item["branch_name"]
        repository = work_item["repository"]
        title = work_item["title"]

        logger.info(f"📤 Creating pull request for issue #{issue_number}")

        try:
            # Change to workspace directory
            os.chdir(workspace)

            # Configure git
            subprocess.run(
                ["git", "config", "user.name", "AI Scrum Master"],
                check=True, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.email", "ai@scrum-master.local"],
                check=True, capture_output=True
            )

            # Push branch to remote
            logger.info(f"Pushing branch {branch_name}...")
            subprocess.run(
                ["git", "push", "-u", "origin", branch_name],
                check=True,
                capture_output=True,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}
            )

            # Create PR using GitHub CLI
            pr_body = f"""Automated implementation of issue #{issue_number}

## Implementation Summary
This PR was automatically generated by AI Scrum Master.

### Changes
- Implemented by: Architect agent
- Security hardened by: Security agent
- Tested by: Tester agent
- Approved by: Product Owner agent

### Related Issue
Closes #{issue_number}

---
🤖 Generated by [AI Scrum Master](https://github.com/YOUR_ORG/ai-scrum-master-v2)
Worker: {self.worker_id}
"""

            logger.info("Creating pull request...")
            result = subprocess.run(
                [
                    "gh", "pr", "create",
                    "--repo", repository,
                    "--title", f"[AI] {title}",
                    "--body", pr_body,
                    "--head", branch_name,
                    "--base", "main",
                ],
                check=True,
                capture_output=True,
                text=True,
                env={**os.environ, "GH_TOKEN": self.github_token}
            )

            pr_url = result.stdout.strip()
            logger.info(f"✅ Pull request created: {pr_url}")
            return pr_url

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to create PR: {e.stderr}"
            logger.error(error_msg)
            raise Exception(error_msg)

    def cleanup_workspace(self, workspace: Path):
        """
        Clean up workspace after completion

        Args:
            workspace: Workspace directory to clean
        """
        try:
            if workspace and workspace.exists():
                import shutil
                shutil.rmtree(workspace)
                logger.info(f"🧹 Cleaned up workspace: {workspace}")
        except Exception as e:
            logger.warning(f"Failed to cleanup workspace: {e}")


def main():
    """Main entry point"""
    # Get configuration from environment
    worker_id = os.getenv("WORKER_ID")
    orchestrator_url = os.getenv("ORCHESTRATOR_URL")

    if not worker_id:
        logger.error("WORKER_ID environment variable not set")
        sys.exit(1)

    if not orchestrator_url:
        logger.error("ORCHESTRATOR_URL environment variable not set")
        sys.exit(1)

    # Verify ANTHROPIC_API_KEY is set
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Create and run worker
    worker = DistributedWorker(worker_id, orchestrator_url)
    worker.run()


if __name__ == "__main__":
    main()
