"""
Synchronous GitHub API Client for Workers

Uses requests library for synchronous GitHub API operations.
Workers use this instead of gh CLI for better reliability and no external dependencies.
"""

import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """Synchronous GitHub API client for worker operations"""

    def __init__(self, token: str):
        """
        Initialize GitHub API client

        Args:
            token: GitHub personal access token
        """
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def add_issue_comment(self, repository: str, issue_number: int, body: str) -> bool:
        """
        Add a comment to a GitHub issue

        Args:
            repository: Repository in format "owner/repo"
            issue_number: Issue number
            body: Comment body (markdown supported)

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/repos/{repository}/issues/{issue_number}/comments"

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={"body": body},
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Added comment to issue #{issue_number}")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to add comment to issue #{issue_number}: {e}")
            return False

    def add_issue_label(self, repository: str, issue_number: int, label: str) -> bool:
        """
        Add a label to a GitHub issue

        Args:
            repository: Repository in format "owner/repo"
            issue_number: Issue number
            label: Label name to add

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/repos/{repository}/issues/{issue_number}/labels"

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json={"labels": [label]},
                timeout=30
            )
            response.raise_for_status()
            logger.info(f"Added label '{label}' to issue #{issue_number}")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to add label '{label}' to issue #{issue_number}: {e}")
            return False

    def remove_issue_label(self, repository: str, issue_number: int, label: str) -> bool:
        """
        Remove a label from a GitHub issue

        Args:
            repository: Repository in format "owner/repo"
            issue_number: Issue number
            label: Label name to remove

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/repos/{repository}/issues/{issue_number}/labels/{label}"

        try:
            response = requests.delete(
                url,
                headers=self.headers,
                timeout=30
            )

            # 200, 204, or 404 (already removed) are all acceptable
            if response.status_code in (200, 204, 404):
                logger.info(f"Removed label '{label}' from issue #{issue_number}")
                return True

            response.raise_for_status()
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to remove label '{label}' from issue #{issue_number}: {e}")
            return False

    def create_pull_request(
        self,
        repository: str,
        title: str,
        body: str,
        head: str,
        base: str = "main",
        labels: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Create a pull request

        Args:
            repository: Repository in format "owner/repo"
            title: PR title
            body: PR description (markdown supported)
            head: Head branch name
            base: Base branch name (default: "main")
            labels: Optional list of labels to add

        Returns:
            PR URL if successful, None otherwise
        """
        url = f"{self.base_url}/repos/{repository}/pulls"

        try:
            # Create PR
            response = requests.post(
                url,
                headers=self.headers,
                json={
                    "title": title,
                    "body": body,
                    "head": head,
                    "base": base,
                },
                timeout=30
            )
            response.raise_for_status()

            pr_data = response.json()
            pr_url = pr_data.get("html_url")
            pr_number = pr_data.get("number")

            logger.info(f"Created PR #{pr_number}: {pr_url}")

            # Add labels if provided
            if labels and pr_number:
                labels_url = f"{self.base_url}/repos/{repository}/issues/{pr_number}/labels"
                try:
                    requests.post(
                        labels_url,
                        headers=self.headers,
                        json={"labels": labels},
                        timeout=30
                    )
                    logger.info(f"Added labels {labels} to PR #{pr_number}")
                except requests.RequestException as e:
                    logger.warning(f"Failed to add labels to PR: {e}")

            return pr_url

        except requests.RequestException as e:
            logger.error(f"Failed to create pull request: {e}")
            return None

    def update_issue_labels(
        self,
        repository: str,
        issue_number: int,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None
    ) -> bool:
        """
        Update issue labels (add and/or remove multiple labels)

        Args:
            repository: Repository in format "owner/repo"
            issue_number: Issue number
            add_labels: List of labels to add
            remove_labels: List of labels to remove

        Returns:
            True if all operations successful
        """
        success = True

        # Add labels
        if add_labels:
            for label in add_labels:
                if not self.add_issue_label(repository, issue_number, label):
                    success = False

        # Remove labels
        if remove_labels:
            for label in remove_labels:
                if not self.remove_issue_label(repository, issue_number, label):
                    success = False

        return success
