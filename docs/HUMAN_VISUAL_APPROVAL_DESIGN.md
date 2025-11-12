# Human-in-the-Loop Visual Approval System (v2.4)

## The Problem

Current v2.3 design has critical limitations:

1. **No Human Approval Step**
   - Agents take screenshots but proceed automatically
   - No mechanism to pause and ask user "does this look right?"
   - User only sees results AFTER workflow completes

2. **No Agent Feedback Loop**
   - Agent can't receive human feedback
   - Can't iterate based on user's visual assessment
   - One-shot attempt, no visual refinement

3. **No Sandbox Preview**
   - Agent modifies actual codebase
   - No "preview mode" to show design before committing
   - Can't experiment without affecting main code

4. **Claude Can't Browse**
   - Claude Code can VIEW screenshots (images)
   - But cannot OPEN browser or render HTML live
   - Relies on static screenshots only

## Proposed Solution: Interactive Visual Checkpoints

### Architecture

```
User Story: "Add dark mode"
       ↓
Architect Phase
       ↓
Architect creates implementation
       ↓
Capture screenshot
       ↓
┌─────────────────────────────────────┐
│ VISUAL CHECKPOINT 1                 │
│                                     │
│ Show screenshot to user             │
│ Options:                            │
│   A) Approve - continue to security │
│   R) Revise - provide feedback      │
│   C) Cancel - abort workflow        │
└─────────────────────────────────────┘
       ↓
   If REVISE:
       ↓
   User provides feedback:
   "The button should be on the left, not right"
   "Use darker shade of blue #1a3d5c"
   "Make font 16px not 14px"
       ↓
   Architect re-implements with feedback
       ↓
   New screenshot captured
       ↓
   Show to user again (loop until approved)
       ↓
   If APPROVE:
       ↓
Security Phase
       ↓
   ... (continue workflow)
```

### Implementation Components

#### 1. Visual Checkpoint Manager

```python
# visual_checkpoint.py

from pathlib import Path
from typing import Optional, Dict, Literal
import subprocess
from visual_tester import VisualTester

VisualDecision = Literal["approve", "revise", "cancel"]

class VisualCheckpoint:
    """
    Manages human-in-the-loop visual approval

    Features:
    - Displays screenshot to user
    - Prompts for approval/revision/cancel
    - Collects user feedback for revisions
    - Opens HTML in browser for live preview
    """

    def __init__(self, visual_tester: VisualTester):
        self.visual_tester = visual_tester

    def show_checkpoint(
        self,
        phase_name: str,
        screenshot_path: Path,
        html_file: Optional[Path] = None
    ) -> Dict[str, any]:
        """
        Display visual checkpoint to user and collect decision

        Args:
            phase_name: Name of the phase (e.g., "Architect")
            screenshot_path: Path to screenshot to show
            html_file: Optional path to HTML file for live preview

        Returns:
            Dict with:
            {
                "decision": "approve" | "revise" | "cancel",
                "feedback": str (if revise),
                "live_preview_used": bool
            }
        """
        print("\n" + "="*60)
        print(f"🎨 VISUAL CHECKPOINT: {phase_name} Phase")
        print("="*60)

        # Show screenshot path
        print(f"\n📸 Screenshot: {screenshot_path}")

        # Offer to open in browser if HTML file provided
        if html_file and html_file.exists():
            print(f"\n🌐 HTML File: {html_file}")
            open_browser = self._ask_yes_no(
                "Would you like to open HTML in browser for live preview?"
            )

            if open_browser:
                self._open_in_browser(html_file)

        # Show screenshot (if on macOS, use Quick Look)
        print(f"\n📷 Opening screenshot preview...")
        self._show_screenshot(screenshot_path)

        # Get user decision
        print("\n" + "-"*60)
        print("Please review the visual design and choose:")
        print("  A) APPROVE - Design looks good, continue workflow")
        print("  R) REVISE - Provide feedback for changes")
        print("  C) CANCEL - Abort workflow")
        print("-"*60)

        decision = self._get_user_decision()

        result = {
            "decision": decision,
            "feedback": None,
            "live_preview_used": html_file is not None
        }

        if decision == "revise":
            result["feedback"] = self._collect_revision_feedback()

        return result

    def _open_in_browser(self, html_file: Path):
        """Open HTML file in default browser"""
        import platform

        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(html_file)])
            elif platform.system() == "Windows":
                subprocess.run(["start", str(html_file)], shell=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(html_file)])

            print(f"✅ Opened in browser: {html_file}")

        except Exception as e:
            print(f"⚠️  Could not open browser: {e}")

    def _show_screenshot(self, screenshot_path: Path):
        """Display screenshot using system viewer"""
        import platform

        try:
            if platform.system() == "Darwin":  # macOS - use Quick Look
                subprocess.run(["qlmanage", "-p", str(screenshot_path)],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            else:
                # On other systems, just print the path
                print(f"View screenshot at: {screenshot_path}")

        except Exception:
            print(f"View screenshot at: {screenshot_path}")

    def _ask_yes_no(self, question: str) -> bool:
        """Ask user a yes/no question"""
        while True:
            response = input(f"{question} (y/n): ").strip().lower()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")

    def _get_user_decision(self) -> VisualDecision:
        """Get user's visual approval decision"""
        while True:
            response = input("\nYour decision (A/R/C): ").strip().upper()

            if response == 'A':
                return "approve"
            elif response == 'R':
                return "revise"
            elif response == 'C':
                return "cancel"
            else:
                print("Please enter 'A' (approve), 'R' (revise), or 'C' (cancel)")

    def _collect_revision_feedback(self) -> str:
        """Collect detailed revision feedback from user"""
        print("\n" + "="*60)
        print("📝 REVISION FEEDBACK")
        print("="*60)
        print("Please describe what needs to be changed.")
        print("Be specific about:")
        print("  - Layout/positioning issues")
        print("  - Color corrections")
        print("  - Size/spacing adjustments")
        print("  - Any other visual problems")
        print("\nPress Ctrl+D (Unix) or Ctrl+Z (Windows) when done.")
        print("-"*60)

        # Collect multi-line feedback
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass

        feedback = "\n".join(lines).strip()

        if not feedback:
            print("⚠️  No feedback provided - using generic revision request")
            feedback = "Please review and improve the visual design."

        return feedback


#### 2. Orchestrator Integration

```python
# orchestrator.py updates

class Orchestrator:
    def __init__(self, workspace_dir: Optional[Path] = None):
        # ... existing code ...
        self.visual_checkpoint = None
        self.enable_visual_checkpoints = True  # New config option

    def process_user_story(self, user_story: str) -> WorkflowResult:
        """Process user story with visual checkpoints"""

        is_ui_task = self._is_ui_task(user_story)

        if is_ui_task:
            self.visual_tester = VisualTester(self.workspace, self.workflow_id)

            if self.enable_visual_checkpoints:
                self.visual_checkpoint = VisualCheckpoint(self.visual_tester)

            # Capture baseline
            self.visual_tester.capture_all_phases("baseline")

        # Run Architect
        architect_result = self._run_architect(user_story)

        # VISUAL CHECKPOINT: After Architect
        if is_ui_task and self.visual_checkpoint:
            checkpoint_result = self._visual_checkpoint_after_phase(
                phase_name="Architect",
                html_files=self.visual_tester.detect_ui_files()
            )

            if checkpoint_result["decision"] == "cancel":
                return self._create_cancelled_result("User cancelled during visual review")

            elif checkpoint_result["decision"] == "revise":
                # RE-RUN ARCHITECT with user feedback
                revision_prompt = f"""
                The user reviewed your visual design and requests changes:

                USER FEEDBACK:
                {checkpoint_result["feedback"]}

                Please implement these visual changes while keeping the rest of your implementation.
                """

                architect_result = self._run_architect_revision(revision_prompt)

                # Capture new screenshot and check again
                self.visual_tester.capture_all_phases("architect-revision")

                # Loop until approved (max 3 revisions)
                revision_count = 0
                while revision_count < 3:
                    checkpoint_result = self._visual_checkpoint_after_phase(
                        phase_name=f"Architect (Revision {revision_count + 1})",
                        html_files=self.visual_tester.detect_ui_files()
                    )

                    if checkpoint_result["decision"] == "approve":
                        break
                    elif checkpoint_result["decision"] == "cancel":
                        return self._create_cancelled_result("User cancelled")
                    else:
                        # Another revision
                        revision_count += 1
                        architect_result = self._run_architect_revision(
                            checkpoint_result["feedback"]
                        )

        # Continue with rest of workflow...
        # (Security, Tester, PO phases)

    def _visual_checkpoint_after_phase(
        self,
        phase_name: str,
        html_files: List[Path]
    ) -> Dict:
        """
        Show visual checkpoint to user after a phase

        Returns user's decision (approve/revise/cancel)
        """
        if not html_files:
            print(f"⚠️  No HTML files found, skipping visual checkpoint")
            return {"decision": "approve"}

        # Use first HTML file (or could show all)
        html_file = html_files[0]

        # Get latest screenshot for this phase
        screenshots = self.visual_tester.get_all_screenshots_for_file(html_file)
        if not screenshots:
            print(f"⚠️  No screenshots available, skipping checkpoint")
            return {"decision": "approve"}

        latest_screenshot = Path(screenshots[-1]["path"])

        # Show checkpoint
        return self.visual_checkpoint.show_checkpoint(
            phase_name=phase_name,
            screenshot_path=latest_screenshot,
            html_file=html_file
        )
```

#### 3. Configuration

```python
# config.py

VISUAL_TESTING_CONFIG = {
    "enabled": True,
    "screenshot_on_ui_tasks": True,

    # NEW: Human approval settings
    "require_human_visual_approval": True,  # Pause for user review
    "checkpoint_after_architect": True,     # Always check after architect
    "checkpoint_after_security": False,      # Optional: check after security
    "checkpoint_after_tester": False,        # Optional: check after tester

    "max_visual_revisions": 3,              # Max revision loops per phase
    "auto_open_browser": True,              # Automatically open HTML in browser
    "auto_open_screenshot": True,           # Automatically show screenshot

    # Screenshot settings
    "screenshot_tool": "playwright",
    "comparison_threshold": 0.05,
}
```

### Workflow Example

#### User Experience

```
$ ./run.sh --workspace ~/calculator-app "Add dark mode toggle"

🚀 Starting AI Scrum Master
📁 Working on external project: /Users/simon/calculator-app
🎨 UI task detected - enabling visual testing

============================================================
🤖 Architect Agent Starting
============================================================
⏳ Running Claude Code...
✓ Completed in 45.2 seconds

📸 Capturing screenshot...
✅ Screenshot saved: index_after-architect_20251110_223045.png

============================================================
🎨 VISUAL CHECKPOINT: Architect Phase
============================================================

📸 Screenshot: logs/screenshots/20251110_223045/index_after-architect_20251110_223045.png
🌐 HTML File: ~/calculator-app/index.html

Would you like to open HTML in browser for live preview? (y/n): y
✅ Opened in browser: ~/calculator-app/index.html

📷 Opening screenshot preview...
[Quick Look opens showing screenshot]

------------------------------------------------------------
Please review the visual design and choose:
  A) APPROVE - Design looks good, continue workflow
  R) REVISE - Provide feedback for changes
  C) CANCEL - Abort workflow
------------------------------------------------------------

Your decision (A/R/C): R

============================================================
📝 REVISION FEEDBACK
============================================================
Please describe what needs to be changed.
Be specific about:
  - Layout/positioning issues
  - Color corrections
  - Size/spacing adjustments
  - Any other visual problems

Press Ctrl+D when done.
------------------------------------------------------------
The toggle button should be on the LEFT side of the header, not right.
Also, the dark mode background is too dark - use #2c2c2e instead of #1c1c1e.
^D

✅ Feedback collected. Re-running Architect with revisions...

============================================================
🤖 Architect Agent Starting (Revision 1)
============================================================
Task: Implement user feedback:
- Move toggle button to left side
- Change dark mode background to #2c2c2e
...

✓ Completed in 32.1 seconds

📸 Capturing screenshot...
✅ Screenshot saved: index_architect-revision_20251110_223234.png

============================================================
🎨 VISUAL CHECKPOINT: Architect (Revision 1)
============================================================

[Opens browser and screenshot again]

Your decision (A/R/C): A

✅ Visual design approved! Continuing workflow...

============================================================
🔒 Security Phase Starting
============================================================
...
```

## Benefits

### 1. Human Control

- ✅ User sees design BEFORE committing to workflow
- ✅ Can iterate on visual design interactively
- ✅ Prevents wasted workflow costs on wrong designs

### 2. Live Preview

- ✅ Opens HTML in browser automatically
- ✅ User can interact with UI (buttons, forms, etc.)
- ✅ Test responsive design by resizing browser
- ✅ Better than static screenshots alone

### 3. Iterative Refinement

- ✅ Agent learns from user feedback
- ✅ Can correct colors, layout, spacing immediately
- ✅ Max 3 revisions prevents infinite loops
- ✅ Each revision is faster (focused changes)

### 4. Fail Fast

- ✅ User can cancel workflow early
- ✅ Saves money on workflows going wrong direction
- ✅ No need to complete full workflow just to reject

## Limitations

### What This Doesn't Solve

1. **No True Sandbox**
   - Agent still modifies actual files
   - No "preview branch" separate from main
   - Could add git stash mechanism later

2. **Blocking Workflow**
   - User must be present to approve
   - Can't run overnight without supervision
   - Could add "auto-approve after timeout" option

3. **Single HTML File**
   - Current design shows first HTML file only
   - Multi-file projects need better UI
   - Could add "review all files" mode

### Future Enhancements (v2.5+)

1. **Git-Based Sandbox**
   ```python
   # Create sandbox branch for preview
   git.create_branch("preview/architect")
   architect.work_in_branch("preview/architect")
   # User reviews
   if approved:
       git.merge("preview/architect" -> "architect-branch")
   else:
       git.delete_branch("preview/architect")
   ```

2. **Web-Based Review UI**
   ```
   http://localhost:5000/review/workflow_ID

   Shows:
   - Side-by-side before/after
   - Slider to blend screenshots
   - Embedded live HTML preview
   - Feedback form
   - Approve/Revise/Cancel buttons
   ```

3. **Async Approval**
   ```python
   # Pause workflow and notify user
   send_notification("Visual approval needed")
   wait_for_approval(timeout=3600)  # 1 hour
   if not approved:
       auto_revise_with_ai_suggestions()
   ```

4. **Multi-File Review**
   ```
   Show all modified HTML files
   Allow per-file approve/revise
   Collect feedback for each file separately
   ```

## Configuration Options

### Conservative Mode (Default)

```python
VISUAL_TESTING_CONFIG = {
    "require_human_visual_approval": True,
    "checkpoint_after_architect": True,
    "checkpoint_after_security": False,
    "checkpoint_after_tester": False,
}
```

User reviews once after Architect, then agents continue.

### Paranoid Mode

```python
VISUAL_TESTING_CONFIG = {
    "require_human_visual_approval": True,
    "checkpoint_after_architect": True,
    "checkpoint_after_security": True,
    "checkpoint_after_tester": True,
}
```

User reviews after EVERY phase. Maximum control.

### Automated Mode (v2.3 Behavior)

```python
VISUAL_TESTING_CONFIG = {
    "require_human_visual_approval": False,
    "checkpoint_after_architect": False,
}
```

No human checkpoints. Screenshots captured but workflow continues automatically.

## Implementation Plan

### Phase 1: Basic Checkpoint (v2.4)
- [ ] Create VisualCheckpoint class
- [ ] Integrate into orchestrator after Architect
- [ ] Add browser opening functionality
- [ ] Add screenshot display (macOS Quick Look)
- [ ] Collect user feedback via CLI
- [ ] Re-run Architect with feedback

**Estimated Time:** 4-6 hours

### Phase 2: Multi-Phase Checkpoints (v2.4.1)
- [ ] Add checkpoints after Security/Tester
- [ ] Configurable checkpoint locations
- [ ] Better multi-file handling

**Estimated Time:** 2-3 hours

### Phase 3: Git Sandbox (v2.5)
- [ ] Preview branches for isolation
- [ ] Sandbox merge on approval
- [ ] Branch cleanup on cancel

**Estimated Time:** 6-8 hours

### Phase 4: Web UI (v2.6)
- [ ] Flask/FastAPI web server
- [ ] Visual review interface
- [ ] Side-by-side comparison
- [ ] Async approval notifications

**Estimated Time:** 12-16 hours

---

## Summary

Your question revealed a critical missing piece: **human visual approval**.

The v2.3 design (automated screenshots) catches problems but doesn't let users FIX them interactively.

The v2.4 design (human checkpoints) gives users:
- ✅ Live preview in browser
- ✅ Approve/revise/cancel decisions
- ✅ Iterative refinement with feedback
- ✅ Early cancellation to save costs

This is the missing link between "agent says it's done" and "user verifies it looks right".

**Recommendation:** Implement v2.4 Human Checkpoints as next priority after v2.3.
