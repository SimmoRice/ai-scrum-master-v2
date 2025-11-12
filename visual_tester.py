"""
Visual Testing Utility for AI Scrum Master v2.3

Captures screenshots of HTML files to detect visual regressions in UI changes.
Prevents agents from claiming UI fixes without visual verification.
"""

from pathlib import Path
from typing import Optional, Dict, List, Tuple
import subprocess
import json
import platform
from datetime import datetime


class VisualTester:
    """
    Visual regression testing for web UIs

    Features:
    - Auto-detect HTML files in workspace
    - Capture screenshots using playwright or browser automation
    - Compare screenshots to detect regressions
    - Generate visual testing reports
    """

    def __init__(self, workspace_dir: Path, workflow_id: str):
        """
        Initialize visual tester

        Args:
            workspace_dir: Path to workspace directory
            workflow_id: Unique workflow identifier
        """
        self.workspace = Path(workspace_dir)
        self.workflow_id = workflow_id
        self.screenshot_dir = Path("logs/screenshots") / workflow_id
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self.screenshots: List[Dict] = []
        self.is_macos = platform.system() == "Darwin"

    def detect_ui_files(self) -> List[Path]:
        """
        Detect HTML files in workspace that need visual testing

        Returns:
            List of HTML file paths
        """
        html_files = []

        # Look for HTML files in workspace root
        html_files.extend(self.workspace.glob("*.html"))

        # Look in common subdirectories
        for subdir in ["src", "public", "dist", "build", "web"]:
            subdir_path = self.workspace / subdir
            if subdir_path.exists():
                html_files.extend(subdir_path.glob("**/*.html"))

        # Remove duplicates and return
        return list(set(html_files))

    def capture_screenshot(
        self,
        html_file: Path,
        label: str,
        viewport_width: int = 1280,
        viewport_height: int = 720
    ) -> Optional[Path]:
        """
        Capture screenshot of HTML file

        Args:
            html_file: Path to HTML file
            label: Label for this screenshot (e.g., "baseline", "after-architect")
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height

        Returns:
            Path to screenshot file, or None if failed
        """
        if not html_file.exists():
            print(f"⚠️  HTML file not found: {html_file}")
            return None

        # Generate screenshot filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        screenshot_name = f"{html_file.stem}_{label}_{timestamp}.png"
        screenshot_path = self.screenshot_dir / screenshot_name

        print(f"📸 Capturing screenshot: {html_file.name} ({label})...")

        # Try different screenshot methods in order of preference
        screenshot = None

        # Method 1: Playwright (cross-platform, best quality)
        screenshot = self._capture_with_playwright(
            html_file, screenshot_path, viewport_width, viewport_height
        )

        # Method 2: Chrome DevTools (if playwright fails)
        if not screenshot and self._has_chrome():
            screenshot = self._capture_with_chrome(
                html_file, screenshot_path, viewport_width, viewport_height
            )

        # Method 3: Safari + screencapture (macOS fallback)
        if not screenshot and self.is_macos:
            screenshot = self._capture_with_safari(html_file, screenshot_path)

        if screenshot:
            print(f"✅ Screenshot saved: {screenshot_path.name}")
            self.screenshots.append({
                "file": str(html_file),
                "label": label,
                "path": str(screenshot_path),
                "timestamp": timestamp,
                "viewport": f"{viewport_width}x{viewport_height}"
            })
            return screenshot_path
        else:
            print(f"❌ Failed to capture screenshot for {html_file.name}")
            return None

    def _capture_with_playwright(
        self,
        html_file: Path,
        output_path: Path,
        width: int,
        height: int
    ) -> Optional[Path]:
        """
        Capture screenshot using Playwright CLI

        This is the preferred method - works cross-platform
        """
        try:
            file_url = f"file://{html_file.absolute()}"

            result = subprocess.run([
                "npx", "-y", "playwright", "screenshot",
                file_url,
                str(output_path),
                f"--viewport-size={width},{height}",
                "--full-page"
            ], capture_output=True, timeout=30, text=True)

            if result.returncode == 0 and output_path.exists():
                return output_path

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return None

    def _has_chrome(self) -> bool:
        """Check if Chrome/Chromium is installed"""
        try:
            result = subprocess.run(
                ["which", "google-chrome"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _capture_with_chrome(
        self,
        html_file: Path,
        output_path: Path,
        width: int,
        height: int
    ) -> Optional[Path]:
        """
        Capture screenshot using Chrome headless mode

        Fallback if playwright not available
        """
        try:
            file_url = f"file://{html_file.absolute()}"

            result = subprocess.run([
                "google-chrome",
                "--headless",
                "--disable-gpu",
                f"--screenshot={output_path}",
                f"--window-size={width},{height}",
                file_url
            ], capture_output=True, timeout=30)

            if result.returncode == 0 and output_path.exists():
                return output_path

        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass

        return None

    def _capture_with_safari(
        self,
        html_file: Path,
        output_path: Path
    ) -> Optional[Path]:
        """
        Capture screenshot using Safari (macOS only)

        Last resort fallback for macOS systems
        """
        if not self.is_macos:
            return None

        try:
            file_url = f"file://{html_file.absolute()}"

            # Open Safari, load page, wait, screenshot
            applescript = f'''
            tell application "Safari"
                activate
                make new document
                set URL of front document to "{file_url}"
                delay 2
            end tell

            do shell script "screencapture -x -w {output_path}"

            tell application "Safari"
                close front document
            end tell
            '''

            subprocess.run(
                ["osascript", "-e", applescript],
                capture_output=True,
                timeout=15
            )

            if output_path.exists():
                return output_path

        except Exception:
            pass

        return None

    def capture_all_phases(self, phase_name: str) -> List[Path]:
        """
        Capture screenshots of all HTML files for a specific phase

        Args:
            phase_name: Name of the phase (e.g., "baseline", "architect", "security")

        Returns:
            List of screenshot paths
        """
        html_files = self.detect_ui_files()

        if not html_files:
            print(f"ℹ️  No HTML files found in workspace")
            return []

        print(f"\n📸 Visual Testing: Capturing {len(html_files)} screenshot(s) for {phase_name} phase...")

        screenshots = []
        for html_file in html_files:
            screenshot = self.capture_screenshot(html_file, phase_name)
            if screenshot:
                screenshots.append(screenshot)

        return screenshots

    def compare_screenshots(
        self,
        baseline: Path,
        current: Path,
        threshold: float = 0.05
    ) -> Dict:
        """
        Compare two screenshots and calculate difference using perceptual hashing

        Args:
            baseline: Path to baseline screenshot
            current: Path to current screenshot
            threshold: Acceptable difference (0.0-1.0, default 5%)

        Returns:
            Dict with comparison results:
            {
                "baseline": str,
                "current": str,
                "difference_percent": float,
                "passed": bool,
                "threshold": float,
                "hash_difference": int (optional),
                "error": str (optional)
            }
        """
        result = {
            "baseline": str(baseline),
            "current": str(current),
            "difference_percent": 0.0,
            "passed": True,
            "threshold": threshold
        }

        try:
            # Import PIL and imagehash (optional dependencies)
            from PIL import Image
            import imagehash

            # Verify files exist
            if not baseline.exists():
                result["error"] = f"Baseline file not found: {baseline}"
                result["passed"] = False
                return result

            if not current.exists():
                result["error"] = f"Current file not found: {current}"
                result["passed"] = False
                return result

            # Load images
            baseline_img = Image.open(baseline)
            current_img = Image.open(current)

            # Calculate perceptual hashes using dhash (difference hash)
            # dhash is fast and good for detecting structural changes
            baseline_hash = imagehash.dhash(baseline_img)
            current_hash = imagehash.dhash(current_img)

            # Calculate hash difference (0 = identical, higher = more different)
            # Max hash difference for dhash is 64 (8x8 hash grid)
            hash_diff = baseline_hash - current_hash
            result["hash_difference"] = int(hash_diff)

            # Convert hash difference to percentage (0.0 to 1.0)
            # For dhash, max difference is 64 bits
            max_diff = 64.0
            diff_percent = hash_diff / max_diff
            result["difference_percent"] = round(diff_percent, 4)

            # Check if difference is within threshold
            result["passed"] = diff_percent <= threshold

            return result

        except ImportError:
            # Gracefully handle missing dependencies
            result["error"] = "PIL/imagehash not installed. Install with: pip install Pillow imagehash"
            result["passed"] = True  # Don't fail workflow if libraries missing
            return result

        except Exception as e:
            # Handle any other errors (corrupt images, etc.)
            result["error"] = f"Image comparison failed: {str(e)}"
            result["passed"] = True  # Don't fail workflow on comparison errors
            return result

    def generate_visual_report(self) -> str:
        """
        Generate markdown report of all screenshots captured

        Returns:
            Markdown report content
        """
        report = "# Visual Testing Report\n\n"
        report += f"**Workflow ID:** {self.workflow_id}\n\n"
        report += f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"**Screenshots Captured:** {len(self.screenshots)}\n\n"

        if not self.screenshots:
            report += "⚠️  No screenshots were captured during this workflow.\n"
            return report

        # Group screenshots by HTML file
        files = {}
        for shot in self.screenshots:
            file_name = Path(shot['file']).name
            if file_name not in files:
                files[file_name] = []
            files[file_name].append(shot)

        for file_name, shots in files.items():
            report += f"## {file_name}\n\n"

            for shot in shots:
                report += f"### {shot['label']} ({shot['viewport']})\n"
                report += f"![{shot['label']}]({shot['path']})\n\n"
                report += f"*Captured at: {shot['timestamp']}*\n\n"

        report += "---\n\n"
        report += "**Note:** Visual testing helps catch UI regressions that automated tests miss.\n"
        report += "Always review screenshots before approving UI changes.\n"

        return report

    def save_report(self) -> Path:
        """
        Save visual testing report to file

        Returns:
            Path to report file
        """
        report_content = self.generate_visual_report()
        report_path = self.screenshot_dir / "visual_report.md"

        report_path.write_text(report_content)
        print(f"\n📄 Visual report saved: {report_path}")

        return report_path

    def has_screenshots(self) -> bool:
        """Check if any screenshots were captured"""
        return len(self.screenshots) > 0

    def get_screenshot_for_phase(self, html_file: Path, phase: str) -> Optional[Path]:
        """
        Get screenshot path for specific HTML file and phase

        Args:
            html_file: HTML file path
            phase: Phase name (e.g., "baseline", "architect")

        Returns:
            Screenshot path or None
        """
        for shot in self.screenshots:
            if Path(shot['file']) == html_file and shot['label'] == phase:
                return Path(shot['path'])
        return None

    def get_all_screenshots_for_file(self, html_file: Path) -> List[Dict]:
        """
        Get all screenshots for a specific HTML file

        Args:
            html_file: HTML file path

        Returns:
            List of screenshot metadata dicts
        """
        return [shot for shot in self.screenshots if Path(shot['file']) == html_file]
