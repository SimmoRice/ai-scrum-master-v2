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
        Merge source branch into target branch with automatic cleanup on failure

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into
            message: Optional custom merge message

        Returns:
            True if merge succeeded, False otherwise
        """
        # Track original branch before merge to restore on failure
        original_branch = self.get_current_branch()
        merge_succeeded = False

        try:
            # Checkout target branch
            self.checkout_branch(target_branch)

            # Merge source branch
            merge_msg = message or f"Merge {source_branch} into {target_branch}"

            try:
                self._run_git("merge", source_branch, "-m", merge_msg)
                print(f"✅ Merged '{source_branch}' into '{target_branch}'")
                merge_succeeded = True
                return True

            except subprocess.CalledProcessError as e:
                # Enhanced error messages showing what conflicted
                error_output = e.stderr.strip() if e.stderr else ""

                print(f"❌ Merge failed: {source_branch} → {target_branch}")

                # Check if it's a merge conflict
                if "CONFLICT" in error_output or "conflict" in error_output.lower():
                    print("⚠️  Merge conflicts detected:")
                    # Extract conflict information from git output
                    for line in error_output.split('\n'):
                        if 'CONFLICT' in line or 'conflict' in line.lower():
                            print(f"   {line}")

                    # Show how to fix
                    print("\n💡 How to fix manually:")
                    print(f"   1. git checkout {target_branch}")
                    print(f"   2. git merge {source_branch}")
                    print(f"   3. Resolve conflicts in the listed files")
                    print(f"   4. git add <resolved-files>")
                    print(f"   5. git commit")
                else:
                    # Other merge errors
                    print(f"   Error details: {error_output}")

                return False

        finally:
            # Ensure cleanup happens regardless of success or failure
            # Check if repository is in MERGING state
            merge_head = self.workspace / ".git" / "MERGE_HEAD"
            if merge_head.exists():
                print("🔄 Cleaning up failed merge state...")
                try:
                    # Abort the merge to restore clean state
                    self._run_git("merge", "--abort", check=False)
                    print("✅ Merge aborted, repository restored to clean state")
                except subprocess.CalledProcessError as abort_error:
                    print(f"⚠️  Could not abort merge: {abort_error.stderr}")
                    print("⚠️  Repository may be in MERGING state - manual intervention needed")
                    print(f"   Run: cd {self.workspace} && git merge --abort")

                # Try to return to original branch only if merge failed
                if not merge_succeeded:
                    current = self.get_current_branch()
                    if current != original_branch:
                        try:
                            self.checkout_branch(original_branch)
                            print(f"🔄 Restored to original branch '{original_branch}'")
                        except subprocess.CalledProcessError:
                            # Can't switch back, stay on target branch
                            print(f"⚠️  Could not return to '{original_branch}', staying on '{current}'")

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

    def branch_exists(self, branch_name: str) -> bool:
        """
        Check if a branch exists

        Args:
            branch_name: Name of the branch to check

        Returns:
            True if branch exists, False otherwise
        """
        result = self._run_git("branch", "--list", branch_name, check=False)
        return bool(result.stdout.strip())

    def branch_has_commits(self, branch_name: str, since_branch: str = "main") -> bool:
        """
        Check if a branch has commits beyond the base branch

        Args:
            branch_name: Name of the branch to check
            since_branch: Base branch to compare against (default: main)

        Returns:
            True if branch has commits beyond base, False otherwise
        """
        if not self.branch_exists(branch_name):
            return False

        try:
            result = self._run_git("rev-list", f"{since_branch}..{branch_name}", check=False)
            return bool(result.stdout.strip())
        except Exception as e:
            print(f"⚠️  Error checking branch commits: {e}")
            return False

    def delete_branch(self, branch_name: str, force: bool = False) -> bool:
        """
        Delete a branch

        Args:
            branch_name: Name of the branch to delete
            force: Force delete even if not merged

        Returns:
            True if deleted successfully, False otherwise
        """
        if not self.branch_exists(branch_name):
            return False

        try:
            flag = "-D" if force else "-d"
            self._run_git("branch", flag, branch_name)
            print(f"✅ Deleted branch '{branch_name}'")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to delete branch '{branch_name}': {e.stderr}")
            return False

    def list_files(self, branch_name: Optional[str] = None) -> List[str]:
        """
        List all tracked files in a branch

        Args:
            branch_name: Branch to list files from (default: current branch)

        Returns:
            List of file paths
        """
        try:
            if branch_name:
                result = self._run_git("ls-tree", "-r", "--name-only", branch_name, check=False)
            else:
                result = self._run_git("ls-files", check=False)

            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip().split('\n')
            return []
        except Exception as e:
            print(f"⚠️  Error listing files: {e}")
            return []

    def __repr__(self) -> str:
        current = self.get_current_branch()
        return f"GitManager(workspace='{self.workspace}', current_branch='{current}')"
