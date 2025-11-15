"""
Orchestrator - Coordinates the AI Scrum Master workflow

Manages the sequential execution of agents:
Architect -> Security -> Tester -> Product Owner
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, List
from claude_agent import ClaudeCodeAgent
from git_manager import GitManager
from logger import WorkflowLogger
from ui_protector import UIProtectionOrchestrator
from agents import (
    ARCHITECT_PROMPT,
    SECURITY_PROMPT,
    TESTER_PROMPT,
    PRODUCT_OWNER_PROMPT
)
from config import (
    WORKSPACE_DIR,
    ARCHITECT_BRANCH,
    SECURITY_BRANCH,
    TESTER_BRANCH,
    MAIN_BRANCH,
    WORKFLOW_CONFIG,
    GITHUB_CONFIG,
    CACHE_CONFIG
)
from github_integration import GitHubIntegration
from cache_manager import WorkflowCache


@dataclass
class AgentResult:
    """Result from a single agent execution"""
    agent: str
    success: bool
    cost_usd: float = 0.0
    duration_ms: int = 0
    num_turns: int = 0
    error: Optional[str] = None


@dataclass
class WorkflowResult:
    """Result of a complete workflow execution"""
    user_story: str = ""
    agents: List[AgentResult] = field(default_factory=list)
    architect_result: Optional[Dict[str, Any]] = None
    security_result: Optional[Dict[str, Any]] = None
    tester_result: Optional[Dict[str, Any]] = None
    po_decision: Optional[str] = None
    po_result: Optional[Dict[str, Any]] = None
    revision_count: int = 0
    approved: bool = False
    total_cost: float = 0.0
    total_duration_ms: int = 0
    errors: List[str] = field(default_factory=list)
    pr_url: Optional[str] = None
    issue_number: Optional[int] = None

    def add_cost(self, cost: float) -> None:
        """Add to total cost"""
        self.total_cost += cost

    def add_duration(self, duration_ms: int) -> None:
        """Add to total duration"""
        self.total_duration_ms += duration_ms

    def __repr__(self) -> str:
        status = "APPROVED" if self.approved else "IN PROGRESS"
        return f"WorkflowResult(status='{status}', cost=${self.total_cost:.4f}, revisions={self.revision_count})"


class Orchestrator:
    """
    Coordinates the multi-agent workflow

    Responsibilities:
    - Initialize workspace and git repository
    - Execute agents in sequence
    - Manage git branches
    - Handle Product Owner decisions
    - Coordinate revisions
    """

    def __init__(self, workspace_dir: Optional[Path] = None, verbose: bool = False, github: Any = None, repository_url: Optional[str] = None):
        """
        Initialize the orchestrator

        Args:
            workspace_dir: Optional custom workspace directory
            verbose: If True, stream Claude Code output in real-time
            github: Optional GitHub integration object (prevents auto-merge when using PR workflow)
            repository_url: Optional GitHub repository URL to clone (e.g., https://github.com/owner/repo.git)
        """
        self.verbose = verbose
        self.github = github  # Store GitHub integration to prevent auto-merge
        self.repository_url = repository_url

        # Determine workspace and git root
        if workspace_dir:
            # External workspace mode - work in the specified directory
            self.workspace = Path(workspace_dir)
            self.workspace.mkdir(parents=True, exist_ok=True)
            # Use the external workspace for git operations
            git_root = self.workspace
            # Agents work in the same directory as git
            self.agent_workspace = self.workspace
            self.is_external_workspace = True
        else:
            # Internal workspace mode - work on AI Scrum Master itself
            self.workspace = WORKSPACE_DIR
            self.workspace.mkdir(parents=True, exist_ok=True)
            # Use project root (parent of workspace) for git operations
            # This prevents creating workspace/.git and uses the main repo
            git_root = WORKSPACE_DIR.parent
            # Agents work in git root (project root) to access all files
            self.agent_workspace = git_root
            self.is_external_workspace = False

        # Initialize git manager with appropriate root
        self.git = GitManager(git_root)

        # Logger will be initialized per workflow
        self.logger = None

        # GitHub integration
        self.github = GitHubIntegration(GITHUB_CONFIG) if GITHUB_CONFIG.get('enabled') else None

        # UI protection integration
        self.ui_protector = UIProtectionOrchestrator(self.workspace)

        # Agent output cache
        cache_enabled = CACHE_CONFIG.get('enabled', True)
        self.cache = WorkflowCache() if cache_enabled else None

        # Initialize workspace (only creates git repo for external workspaces)
        self._initialize_workspace()

    def _initialize_workspace(self):
        """Set up workspace and git repository"""
        print("\n🚀 Initializing AI Scrum Master Workspace")
        print("="*60)

        if self.is_external_workspace:
            # External workspace - clone repository or initialize new one
            if self.repository_url:
                # Clone the GitHub repository
                self.git.clone_repository(self.repository_url)
            else:
                # Initialize a new git repository
                self.git.initialize_repository()
        else:
            # Internal workspace - use existing project git repo
            print(f"✅ Using project git repository at {self.git.workspace}")
            print(f"📁 Agents will work in: {self.agent_workspace}")
            print(f"📂 Workspace directory: {self.workspace} (for organization only)")

        # Note: Workflow branches are created dynamically during workflow execution
        # This ensures each branch builds on the previous agent's actual work

        print("="*60)
        print("✅ Workspace ready!\n")

    def process_user_story(self, user_story: str) -> WorkflowResult:
        """
        Execute the complete workflow for a user story

        Args:
            user_story: The user story/requirement to implement

        Returns:
            WorkflowResult with execution details
        """
        # Initialize logger for this workflow
        self.logger = WorkflowLogger()
        self.logger.log_user_story(user_story)

        print("\n" + "="*60)
        print("📋 STARTING NEW USER STORY")
        print("="*60)
        print(f"Story: {user_story[:100]}{'...' if len(user_story) > 100 else ''}")
        print(f"\n🔄 Workflow: Architect → Security → Tester → Product Owner")
        print(f"⏱️  Expected time: 2-5 minutes")
        print(f"💰 Expected cost: $0.06-0.15")
        print(f"📝 Logs: logs/workflow_{self.logger.workflow_id}.log")
        print("="*60 + "\n")

        result = WorkflowResult()
        result.user_story = user_story

        # Clean up old workflow branches ONLY on first iteration (not on revisions)
        # This ensures each NEW task starts fresh from main
        self._cleanup_workflow_branches()

        # Execute workflow with revision loop
        max_revisions = WORKFLOW_CONFIG['max_revisions']

        for revision in range(max_revisions + 1):
            if revision > 0:
                print(f"\n🔄 REVISION #{revision}")
                print("="*60 + "\n")
                result.revision_count = revision

                # Log revision
                self.logger.log_revision(revision, result.po_decision or "PO requested changes")

                # On revision, only clean up downstream branches (security, tester)
                # Keep architect-branch so the Architect can iterate on existing code
                self._cleanup_downstream_branches()

            # Execute sequential agents (branches created dynamically during execution)
            success = self._execute_workflow_sequence(user_story, result, is_revision=revision > 0)

            if not success:
                print("\n❌ Workflow failed during execution")
                self.logger.log_workflow_complete("failed")
                return result

            # UI Protection Check (before Product Owner review)
            if not self._verify_ui_protection():
                print("\n❌ UI Protection Violation Detected")
                print("   Agents modified protected Figma-designed UI")
                print("   Please revert UI changes or update design in Figma")
                result.errors.append("UI protection violated - protected files were modified")
                result.approved = False
                self.logger.log_workflow_complete("ui_protection_violated")
                return result

            # Product Owner review
            po_decision = self._product_owner_review(user_story, result)

            if po_decision == "APPROVE":
                result.approved = True
                print("\n" + "="*60)
                print("🎉 PRODUCT OWNER APPROVED!")
                print("="*60)
                self.logger.log_decision("APPROVE", result.po_decision)

                # Create GitHub PR if enabled
                if self.github and GITHUB_CONFIG.get('auto_create_pr'):
                    print("\n📝 Creating GitHub Pull Request...")
                    try:
                        result.pr_url = self.github.create_pr(
                            workflow_result=result,
                            issue_number=result.issue_number
                        )
                        if result.pr_url:
                            print(f"✅ PR created successfully!")
                            print(f"   URL: {result.pr_url}")
                            print(f"\n⚠️  NEXT STEP: Review the PR and merge manually when ready")
                            self.logger.logger.info(f"✅ PR created: {result.pr_url}")
                    except Exception as e:
                        print(f"⚠️  PR creation failed: {e}")
                        print(f"   Continuing without PR...")
                        self.logger.log_error(f"PR creation failed: {e}")

                # Merge to main if configured (deprecated in v2.2, use PR workflow instead)
                # Only merge if we're NOT using GitHub integration (which requires PR workflow)
                github_integration = hasattr(self, 'github') and self.github is not None

                # DEBUG: Log the condition values
                print(f"\n🔍 DEBUG - Auto-merge check:")
                print(f"   auto_merge_on_approval: {WORKFLOW_CONFIG['auto_merge_on_approval']}")
                print(f"   result.pr_url: {result.pr_url}")
                print(f"   hasattr(self, 'github'): {hasattr(self, 'github')}")
                print(f"   self.github is not None: {self.github is not None if hasattr(self, 'github') else 'N/A'}")
                print(f"   github_integration: {github_integration}")
                print(f"   Should auto-merge? {WORKFLOW_CONFIG['auto_merge_on_approval'] and not result.pr_url and not github_integration}")

                if WORKFLOW_CONFIG['auto_merge_on_approval'] and not result.pr_url and not github_integration:
                    print("\n🔀 Merging approved work to main branch...")
                    if self.git.merge_workflow_to_main():
                        print("✅ Successfully merged to main!")
                        self.logger.logger.info("✅ Merged to main branch")
                    else:
                        print("⚠️  Merge failed - manual intervention needed")
                        self.logger.log_error("Merge to main failed")
                else:
                    print("\n⏭️  Skipping auto-merge (using PR workflow instead)")

                self.logger.log_workflow_complete("approved")
                return result

            elif po_decision == "REJECT":
                print("\n❌ Product Owner REJECTED the implementation")
                self.logger.log_decision("REJECT", result.po_decision)
                result.errors.append(f"Rejected after {revision} revision(s)")
                self.logger.log_workflow_complete("rejected")
                return result

            elif po_decision == "REVISE":
                self.logger.log_decision("REVISE", result.po_decision)
                if revision < max_revisions:
                    print(f"\n🔄 Product Owner requested REVISIONS ({revision + 1}/{max_revisions})")
                    # Continue to next iteration
                    continue
                else:
                    print(f"\n⚠️  Maximum revisions ({max_revisions}) reached")
                    result.errors.append(f"Max revisions reached without approval")
                    self.logger.log_workflow_complete("max_revisions_reached")
                    return result

        self.logger.log_workflow_complete("completed")
        return result

    def _execute_agent_with_retry(
        self,
        agent: ClaudeCodeAgent,
        task: str,
        agent_name: str,
        branch_name: str,
        base_branch: str = None
    ) -> Dict[str, Any]:
        """
        Execute an agent with retry logic on transient failures

        Args:
            agent: The agent to execute
            task: The task description
            agent_name: Name of the agent for logging
            branch_name: Git branch for this agent
            base_branch: Base branch to reset from on retry (optional)

        Returns:
            Agent execution result dict
        """
        import time

        max_retries = WORKFLOW_CONFIG.get('max_agent_retries', 2)
        backoff = WORKFLOW_CONFIG.get('retry_backoff_seconds', 5)

        for attempt in range(max_retries + 1):
            if attempt > 0:
                wait_time = backoff * (2 ** (attempt - 1))  # Exponential backoff
                print(f"\n⚠️  Retry attempt {attempt}/{max_retries} for {agent_name} after {wait_time}s...")
                time.sleep(wait_time)

                # Reset branch to clean state for retry
                if base_branch and self.git.branch_exists(branch_name):
                    print(f"🔄 Resetting '{branch_name}' to clean state...")
                    # Checkout base branch before deleting target branch
                    self.git.checkout_branch(base_branch)
                    self.git.delete_branch(branch_name, force=True)
                    self.git.create_branch(branch_name, from_branch=base_branch)

            # Ensure we're on the correct branch before executing agent
            current_branch = self.git.get_current_branch()
            if current_branch != branch_name:
                print(f"🔄 Switching to branch '{branch_name}' for {agent_name}")
                self.git.checkout_branch(branch_name)

            # Execute agent
            self.logger.log_agent_start(agent_name, task)
            agent_result = agent.execute_task(task)
            self.logger.log_agent_end(agent_name, agent_result)
            agent.print_result(agent_result)

            # Check if we should retry
            if agent_result['success']:
                return agent_result

            # Check if this is a retryable error
            error = agent_result.get('error', '')
            if 'Claude Code exited with code 1' in error or 'timeout' in error.lower():
                # Transient error - can retry
                self.logger.log_error(f"{agent_name} failed (attempt {attempt + 1}): {error}")
                if attempt < max_retries:
                    continue
            else:
                # Non-retryable error (validation failure, etc.) - don't retry
                self.logger.log_error(f"{agent_name} failed with non-retryable error: {error}")
                return agent_result

        # All retries exhausted
        return agent_result

    def _execute_workflow_sequence(
        self,
        user_story: str,
        result: WorkflowResult,
        is_revision: bool = False
    ) -> bool:
        """
        Execute the Architect -> Security -> Tester sequence

        Args:
            user_story: The user story being implemented
            result: WorkflowResult to update
            is_revision: Whether this is a revision iteration

        Returns:
            True if all agents succeeded
        """
        # Phase 1: Architect Implementation
        print("\n🏗️  PHASE 1: ARCHITECT")
        print("="*60)

        # On revision, preserve existing architect-branch with code
        # On first iteration, create fresh architect-branch from main
        if is_revision:
            # CRITICAL: Use existing architect-branch so Architect can iterate
            if self.git.branch_exists(ARCHITECT_BRANCH):
                self.git.checkout_branch(ARCHITECT_BRANCH)
                print(f"✅ Using existing '{ARCHITECT_BRANCH}' for revision")
            else:
                # Fallback: create from main if somehow missing
                print(f"⚠️  Architect branch missing, creating from main")
                self.git.checkout_branch(MAIN_BRANCH)
                self.git.create_branch(ARCHITECT_BRANCH, from_branch=MAIN_BRANCH)
        else:
            # First iteration: create fresh from main
            self.git.checkout_branch(MAIN_BRANCH)
            self.git.create_branch(ARCHITECT_BRANCH, from_branch=MAIN_BRANCH)

        architect = ClaudeCodeAgent("Architect", self.agent_workspace, ARCHITECT_PROMPT, verbose=self.verbose)

        arch_task = user_story
        if is_revision and result.po_decision:
            # Get list of files for context
            files = self.git.list_files()
            files_context = f"\n\nExisting files in your implementation:\n" + "\n".join(f"- {f}" for f in files[:20])
            if len(files) > 20:
                files_context += f"\n... and {len(files) - 20} more files"

            arch_task = f"""REVISION REQUEST - IMPROVE YOUR EXISTING CODE

Original User Story:
{user_story}

Product Owner Feedback:
{result.po_decision}

IMPORTANT: You have already implemented code for this story. The files are still in your working directory.
Review your existing implementation, understand the Product Owner's feedback, and IMPROVE it.
Do NOT start from scratch - build upon what you already created.
{files_context}

Please address the feedback and improve your implementation."""

        # Execute with retry logic
        arch_result = self._execute_agent_with_retry(
            agent=architect,
            task=arch_task,
            agent_name="Architect",
            branch_name=ARCHITECT_BRANCH,
            base_branch=MAIN_BRANCH if not is_revision else None  # Only reset on first iteration
        )

        if not arch_result['success']:
            result.errors.append(f"Architect failed: {arch_result.get('error')}")
            return False

        result.architect_result = arch_result
        result.add_cost(arch_result.get('cost_usd', 0.0))
        result.add_duration(arch_result.get('duration_ms', 0))
        result.agents.append(arch_result)  # Track for PR body

        # VALIDATION GATE: Ensure Architect completed work
        if not self.git.branch_has_commits(ARCHITECT_BRANCH, MAIN_BRANCH):
            error_msg = "❌ Cannot proceed: Architect hasn't committed any code"
            print(f"\n{error_msg}")
            result.errors.append(error_msg)
            return False

        # Phase 2: Security Review
        print("\n🔒 PHASE 2: SECURITY")
        print("="*60)

        # Create security branch from architect (inherits Architect's work)
        self.git.create_branch(SECURITY_BRANCH, from_branch=ARCHITECT_BRANCH)

        security = ClaudeCodeAgent("Security", self.agent_workspace, SECURITY_PROMPT, verbose=self.verbose)

        sec_task = f"""ORIGINAL USER STORY:
{user_story}

---

Review the implementation created by the Architect.

Identify and fix any security vulnerabilities:
- Input validation
- SQL injection
- XSS prevention
- Authentication/authorization issues
- Sensitive data handling
- Error handling

If this is an analysis-only task (see system prompt), create a security analysis document.
Otherwise, edit files directly to add security improvements, then commit your changes."""

        # Execute with retry logic
        sec_result = self._execute_agent_with_retry(
            agent=security,
            task=sec_task,
            agent_name="Security",
            branch_name=SECURITY_BRANCH,
            base_branch=ARCHITECT_BRANCH
        )

        if not sec_result['success']:
            result.errors.append(f"Security failed: {sec_result.get('error')}")
            return False

        result.security_result = sec_result
        result.add_cost(sec_result.get('cost_usd', 0.0))
        result.add_duration(sec_result.get('duration_ms', 0))
        result.agents.append(sec_result)  # Track for PR body

        # VALIDATION GATE: Ensure Security completed work
        # Allow proceeding if Security explicitly approved without finding issues
        if not self.git.branch_has_commits(SECURITY_BRANCH, ARCHITECT_BRANCH):
            # Check if Security explicitly approved the implementation
            if self._agent_approved_without_changes(sec_result):
                print("\n✅ Security approved implementation (no security issues found)")
            else:
                error_msg = "❌ Cannot proceed: Security hasn't committed any changes"
                print(f"\n{error_msg}")
                result.errors.append(error_msg)
                return False

        # Phase 3: Testing
        print("\n🧪 PHASE 3: TESTER")
        print("="*60)

        # Create tester branch from security (inherits Architect + Security's work)
        self.git.create_branch(TESTER_BRANCH, from_branch=SECURITY_BRANCH)

        tester = ClaudeCodeAgent("Tester", self.agent_workspace, TESTER_PROMPT, verbose=self.verbose)

        test_task = f"""ORIGINAL USER STORY:
{user_story}

---

Create comprehensive tests for the implementation.

Write actual, runnable tests covering:
- Happy path functionality
- Edge cases
- Error handling
- Security validations

If this is an analysis-only task (see system prompt), create a test plan document.
Otherwise, create and RUN actual tests to verify they pass. Commit test files and results."""

        # Execute with retry logic
        test_result = self._execute_agent_with_retry(
            agent=tester,
            task=test_task,
            agent_name="Tester",
            branch_name=TESTER_BRANCH,
            base_branch=SECURITY_BRANCH
        )

        if not test_result['success']:
            result.errors.append(f"Tester failed: {test_result.get('error')}")
            return False

        result.tester_result = test_result
        result.add_cost(test_result.get('cost_usd', 0.0))
        result.add_duration(test_result.get('duration_ms', 0))
        result.agents.append(test_result)  # Track for PR body

        return True

    def _agent_approved_without_changes(self, agent_result: Dict[str, Any]) -> bool:
        """
        Check if an agent (Security or Tester) explicitly approved without finding issues

        This allows workflows to proceed when agents determine no changes are needed.

        Args:
            agent_result: Result dictionary from agent execution

        Returns:
            True if agent explicitly approved without issues, False otherwise
        """
        if not agent_result.get('success'):
            return False

        response = agent_result.get('result', '').lower()

        # Keywords that indicate explicit approval without changes needed
        approval_indicators = [
            'approve',
            'approved',
            'no changes needed',
            'no changes required',
            'no security issues',
            'no vulnerabilities',
            'no issues found',
            'already secure',
            'excellent security',
            'passes security review',
            'security review passed',
            'no security improvements needed',
            'implementation is secure',
        ]

        # Check if response contains approval indicators
        return any(indicator in response for indicator in approval_indicators)

    def _check_workspace_cleanliness(self) -> tuple[bool, list[str]]:
        """
        Check for common test artifacts and temporary files

        Returns:
            (is_clean, list_of_issues)
        """
        issues = []
        files = self.git.list_files()

        # Common test/temp file patterns
        suspicious_patterns = [
            ('test.html', 'Test HTML file'),
            ('temp.', 'Temporary file'),
            ('debug.', 'Debug file'),
            ('old_', 'Old version file'),
            ('.tmp', 'Temporary file'),
            ('scratch', 'Scratch file'),
            ('hello', 'Test/demo file (like hello.html, hello.txt)'),
        ]

        for file in files:
            file_lower = file.lower()
            for pattern, description in suspicious_patterns:
                if pattern in file_lower and not file.startswith('.'):  # Ignore dotfiles
                    issues.append(f"  - {file} (suspicious: {description})")

        return (len(issues) == 0, issues)

    def _product_owner_review(self, user_story: str, result: WorkflowResult) -> str:
        """
        Product Owner reviews the completed work

        Args:
            user_story: Original user story
            result: Current workflow result

        Returns:
            Decision: "APPROVE", "REVISE", or "REJECT"
        """
        print("\n👔 PHASE 4: PRODUCT OWNER REVIEW")
        print("="*60)

        # Stay on tester branch for review
        self.git.checkout_branch(TESTER_BRANCH)

        # Check for suspicious files before PO review
        is_clean, issues = self._check_workspace_cleanliness()
        if not is_clean:
            print("\n⚠️  WARNING: Suspicious files detected in workspace:")
            for issue in issues:
                print(issue)
            print("These may be test artifacts that should be removed.\n")

        po = ClaudeCodeAgent("ProductOwner", self.agent_workspace, PRODUCT_OWNER_PROMPT, verbose=self.verbose)

        # Get list of tracked files (excludes node_modules, .git, etc.)
        files = self.git.list_files()

        # Safety check: If no files exist, reject immediately
        if not files:
            print("❌ No files to review - workflow failed to create any code")
            result.errors.append("No files created by workflow")
            return "REJECT"

        files_list = "\n".join(f"- {f}" for f in files)

        review_task = f"""Review the completed implementation against the original user story.

ORIGINAL USER STORY:
{user_story}

FILES TO REVIEW:
{files_list}

Review the files listed above and make ONE decision:
- APPROVE: Meets requirements, ready to merge
- REVISE: Good but needs improvements (provide specific feedback)
- REJECT: Fundamentally flawed, needs complete redo

Your response MUST start with: DECISION: [APPROVE|REVISE|REJECT]

Provide detailed reasoning and specific feedback if requesting revisions."""

        # Execute with retry logic (no base branch for PO - doesn't modify code)
        po_result = self._execute_agent_with_retry(
            agent=po,
            task=review_task,
            agent_name="ProductOwner",
            branch_name=TESTER_BRANCH,
            base_branch=None  # PO doesn't modify code, no need to reset
        )

        result.po_result = po_result
        result.add_cost(po_result.get('cost_usd', 0.0))
        result.add_duration(po_result.get('duration_ms', 0))
        result.agents.append(po_result)  # Track for PR body

        # Parse decision from response
        if po_result['success']:
            response = po_result['result'].upper()

            if "DECISION: APPROVE" in response or "DECISION:APPROVE" in response:
                result.po_decision = po_result['result']
                return "APPROVE"
            elif "DECISION: REVISE" in response or "DECISION:REVISE" in response:
                result.po_decision = po_result['result']
                return "REVISE"
            elif "DECISION: REJECT" in response or "DECISION:REJECT" in response:
                result.po_decision = po_result['result']
                return "REJECT"
            else:
                print("⚠️  Could not parse PO decision, defaulting to REVISE")
                result.po_decision = po_result['result']
                return "REVISE"
        else:
            print("❌ Product Owner review failed")
            result.errors.append("PO review failed")
            return "REJECT"

    def _cleanup_workflow_branches(self) -> None:
        """
        Clean up old workflow branches before starting new task

        Deletes architect, security, and tester branches if they exist.
        This ensures each workflow starts fresh from main.
        """
        print("\n🧹 Cleaning up old workflow branches...")

        # Ensure repository has at least one commit before branch operations
        self.git.ensure_initial_commit()

        # Ensure we're on main before deleting branches
        self.git.checkout_branch(MAIN_BRANCH)

        # Delete branches in reverse order (tester -> security -> architect)
        for branch in [TESTER_BRANCH, SECURITY_BRANCH, ARCHITECT_BRANCH]:
            if self.git.branch_exists(branch):
                self.git.delete_branch(branch, force=True)

        print("✅ Cleanup complete\n")

    def _cleanup_downstream_branches(self) -> None:
        """
        Clean up downstream branches for a revision iteration

        ONLY deletes security-branch and tester-branch.
        Preserves architect-branch so Architect can iterate on existing code.

        This is called during revisions to allow Security and Tester to
        regenerate their work from the revised Architect implementation.
        """
        print("\n🧹 Cleaning downstream branches for revision...")

        # Ensure we're on main before deleting branches
        self.git.checkout_branch(MAIN_BRANCH)

        # Only delete security and tester - keep architect!
        for branch in [TESTER_BRANCH, SECURITY_BRANCH]:
            if self.git.branch_exists(branch):
                self.git.delete_branch(branch, force=True)

        print("✅ Downstream branches cleared (architect-branch preserved)\n")

    def _verify_ui_protection(self) -> bool:
        """
        Verify that no protected UI files were modified by agents

        Returns:
            True if all protected files are unchanged, False otherwise
        """
        # Check if there are any protected files
        protected_files = self.ui_protector.protector.list_protected_files()

        if not protected_files:
            # No protected files - skip verification
            return True

        print("\n🔒 Verifying UI Protection...")
        return self.ui_protector.verify_before_commit()

    def get_workspace_status(self) -> Dict[str, Any]:
        """
        Get current workspace status

        Returns:
            Dictionary with workspace information
        """
        return {
            'workspace': str(self.workspace),
            'current_branch': self.git.get_current_branch(),
            'main_commits': self.git.get_branch_log(MAIN_BRANCH, 5),
            'architect_commits': self.git.get_branch_log(ARCHITECT_BRANCH, 5),
            'security_commits': self.git.get_branch_log(SECURITY_BRANCH, 5),
            'tester_commits': self.git.get_branch_log(TESTER_BRANCH, 5),
        }

    def __repr__(self):
        return f"Orchestrator(workspace='{self.workspace}')"
