#!/usr/bin/env python3
"""
AI Scrum Master - Main CLI

Multi-agent development system powered by Claude Code
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
from orchestrator import Orchestrator, WorkflowResult
from config import VERSION


def print_banner():
    """Print welcome banner"""
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║              AI SCRUM MASTER v{VERSION:<24}║
║          Claude Code Multi-Agent System                   ║
╚═══════════════════════════════════════════════════════════╝
""")


def get_multiline_input(prompt: str = "> ") -> str:
    r"""
    Get input from user with multi-line support

    Supports two methods:
    1. Backslash continuation: Line ending with \ continues to next line
    2. Double blank line submission: Two empty lines in a row submits

    Args:
        prompt: The prompt to display

    Returns:
        Complete user input as a single string
    """
    lines = []
    first_line = True
    consecutive_blank_lines = 0

    while True:
        try:
            if first_line:
                line = input(prompt).rstrip()
                first_line = False
            else:
                line = input("... ").rstrip()

            # Check for backslash continuation
            if line.endswith("\\"):
                # Remove backslash and add line
                lines.append(line[:-1].rstrip())
                consecutive_blank_lines = 0
                continue

            # Track consecutive blank lines
            if not line:
                consecutive_blank_lines += 1

                # Two consecutive blank lines = submit (if we have content)
                if consecutive_blank_lines >= 2 and lines:
                    # Remove the last blank line we added
                    if lines and lines[-1] == '':
                        lines.pop()
                    break

                # First blank line - add it to preserve formatting
                if lines:  # Only add blank lines after we have content
                    lines.append(line)
                continue
            else:
                # Non-blank line resets the counter
                consecutive_blank_lines = 0

            # Add the line
            lines.append(line)

        except EOFError:
            # Ctrl+D pressed - submit what we have
            break

    # Join all lines with newlines and return
    return "\n".join(lines)


def print_help():
    """Print available commands"""
    print("""
Available Commands:
  task <description>  - Create and implement a new user story
  status             - Show current workspace status
  help               - Show this help message
  quit               - Exit the program

Multi-line Input:
  📋 Paste complex requirements easily!

  Two ways to enter multi-line input:
  1. Double blank line - Press Enter TWICE on empty lines to submit
  2. Backslash continuation - End line with \\ to continue

  Single blank lines within your text are preserved!

How it works:
  1. You provide a user story/requirement
  2. Architect implements the feature
  3. Security reviews and hardens the code
  4. Tester creates and runs tests
  5. Product Owner reviews and decides:
     - APPROVE → Merge to main
     - REVISE → Request improvements (up to 3 revisions)
     - REJECT → Start over

Examples:
  Single-line (works as before):
    > task Build a simple calculator web app

  Multi-line (paste and press Enter TWICE to submit):
    > task Build a REST API for todos
    ...
    ... Requirements:
    ... - GET /todos - List all
    ... - POST /todos - Create new
    ... - PUT /todos/:id - Update
    ... - DELETE /todos/:id - Delete
    ...
    ... (press Enter TWICE on empty lines)

  Backslash continuation:
    > task Create user authentication with \\
    ... JWT tokens and bcrypt hashing
""")


def print_result_summary(result: WorkflowResult):
    """Print workflow result summary"""
    print("\n" + "="*60)
    print("📈 WORKFLOW SUMMARY")
    print("="*60)
    print(f"Status: {'✅ APPROVED' if result.approved else '❌ NOT APPROVED'}")
    print(f"Revisions: {result.revision_count}")
    print(f"Total Cost: ${result.total_cost:.4f}")

    if result.errors:
        print(f"\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    if result.po_decision:
        print(f"\nProduct Owner Decision:")
        # Print first 300 chars of decision
        decision_preview = result.po_decision[:300]
        if len(result.po_decision) > 300:
            decision_preview += "..."
        print(f"  {decision_preview}")

    print("="*60 + "\n")


def main():
    """Main CLI loop"""
    # Load environment variables
    load_dotenv()

    print_banner()

    # Initialize orchestrator
    try:
        orchestrator = Orchestrator()
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        print("\nMake sure:")
        print("  1. Claude Code is installed (claude --version)")
        print("  2. ANTHROPIC_API_KEY is set in .env")
        print("  3. You have write permissions to the workspace directory")
        sys.exit(1)

    print(f"✅ AI Scrum Master v{VERSION} ready!")
    print("Type 'help' for available commands\n")

    # Main command loop
    while True:
        try:
            # Use multi-line input
            user_input = get_multiline_input("> ").strip()

            if not user_input:
                continue

            # Parse command
            parts = user_input.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            # Handle commands
            if command == "quit" or command == "exit":
                print("\n👋 Shutting down AI Scrum Master. Goodbye!")
                break

            elif command == "help":
                print_help()

            elif command == "task":
                if not args:
                    print("❌ Please provide a task description")
                    print("   Example: task Build a calculator web app")
                    continue

                # Execute workflow
                try:
                    result = orchestrator.process_user_story(args)
                    print_result_summary(result)

                    if result.approved:
                        print("🎉 Task completed and merged to main!")
                    else:
                        print("⚠️  Task not completed. Check errors above.")

                except KeyboardInterrupt:
                    print("\n\n⚠️  Workflow interrupted by user")
                    print("Note: Partial work may exist in git branches")
                except Exception as e:
                    print(f"\n❌ Workflow error: {e}")
                    import traceback
                    traceback.print_exc()

            elif command == "status":
                status = orchestrator.get_workspace_status()
                print("\n" + "="*60)
                print("📊 WORKSPACE STATUS")
                print("="*60)
                print(f"Workspace: {status['workspace']}")
                print(f"Current Branch: {status['current_branch']}")

                print(f"\nRecent Commits:")
                print(f"  Main ({len(status['main_commits'])} commits):")
                for commit in status['main_commits'][:3]:
                    print(f"    {commit}")

                print(f"  Architect ({len(status['architect_commits'])} commits):")
                for commit in status['architect_commits'][:3]:
                    print(f"    {commit}")

                print(f"  Security ({len(status['security_commits'])} commits):")
                for commit in status['security_commits'][:3]:
                    print(f"    {commit}")

                print(f"  Tester ({len(status['tester_commits'])} commits):")
                for commit in status['tester_commits'][:3]:
                    print(f"    {commit}")

                print("="*60 + "\n")

            else:
                print(f"❌ Unknown command: {command}")
                print("   Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted. Type 'quit' to exit.")
        except EOFError:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Type 'help' for available commands")


if __name__ == "__main__":
    main()
