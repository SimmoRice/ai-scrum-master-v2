"""
Test suite for logger.py

Tests WorkflowLogger functionality including logging, file operations, and metrics.
Covers happy paths, edge cases, and error handling.
"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from logger import WorkflowLogger, create_logger


class TestWorkflowLoggerInitialization:
    """Test WorkflowLogger initialization"""

    def test_init_creates_logger(self):
        """Test basic logger initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            assert logger.workflow_id is not None
            assert logger.log_dir == Path(tmpdir)
            assert logger.log_file.exists()

    def test_init_creates_log_directory(self):
        """Test that logger creates log directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            assert not log_dir.exists()

            logger = WorkflowLogger(log_dir=log_dir)

            assert log_dir.exists()
            assert log_dir.is_dir()

    def test_init_with_custom_workflow_id(self):
        """Test initialization with custom workflow ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_id = "test_workflow_123"
            logger = WorkflowLogger(log_dir=Path(tmpdir), workflow_id=custom_id)

            assert logger.workflow_id == custom_id
            assert custom_id in logger.log_file.name

    def test_init_generates_timestamp_workflow_id(self):
        """Test that logger generates timestamp-based workflow ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            # Should contain date components
            assert len(logger.workflow_id) > 0
            # Should be in format YYYYMMDD_HHMMSS
            parts = logger.workflow_id.split('_')
            assert len(parts) == 2

    def test_init_creates_json_log_file(self):
        """Test that JSON log file is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            assert logger.json_log_file.exists()
            assert logger.json_log_file.suffix == ".json"

    def test_init_workflow_data_structure(self):
        """Test that workflow data has correct initial structure"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            assert "workflow_id" in logger.workflow_data
            assert "start_time" in logger.workflow_data
            assert "agents" in logger.workflow_data
            assert "total_cost" in logger.workflow_data
            assert "status" in logger.workflow_data
            assert logger.workflow_data["status"] == "running"


class TestLoggingUserStory:
    """Test logging user stories"""

    def test_log_user_story(self):
        """Test logging a user story"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            user_story = "Add authentication feature"
            logger.log_user_story(user_story)

            assert logger.workflow_data["user_story"] == user_story

    def test_log_user_story_saves_to_json(self):
        """Test that logging user story saves to JSON file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            user_story = "Add authentication feature"
            logger.log_user_story(user_story)

            # Read JSON file
            with open(logger.json_log_file) as f:
                data = json.load(f)

            assert data["user_story"] == user_story

    def test_log_long_user_story(self):
        """Test logging a very long user story"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            long_story = "A" * 10000
            logger.log_user_story(long_story)

            assert logger.workflow_data["user_story"] == long_story


class TestLoggingAgentExecution:
    """Test logging agent execution"""

    def test_log_agent_start(self):
        """Test logging agent start"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_agent_start("Architect", "Build the feature")

            assert len(logger.workflow_data["agents"]) == 1
            agent_data = logger.workflow_data["agents"][0]
            assert agent_data["agent"] == "Architect"
            assert agent_data["task"] == "Build the feature"
            assert agent_data["success"] is None
            assert agent_data["end_time"] is None

    def test_log_agent_end_success(self):
        """Test logging successful agent completion"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_agent_start("Architect", "Build the feature")

            result = {
                "success": True,
                "cost_usd": 0.05,
                "duration_ms": 5000,
                "num_turns": 3
            }
            logger.log_agent_end("Architect", result)

            agent_data = logger.workflow_data["agents"][0]
            assert agent_data["success"] is True
            assert agent_data["cost_usd"] == 0.05
            assert agent_data["duration_ms"] == 5000
            assert agent_data["num_turns"] == 3
            assert agent_data["end_time"] is not None

    def test_log_agent_end_failure(self):
        """Test logging failed agent completion"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_agent_start("Security", "Review code")

            result = {
                "success": False,
                "error": "Security check failed"
            }
            logger.log_agent_end("Security", result)

            agent_data = logger.workflow_data["agents"][0]
            assert agent_data["success"] is False
            assert agent_data["error"] == "Security check failed"
            assert "Security check failed" in logger.workflow_data["errors"]

    def test_log_agent_updates_total_cost(self):
        """Test that agent logging updates total cost"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_agent_start("Architect", "Build")
            logger.log_agent_end("Architect", {"success": True, "cost_usd": 0.05, "duration_ms": 1000, "num_turns": 1})

            logger.log_agent_start("Security", "Review")
            logger.log_agent_end("Security", {"success": True, "cost_usd": 0.03, "duration_ms": 1000, "num_turns": 1})

            assert logger.workflow_data["total_cost"] == 0.08

    def test_log_agent_updates_total_duration(self):
        """Test that agent logging updates total duration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_agent_start("Architect", "Build")
            logger.log_agent_end("Architect", {"success": True, "cost_usd": 0.05, "duration_ms": 5000, "num_turns": 1})

            logger.log_agent_start("Security", "Review")
            logger.log_agent_end("Security", {"success": True, "cost_usd": 0.03, "duration_ms": 3000, "num_turns": 1})

            assert logger.workflow_data["total_duration_ms"] == 8000

    def test_log_multiple_agents(self):
        """Test logging multiple agents in sequence"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            agents = ["Architect", "Security", "Tester", "ProductOwner"]
            for agent in agents:
                logger.log_agent_start(agent, f"{agent} task")
                logger.log_agent_end(agent, {"success": True, "cost_usd": 0.01, "duration_ms": 1000, "num_turns": 1})

            assert len(logger.workflow_data["agents"]) == 4


class TestLoggingRevisions:
    """Test logging revisions"""

    def test_log_revision(self):
        """Test logging a revision"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_revision(1, "Product Owner requested changes")

            assert logger.workflow_data["revision_count"] == 1

    def test_log_multiple_revisions(self):
        """Test logging multiple revisions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            for i in range(1, 4):
                logger.log_revision(i, f"Revision {i}")

            assert logger.workflow_data["revision_count"] == 3


class TestLoggingDecisions:
    """Test logging Product Owner decisions"""

    def test_log_decision_approve(self):
        """Test logging APPROVE decision"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_decision("APPROVE", "Looks good!")

            assert logger.workflow_data["po_decision"] == "APPROVE"

    def test_log_decision_revise(self):
        """Test logging REVISE decision"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_decision("REVISE", "Needs improvements")

            assert logger.workflow_data["po_decision"] == "REVISE"

    def test_log_decision_reject(self):
        """Test logging REJECT decision"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_decision("REJECT", "Fundamentally flawed")

            assert logger.workflow_data["po_decision"] == "REJECT"


class TestLoggingErrors:
    """Test logging errors"""

    def test_log_error(self):
        """Test logging an error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_error("Something went wrong")

            assert "Something went wrong" in logger.workflow_data["errors"]

    def test_log_multiple_errors(self):
        """Test logging multiple errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            errors = ["Error 1", "Error 2", "Error 3"]
            for error in errors:
                logger.log_error(error)

            assert len(logger.workflow_data["errors"]) == 3
            for error in errors:
                assert error in logger.workflow_data["errors"]


class TestWorkflowCompletion:
    """Test workflow completion logging"""

    def test_log_workflow_complete(self):
        """Test logging workflow completion"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_workflow_complete("approved")

            assert logger.workflow_data["status"] == "approved"
            assert logger.workflow_data["end_time"] is not None

    def test_log_workflow_complete_statuses(self):
        """Test logging different completion statuses"""
        statuses = ["approved", "rejected", "failed", "completed", "max_revisions_reached"]

        for status in statuses:
            with tempfile.TemporaryDirectory() as tmpdir:
                logger = WorkflowLogger(log_dir=Path(tmpdir))
                logger.log_workflow_complete(status)
                assert logger.workflow_data["status"] == status

    def test_log_workflow_complete_saves_to_json(self):
        """Test that completion saves final state to JSON"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_user_story("Test story")
            logger.log_agent_start("Architect", "Build")
            logger.log_agent_end("Architect", {"success": True, "cost_usd": 0.05, "duration_ms": 5000, "num_turns": 3})
            logger.log_workflow_complete("approved")

            # Read JSON file
            with open(logger.json_log_file) as f:
                data = json.load(f)

            assert data["status"] == "approved"
            assert data["user_story"] == "Test story"
            assert len(data["agents"]) == 1


class TestGetSummary:
    """Test getting workflow summary"""

    def test_get_summary(self):
        """Test getting workflow summary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_user_story("Test story")
            logger.log_agent_start("Architect", "Build")
            logger.log_agent_end("Architect", {"success": True, "cost_usd": 0.05, "duration_ms": 5000, "num_turns": 3})
            logger.log_workflow_complete("approved")

            summary = logger.get_summary()

            assert "workflow_id" in summary
            assert summary["status"] == "approved"
            assert summary["total_cost"] == 0.05
            assert summary["total_duration_s"] == 5.0
            assert summary["agents_executed"] == 1
            assert summary["errors"] == 0

    def test_get_summary_with_errors(self):
        """Test summary with errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_error("Error 1")
            logger.log_error("Error 2")

            summary = logger.get_summary()

            assert summary["errors"] == 2

    def test_get_summary_with_revisions(self):
        """Test summary with revisions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_revision(1, "Revision 1")
            logger.log_revision(2, "Revision 2")

            summary = logger.get_summary()

            assert summary["revisions"] == 2


class TestJSONPersistence:
    """Test JSON file persistence"""

    def test_json_file_created_on_init(self):
        """Test that JSON file is created on initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            assert logger.json_log_file.exists()

    def test_json_file_updated_on_changes(self):
        """Test that JSON file is updated with each change"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_user_story("Test story")

            # Read JSON file
            with open(logger.json_log_file) as f:
                data = json.load(f)

            assert data["user_story"] == "Test story"

    def test_json_file_valid_format(self):
        """Test that JSON file maintains valid format"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_user_story("Test story")
            logger.log_agent_start("Architect", "Build")
            logger.log_agent_end("Architect", {"success": True, "cost_usd": 0.05, "duration_ms": 5000, "num_turns": 3})

            # Should be able to read as valid JSON
            with open(logger.json_log_file) as f:
                data = json.load(f)

            # Check structure
            assert isinstance(data, dict)
            assert "workflow_id" in data
            assert "agents" in data
            assert isinstance(data["agents"], list)


class TestLogFile:
    """Test text log file"""

    def test_log_file_created(self):
        """Test that log file is created"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            assert logger.log_file.exists()

    def test_log_file_contains_messages(self):
        """Test that log file contains logged messages"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_user_story("Test story")

            # Read log file
            content = logger.log_file.read_text()

            assert "Test story" in content


class TestCreateLogger:
    """Test create_logger helper function"""

    def test_create_logger_function(self):
        """Test create_logger function"""
        logger = create_logger()

        assert isinstance(logger, WorkflowLogger)
        assert logger.workflow_id is not None

    def test_create_logger_with_custom_id(self):
        """Test create_logger with custom ID"""
        custom_id = "custom_123"
        logger = create_logger(workflow_id=custom_id)

        assert logger.workflow_id == custom_id


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_log_agent_end_without_start(self):
        """Test logging agent end without corresponding start"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            # Log end without start - should not crash
            logger.log_agent_end("Architect", {"success": True, "cost_usd": 0.05, "duration_ms": 5000, "num_turns": 3})

            # Should not update anything since no matching start
            assert len(logger.workflow_data["agents"]) == 0

    def test_log_empty_strings(self):
        """Test logging empty strings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            logger.log_user_story("")
            logger.log_error("")
            logger.log_decision("APPROVE", "")

            # Should not crash
            assert logger.workflow_data["user_story"] == ""

    def test_log_special_characters(self):
        """Test logging special characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = WorkflowLogger(log_dir=Path(tmpdir))

            special_story = "Story with 'quotes' and \"double\" and \nnewlines"
            logger.log_user_story(special_story)

            assert logger.workflow_data["user_story"] == special_story

    def test_concurrent_logger_instances(self):
        """Test multiple logger instances don't interfere"""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger1 = WorkflowLogger(log_dir=Path(tmpdir), workflow_id="workflow1")
            logger2 = WorkflowLogger(log_dir=Path(tmpdir), workflow_id="workflow2")

            logger1.log_user_story("Story 1")
            logger2.log_user_story("Story 2")

            assert logger1.workflow_data["user_story"] == "Story 1"
            assert logger2.workflow_data["user_story"] == "Story 2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
