"""
Multi-Repository Manager

Manages multiple GitHub repositories for the orchestrator
"""

import logging
from typing import Dict, List, Optional
from orchestrator_service.github_client import GitHubClient

logger = logging.getLogger(__name__)


class MultiRepoManager:
    """Manages multiple GitHub repositories"""

    def __init__(self, github_token: str, repositories: List[str]):
        """
        Initialize multi-repo manager

        Args:
            github_token: GitHub personal access token
            repositories: List of repositories in format "owner/repo"
        """
        self.github_token = github_token
        self.clients: Dict[str, GitHubClient] = {}

        # Create a GitHub client for each repository
        for repo in repositories:
            repo = repo.strip()
            if repo:
                try:
                    client = GitHubClient(github_token, repo)
                    self.clients[repo] = client
                    logger.info(f"Initialized GitHub client for {repo}")
                except Exception as e:
                    logger.error(f"Failed to initialize client for {repo}: {e}")

        if not self.clients:
            raise ValueError("No valid repositories configured")

        logger.info(f"Multi-repo manager initialized with {len(self.clients)} repositories")

    def get_repositories(self) -> List[str]:
        """Get list of configured repositories"""
        return list(self.clients.keys())

    def get_client(self, repo: str) -> Optional[GitHubClient]:
        """
        Get GitHub client for a specific repository

        Args:
            repo: Repository name in format "owner/repo"

        Returns:
            GitHubClient or None if not found
        """
        return self.clients.get(repo)

    async def fetch_all_issues(
        self,
        labels: Optional[List[str]] = None,
        state: str = "open"
    ) -> List[Dict]:
        """
        Fetch issues from all repositories

        Args:
            labels: Filter by labels
            state: Issue state (open, closed, all)

        Returns:
            List of issues with repository information
        """
        all_issues = []

        for repo, client in self.clients.items():
            try:
                issues = await client.fetch_issues(labels=labels, state=state)

                # Add repository info to each issue
                for issue in issues:
                    issue["repository"] = repo
                    all_issues.append(issue)

                logger.debug(f"Fetched {len(issues)} issues from {repo}")

            except Exception as e:
                logger.error(f"Failed to fetch issues from {repo}: {e}")

        return all_issues

    async def add_issue_comment(self, repo: str, issue_number: int, comment: str) -> bool:
        """
        Add comment to an issue

        Args:
            repo: Repository name
            issue_number: Issue number
            comment: Comment text

        Returns:
            True if successful
        """
        client = self.get_client(repo)
        if not client:
            logger.error(f"No client found for repository {repo}")
            return False

        try:
            await client.add_issue_comment(issue_number, comment)
            return True
        except Exception as e:
            logger.error(f"Failed to add comment to {repo}#{issue_number}: {e}")
            return False

    async def add_issue_label(self, repo: str, issue_number: int, label: str) -> bool:
        """
        Add label to an issue

        Args:
            repo: Repository name
            issue_number: Issue number
            label: Label to add

        Returns:
            True if successful
        """
        client = self.get_client(repo)
        if not client:
            logger.error(f"No client found for repository {repo}")
            return False

        try:
            await client.add_issue_label(issue_number, label)
            return True
        except Exception as e:
            logger.error(f"Failed to add label to {repo}#{issue_number}: {e}")
            return False

    async def remove_issue_label(self, repo: str, issue_number: int, label: str) -> bool:
        """
        Remove label from an issue

        Args:
            repo: Repository name
            issue_number: Issue number
            label: Label to remove

        Returns:
            True if successful
        """
        client = self.get_client(repo)
        if not client:
            logger.error(f"No client found for repository {repo}")
            return False

        try:
            await client.remove_issue_label(issue_number, label)
            return True
        except Exception as e:
            logger.error(f"Failed to remove label from {repo}#{issue_number}: {e}")
            return False
