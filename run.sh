#!/bin/bash
#
# AI Scrum Master - Convenient wrapper script
#
# Usage:
#   ./run.sh                          # Interactive mode
#   ./run.sh "user story here"        # Direct execution
#   ./run.sh --help                   # Show help
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Error: main.py not found${NC}"
    echo "   Make sure you're running this from the AI Scrum Master root directory"
    exit 1
fi

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

# Check for .env file (optional but recommended)
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Warning: .env file not found${NC}"
    echo "   Create a .env file with:"
    echo "   ANTHROPIC_API_KEY=your_api_key_here"
    echo ""
fi

# Show help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "AI Scrum Master - Multi-Agent Development System"
    echo ""
    echo "Usage:"
    echo "  ./run.sh                    Start interactive mode"
    echo "  ./run.sh \"user story\"       Execute a single task"
    echo "  ./run.sh --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Interactive mode"
    echo "  ./run.sh"
    echo ""
    echo "  # Direct execution"
    echo "  ./run.sh \"Build a calculator web app with dark mode\""
    echo ""
    echo "  # Multi-line (use quotes)"
    echo "  ./run.sh \"Build a REST API for todos with:"
    echo "  - GET /todos"
    echo "  - POST /todos"
    echo "  - PUT /todos/:id"
    echo "  - DELETE /todos/:id\""
    echo ""
    echo "Environment Variables:"
    echo "  ANTHROPIC_API_KEY    Required - Your Anthropic API key"
    echo ""
    echo "Documentation:"
    echo "  docs/SETUP_GITHUB_INTEGRATION.md    GitHub setup guide"
    echo "  docs/PRODUCTION_DEPLOYMENT_WORKFLOW.md    Full CI/CD workflow"
    echo "  RELEASE_NOTES_v2.2.md                v2.2 release notes"
    echo ""
    exit 0
fi

# If no arguments, run interactive mode
if [ $# -eq 0 ]; then
    echo -e "${BLUE}🚀 Starting AI Scrum Master (Interactive Mode)${NC}"
    echo ""
    python3 main.py
    exit 0
fi

# Direct execution mode - run a single task
USER_STORY="$*"

echo -e "${BLUE}🚀 Starting AI Scrum Master${NC}"
echo -e "${GREEN}User Story: ${USER_STORY}${NC}"
echo ""

# Create a temporary Python script to run the task directly
python3 - <<PYTHON_SCRIPT
import sys
from orchestrator import Orchestrator

# Capture user story from command line
user_story = """${USER_STORY}"""

print("Initializing AI Scrum Master...")
try:
    orchestrator = Orchestrator()
    print("✅ Ready! Starting workflow...\n")

    result = orchestrator.process_user_story(user_story)

    # Print summary
    print("\n" + "="*60)
    print("📈 WORKFLOW SUMMARY")
    print("="*60)
    print(f"Status: {'✅ APPROVED' if result.approved else '❌ NOT APPROVED'}")
    print(f"Revisions: {result.revision_count}")
    print(f"Total Cost: \${result.total_cost:.4f}")

    if result.pr_url:
        print(f"GitHub PR: {result.pr_url}")

    if result.errors:
        print(f"\nErrors:")
        for error in result.errors:
            print(f"  - {error}")

    print("="*60 + "\n")

    if result.approved:
        print("🎉 Task completed successfully!")
        if result.pr_url:
            print(f"\n📝 Next steps:")
            print(f"   1. Review the PR: {result.pr_url}")
            print(f"   2. Complete the review checklist")
            print(f"   3. Merge to staging when ready")
        sys.exit(0)
    else:
        print("⚠️  Task not completed. Check errors above.")
        sys.exit(1)

except KeyboardInterrupt:
    print("\n⚠️  Workflow interrupted by user")
    sys.exit(130)
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYTHON_SCRIPT
