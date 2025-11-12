"""
Tests for utils module

Tests shared utility functions including sanitization and validation.
"""

import pytest
from utils import (
    sanitize_user_input,
    sanitize_commit_message,
    sanitize_github_text,
    validate_branch_name,
    validate_github_label,
    validate_issue_number
)


class TestSanitizeUserInput:
    """Test sanitize_user_input function"""

    def test_removes_null_bytes(self):
        result = sanitize_user_input("Hello\x00World")
        assert result == "HelloWorld"

    def test_removes_control_characters(self):
        result = sanitize_user_input("Hello\x01\x02World")
        assert result == "HelloWorld"

    def test_keeps_newlines_and_tabs(self):
        result = sanitize_user_input("Hello\nWorld\tTest")
        assert "Hello" in result
        assert "World" in result

    def test_truncates_long_input(self):
        long_text = "A" * 100000
        result = sanitize_user_input(long_text, max_length=1000)
        assert len(result) == 1000

    def test_handles_empty_string(self):
        result = sanitize_user_input("")
        assert result == ""

    def test_strips_whitespace(self):
        result = sanitize_user_input("  Hello World  ")
        assert result == "Hello World"


class TestSanitizeCommitMessage:
    """Test sanitize_commit_message function"""

    def test_removes_null_bytes(self):
        result = sanitize_commit_message("Fix\x00bug")
        assert result == "Fixbug"

    def test_removes_control_characters(self):
        result = sanitize_commit_message("Fix\x01bug\x02")
        assert result == "Fixbug"

    def test_keeps_newlines(self):
        result = sanitize_commit_message("Title\n\nBody")
        assert "Title" in result
        assert "Body" in result

    def test_truncates_long_message(self):
        long_msg = "A" * 10000
        result = sanitize_commit_message(long_msg)
        assert len(result) <= 5050  # 5000 + truncation message

    def test_handles_empty_message(self):
        result = sanitize_commit_message("")
        assert result == "Empty commit message"

    def test_strips_whitespace(self):
        result = sanitize_commit_message("  Fix bug  ")
        assert result == "Fix bug"


class TestSanitizeGithubText:
    """Test sanitize_github_text function"""

    def test_removes_null_bytes(self):
        result = sanitize_github_text("PR\x00Title")
        assert result == "PRTitle"

    def test_removes_control_characters(self):
        result = sanitize_github_text("PR\x01Title")
        assert result == "PRTitle"

    def test_keeps_newlines_and_tabs(self):
        result = sanitize_github_text("Line1\nLine2\tTab")
        assert "Line1" in result
        assert "Line2" in result

    def test_truncates_long_text(self):
        long_text = "A" * 20000
        result = sanitize_github_text(long_text, max_length=1000)
        assert len(result) <= 1050  # 1000 + truncation message

    def test_handles_empty_string(self):
        result = sanitize_github_text("")
        assert result == ""


class TestValidateBranchName:
    """Test validate_branch_name function"""

    def test_accepts_valid_branch_names(self):
        valid_names = [
            "main",
            "feature-branch",
            "feature_branch",
            "feature/branch",
            "feature-123",
            "FEATURE-BRANCH"
        ]
        for name in valid_names:
            assert validate_branch_name(name), f"Should accept: {name}"

    def test_rejects_dangerous_characters(self):
        dangerous_names = [
            "branch;rm",
            "branch&ls",
            "branch|cat",
            "branch$USER",
            "branch`whoami`",
            "branch<file",
            "branch>file",
            'branch"test',
            "branch'test",
            "branch with space"
        ]
        for name in dangerous_names:
            assert not validate_branch_name(name), f"Should reject: {name}"

    def test_rejects_empty_string(self):
        assert not validate_branch_name("")

    def test_rejects_special_chars(self):
        assert not validate_branch_name("branch@test")
        assert not validate_branch_name("branch#test")
        assert not validate_branch_name("branch!test")


class TestValidateGithubLabel:
    """Test validate_github_label function"""

    def test_accepts_valid_labels(self):
        valid_labels = [
            "bug",
            "feature",
            "enhancement",
            "bug-fix",
            "bug_fix",
            "P1",
            "v2-0-0"
        ]
        for label in valid_labels:
            result = validate_github_label(label)
            assert result == label, f"Should accept: {label}"

    def test_rejects_invalid_labels(self):
        invalid_labels = [
            "bug;test",
            "bug&test",
            "bug|test",
            "bug test",
            "bug@test",
            "bug#test"
        ]
        for label in invalid_labels:
            result = validate_github_label(label)
            assert result is None, f"Should reject: {label}"

    def test_rejects_empty_string(self):
        assert validate_github_label("") is None

    def test_rejects_too_long(self):
        long_label = "A" * 51
        assert validate_github_label(long_label) is None

    def test_accepts_max_length(self):
        max_label = "A" * 50
        assert validate_github_label(max_label) == max_label


class TestValidateIssueNumber:
    """Test validate_issue_number function"""

    def test_accepts_positive_integers(self):
        assert validate_issue_number(1)
        assert validate_issue_number(123)
        assert validate_issue_number(999999)

    def test_rejects_zero(self):
        assert not validate_issue_number(0)

    def test_rejects_negative(self):
        assert not validate_issue_number(-1)
        assert not validate_issue_number(-123)

    def test_rejects_strings(self):
        assert not validate_issue_number("123")
        assert not validate_issue_number("abc")

    def test_rejects_floats(self):
        assert not validate_issue_number(123.45)

    def test_rejects_none(self):
        assert not validate_issue_number(None)


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""

    def test_sanitize_malicious_user_story(self):
        malicious = "Fix bug;\x00rm -rf /; ls -la"
        result = sanitize_user_input(malicious)
        assert "\x00" not in result
        # Should still contain the legitimate text
        assert "Fix bug" in result

    def test_sanitize_commit_with_injection_attempt(self):
        malicious = "Update code`whoami`"
        result = sanitize_commit_message(malicious)
        # Backticks not explicitly filtered but command won't execute
        assert "Update code" in result

    def test_branch_name_injection_prevented(self):
        malicious = "feature;rm -rf /"
        assert not validate_branch_name(malicious)

    def test_github_label_sql_injection_prevented(self):
        malicious = "bug'; DROP TABLE users--"
        assert validate_github_label(malicious) is None
