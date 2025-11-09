#!/usr/bin/env python3
"""
AI Scrum Master v2.0 - Main CLI

Multi-agent development system powered by Claude Code
"""
import sys
from pathlib import Path
from dotenv import load_dotenv
from orchestrator import Orchestrator, WorkflowResult


def print_banner():
    """Print welcome banner"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║              AI SCRUM MASTER v2.0                         ║
║          Claude Code Multi-Agent System                   ║
╚═══════════════════════════════════════════════════════════╝
""")


def print_help():
    """Print available commands"""
    print("""
Available Commands:
  task <description>  - Create and implement a new user story
  status             - Show current workspace status
  help               - Show this help message
  quit               - Exit the program

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
  > task Build a REST API for managing todos with CRUD operations

  > task Create a calculator web app with HTML, CSS, and JavaScript

  > task Implement user authentication with JWT tokens and bcrypt
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

    print("✅ AI Scrum Master v2.0 ready!")
    print("Type 'help' for available commands\n")

    # Main command loop
    while True:
        try:
            user_input = input("> ").strip()

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
