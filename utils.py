"""
Shared utility functions for AI Scrum Master

This module provides common utilities used across multiple modules,
particularly for input sanitization and validation.
"""

import re
from typing import Optional


def sanitize_user_input(text: str, max_length: int = 50000) -> str:
    """
    Sanitize user input to prevent injection attacks

    Security: Removes null bytes, limits length, and cleans control characters

    Args:
        text: Raw user input
        max_length: Maximum allowed length (default: 50KB)

    Returns:
        Sanitized text

    Example:
        >>> sanitize_user_input("Hello\\x00World")
        'HelloWorld'
    """
    if not text:
        return ""

    # Security: Remove null bytes
    text = text.replace('\0', '')

    # Security: Limit input length to prevent DoS
    if len(text) > max_length:
        text = text[:max_length]

    # Security: Remove potentially dangerous control characters (keep newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', text)

    return text.strip()


def sanitize_commit_message(message: str) -> str:
    """
    Sanitize git commit message to prevent command injection

    Security: Removes potentially dangerous characters from commit messages

    Args:
        message: Commit message to sanitize

    Returns:
        Sanitized commit message

    Example:
        >>> sanitize_commit_message("Fix\\x00bug")
        'Fixbug'
    """
    if not message:
        return "Empty commit message"

    # Security: Remove null bytes
    message = message.replace('\0', '')

    # Security: Remove control characters except newlines
    message = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', message)

    # Security: Limit message length to prevent DoS
    max_length = 5000
    if len(message) > max_length:
        message = message[:max_length] + "... (truncated for security)"

    return message.strip()


def sanitize_github_text(text: str, max_length: int = 10000) -> str:
    """
    Sanitize text for use in GitHub commands

    Security: Removes dangerous characters and limits length

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text

    Example:
        >>> sanitize_github_text("PR Title\\x00")
        'PR Title'
    """
    if not text:
        return ""

    # Security: Remove null bytes
    text = text.replace('\0', '')

    # Security: Limit length to prevent DoS
    if len(text) > max_length:
        text = text[:max_length] + "... (truncated for security)"

    # Security: Remove control characters except newlines and tabs
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)

    return text.strip()


def validate_branch_name(branch_name: str) -> bool:
    """
    Validate git branch name for security

    Security: Prevents command injection via branch names

    Args:
        branch_name: Branch name to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_branch_name("feature-branch")
        True
        >>> validate_branch_name("v1.0.0")
        True
        >>> validate_branch_name("bad;branch")
        False
    """
    if not branch_name:
        return False

    # Only allow alphanumeric, hyphen, underscore, slash, period
    if not re.match(r'^[a-zA-Z0-9/_.-]+$', branch_name):
        return False

    # Block dangerous characters
    dangerous_chars = [';', '&', '|', '$', '`', '<', '>', '\\', '"', "'", ' ', '\n', '\r', '\t']
    return not any(char in branch_name for char in dangerous_chars)


def validate_github_label(label: str) -> Optional[str]:
    """
    Validate and sanitize GitHub label name

    Security: Prevents command injection via labels

    Args:
        label: Label name to validate

    Returns:
        Sanitized label if valid, None if invalid

    Example:
        >>> validate_github_label("bug")
        'bug'
        >>> validate_github_label("bad;label")
        None
    """
    if not label:
        return None

    # Only allow alphanumeric, hyphen, underscore
    if not re.match(r'^[a-zA-Z0-9_-]+$', label):
        return None

    # Limit length
    if len(label) > 50:
        return None

    return label


def validate_issue_number(issue_number) -> bool:
    """
    Validate GitHub issue number

    Security: Ensures issue number is a positive integer

    Args:
        issue_number: Issue number to validate

    Returns:
        True if valid, False otherwise

    Example:
        >>> validate_issue_number(123)
        True
        >>> validate_issue_number(-1)
        False
        >>> validate_issue_number("abc")
        False
    """
    if not isinstance(issue_number, int):
        return False

    return issue_number > 0
