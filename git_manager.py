"""
GitManager - Handles git operations for the AI Scrum Master workflow

Manages branch creation, switching, merging, and the overall git workflow
for the sequential agent process.
"""
import subprocess
from pathlib import Path
from typing import List, Optional
from config import (
    MAIN_BRANCH,
    ARCHITECT_BRANCH,
    SECURITY_BRANCH,
    TESTER_BRANCH,
    GIT_CONFIG
)


class GitManager:
    """
    Manages git operations for the workspace

    Handles the sequential branch workflow:
    main -> architect-branch -> security-branch -> tester-branch -> main
    """

    def __init__(self, workspace: Path):
        """
        Initialize GitManager

        Args:
            workspace: Path to the git repository workspace
        """
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    def _run_git(self, *args, check=True) -> subprocess.CompletedProcess:
        """
        Run a git command in the workspace

        Args:
            *args: Git command arguments
            check: Whether to raise exception on failure

        Returns:
            CompletedProcess result
        """
        cmd = ["git"] + list(args)
        return subprocess.run(
            cmd,
            cwd=str(self.workspace),
            capture_output=True,
            text=True,
            check=check
        )

    def initialize_repository(self) -> None:
        """
        Initialize a new git repository with proper configuration

        Creates:
        - Git repo
        - Sets user name and email
        - Creates main branch with initial commit
        """
        # Check if already initialized
        git_dir = self.workspace / ".git"
        if git_dir.exists():
            print(f"✅ Git repository already initialized at {self.workspace}")
            return

        print(f"🔧 Initializing git repository at {self.workspace}...")

        # Initialize git repo
        self._run_git("init")

        # Configure user
        self._run_git("config", "user.name", GIT_CONFIG["user_name"])
        self._run_git("config", "user.email", GIT_CONFIG["user_email"])

        # Create initial commit (needed for branches)
        readme = self.workspace / "README.md"
        readme.write_text("# AI Scrum Master Workspace\n\nThis workspace is managed by AI agents.\n")

        self._run_git("add", "README.md")
        self._run_git("commit", "-m", "Initial commit: Workspace initialized")

        print(f"✅ Git repository initialized on branch '{MAIN_BRANCH}'")

    def create_branch(self, branch_name: str, from_branch: Optional[str] = None) -> None:
        """
        Create a new branch

        Args:
            branch_name: Name of the branch to create
            from_branch: Branch to branch from (default: current branch)
        """
        # Checkout source branch if specified
        if from_branch:
            self.checkout_branch(from_branch)

        # Check if branch already exists
        result = self._run_git("branch", "--list", branch_name, check=False)
        if result.stdout.strip():
            print(f"⚠️  Branch '{branch_name}' already exists")
            return

        # Create and checkout new branch
        self._run_git("checkout", "-b", branch_name)
        print(f"✅ Created branch '{branch_name}'")

    def checkout_branch(self, branch_name: str) -> None:
        """
        Switch to a different branch

        Args:
            branch_name: Name of the branch to checkout
        """
        self._run_git("checkout", branch_name)
        print(f"✅ Switched to branch '{branch_name}'")

    def get_current_branch(self) -> str:
        """
        Get the name of the current branch

        Returns:
            Current branch name
        """
        result = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        return result.stdout.strip()

    def commit_changes(self, message: str, allow_empty: bool = False) -> bool:
        """
        Commit all changes in the workspace

        Args:
            message: Commit message
            allow_empty: Allow empty commits

        Returns:
            True if commit succeeded, False if nothing to commit
        """
        # Stage all changes
        self._run_git("add", ".")

        # Check if there are changes to commit
        result = self._run_git("diff", "--cached", "--quiet", check=False)
        has_changes = result.returncode != 0

        if not has_changes and not allow_empty:
            print("ℹ️  No changes to commit")
            return False

        # Commit
        cmd = ["commit", "-m", message]
        if allow_empty:
            cmd.append("--allow-empty")

        self._run_git(*cmd)
        print(f"✅ Committed: {message}")
        return True

    def merge_branch(self, source_branch: str, target_branch: str, message: Optional[str] = None) -> bool:
        """
        Merge source branch into target branch

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            message: Optional custom merge message

        Returns:
            True if merge succeeded, False otherwise
        """
        # Checkout target branch
        self.checkout_branch(target_branch)

        # Merge source branch
        merge_msg = message or f"Merge {source_branch} into {target_branch}"

        try:
            self._run_git("merge", source_branch, "-m", merge_msg)
            print(f"✅ Merged '{source_branch}' into '{target_branch}'")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Merge failed: {e.stderr}")
            return False

    def setup_workflow_branches(self) -> None:
        """
        Set up all branches needed for the workflow

        Creates:
        - architect-branch (from main)
        - security-branch (from architect)
        - tester-branch (from security)
        """
        print("\n🔧 Setting up workflow branches...")

        # Ensure we're on main
        current = self.get_current_branch()
        if current != MAIN_BRANCH:
            self.checkout_branch(MAIN_BRANCH)

        # Create architect branch from main
        self.create_branch(ARCHITECT_BRANCH, from_branch=MAIN_BRANCH)

        # Create security branch from architect
        self.create_branch(SECURITY_BRANCH, from_branch=ARCHITECT_BRANCH)

        # Create tester branch from security
        self.create_branch(TESTER_BRANCH, from_branch=SECURITY_BRANCH)

        # Return to main
        self.checkout_branch(MAIN_BRANCH)

        print("✅ All workflow branches created")

    def reset_workflow_branches(self) -> None:
        """
        Delete and recreate all workflow branches

        Useful for starting fresh on a new task
        """
        print("\n🔄 Resetting workflow branches...")

        # Checkout main
        self.checkout_branch(MAIN_BRANCH)

        # Delete existing branches
        for branch in [TESTER_BRANCH, SECURITY_BRANCH, ARCHITECT_BRANCH]:
            result = self._run_git("branch", "--list", branch, check=False)
            if result.stdout.strip():
                self._run_git("branch", "-D", branch)
                print(f"  Deleted '{branch}'")

        # Recreate branches
        self.setup_workflow_branches()

    def merge_workflow_to_main(self) -> bool:
        """
        Merge the complete workflow back to main

        Performs sequential merges:
        tester -> security -> architect -> main

        Returns:
            True if all merges succeeded
        """
        print("\n🔀 Merging workflow branches to main...")

        # Merge tester into security
        if not self.merge_branch(TESTER_BRANCH, SECURITY_BRANCH):
            return False

        # Merge security into architect
        if not self.merge_branch(SECURITY_BRANCH, ARCHITECT_BRANCH):
            return False

        # Merge architect into main
        if not self.merge_branch(ARCHITECT_BRANCH, MAIN_BRANCH):
            return False

        print("✅ All workflow branches merged to main")
        return True

    def get_branch_log(self, branch: str, max_commits: int = 10) -> List[str]:
        """
        Get commit log for a branch

        Args:
            branch: Branch name
            max_commits: Maximum number of commits to retrieve

        Returns:
            List of commit messages
        """
        result = self._run_git("log", f"-{max_commits}", "--oneline", branch, check=False)
        if result.returncode == 0:
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        return []

    def __repr__(self) -> str:
        current = self.get_current_branch()
        return f"GitManager(workspace='{self.workspace}', current_branch='{current}')"
