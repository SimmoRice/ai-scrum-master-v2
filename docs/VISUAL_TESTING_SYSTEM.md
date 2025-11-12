# Visual Testing System for AI Scrum Master v2.3

## Problem Statement

**Critical Bug Identified:** Agents claim UI fixes are complete but don't verify visual correctness.

### Real-World Example (Calculator App)

**Workflow 1 - Initial Build:** ✅ Success
- Created calculator with proper layout
- All buttons displayed correctly
- Cost: $1.20, Time: 9m 27s

**Workflow 2 - Add Dark Mode:** ⚠️ Broke UI
- Added theme toggle successfully
- **But broke button grid layout** (equals button positioning)
- Agents didn't notice the visual breakage
- Cost: $1.90, Time: 12m 8s

**Workflow 3 - Fix Layout:** ❌ Failed
- Architect claimed: "successfully fixed the layout"
- Security approved: "implementation looks excellent"
- Product Owner approved: "successfully fixes the layout"
- **Reality: Made ZERO actual changes to button order**
- Only added a useless HTML comment
- Cost: $1.94 wasted on fake fix

### Root Causes

1. **No Visual Verification**
   - Agents test code structure but never render the UI
   - Tests pass but UI is broken
   - 165 tests passing ≠ working visual layout

2. **False Reporting**
   - Architect says "fixed" without making changes
   - Product Owner approves without visual inspection
   - Tester validates DOM structure, not visual rendering

3. **No Screenshot Comparison**
   - No before/after visual comparison
   - No regression detection
   - No pixel-level validation

## Proposed Solution: Multi-Layer Visual Testing

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  User Story Input                    │
│              (with UI requirements)                  │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            1. Pre-Flight Screenshot                  │
│   Capture baseline before any changes               │
│   (if HTML/CSS files exist in project)              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            2. Architect Phase                        │
│   - Build feature                                    │
│   - **NEW: Visual verification required**           │
│   - Take screenshot of implementation                │
│   - Claude Code can view images natively             │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            3. Security Phase                         │
│   - Review code                                      │
│   - **NEW: Check for UI regressions**               │
│   - Screenshot comparison if visual changes made    │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            4. Tester Phase                           │
│   - Write tests                                      │
│   - **NEW: Visual regression tests**                │
│   - Screenshot tests for UI components              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            5. Product Owner Phase                    │
│   - **NEW: Mandatory visual review**                │
│   - View before/after screenshots                   │
│   - Explicit UI approval checklist                  │
│   - Human review prompt for UI changes              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            6. Final Screenshot                       │
│   Capture final state for documentation             │
│   Store in logs/screenshots/workflow_ID/            │
└─────────────────────────────────────────────────────┘
```

## Implementation Components

### 1. Screenshot Utility (`visual_tester.py`)

```python
"""
Visual testing utility for AI Scrum Master

Uses playwright to capture screenshots and detect visual regressions
"""

from pathlib import Path
from typing import Optional, Dict, List
import subprocess
import json
from datetime import datetime


class VisualTester:
    """Visual regression testing for web UIs"""

    def __init__(self, workspace_dir: Path, workflow_id: str):
        self.workspace = workspace_dir
        self.workflow_id = workflow_id
        self.screenshot_dir = Path("logs/screenshots") / workflow_id
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    def detect_ui_files(self) -> List[Path]:
        """
        Detect HTML files in workspace that need visual testing

        Returns:
            List of HTML file paths
        """
        html_files = []

        # Look for HTML files
        for pattern in ["*.html", "**/*.html"]:
            html_files.extend(self.workspace.glob(pattern))

        return html_files

    def capture_screenshot(
        self,
        html_file: Path,
        label: str,
        viewport_width: int = 1280,
        viewport_height: int = 720
    ) -> Optional[Path]:
        """
        Capture screenshot of HTML file using playwright

        Args:
            html_file: Path to HTML file
            label: Label for this screenshot (e.g., "baseline", "after-architect")
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height

        Returns:
            Path to screenshot file, or None if failed
        """
        # Generate screenshot filename
        screenshot_name = f"{html_file.stem}_{label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        screenshot_path = self.screenshot_dir / screenshot_name

        # Use playwright via npx (no installation needed if node_modules exists)
        # Alternative: Use browser's built-in screenshot via AppleScript on macOS

        try:
            # Try playwright first
            result = subprocess.run([
                "npx", "-y", "playwright", "screenshot",
                f"file://{html_file.absolute()}",
                str(screenshot_path),
                f"--viewport-size={viewport_width},{viewport_height}",
                "--full-page"
            ], capture_output=True, timeout=30)

            if result.returncode == 0 and screenshot_path.exists():
                print(f"📸 Screenshot captured: {screenshot_path}")
                return screenshot_path

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: Use browser automation via osascript (macOS)
        # This is more reliable but macOS-only
        if self._is_macos():
            return self._capture_via_safari(html_file, screenshot_path)

        print(f"⚠️  Could not capture screenshot for {html_file}")
        return None

    def _is_macos(self) -> bool:
        """Check if running on macOS"""
        import platform
        return platform.system() == "Darwin"

    def _capture_via_safari(self, html_file: Path, output_path: Path) -> Optional[Path]:
        """
        Capture screenshot using Safari (macOS only)

        This is a fallback method that doesn't require playwright
        """
        applescript = f'''
        tell application "Safari"
            activate
            make new document
            set URL of front document to "file://{html_file.absolute()}"
            delay 2
            do JavaScript "document.documentElement.scrollHeight" in front document
        end tell

        do shell script "screencapture -x -R 100,100,800,600 {output_path}"

        tell application "Safari"
            close front document
        end tell
        '''

        try:
            subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                timeout=10
            )

            if output_path.exists():
                return output_path
        except Exception:
            pass

        return None

    def compare_screenshots(
        self,
        baseline: Path,
        current: Path,
        threshold: float = 0.1
    ) -> Dict:
        """
        Compare two screenshots and detect differences

        Args:
            baseline: Path to baseline screenshot
            current: Path to current screenshot
            threshold: Acceptable difference percentage (0.0-1.0)

        Returns:
            Dict with comparison results
        """
        # Use pixelmatch or similar library
        # For now, return a simple structure

        result = {
            "baseline": str(baseline),
            "current": str(current),
            "difference_percent": 0.0,
            "passed": True,
            "diff_image": None
        }

        # TODO: Implement actual image comparison
        # Options:
        # 1. pixelmatch (requires node)
        # 2. PIL + ImageChops (Python)
        # 3. OpenCV (Python)

        return result

    def generate_visual_report(self, screenshots: List[Dict]) -> str:
        """
        Generate markdown report of visual testing results

        Args:
            screenshots: List of screenshot metadata

        Returns:
            Markdown report content
        """
        report = "# Visual Testing Report\n\n"
        report += f"**Workflow ID:** {self.workflow_id}\n\n"
        report += f"**Screenshots Captured:** {len(screenshots)}\n\n"

        report += "## Screenshots\n\n"
        for shot in screenshots:
            report += f"### {shot['label']}\n"
            report += f"![{shot['label']}]({shot['path']})\n\n"

        return report
```

### 2. Agent Prompt Updates

#### Architect Agent Prompt Addition

```python
# In prompts/architect_prompt.py

UI_VERIFICATION_SECTION = """
## 🎨 VISUAL VERIFICATION (CRITICAL FOR UI CHANGES)

If your implementation includes UI changes (HTML, CSS, or visual components):

1. **MANDATORY: View your work**
   - Open the HTML file in a browser OR
   - Use the Read tool to view the file as an image
   - Verify the visual layout matches requirements

2. **Take a screenshot**
   - Use: screenshot <filename.html>
   - The screenshot will be reviewed by Product Owner

3. **Visual checklist**
   - [ ] Layout matches user story description
   - [ ] No broken/overlapping elements
   - [ ] Responsive design works
   - [ ] Colors/styling are correct
   - [ ] All interactive elements visible

4. **Report visual status**
   In your final summary, include:
   - "Visual verification: COMPLETED" or "NOT APPLICABLE"
   - Brief description of what you visually confirmed
   - Screenshot filename if UI changes made

⚠️  **WARNING:** Do NOT claim UI is "fixed" or "complete" without visual verification.
The Product Owner will review your screenshots.
"""
```

#### Product Owner Prompt Addition

```python
# In prompts/product_owner_prompt.py

UI_REVIEW_SECTION = """
## 🎨 VISUAL REVIEW (MANDATORY FOR UI USER STORIES)

If the user story involves UI/UX changes, you MUST perform visual review:

1. **Check for screenshots**
   - Look in logs/screenshots/{workflow_id}/
   - Architect should have provided screenshots

2. **Visual comparison required**
   - Compare "before" vs "after" screenshots
   - Verify layout, spacing, colors, alignment
   - Check for broken elements or overlaps

3. **UI Approval Checklist**
   - [ ] Screenshots provided by Architect
   - [ ] Visual layout matches user story
   - [ ] No UI regressions (broken layouts)
   - [ ] Responsive design maintained
   - [ ] Color scheme is appropriate
   - [ ] Typography is readable
   - [ ] Interactive elements are visible and accessible

4. **Decision criteria**
   - APPROVE: Only if visual verification confirms UI works correctly
   - REVISE: If screenshots missing OR visual issues found
   - REJECT: If fundamental UI problems exist

⚠️  **CRITICAL:** Never approve UI changes without reviewing screenshots.
Tests passing ≠ UI working correctly.
"""
```

### 3. Orchestrator Integration

```python
# In orchestrator.py

class Orchestrator:
    """Main workflow orchestrator"""

    def __init__(self, workspace_dir: Optional[Path] = None):
        # ... existing code ...
        self.visual_tester = None

    def process_user_story(self, user_story: str) -> WorkflowResult:
        """Process user story through agent workflow"""

        # Detect if this is a UI-related user story
        is_ui_task = self._is_ui_task(user_story)

        if is_ui_task:
            print("🎨 UI task detected - enabling visual testing")
            self.visual_tester = VisualTester(
                workspace_dir=self.workspace,
                workflow_id=self.workflow_id
            )

            # Capture baseline screenshots before changes
            self._capture_baseline_screenshots()

        # ... existing workflow code ...

        # Run agents
        architect_result = self._run_architect(user_story)

        # After architect: Capture screenshots if UI task
        if is_ui_task:
            self._capture_screenshots_after_phase("architect")

        security_result = self._run_security(architect_result)

        if is_ui_task:
            self._capture_screenshots_after_phase("security")

        tester_result = self._run_tester(security_result)

        if is_ui_task:
            self._capture_screenshots_after_phase("tester")

        po_result = self._run_product_owner(user_story, tester_result)

        # ... rest of workflow ...

    def _is_ui_task(self, user_story: str) -> bool:
        """
        Detect if user story involves UI/visual changes

        Args:
            user_story: User story text

        Returns:
            True if UI task detected
        """
        ui_keywords = [
            "ui", "layout", "design", "button", "color", "style",
            "css", "html", "theme", "dark mode", "light mode",
            "responsive", "visual", "appearance", "display",
            "grid", "flex", "position", "align", "spacing",
            "component", "interface", "frontend", "page"
        ]

        story_lower = user_story.lower()
        return any(keyword in story_lower for keyword in ui_keywords)

    def _capture_baseline_screenshots(self):
        """Capture baseline screenshots before any changes"""
        if not self.visual_tester:
            return

        html_files = self.visual_tester.detect_ui_files()

        if html_files:
            print(f"\n📸 Capturing baseline screenshots for {len(html_files)} HTML files...")
            for html_file in html_files:
                self.visual_tester.capture_screenshot(html_file, "baseline")

    def _capture_screenshots_after_phase(self, phase_name: str):
        """Capture screenshots after an agent phase completes"""
        if not self.visual_tester:
            return

        html_files = self.visual_tester.detect_ui_files()

        if html_files:
            print(f"\n📸 Capturing screenshots after {phase_name} phase...")
            for html_file in html_files:
                self.visual_tester.capture_screenshot(html_file, f"after-{phase_name}")
```

### 4. Configuration Updates

```python
# In config.py

# Visual Testing Configuration (v2.3)
VISUAL_TESTING_CONFIG = {
    "enabled": True,  # Enable visual regression testing
    "screenshot_on_ui_tasks": True,  # Auto-detect and screenshot UI tasks
    "require_visual_approval": True,  # PO must review screenshots for UI tasks
    "screenshot_viewports": [
        {"width": 1920, "height": 1080, "label": "desktop"},
        {"width": 768, "height": 1024, "label": "tablet"},
        {"width": 375, "height": 667, "label": "mobile"}
    ],
    "screenshot_tool": "playwright",  # or "safari" (macOS only)
    "comparison_threshold": 0.05,  # 5% acceptable difference
    "store_screenshots_in_git": False,  # Don't commit screenshots (too large)
}
```

### 5. User Story Templates

Create template files to guide users on UI tasks:

```markdown
# UI Task Template

When requesting UI/visual changes, provide:

## Required Information

1. **Visual Description**
   - Describe the desired layout
   - Specify colors, spacing, alignment
   - Mention responsive behavior

2. **Reference Images** (Highly Recommended)
   - Provide mockups, wireframes, or screenshots
   - Show existing designs to match
   - Include examples of similar UIs

3. **Acceptance Criteria**
   - List specific visual requirements
   - Define what "correct" looks like
   - Specify browser/device support

## Example: Good UI User Story

```
Add dark mode toggle to calculator app:

VISUAL REQUIREMENTS:
- Toggle button in top-right corner
- Sun icon (☀️) for light mode, moon icon (🌙) for dark mode
- Button should be circular, 36px diameter
- Smooth rotation animation on hover (20deg)

COLOR SCHEME:
- Light mode background: #f0f0f0
- Dark mode background: #1c1c1e
- Operator buttons: #ff9f0a (macOS orange)
- Number buttons light: #f5f5f5
- Number buttons dark: #505050

REFERENCE:
Match the macOS Calculator app aesthetic exactly

ACCEPTANCE:
- [ ] Toggle button visible in header
- [ ] Theme persists in localStorage
- [ ] Smooth transitions (0.3s ease)
- [ ] All elements visible in both modes
```

## Example: Bad UI User Story (Don't Do This)

```
Add dark mode
```
(Too vague - agents will guess and likely break things)
```

## Testing Strategy

### Phase 1: Baseline Capture
- Before any changes, capture screenshots of existing UI
- Store in `logs/screenshots/{workflow_id}/baseline/`

### Phase 2: Progressive Screenshots
- After each agent phase, capture screenshots
- Compare to baseline automatically
- Flag significant visual differences

### Phase 3: Product Owner Visual Review
- Present before/after screenshots to PO
- PO must explicitly approve visual changes
- Reject if screenshots not provided for UI tasks

### Phase 4: Regression Detection
- Compare current screenshots to baseline
- Calculate pixel difference percentage
- Auto-fail if difference > threshold AND no UI task detected

## Benefits

1. **Prevents False Approvals**
   - Agents can't claim "fixed" without proof
   - Screenshots don't lie

2. **Catches Regressions Early**
   - See visual breakage immediately
   - Don't wait until production

3. **Documentation**
   - Visual history of all UI changes
   - Easy to review what changed

4. **Human Oversight**
   - PO sees actual visual results
   - Not just code and test results

## Dependencies

### Required
- Python 3.8+
- Node.js (for playwright) OR macOS (for Safari automation)

### Optional
- `playwright` (for cross-platform screenshots)
- `pixelmatch` (for visual diff)
- `PIL` or `opencv-python` (for image comparison)

### Installation

```bash
# Install playwright for screenshots
npx playwright install chromium

# Or use system browser (macOS only)
# No installation needed, uses Safari + AppleScript
```

## Limitations

1. **Not Pixel-Perfect**
   - Fonts may render differently across systems
   - Use threshold-based comparison

2. **No JavaScript Interaction Testing**
   - Screenshots are static
   - Can't test animations or interactions
   - Tester agent should still write interaction tests

3. **Manual Review Still Needed**
   - Automated comparison can miss subtle issues
   - Human Product Owner review is essential

## Migration Path

### v2.2 → v2.3

1. **Add visual_tester.py**
2. **Update agent prompts**
3. **Modify orchestrator workflow**
4. **Update config.py**
5. **Test with calculator app fix**

### Backward Compatibility

- Visual testing only activates for UI tasks
- Non-UI tasks work exactly as before
- No breaking changes to existing workflows

## Success Metrics

After implementing visual testing, we should see:

- ✅ Zero false approvals for UI tasks
- ✅ UI regressions caught before merge
- ✅ Higher first-time approval rate (fewer revisions)
- ✅ Better alignment with user expectations
- ✅ Reduced wasted costs on "fake fixes"

---

**Status:** Design Complete - Ready for Implementation
**Target Release:** v2.3.0
**Priority:** Critical (addresses major user pain point)
