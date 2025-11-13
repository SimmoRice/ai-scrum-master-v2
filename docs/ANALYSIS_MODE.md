# Analysis-Only Mode

## Overview

AI Scrum Master now supports **Analysis-Only Mode** for Security and Tester agents. This allows the system to review codebases and provide recommendations **without implementing changes**.

## How It Works

### Detection Logic

Security and Tester agents now receive the **original user story** and can detect if it's an analysis-only task by looking for keywords like:

- "review"
- "analyze"
- "assess"
- "evaluate"
- "provide feedback"
- "recommendations"

If the user story contains ONLY analysis terms and does NOT explicitly request implementation, both agents will operate in **Analysis-Only Mode**.

### Agent Behavior

#### Security Agent

**Analysis-Only Mode:**
- Reviews all code files
- Identifies security vulnerabilities
- Creates `SECURITY_ANALYSIS.md` with:
  - List of vulnerabilities found
  - Risk levels (High/Medium/Low)
  - Recommended fixes
  - Best practices to implement
- Does NOT edit code files
- Commits only the analysis document

**Implementation Mode (default):**
- Reviews all code files
- Identifies security vulnerabilities
- **Fixes issues directly in code**
- Adds input validation and sanitization
- Commits security improvements

#### Tester Agent

**Analysis-Only Mode:**
- Reviews implementation files
- Creates `TEST_PLAN.md` with:
  - List of test cases that should be created
  - Test coverage recommendations
  - Edge cases and scenarios to test
  - Testing strategy
  - Risk areas needing thorough testing
- Does NOT create actual test files
- Commits only the test plan document

**Implementation Mode (default):**
- Creates actual test files
- Writes runnable tests (pytest, jest, etc.)
- **Runs tests to verify they pass**
- Commits test files and results

## Example Use Cases

### Analysis-Only Task

**User Story:**
```
Review the entire code base and provide feedback and ideas that
will improve performance and profitability
```

**Result:**
- Architect creates analysis documents
- Security creates `SECURITY_ANALYSIS.md` with vulnerability recommendations
- Tester creates `TEST_PLAN.md` with testing recommendations
- Product Owner reviews the analysis documents
- **No code is modified**

### Implementation Task

**User Story:**
```
Implement user authentication with JWT tokens and role-based access control
```

**Result:**
- Architect implements authentication system
- Security reviews and **fixes security issues in code**
- Tester creates and **runs actual tests**
- Product Owner reviews working implementation
- **Code is fully implemented and tested**

## Benefits

1. **Non-invasive Reviews**: Analyze external projects without modifying their code
2. **Clear Recommendations**: Get structured analysis documents for decision-making
3. **Flexible Workflow**: Same system handles both analysis and implementation
4. **Cost Effective**: Analysis is faster and cheaper than implementation

## Technical Implementation

### Files Modified

1. **agents/security_prompt.py**
   - Added analysis-only mode detection logic
   - Instructions for creating SECURITY_ANALYSIS.md

2. **agents/tester_prompt.py**
   - Added analysis-only mode detection logic
   - Instructions for creating TEST_PLAN.md

3. **orchestrator.py**
   - Updated Security agent task to include original user story
   - Updated Tester agent task to include original user story
   - Both agents can now see full context to make mode decision

### Validation Gates

The existing validation gates continue to work because:
- Analysis documents (SECURITY_ANALYSIS.md, TEST_PLAN.md) are committed
- Git branch validation checks for commits, which will exist in both modes
- No code changes needed to validation logic

## Migration Notes

This is a **backward-compatible** enhancement:

- Existing implementation-focused user stories continue to work as before
- Only user stories with analysis-only language trigger the new mode
- No configuration changes required
- Default behavior remains implementation mode

## Future Enhancements

Possible improvements:

1. **Explicit Mode Flag**: Add `--analysis-only` flag to force mode
2. **Architect Analysis Mode**: Extend to Architect agent for code reviews
3. **Combined Mode**: Option to create both analysis and implementation
4. **Template Customization**: Allow custom analysis document templates
