# GitHub Issue Creator with AI Enhancement

Create detailed, well-structured GitHub issues from simple user stories using AI to ask clarifying questions and expand requirements.

## Overview

This tool takes a basic user story and uses Claude AI to:
1. Ask 3-5 clarifying questions about requirements, constraints, and acceptance criteria
2. Process your answers
3. Generate a comprehensive GitHub issue with detailed specifications
4. Create the issue in your repository with `ready-for-dev` label

The AI expands your story similar to how [analyze_ai_calc.py](../analyze_ai_calc.py) created detailed issues for the calculator project.

## Features

- **AI-Powered Enhancement**: Claude asks smart questions to understand your needs
- **Interactive Q&A**: Answer questions to refine requirements
- **Detailed Issue Structure**: Generates issues with Overview, Requirements, Constraints, Testing, Acceptance Criteria
- **Repository Setup**: Automatically sets up GitHub repo if needed
- **Label Management**: Creates workflow labels automatically
- **Preview Before Creation**: Review the generated issue before posting

## Usage

### Interactive Mode (Recommended)

```bash
python create_github_issue.py --repo ~/path/to/repo
```

This will:
1. Prompt you to enter your user story
2. AI generates clarifying questions
3. You answer the questions
4. AI creates detailed issue
5. You review and confirm
6. Issue is created on GitHub

### With User Story Argument

```bash
python create_github_issue.py --repo ~/path/to/repo --story "Add dark mode toggle to settings"
```

### Skip Clarifying Questions

If you want to generate an issue directly without Q&A:

```bash
python create_github_issue.py --repo ~/path/to/repo --story "Add user authentication" --skip-questions
```

### Custom Labels

```bash
python create_github_issue.py --repo ~/path/to/repo --story "Fix login bug" --labels "bug,high-priority,ready-for-dev"
```

## Examples

### Example 1: Feature Request

```bash
python create_github_issue.py --repo ~/Development/repos/my-app --story "Add export to PDF functionality"
```

**AI might ask:**
- Q: What formats should the PDF export support (A4, letter, custom)?
- Q: Should users be able to customize the PDF layout or styling?
- Q: Are there any existing PDF libraries in the project, or should I choose one?
- Q: What elements from the app should be included in the PDF?
- Q: Should this work for all users or require specific permissions?

**Your answers guide the AI to generate a detailed issue like:**

```markdown
## Overview
Add PDF export functionality allowing users to export their data as formatted PDF documents.

## Requirements
- Support A4 and letter paper sizes
- Use existing pdfkit library for consistency
- Export includes: header, main content, footer with page numbers
- Available to all authenticated users

## Constraints
- Do not change existing export functionality (CSV, JSON)
- Must work in both Chrome and Safari
- PDF generation should not block UI (use async processing)

## Implementation Guidelines
- Add "Export PDF" button to export menu
- Use pdfkit library with html-pdf-node wrapper
- Create PDF template in views/pdf_template.html
- Add /api/export/pdf endpoint
- Handle large documents (>100 pages) with streaming

## Testing Requirements
- [ ] PDF exports correctly formatted on A4
- [ ] PDF exports correctly formatted on letter
- [ ] All content sections included
- [ ] Page numbers displayed correctly
- [ ] Works in Chrome and Safari
- [ ] Large documents (>100 pages) handled gracefully
- [ ] Error handling for invalid data

## Acceptance Criteria
- [ ] Users can export data as PDF
- [ ] PDF includes all specified sections
- [ ] No regression in existing export features
- [ ] Performance acceptable (<5 seconds for typical doc)

## Priority & Complexity
**Priority:** Medium - Nice to have feature
**Complexity:** Medium - Requires PDF library integration
```

### Example 2: Bug Fix

```bash
python create_github_issue.py --repo ~/Development/repos/my-app --story "Fix: Users getting logged out randomly"
```

**AI might ask:**
- Q: How frequently does this occur (always, intermittently, specific conditions)?
- Q: Does this happen on specific browsers or all browsers?
- Q: Are there any error messages in the console or logs?
- Q: When did this issue start appearing?
- Q: Are there any patterns (time of day, specific actions)?

### Example 3: ai-calc-2 (Theme System)

Let's test it with the actual ai-calc-2 repo:

```bash
python create_github_issue.py --repo ~/Development/repos/ai-calc-2 \
  --story "Add ability for users to create and save custom color themes"
```

**AI might ask:**
- Q: Should users be able to share their custom themes with others?
- Q: How many custom themes should users be allowed to save?
- Q: Should there be a theme editor UI or just preset color pickers?
- Q: Should custom themes persist across devices/accounts?
- Q: Are there any brand colors that should not be changeable?

## Issue Structure

Generated issues follow this structure:

```markdown
## Overview
High-level summary of the feature/fix

## Requirements
- Specific requirement 1
- Specific requirement 2
- Specific requirement 3

## Constraints
- What should NOT be changed
- Technical limitations
- Performance requirements

## Implementation Guidelines
- Specific technical approaches
- Libraries/frameworks to use
- Architecture decisions
- Code organization

## Testing Requirements
- [ ] Test case 1
- [ ] Test case 2
- [ ] Edge cases
- [ ] Browser compatibility
- [ ] Performance tests

## Acceptance Criteria
- [ ] Feature works as described
- [ ] No breaking changes
- [ ] Tests passing
- [ ] Documentation updated

## Priority & Complexity
**Priority:** High/Medium/Low
**Complexity:** High/Medium/Low
```

## How It Works

### Step 1: Repository Detection

The script detects your repository type:
- JavaScript/Node.js (package.json)
- Python (requirements.txt, setup.py)
- Go (go.mod)
- Rust (Cargo.toml)

This helps the AI provide language-specific guidance.

### Step 2: Clarifying Questions

Claude analyzes your user story and asks 3-5 targeted questions about:
- **Requirements**: What specifically needs to be built?
- **Constraints**: What should NOT be changed?
- **Technical Details**: Preferred libraries, frameworks?
- **Acceptance**: How will we know it's done?
- **Priority**: How urgent is this?

### Step 3: Issue Generation

Using your answers, Claude generates a comprehensive issue with:
- Clear, actionable requirements
- Specific implementation guidelines
- Detailed testing checklist
- Measurable acceptance criteria
- Priority and complexity assessment

### Step 4: Review and Create

You review the generated issue and can:
- Approve and create it on GitHub
- Cancel if it needs refinement
- Edit manually after creation

## Workflow Integration

After creating an issue, run AI Scrum Master:

```bash
# Create detailed issue
python create_github_issue.py --repo ~/my-project

# AI generates issue #3 with label 'ready-for-dev'

# Run AI Scrum Master on it
python test_single_agent_github.py --repo ~/my-project --issue 3 --verbose
```

## Comparison with Manual Issues

### Without AI Enhancement

```
Title: Add dark mode

Body:
Users want a dark mode.
```

### With AI Enhancement

```markdown
Title: Feature: Add dark mode toggle with theme persistence

## Overview
Implement a dark mode theme that users can toggle between light and dark color schemes,
with preference persistence across sessions.

## Requirements
- Toggle button in settings menu (top-right corner)
- Dark color scheme following WCAG AA contrast standards
- Smooth transition animation (200ms fade)
- Persist preference to localStorage
- Apply theme immediately on page load
- Support system preference detection (prefers-color-scheme)

## Constraints
- Do not modify existing layout or component positioning
- Maintain current responsive breakpoints
- Keep all functionality working in both themes
- CSS-only solution (no JavaScript framework changes)

## Implementation Guidelines
- Add CSS custom properties in :root and [data-theme="dark"]
- Use localStorage key: 'theme-preference'
- Add theme toggle component in Header.jsx
- Apply theme via data-theme attribute on <html>
- Detect system preference: window.matchMedia('(prefers-color-scheme: dark)')

## Testing Requirements
- [ ] Toggle switches themes correctly
- [ ] Theme persists after page refresh
- [ ] System preference detected on first visit
- [ ] All text readable in both themes (contrast check)
- [ ] Transition animation smooth
- [ ] Works on mobile and desktop
- [ ] localStorage handling graceful if disabled

## Acceptance Criteria
- [ ] Users can toggle between light and dark mode
- [ ] Selected theme persists across browser sessions
- [ ] All UI elements visible and readable in both themes
- [ ] No layout shifts when switching themes
- [ ] Respects user's system preference by default

## Priority & Complexity
**Priority:** Medium - User experience enhancement
**Complexity:** Low - CSS theming with localStorage
```

## Tips for Best Results

### 1. Be Specific in Your Initial Story

Instead of: "Add user management"
Better: "Add ability for admins to create, edit, and delete user accounts"

### 2. Provide Context When Asked

The AI asks questions to understand:
- Your technical environment
- Existing constraints
- User expectations
- Quality requirements

### 3. Mention Constraints Upfront

If there are things that MUST NOT change, mention them:
```bash
python create_github_issue.py --repo ~/my-app \
  --story "Add search functionality. Do not change the existing navigation bar layout."
```

### 4. Reference Existing Patterns

```bash
python create_github_issue.py --repo ~/my-app \
  --story "Add user profile page, similar to the existing settings page design"
```

### 5. Specify Testing Needs

```bash
python create_github_issue.py --repo ~/my-app \
  --story "Add payment processing. Must include comprehensive test coverage."
```

## Advanced Usage

### Batch Issue Creation

Create multiple issues from a file:

```bash
# issues.txt contains one story per line
while IFS= read -r story; do
  python create_github_issue.py --repo ~/my-app --story "$story" --skip-questions
done < issues.txt
```

### Custom Issue Templates

The AI follows the system prompt structure. You can fork and customize the `generate_detailed_issue()` function to match your team's issue format.

### Integration with Analysis Scripts

Combine with project analysis:

```bash
# 1. Analyze project for improvement opportunities
python analyze_project.py ~/my-app > analysis.txt

# 2. Review analysis and create issues for each improvement
python create_github_issue.py --repo ~/my-app --story "Based on analysis: improve error handling"
```

## Troubleshooting

### "ANTHROPIC_API_KEY not found"

Create a `.env` file in the ai-scrum-master-v2 directory:
```
ANTHROPIC_API_KEY=your_api_key_here
```

### "GitHub CLI not installed"

```bash
brew install gh
gh auth login
```

### "Repository not found"

The script can create the GitHub repository for you. When prompted, answer 'y' to create it.

### Issue Body Too Long

If the AI generates a very long issue, GitHub has a limit of ~65,536 characters. The AI typically stays well within this limit.

### Questions Not Relevant

Use `--skip-questions` to generate issues directly from your story without Q&A.

## Requirements

- Python 3.8+
- anthropic package (`pip install anthropic`)
- GitHub CLI (`brew install gh`)
- ANTHROPIC_API_KEY in .env file

## See Also

- [analyze_ai_calc.py](../analyze_ai_calc.py) - Example of detailed issue creation for specific project
- [test_single_agent_github.py](../test_single_agent_github.py) - Run AI Scrum Master on issues
- [GITHUB_ISSUE_WORKFLOW.md](GITHUB_ISSUE_WORKFLOW.md) - Complete GitHub workflow documentation
