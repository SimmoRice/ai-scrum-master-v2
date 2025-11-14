#!/usr/bin/env python3
"""
Analyze ai-calc-2 project and create GitHub issues for enhancements

This script will:
1. Analyze the existing calculator implementation
2. Create detailed GitHub issues for:
   - Adding scientific calculator features
   - Adding 3 custom color themes (keeping macOS as default)
"""

import subprocess
import sys
from pathlib import Path
from setup_github_repo import (
    check_gh_cli,
    check_if_git_repo,
    init_git_repo,
    check_git_remote,
    create_github_repo,
    enable_issues,
    create_labels
)


def create_scientific_calculator_issue(repo_path: Path):
    """Create GitHub issue for scientific calculator features"""

    title = "Feature: Add scientific calculator functionality"

    body = """## Overview
Add scientific calculator capabilities to the existing calculator while maintaining the current layout and positioning.

## Requirements
- Keep existing basic calculator layout and positioning unchanged
- Add scientific functions accessible via additional buttons or mode toggle
- Maintain macOS calculator visual theme as default

## Scientific Functions to Add
### Trigonometric Functions
- [ ] sin, cos, tan (with degree/radian toggle)
- [ ] asin, acos, atan (inverse functions)

### Exponential & Logarithmic
- [ ] log (base 10)
- [ ] ln (natural log)
- [ ] exp (e^x)
- [ ] x^y (power function)
- [ ] √ (square root - if not present)
- [ ] x² (square function)

### Advanced Operations
- [ ] π (pi constant)
- [ ] e (euler's number)
- [ ] % (percentage)
- [ ] 1/x (reciprocal)
- [ ] +/- (sign change - if not present)

### Memory Functions (if not present)
- [ ] MC (Memory Clear)
- [ ] MR (Memory Recall)
- [ ] M+ (Memory Add)
- [ ] M- (Memory Subtract)

## Implementation Guidelines
- **DO NOT** change existing layout or button positioning
- **DO NOT** modify the default macOS calculator theme styling
- Add scientific functions in a way that doesn't break existing functionality
- Consider a toggle/mode switch between basic and scientific modes
- Maintain keyboard shortcuts for existing operations
- Add keyboard shortcuts for new scientific functions
- Ensure proper order of operations for all functions

## Testing Requirements
- [ ] All existing calculator functions still work
- [ ] Scientific functions produce accurate results
- [ ] Degree/radian mode works correctly
- [ ] Edge cases handled (division by zero, domain errors, etc.)
- [ ] Keyboard shortcuts work for new functions

## Priority
**Medium** - Enhancement to existing functionality

## Complexity
**Medium** - Requires careful integration without breaking existing features

## Dependencies
- Issue #2 (Theme system) should be implemented independently
"""

    try:
        result = subprocess.run([
            'gh', 'issue', 'create',
            '--repo', 'SimmoRice/ai-calc-2',
            '--title', title,
            '--body', body,
            '--label', 'enhancement,ready-for-dev'
        ], capture_output=True, text=True, timeout=30, cwd=repo_path)

        if result.returncode == 0:
            issue_url = result.stdout.strip()
            print(f"✅ Created issue: {issue_url}")
            return issue_url
        else:
            print(f"❌ Failed to create scientific calculator issue: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print("❌ Timeout creating scientific calculator issue")
        return None
    except Exception as e:
        print(f"❌ Error creating scientific calculator issue: {e}")
        return None


def create_theme_system_issue(repo_path: Path):
    """Create GitHub issue for color theme system"""

    title = "Feature: Add 3 custom color themes with theme switcher"

    body = """## Overview
Add a theme system allowing users to switch between 3 different color schemes while keeping the macOS calculator theme as the default.

## Requirements
- Keep existing layout and positioning unchanged
- Maintain macOS calculator theme as Theme 1 (default)
- Add 2 additional custom color themes
- Add theme switcher UI (dropdown/buttons)
- Persist theme selection across sessions (localStorage)

## Theme Specifications

### Theme 1: macOS Calculator (Default - Current)
- Keep existing color scheme exactly as is
- This is the baseline theme

### Theme 2: Dark Mode Professional
**Suggested Colors:**
- Background: #1E1E1E (dark gray)
- Display: #2D2D2D (slightly lighter gray)
- Display Text: #FFFFFF (white)
- Number Buttons: #3D3D3D (medium gray)
- Number Button Text: #FFFFFF (white)
- Operator Buttons: #FF9500 (orange accent)
- Operator Button Text: #FFFFFF (white)
- Function Buttons: #505050 (light gray)
- Function Button Text: #FFFFFF (white)

### Theme 3: Modern Blue
**Suggested Colors:**
- Background: #F0F4F8 (light blue-gray)
- Display: #FFFFFF (white)
- Display Text: #1A202C (dark blue-gray)
- Number Buttons: #4299E1 (blue)
- Number Button Text: #FFFFFF (white)
- Operator Buttons: #3182CE (darker blue)
- Operator Button Text: #FFFFFF (white)
- Function Buttons: #E2E8F0 (very light gray-blue)
- Function Button Text: #2D3748 (dark gray)

## Implementation Guidelines
- **DO NOT** change layout, positioning, or button sizes
- **DO NOT** modify any functionality
- Use CSS variables or CSS classes for theme switching
- Add theme switcher UI in a non-intrusive location (settings icon/dropdown)
- Store selected theme in localStorage
- Apply saved theme on page load
- Ensure good contrast ratios for accessibility (WCAG AA minimum)
- Test all themes with existing and scientific calculator features

## Theme Switcher UI Options
1. Settings icon (⚙️) that opens theme selector modal
2. Dropdown menu at top of calculator
3. Small theme toggle buttons (recommend this for simplicity)

## Technical Implementation
```javascript
// Example structure
const themes = {
  macos: { /* current colors */ },
  dark: { /* dark theme colors */ },
  blue: { /* blue theme colors */ }
};

// Apply theme via CSS variables or class switching
function applyTheme(themeName) {
  // Implementation
}

// Persist to localStorage
localStorage.setItem('calculator-theme', themeName);
```

## Testing Requirements
- [ ] All 3 themes render correctly
- [ ] Theme persists across page refreshes
- [ ] Theme switcher is intuitive
- [ ] All buttons visible and readable in each theme
- [ ] No layout shifts when switching themes
- [ ] Works with both basic and scientific calculator modes

## Priority
**Low** - Nice-to-have enhancement, doesn't affect functionality

## Complexity
**Low** - Straightforward CSS/styling changes with localStorage

## Dependencies
- Can be implemented independently of Issue #1 (Scientific features)
"""

    try:
        result = subprocess.run([
            'gh', 'issue', 'create',
            '--repo', 'SimmoRice/ai-calc-2',
            '--title', title,
            '--body', body,
            '--label', 'enhancement,ready-for-dev'
        ], capture_output=True, text=True, timeout=30, cwd=repo_path)

        if result.returncode == 0:
            issue_url = result.stdout.strip()
            print(f"✅ Created issue: {issue_url}")
            return issue_url
        else:
            print(f"❌ Failed to create theme system issue: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print("❌ Timeout creating theme system issue")
        return None
    except Exception as e:
        print(f"❌ Error creating theme system issue: {e}")
        return None


def main():
    """Main entry point"""
    repo_path = Path.home() / "Development/repos/ai-calc-2"
    repo_name = "ai-calc-2"

    print("="*60)
    print("🧪 AI Calculator Enhancement Analysis")
    print("="*60)

    # Check if repo exists
    if not repo_path.exists():
        print(f"\n❌ Repository not found at: {repo_path}")
        print("   Please ensure the ai-calc-2 repository is cloned")
        return 1

    print(f"\n📁 Analyzing repository: {repo_path}")

    # Check if gh CLI is available
    gh_ok, gh_msg = check_gh_cli()
    if not gh_ok:
        print(f"\n❌ {gh_msg}")
        if "not installed" in gh_msg:
            print("   Install: brew install gh")
        else:
            print("   Authenticate: gh auth login")
        return 1

    print("✓ GitHub CLI ready")

    # Setup GitHub repository if needed
    print("\n🔧 Setting up GitHub repository...")

    # Initialize git if needed
    if not check_if_git_repo(repo_path):
        print("  → Initializing git repository...")
        if not init_git_repo(repo_path):
            return 1
    else:
        print("  ✓ Git repository exists")

    # Check for remote and create repo if needed
    has_remote, remote_url = check_git_remote(repo_path)
    if not has_remote:
        print("  → Creating GitHub repository...")
        success, repo_url = create_github_repo(
            repo_path,
            repo_name,
            "AI-powered calculator with macOS theme",
            public=True
        )
        if not success:
            print("  ✗ Failed to create GitHub repository")
            return 1
        print(f"  ✓ Repository created: {repo_url}")
    else:
        print(f"  ✓ Remote exists: {remote_url}")

    # Enable issues
    print("  → Enabling issues...")
    enable_issues(repo_path)

    # Create labels
    print("  → Creating labels...")
    create_labels(repo_path)

    print("\n📋 Creating GitHub issues for ai-calc-2...")
    print()

    # Create issues
    print("1️⃣  Creating issue: Scientific Calculator Features")
    issue1 = create_scientific_calculator_issue(repo_path)

    print("\n2️⃣  Creating issue: Custom Color Themes")
    issue2 = create_theme_system_issue(repo_path)

    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)

    created_count = sum([1 for issue in [issue1, issue2] if issue])
    print(f"✅ Created {created_count}/2 issues")

    if issue1:
        print(f"\n📌 Issue #1: Scientific Calculator")
        print(f"   {issue1}")

    if issue2:
        print(f"\n📌 Issue #2: Theme System")
        print(f"   {issue2}")

    print("\n" + "="*60)
    print("✅ Ready for AI Scrum Master to work on issues!")
    print()
    print("Next steps:")
    print("  1. Review issues on GitHub")
    print("  2. Run: python test_single_agent_github.py --repo SimmoRice/ai-calc-2")
    print("="*60)

    return 0 if created_count == 2 else 1


if __name__ == "__main__":
    sys.exit(main())
