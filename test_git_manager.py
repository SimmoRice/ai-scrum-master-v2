"""
Test suite for git_manager.py

Tests git operations, branch management, and security validations.
Covers happy paths, edge cases, error handling, and security validations.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from git_manager import GitManager


class TestGitManagerInitialization:
    """Test GitManager initialization"""

    def test_init_with_valid_path(self):
        """Test initialization with valid workspace path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "test_workspace"
            git_manager = GitManager(workspace)

            assert git_manager.workspace == workspace.resolve()
            assert git_manager.workspace.exists()

    def test_init_creates_workspace_directory(self):
        """Test that initialization creates workspace directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "new_workspace"
            assert not workspace.exists()

            git_manager = GitManager(workspace)

            assert workspace.exists()
            assert workspace.is_dir()

    def test_init_with_relative_path_converts_to_absolute(self):
        """Test that relative paths are converted to absolute"""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = Path.cwd()
            try:
                # Change to temp directory
                import os
                os.chdir(tmpdir)

                # Create with relative path
                git_manager = GitManager(Path("relative_workspace"))

                # Should be absolute
                assert git_manager.workspace.is_absolute()
            finally:
                # Restore original directory
                import os
                os.chdir(original_dir)


class TestSecurityValidations:
    """Test security validations in GitManager"""

    def test_reject_system_directory_paths(self):
        """Security: Test that system directory paths are rejected"""
        system_dirs = ['/etc/test', '/usr/test', '/bin/test', '/sbin/test', '/var/log/test']

        for sys_dir in system_dirs:
            with pytest.raises(ValueError, match="Security"):
                GitManager(Path(sys_dir))

    def test_reject_path_traversal(self):
        """Security: Test that path traversal attempts to system dirs are rejected"""
        # Try to create workspace in /etc via traversal (will resolve to /private/etc on macOS)
        traversal_path = Path("/tmp/../etc/test_workspace")
        with pytest.raises(ValueError, match="Security"):
            GitManager(traversal_path)

    def test_validate_branch_name_rejects_special_chars(self):
        """Security: Test that branch names with special characters are rejected"""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_manager = GitManager(Path(tmpdir))

            dangerous_names = [
                "branch;rm -rf /",
                "branch&whoami",
                "branch|cat /etc/passwd",
                "branch$HOME",
                "branch`whoami`",
                "branch()",
                "branch<>",
                "branch\ntest",
            ]

            for bad_name in dangerous_names:
                with pytest.raises(ValueError, match="Security"):
                    git_manager._validate_branch_name(bad_name)

    def test_validate_branch_name_accepts_valid_names(self):
        """Test that valid branch names are accepted"""
        with tempfile.TemporaryDirectory() as tmpdir:
            git_manager = GitManager(Path(tmpdir))

            valid_names = [
                "main",
                "feature-branch",
                "feature_branch",
                "feature/branch",
                "v1.0.0",
                "architect-branch",
            ]

            for name in valid_names:
                # Should not raise exception
                git_manager._validate_branch_name(name)

    def test_sanitize_commit_message_removes_null_bytes(self):
        """Security: Test that null bytes are removed from commit messages"""
        from utils import sanitize_commit_message

        message = "Test\0message\0with\0nulls"
        sanitized = sanitize_commit_message(message)

        assert "\0" not in sanitized

    def test_sanitize_commit_message_removes_control_chars(self):
        """Security: Test that control characters are removed"""
        from utils import sanitize_commit_message

        message = "Test\x01\x02\x03message"
        sanitized = sanitize_commit_message(message)

        # Control characters should be removed
        assert "\x01" not in sanitized
        assert "\x02" not in sanitized
        assert "\x03" not in sanitized

    def test_sanitize_commit_message_limits_length(self):
        """Security: Test that commit messages are length-limited"""
        from utils import sanitize_commit_message

        # Create a very long message
        long_message = "A" * 10000
        sanitized = sanitize_commit_message(long_message)

        # Should be truncated
        assert len(sanitized) <= 5100  # 5000 + truncation message


class TestGitRepositoryOperations:
    """Test git repository operations"""

    def test_initialize_repository(self):
        """Test git repository initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)

            # Initialize repository
            git_manager.initialize_repository()

            # Check .git directory exists
            git_dir = workspace / ".git"
            assert git_dir.exists()
            assert git_dir.is_dir()

    def test_initialize_repository_creates_initial_commit(self):
        """Test that initialization creates an initial commit"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)

            git_manager.initialize_repository()

            # Check that there's at least one commit
            result = git_manager._run_git("log", "--oneline", check=False)
            assert result.returncode == 0
            assert len(result.stdout.strip()) > 0

    def test_initialize_repository_idempotent(self):
        """Test that initializing twice doesn't cause errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)

            # Initialize twice
            git_manager.initialize_repository()
            git_manager.initialize_repository()

            # Should still be valid
            git_dir = workspace / ".git"
            assert git_dir.exists()

    def test_get_current_branch(self):
        """Test getting current branch name"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            current_branch = git_manager.get_current_branch()

            assert current_branch == "main"

    def test_branch_exists(self):
        """Test checking if branch exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Main branch should exist
            assert git_manager.branch_exists("main") is True

            # Non-existent branch should not exist
            assert git_manager.branch_exists("nonexistent-branch") is False


class TestBranchOperations:
    """Test branch creation and management"""

    def test_create_branch(self):
        """Test creating a new branch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create new branch
            git_manager.create_branch("test-branch")

            # Branch should exist
            assert git_manager.branch_exists("test-branch") is True

            # Should be on new branch
            assert git_manager.get_current_branch() == "test-branch"

    def test_create_branch_from_another_branch(self):
        """Test creating a branch from a specific base branch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create first branch
            git_manager.create_branch("branch1")

            # Create second branch from main
            git_manager.create_branch("branch2", from_branch="main")

            # Both branches should exist
            assert git_manager.branch_exists("branch1") is True
            assert git_manager.branch_exists("branch2") is True

    def test_create_branch_already_exists(self):
        """Test creating a branch that already exists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create branch
            git_manager.create_branch("test-branch")

            # Try to create again - should not raise error
            git_manager.create_branch("test-branch")

    def test_checkout_branch(self):
        """Test switching branches"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create and checkout branch
            git_manager.create_branch("test-branch")
            git_manager.checkout_branch("main")

            # Should be on main
            assert git_manager.get_current_branch() == "main"

            # Switch back
            git_manager.checkout_branch("test-branch")
            assert git_manager.get_current_branch() == "test-branch"

    def test_delete_branch(self):
        """Test deleting a branch"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create branch
            git_manager.create_branch("test-branch")
            assert git_manager.branch_exists("test-branch") is True

            # Switch to main before deleting
            git_manager.checkout_branch("main")

            # Delete branch
            result = git_manager.delete_branch("test-branch", force=True)
            assert result is True

            # Branch should not exist
            assert git_manager.branch_exists("test-branch") is False

    def test_delete_nonexistent_branch(self):
        """Test deleting a branch that doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Try to delete non-existent branch
            result = git_manager.delete_branch("nonexistent", force=True)
            assert result is False


class TestCommitOperations:
    """Test commit operations"""

    def test_commit_changes(self):
        """Test committing changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create a file
            test_file = workspace / "test.txt"
            test_file.write_text("Test content")

            # Commit changes
            result = git_manager.commit_changes("Test commit")
            assert result is True

            # Check commit exists
            log = git_manager.get_branch_log("main", 5)
            assert len(log) >= 2  # Initial commit + test commit

    def test_commit_no_changes(self):
        """Test committing when there are no changes"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Try to commit without changes
            result = git_manager.commit_changes("Empty commit", allow_empty=False)
            assert result is False

    def test_commit_allow_empty(self):
        """Test committing with allow_empty=True"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Commit empty
            result = git_manager.commit_changes("Empty commit", allow_empty=True)
            assert result is True

    def test_commit_sanitizes_message(self):
        """Test that commit messages are sanitized"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create a file
            test_file = workspace / "test.txt"
            test_file.write_text("Test content")

            # Commit with dangerous characters (should be sanitized)
            dangerous_message = "Test\0message\x01with\x02control\x03chars"
            result = git_manager.commit_changes(dangerous_message)
            assert result is True

            # Commit should exist
            log = git_manager.get_branch_log("main", 1)
            assert len(log) > 0


class TestBranchInformation:
    """Test branch information retrieval"""

    def test_list_files(self):
        """Test listing files in repository"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create and commit files
            (workspace / "file1.txt").write_text("Content 1")
            (workspace / "file2.txt").write_text("Content 2")
            git_manager.commit_changes("Add files")

            # List files
            files = git_manager.list_files()

            # Should include our files (and README.md from init)
            assert "file1.txt" in files
            assert "file2.txt" in files

    def test_list_files_empty_repo(self):
        """Test listing files in repository with no tracked files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # List files - should have at least README.md
            files = git_manager.list_files()
            assert isinstance(files, list)

    def test_get_branch_log(self):
        """Test getting branch commit log"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create some commits
            for i in range(3):
                (workspace / f"file{i}.txt").write_text(f"Content {i}")
                git_manager.commit_changes(f"Commit {i}")

            # Get log
            log = git_manager.get_branch_log("main", 5)

            # Should have at least 3 commits (plus initial)
            assert len(log) >= 3

    def test_branch_has_commits(self):
        """Test checking if branch has commits beyond base"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create new branch
            git_manager.create_branch("feature-branch")

            # No new commits yet
            assert git_manager.branch_has_commits("feature-branch", "main") is False

            # Add commit
            (workspace / "feature.txt").write_text("Feature")
            git_manager.commit_changes("Add feature")

            # Should have commits now
            assert git_manager.branch_has_commits("feature-branch", "main") is True


class TestMergeOperations:
    """Test merge operations"""

    def test_merge_branch_success(self):
        """Test successful branch merge"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create feature branch
            git_manager.create_branch("feature")
            (workspace / "feature.txt").write_text("Feature")
            git_manager.commit_changes("Add feature")

            # Merge to main
            result = git_manager.merge_branch("feature", "main")
            assert result is True

            # Check we're on main
            assert git_manager.get_current_branch() == "main"

            # Check file exists in main
            assert (workspace / "feature.txt").exists()

    def test_merge_branch_no_conflicts(self):
        """Test merging branches with no conflicts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create branch1
            git_manager.create_branch("branch1")
            (workspace / "file1.txt").write_text("Content 1")
            git_manager.commit_changes("Add file1")

            # Create branch2 from main
            git_manager.checkout_branch("main")
            git_manager.create_branch("branch2")
            (workspace / "file2.txt").write_text("Content 2")
            git_manager.commit_changes("Add file2")

            # Merge branch2 to main (no conflict)
            result = git_manager.merge_branch("branch2", "main")
            assert result is True


class TestWorkflowBranches:
    """Test workflow branch setup"""

    def test_setup_workflow_branches(self):
        """Test setting up all workflow branches"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Setup workflow branches
            git_manager.setup_workflow_branches()

            # All branches should exist
            assert git_manager.branch_exists("architect-branch") is True
            assert git_manager.branch_exists("security-branch") is True
            assert git_manager.branch_exists("tester-branch") is True

    def test_reset_workflow_branches(self):
        """Test resetting workflow branches"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Setup workflow branches
            git_manager.setup_workflow_branches()

            # Add commits to architect branch
            git_manager.checkout_branch("architect-branch")
            (workspace / "architect.txt").write_text("Architect work")
            git_manager.commit_changes("Architect commit")

            # Reset workflow branches
            git_manager.reset_workflow_branches()

            # Branches should exist but be clean
            assert git_manager.branch_exists("architect-branch") is True
            assert git_manager.branch_has_commits("architect-branch", "main") is False


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_checkout_nonexistent_branch_raises_error(self):
        """Test that checking out non-existent branch raises error"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Try to checkout non-existent branch
            with pytest.raises(Exception):
                git_manager.checkout_branch("nonexistent-branch")

    def test_workspace_path_with_spaces(self):
        """Test that workspace paths with spaces are handled"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace with spaces"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Should work fine
            assert workspace.exists()
            assert (workspace / ".git").exists()

    def test_long_branch_names(self):
        """Test handling of long branch names"""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "git_workspace"
            git_manager = GitManager(workspace)
            git_manager.initialize_repository()

            # Create branch with long name
            long_name = "feature-" + "a" * 100
            git_manager.create_branch(long_name)

            assert git_manager.branch_exists(long_name) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
