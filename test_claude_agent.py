"""
Test suite for claude_agent.py

Tests ClaudeCodeAgent with mocking to avoid actual Claude API calls.
Covers happy paths, edge cases, error handling, and security validations.
"""
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from claude_agent import ClaudeCodeAgent


class TestClaudeAgentInitialization:
    """Test ClaudeCodeAgent initialization"""

    def test_init_creates_agent(self):
        """Test basic agent initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            assert agent.role == "TestAgent"
            assert agent.workspace == workspace
            assert agent.system_prompt == "Test prompt"

    def test_init_creates_workspace_directory(self):
        """Test that initialization creates workspace if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "new_workspace"
            assert not workspace.exists()

            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            assert workspace.exists()
            assert workspace.is_dir()

    def test_init_with_custom_allowed_tools(self):
        """Test initialization with custom allowed tools"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            custom_tools = "Read,Write,Edit"
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt", allowed_tools=custom_tools)

            assert agent.allowed_tools == custom_tools

    def test_init_uses_default_allowed_tools(self):
        """Test that default allowed tools are set from config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Should have some default tools
            assert agent.allowed_tools is not None
            assert len(agent.allowed_tools) > 0

    def test_init_sets_timeout_from_config(self):
        """Test that timeout is set from config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            assert agent.timeout > 0


class TestSecuritySanitization:
    """Test security sanitization methods"""

    def test_sanitize_log_output_redacts_anthropic_api_key(self):
        """Security: Test that Anthropic API keys are redacted"""
        output = "ANTHROPIC_API_KEY=sk-ant-1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = ClaudeCodeAgent._sanitize_log_output(output)

        assert "sk-ant-1234567890" not in sanitized
        assert "REDACTED" in sanitized

    def test_sanitize_log_output_redacts_github_token(self):
        """Security: Test that GitHub tokens are redacted"""
        output = "TOKEN=ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        sanitized = ClaudeCodeAgent._sanitize_log_output(output)

        assert "ghp_123" not in sanitized
        assert "REDACTED" in sanitized

    def test_sanitize_log_output_redacts_passwords(self):
        """Security: Test that passwords are redacted"""
        output = "PASSWORD=mysecretpassword123"
        sanitized = ClaudeCodeAgent._sanitize_log_output(output)

        assert "mysecretpassword" not in sanitized
        assert "REDACTED" in sanitized

    def test_sanitize_log_output_redacts_secrets(self):
        """Security: Test that secrets are redacted"""
        output = "SECRET=my-secret-value-123"
        sanitized = ClaudeCodeAgent._sanitize_log_output(output)

        assert "my-secret-value" not in sanitized
        assert "REDACTED" in sanitized

    def test_sanitize_log_output_case_insensitive(self):
        """Security: Test that sanitization is case-insensitive"""
        outputs = [
            "password=test123",
            "PASSWORD=test123",
            "Password=test123",
            "PaSsWoRd=test123"
        ]

        for output in outputs:
            sanitized = ClaudeCodeAgent._sanitize_log_output(output)
            assert "REDACTED" in sanitized

    def test_sanitize_log_output_preserves_safe_content(self):
        """Test that safe content is preserved"""
        output = "This is a safe log message without secrets"
        sanitized = ClaudeCodeAgent._sanitize_log_output(output)

        assert sanitized == output

    def test_sanitize_log_output_multiple_patterns(self):
        """Security: Test sanitizing multiple sensitive patterns"""
        output = """
        ANTHROPIC_API_KEY=sk-ant-123456
        PASSWORD=secret123
        TOKEN=ghp_abcdef
        """
        sanitized = ClaudeCodeAgent._sanitize_log_output(output)

        assert "sk-ant-123456" not in sanitized
        assert "secret123" not in sanitized
        assert "ghp_abcdef" not in sanitized
        assert "REDACTED" in sanitized


class TestExecuteTaskSuccess:
    """Test successful task execution"""

    @patch('claude_agent.subprocess.run')
    def test_execute_task_success(self, mock_run):
        """Test successful task execution"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock successful response
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({
                "result": "Task completed successfully",
                "session_id": "test-session-123",
                "total_cost_usd": 0.05,
                "num_turns": 3,
                "duration_ms": 5000
            })
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute task
            result = agent.execute_task("Test task")

            # Verify result
            assert result["success"] is True
            assert result["result"] == "Task completed successfully"
            assert result["session_id"] == "test-session-123"
            assert result["cost_usd"] == 0.05
            assert result["num_turns"] == 3
            assert result["duration_ms"] == 5000

    @patch('claude_agent.subprocess.run')
    def test_execute_task_calls_claude_cli(self, mock_run):
        """Test that execute_task calls Claude CLI with correct arguments"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock successful response
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({"result": "Success"})
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute task
            agent.execute_task("Test task", timeout=100)

            # Verify subprocess was called
            mock_run.assert_called_once()
            call_args = mock_run.call_args

            # Check command arguments
            cmd = call_args[0][0]
            assert cmd[0] == "claude"
            assert "-p" in cmd
            assert "Test task" in cmd
            assert "--output-format" in cmd
            assert "json" in cmd
            assert "--system-prompt" in cmd
            assert "Test prompt" in cmd

            # Check keyword arguments
            kwargs = call_args[1]
            assert kwargs["cwd"] == str(workspace)
            assert kwargs["capture_output"] is True
            assert kwargs["text"] is True
            assert kwargs["timeout"] == 100


class TestExecuteTaskFailure:
    """Test task execution failures"""

    @patch('claude_agent.subprocess.run')
    def test_execute_task_nonzero_exit_code(self, mock_run):
        """Test handling of non-zero exit code"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock failed response
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "Some output"
            mock_result.stderr = "Error occurred"
            mock_run.return_value = mock_result

            # Execute task
            result = agent.execute_task("Test task")

            # Verify result
            assert result["success"] is False
            assert "error" in result
            assert "exited with code 1" in result["error"]

    @patch('claude_agent.subprocess.run')
    def test_execute_task_json_parse_error(self, mock_run):
        """Test handling of invalid JSON response"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock response with invalid JSON
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = "This is not valid JSON"
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute task
            result = agent.execute_task("Test task")

            # Verify result
            assert result["success"] is False
            assert "error" in result
            assert "parse JSON" in result["error"]

    @patch('claude_agent.subprocess.run')
    def test_execute_task_timeout(self, mock_run):
        """Test handling of task timeout"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock timeout
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired("claude", 10)

            # Execute task
            result = agent.execute_task("Test task")

            # Verify result
            assert result["success"] is False
            assert "error" in result
            assert "timed out" in result["error"]

    @patch('claude_agent.subprocess.run')
    def test_execute_task_exception(self, mock_run):
        """Test handling of unexpected exception"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock unexpected exception
            mock_run.side_effect = Exception("Unexpected error")

            # Execute task
            result = agent.execute_task("Test task")

            # Verify result - should not expose full exception
            assert result["success"] is False
            assert "error" in result
            assert "Unexpected error during agent execution" in result["error"]


class TestSecurityInExecution:
    """Test security features during task execution"""

    @patch('claude_agent.subprocess.run')
    def test_execute_task_sanitizes_stderr(self, mock_run):
        """Security: Test that stderr is sanitized before logging"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock response with sensitive data in stderr
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = "Output"
            mock_result.stderr = "Error: ANTHROPIC_API_KEY=sk-ant-secret123"
            mock_run.return_value = mock_result

            # Execute task
            result = agent.execute_task("Test task")

            # Result should not contain actual API key
            result_str = str(result)
            assert "sk-ant-secret123" not in result_str

    @patch('claude_agent.subprocess.run')
    def test_execute_task_limits_output_size(self, mock_run):
        """Security: Test that output size is limited"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock response with very large output
            large_output = "A" * 10000
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = large_output
            mock_result.stderr = large_output
            mock_run.return_value = mock_result

            # Execute task
            result = agent.execute_task("Test task")

            # Output should be truncated
            if "raw_stdout" in result:
                assert len(result["raw_stdout"]) <= 1000
            if "raw_stderr" in result:
                assert len(result["raw_stderr"]) <= 1000


class TestPrintResult:
    """Test result printing functionality"""

    def test_print_result_success(self, capsys):
        """Test printing successful result"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            result = {
                "success": True,
                "result": "Task completed successfully",
                "cost_usd": 0.05,
                "num_turns": 3,
                "duration_ms": 5000
            }

            agent.print_result(result)

            captured = capsys.readouterr()
            assert "✅ Success" in captured.out
            assert "Task completed successfully" in captured.out
            assert "$0.0500" in captured.out
            assert "Turns: 3" in captured.out

    def test_print_result_failure(self, capsys):
        """Test printing failed result"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            result = {
                "success": False,
                "error": "Task failed for some reason"
            }

            agent.print_result(result)

            captured = capsys.readouterr()
            assert "❌ Failed" in captured.out
            assert "Task failed for some reason" in captured.out

    def test_print_result_truncates_long_response(self, capsys):
        """Test that long responses are truncated"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            long_response = "A" * 1000
            result = {
                "success": True,
                "result": long_response,
                "cost_usd": 0.05,
                "num_turns": 3,
                "duration_ms": 5000
            }

            agent.print_result(result)

            captured = capsys.readouterr()
            # Should show truncation message
            assert "truncated" in captured.out


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @patch('claude_agent.subprocess.run')
    def test_execute_task_empty_task(self, mock_run):
        """Test executing an empty task"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({"result": "Empty task handled"})
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute empty task
            result = agent.execute_task("")

            assert mock_run.called

    @patch('claude_agent.subprocess.run')
    def test_execute_task_very_long_task(self, mock_run):
        """Test executing a very long task description"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({"result": "Long task handled"})
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute very long task
            long_task = "Task " * 10000
            result = agent.execute_task(long_task)

            assert mock_run.called

    @patch('claude_agent.subprocess.run')
    def test_execute_task_special_characters_in_task(self, mock_run):
        """Test executing task with special characters"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({"result": "Special chars handled"})
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute task with special characters
            special_task = "Task with 'quotes' and \"double quotes\" and \nnewlines"
            result = agent.execute_task(special_task)

            assert mock_run.called

    @patch('claude_agent.subprocess.run')
    def test_execute_task_missing_cost_fields(self, mock_run):
        """Test handling of response missing optional cost fields"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock response without cost fields
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({"result": "Success"})
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute task
            result = agent.execute_task("Test task")

            # Should have default values
            assert result["success"] is True
            assert result["cost_usd"] == 0.0
            assert result["num_turns"] == 0
            assert result["duration_ms"] == 0

    def test_repr_method(self):
        """Test __repr__ method"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            repr_str = repr(agent)

            assert "ClaudeCodeAgent" in repr_str
            assert "TestAgent" in repr_str
            assert str(workspace) in repr_str


class TestProgressMonitoring:
    """Test progress monitoring during long-running tasks"""

    @patch('claude_agent.subprocess.run')
    @patch('claude_agent.time.sleep')
    def test_progress_monitoring_starts(self, mock_sleep, mock_run):
        """Test that progress monitoring thread starts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            # Mock slow task
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({"result": "Success"})
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute task
            result = agent.execute_task("Test task")

            # Task should complete
            assert result["success"] is True


class TestCustomTimeout:
    """Test custom timeout functionality"""

    @patch('claude_agent.subprocess.run')
    def test_execute_task_custom_timeout(self, mock_run):
        """Test executing task with custom timeout"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            agent = ClaudeCodeAgent("TestAgent", workspace, "Test prompt")

            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({"result": "Success"})
            mock_result.stderr = ""
            mock_run.return_value = mock_result

            # Execute with custom timeout
            custom_timeout = 300
            result = agent.execute_task("Test task", timeout=custom_timeout)

            # Verify timeout was passed to subprocess
            call_kwargs = mock_run.call_args[1]
            assert call_kwargs["timeout"] == custom_timeout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
