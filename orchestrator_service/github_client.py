"""
GitHub API Client for Orchestrator

Handles fetching issues, updating labels, and creating comments
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for GitHub API operations"""

    def __init__(self, token: str, repo: str):
        """
        Initialize GitHub client

        Args:
            token: GitHub personal access token
            repo: Repository in format 'owner/repo'
        """
        self.token = token
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    async def fetch_issues(
        self,
        labels: Optional[List[str]] = None,
        state: str = "open"
    ) -> List[Dict[str, Any]]:
        """
        Fetch issues from GitHub

        Args:
            labels: List of labels to filter by
            state: Issue state ('open', 'closed', 'all')

        Returns:
            List of issue dictionaries
        """
        url = f"{self.base_url}/repos/{self.repo}/issues"
        params = {
            "state": state,
            "per_page": 100,
        }

        if labels:
            params["labels"] = ",".join(labels)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    response.raise_for_status()
                    issues_data = await response.json()

                    # Filter out pull requests (GitHub API returns PRs as issues)
                    issues = [
                        {
                            "number": issue["number"],
                            "title": issue["title"],
                            "body": issue["body"] or "",
                            "labels": [label["name"] for label in issue["labels"]],
                            "state": issue["state"],
                            "created_at": issue["created_at"],
                            "updated_at": issue["updated_at"],
                        }
                        for issue in issues_data
                        if "pull_request" not in issue
                    ]

                    return issues

        except Exception as e:
            logger.error(f"Failed to fetch issues: {e}")
            return []

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Optional[int]:
        """
        Create a new issue

        Args:
            title: Issue title
            body: Issue body (markdown)
            labels: List of labels to add
            assignees: List of usernames to assign

        Returns:
            Issue number if successful, None otherwise
        """
        url = f"{self.base_url}/repos/{self.repo}/issues"

        payload = {
            "title": title,
            "body": body,
        }

        if labels:
            payload["labels"] = labels

        if assignees:
            payload["assignees"] = assignees

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    issue_data = await response.json()
                    issue_number = issue_data["number"]
                    logger.info(f"Created issue #{issue_number}: {title}")
                    return issue_number

        except Exception as e:
            logger.error(f"Failed to create issue '{title}': {e}")
            return None

    async def add_issue_label(self, issue_number: int, label: str) -> bool:
        """
        Add label to issue

        Args:
            issue_number: Issue number
            label: Label to add

        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/labels"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json={"labels": [label]}
                ) as response:
                    response.raise_for_status()
                    return True

        except Exception as e:
            logger.error(f"Failed to add label '{label}' to issue #{issue_number}: {e}")
            return False

    async def remove_issue_label(self, issue_number: int, label: str) -> bool:
        """
        Remove label from issue

        Args:
            issue_number: Issue number
            label: Label to remove

        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/labels/{label}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, headers=self.headers) as response:
                    # 404 means label wasn't there, which is fine
                    if response.status in (200, 204, 404):
                        return True
                    response.raise_for_status()
                    return True

        except Exception as e:
            logger.error(f"Failed to remove label '{label}' from issue #{issue_number}: {e}")
            return False

    async def add_issue_comment(self, issue_number: int, body: str) -> bool:
        """
        Add comment to issue

        Args:
            issue_number: Issue number
            body: Comment body (markdown)

        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}/comments"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=self.headers,
                    json={"body": body}
                ) as response:
                    response.raise_for_status()
                    return True

        except Exception as e:
            logger.error(f"Failed to add comment to issue #{issue_number}: {e}")
            return False

    async def close_issue(self, issue_number: int) -> bool:
        """
        Close an issue

        Args:
            issue_number: Issue number

        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{self.repo}/issues/{issue_number}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    url,
                    headers=self.headers,
                    json={"state": "closed"}
                ) as response:
                    response.raise_for_status()
                    return True

        except Exception as e:
            logger.error(f"Failed to close issue #{issue_number}: {e}")
            return False
