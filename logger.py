"""
Logging Module for AI Scrum Master

Provides comprehensive logging of workflow execution for debugging and monitoring.
"""
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class WorkflowLogger:
    """
    Comprehensive logging for AI Scrum Master workflows

    Features:
    - Console and file logging
    - Structured JSON logs for analysis
    - Agent-specific log tracking
    - Cost and performance metrics
    - Error tracking
    """

    def __init__(self, log_dir: Optional[Path] = None, workflow_id: Optional[str] = None):
        """
        Initialize workflow logger

        Args:
            log_dir: Directory for log files (default: ./logs)
            workflow_id: Unique ID for this workflow (default: timestamp)
        """
        self.log_dir = Path(log_dir) if log_dir else Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Generate workflow ID
        self.workflow_id = workflow_id or datetime.now().strftime("%Y%m%d_%H%M%S")

        # Log files
        self.log_file = self.log_dir / f"workflow_{self.workflow_id}.log"
        self.json_log_file = self.log_dir / f"workflow_{self.workflow_id}.json"

        # Structured log data
        self.workflow_data = {
            "workflow_id": self.workflow_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "user_story": None,
            "agents": [],
            "total_cost": 0.0,
            "total_duration_ms": 0,
            "revision_count": 0,
            "status": "running",
            "errors": []
        }

        # Setup Python logging
        self.logger = logging.getLogger(f"workflow_{self.workflow_id}")
        self.logger.setLevel(logging.DEBUG)

        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

        self.logger.info(f"=== Workflow {self.workflow_id} Started ===")

    def log_user_story(self, user_story: str):
        """Log the user story being implemented"""
        self.workflow_data["user_story"] = user_story
        self.logger.info(f"User Story: {user_story[:200]}...")
        self._save_json()

    def log_agent_start(self, agent_name: str, task: str):
        """Log when an agent starts execution"""
        agent_data = {
            "agent": agent_name,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "task": task,
            "success": None,
            "cost_usd": 0.0,
            "duration_ms": 0,
            "num_turns": 0,
            "error": None
        }
        self.workflow_data["agents"].append(agent_data)
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🤖 {agent_name} Agent Starting")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Task: {task[:150]}...")
        self._save_json()

    def log_agent_end(self, agent_name: str, result: Dict[str, Any]):
        """Log when an agent completes execution"""
        # Find the most recent agent entry
        for agent_data in reversed(self.workflow_data["agents"]):
            if agent_data["agent"] == agent_name and agent_data["end_time"] is None:
                agent_data["end_time"] = datetime.now().isoformat()
                agent_data["success"] = result.get("success", False)
                agent_data["cost_usd"] = result.get("cost_usd", 0.0)
                agent_data["duration_ms"] = result.get("duration_ms", 0)
                agent_data["num_turns"] = result.get("num_turns", 0)
                agent_data["error"] = result.get("error")

                # Update totals
                self.workflow_data["total_cost"] += agent_data["cost_usd"]
                self.workflow_data["total_duration_ms"] += agent_data["duration_ms"]

                # Log result
                if result.get("success"):
                    self.logger.info(f"✅ {agent_name} completed successfully")
                    self.logger.info(f"   Cost: ${agent_data['cost_usd']:.4f} | Duration: {agent_data['duration_ms']/1000:.1f}s | Turns: {agent_data['num_turns']}")
                else:
                    error = result.get("error", "Unknown error")
                    self.logger.error(f"❌ {agent_name} failed: {error}")
                    agent_data["error"] = error
                    self.workflow_data["errors"].append(f"{agent_name}: {error}")

                break

        self._save_json()

    def log_revision(self, revision_num: int, reason: str):
        """Log when a revision is requested"""
        self.workflow_data["revision_count"] = revision_num
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"🔄 REVISION #{revision_num}")
        self.logger.info(f"Reason: {reason[:200]}...")
        self.logger.info(f"{'='*60}\n")
        self._save_json()

    def log_decision(self, decision: str, details: Optional[str] = None):
        """Log Product Owner decision"""
        self.workflow_data["po_decision"] = decision
        self.logger.info(f"\n👔 Product Owner Decision: {decision}")
        if details:
            self.logger.info(f"Details: {details[:300]}...")
        self._save_json()

    def log_error(self, error: str):
        """Log an error"""
        self.workflow_data["errors"].append(error)
        self.logger.error(f"❌ Error: {error}")
        self._save_json()

    def log_workflow_complete(self, status: str = "completed"):
        """Log workflow completion"""
        self.workflow_data["end_time"] = datetime.now().isoformat()
        self.workflow_data["status"] = status

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"📊 WORKFLOW COMPLETE")
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Status: {status}")
        self.logger.info(f"Total Cost: ${self.workflow_data['total_cost']:.4f}")
        self.logger.info(f"Total Duration: {self.workflow_data['total_duration_ms']/1000:.1f}s")
        self.logger.info(f"Revisions: {self.workflow_data['revision_count']}")
        if self.workflow_data['errors']:
            self.logger.info(f"Errors: {len(self.workflow_data['errors'])}")
        self.logger.info(f"{'='*60}\n")
        self.logger.info(f"Log file: {self.log_file}")
        self.logger.info(f"JSON log: {self.json_log_file}")

        self._save_json()

    def _save_json(self):
        """Save structured log data to JSON file"""
        with open(self.json_log_file, 'w') as f:
            json.dump(self.workflow_data, f, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """Get workflow summary"""
        return {
            "workflow_id": self.workflow_id,
            "status": self.workflow_data["status"],
            "total_cost": self.workflow_data["total_cost"],
            "total_duration_s": self.workflow_data["total_duration_ms"] / 1000,
            "revisions": self.workflow_data["revision_count"],
            "errors": len(self.workflow_data["errors"]),
            "agents_executed": len(self.workflow_data["agents"]),
            "log_file": str(self.log_file),
            "json_log": str(self.json_log_file)
        }


def create_logger(workflow_id: Optional[str] = None) -> WorkflowLogger:
    """
    Create a new workflow logger

    Args:
        workflow_id: Optional workflow ID (default: timestamp)

    Returns:
        WorkflowLogger instance
    """
    return WorkflowLogger(workflow_id=workflow_id)
