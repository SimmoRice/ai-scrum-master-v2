# Changelog

All notable changes to AI Scrum Master will be documented in this file.

## [2.2.1] - 2025-11-10

### Critical Fixes
- **Version Update** - Updated version number to 2.2.1 to reflect patch release with critical branch preservation bug fix from v2.1.0

### Documentation
- **Release Notes** - Added RELEASE_NOTES_v2.2.1.md documenting the critical branch bug fix and verification

## [2.1.0] - 2025-11-09

### Critical Fixes
- **FIXED: Revision loop preserves architect-branch** - The critical bug where architect-branch was deleted and recreated from main during revisions has been fixed. Now the Architect can properly iterate on existing code instead of starting from scratch.
- **FIXED: Only downstream branches cleaned on revision** - During revisions, only security-branch and tester-branch are deleted, preserving the Architect's work.
- **FIXED: Product Owner crash with large workspaces** - Product Owner now reviews only git-tracked files instead of all files in directory, preventing crashes when node_modules or other large directories exist.

### Added
- **Comprehensive logging system** (`logger.py`)
  - Console and file logging for all workflow execution
  - Structured JSON logs for analysis (`logs/workflow_*.json`)
  - Agent-specific execution tracking
  - Cost and performance metrics per agent
  - Error tracking throughout workflow
  - Workflow summary with complete audit trail

- **Git helper methods** (from v1)
  - `branch_exists()` - Check if a branch exists
  - `branch_has_commits()` - Check if branch has commits beyond base
  - `delete_branch()` - Safely delete branches with force option
  - `list_files()` - List tracked files in a branch

- **Validation gates before each agent phase**
  - Architect must commit code before Security can start
  - Security must commit changes before Tester can start
  - Prevents workflow continuation when agents fail silently

### Improved
- **Revision workflow** - Architect now receives:
  - List of existing files for context
  - Clear instruction to improve (not restart)
  - Product Owner feedback integrated into prompt

- **Branch management**
  - Added `_cleanup_downstream_branches()` method for revisions
  - Uses new git helper methods for safer operations
  - Better branch existence checking before operations

- **Error handling**
  - All agent failures logged with details
  - Validation gates catch silent failures
  - Better timeout error messages

### Changed
- Bumped timeout from 300s (5 min) to 600s (10 min) - carried over from v2.0
- Multi-line input support - carried over from v2.0
- Live progress feedback - carried over from v2.0

## [2.0.0] - 2025-11-09

### Initial Release
- Multi-agent workflow with 4 specialized agents (Architect, Security, Tester, Product Owner)
- Claude Code CLI integration for reliable code generation
- Sequential git branch workflow
- Automatic merge on approval
- Revision loop support (up to 3 iterations)
- Cost tracking across workflow
- Interactive CLI interface with multi-line input
