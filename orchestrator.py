"""
Orchestrator - Coordinates the AI Scrum Master workflow

Manages the sequential execution of agents:
Architect -> Security -> Tester -> Product Owner
"""
from pathlib import Path
from typing import Dict, Any, Optional
from claude_agent import ClaudeCodeAgent
from git_manager import GitManager
from logger import WorkflowLogger
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
    WORKFLOW_CONFIG
)


class WorkflowResult:
    """Result of a complete workflow execution"""

    def __init__(self):
        self.user_story = ""
        self.architect_result = None
        self.security_result = None
        self.tester_result = None
        self.po_decision = None
        self.revision_count = 0
        self.approved = False
        self.total_cost = 0.0
        self.errors = []

    def add_cost(self, cost: float):
        """Add to total cost"""
        self.total_cost += cost

    def __repr__(self):
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

    def __init__(self, workspace_dir: Optional[Path] = None):
        """
        Initialize the orchestrator

        Args:
            workspace_dir: Optional custom workspace directory
        """
        self.workspace = Path(workspace_dir) if workspace_dir else WORKSPACE_DIR
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Initialize git manager
        self.git = GitManager(self.workspace)

        # Logger will be initialized per workflow
        self.logger = None

        # Initialize workspace
        self._initialize_workspace()

    def _initialize_workspace(self):
        """Set up workspace and git repository"""
        print("\n🚀 Initializing AI Scrum Master Workspace")
        print("="*60)

        # Initialize git repository (creates main branch with initial commit)
        self.git.initialize_repository()

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

            # Product Owner review
            po_decision = self._product_owner_review(user_story, result)

            if po_decision == "APPROVE":
                result.approved = True
                print("\n✅ Product Owner APPROVED the implementation!")
                self.logger.log_decision("APPROVE", result.po_decision)

                # Merge to main if configured
                if WORKFLOW_CONFIG['auto_merge_on_approval']:
                    print("\n🔀 Merging approved work to main branch...")
                    if self.git.merge_workflow_to_main():
                        print("✅ Successfully merged to main!")
                        self.logger.logger.info("✅ Merged to main branch")
                    else:
                        print("⚠️  Merge failed - manual intervention needed")
                        self.logger.log_error("Merge to main failed")

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

        architect = ClaudeCodeAgent("Architect", self.workspace, ARCHITECT_PROMPT)

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

        self.logger.log_agent_start("Architect", arch_task)
        arch_result = architect.execute_task(arch_task)
        self.logger.log_agent_end("Architect", arch_result)
        architect.print_result(arch_result)

        if not arch_result['success']:
            result.errors.append(f"Architect failed: {arch_result.get('error')}")
            self.logger.log_error(f"Architect failed: {arch_result.get('error')}")
            return False

        result.architect_result = arch_result
        result.add_cost(arch_result.get('cost_usd', 0.0))

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

        security = ClaudeCodeAgent("Security", self.workspace, SECURITY_PROMPT)

        sec_task = """Review the implementation created by the Architect.

Identify and fix any security vulnerabilities:
- Input validation
- SQL injection
- XSS prevention
- Authentication/authorization issues
- Sensitive data handling
- Error handling

Edit files directly to add security improvements, then commit your changes."""

        self.logger.log_agent_start("Security", sec_task)
        sec_result = security.execute_task(sec_task)
        self.logger.log_agent_end("Security", sec_result)
        security.print_result(sec_result)

        if not sec_result['success']:
            result.errors.append(f"Security failed: {sec_result.get('error')}")
            self.logger.log_error(f"Security failed: {sec_result.get('error')}")
            return False

        result.security_result = sec_result
        result.add_cost(sec_result.get('cost_usd', 0.0))

        # VALIDATION GATE: Ensure Security completed work
        if not self.git.branch_has_commits(SECURITY_BRANCH, ARCHITECT_BRANCH):
            error_msg = "❌ Cannot proceed: Security hasn't committed any changes"
            print(f"\n{error_msg}")
            result.errors.append(error_msg)
            return False

        # Phase 3: Testing
        print("\n🧪 PHASE 3: TESTER")
        print("="*60)

        # Create tester branch from security (inherits Architect + Security's work)
        self.git.create_branch(TESTER_BRANCH, from_branch=SECURITY_BRANCH)

        tester = ClaudeCodeAgent("Tester", self.workspace, TESTER_PROMPT)

        test_task = """Create comprehensive tests for the implementation.

Write actual, runnable tests covering:
- Happy path functionality
- Edge cases
- Error handling
- Security validations

Then RUN the tests to verify they pass. Commit test files and results."""

        self.logger.log_agent_start("Tester", test_task)
        test_result = tester.execute_task(test_task)
        self.logger.log_agent_end("Tester", test_result)
        tester.print_result(test_result)

        if not test_result['success']:
            result.errors.append(f"Tester failed: {test_result.get('error')}")
            self.logger.log_error(f"Tester failed: {test_result.get('error')}")
            return False

        result.tester_result = test_result
        result.add_cost(test_result.get('cost_usd', 0.0))

        return True

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

        po = ClaudeCodeAgent("ProductOwner", self.workspace, PRODUCT_OWNER_PROMPT)

        review_task = f"""Review the completed implementation against the original user story.

ORIGINAL USER STORY:
{user_story}

Review ALL files in the current directory and make ONE decision:
- APPROVE: Meets requirements, ready to merge
- REVISE: Good but needs improvements (provide specific feedback)
- REJECT: Fundamentally flawed, needs complete redo

Your response MUST start with: DECISION: [APPROVE|REVISE|REJECT]

Provide detailed reasoning and specific feedback if requesting revisions."""

        self.logger.log_agent_start("ProductOwner", review_task)
        po_result = po.execute_task(review_task)
        self.logger.log_agent_end("ProductOwner", po_result)
        po.print_result(po_result)

        result.add_cost(po_result.get('cost_usd', 0.0))

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
