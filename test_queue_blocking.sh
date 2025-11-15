#!/bin/bash
# Test Queue Blocking System
# This script helps you test the PR review and queue blocking system

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "Queue Blocking System Test"
echo "=========================================="
echo ""

# Check if repo name provided
if [ -z "$1" ]; then
    echo -e "${RED}Usage: ./test_queue_blocking.sh YOUR_USERNAME/repo-name${NC}"
    echo ""
    echo "Example:"
    echo "  ./test_queue_blocking.sh SimmoRice/taskmaster-app"
    echo ""
    echo "This will:"
    echo "  1. Create the repository on GitHub"
    echo "  2. Setup labels"
    echo "  3. Generate ~20 issues from the test project spec"
    echo "  4. Provide monitoring commands"
    exit 1
fi

REPO="$1"
USERNAME=$(echo "$REPO" | cut -d'/' -f1)
REPONAME=$(echo "$REPO" | cut -d'/' -f2)

echo -e "${BLUE}Repository:${NC} $REPO"
echo ""

# Step 1: Create repository
echo -e "${YELLOW}Step 1: Create GitHub Repository${NC}"
read -p "Create repository $REPO on GitHub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating repository..."
    gh repo create "$REPO" --public --clone || {
        echo -e "${RED}Failed to create repository. It may already exist.${NC}"
        echo "Skipping repository creation..."
    }

    if [ -d "$REPONAME" ]; then
        cd "$REPONAME"
        echo "# $REPONAME - AI-Built Task Manager" > README.md
        echo "" >> README.md
        echo "Built by distributed AI Scrum Master cluster" >> README.md
        git add README.md
        git commit -m "Initial commit"
        git push origin main
        cd ..
        echo -e "${GREEN}✅ Repository created${NC}"
    fi
else
    echo "Skipping repository creation"
fi

echo ""

# Step 2: Setup labels
echo -e "${YELLOW}Step 2: Setup Repository Labels${NC}"
read -p "Setup labels for $REPO? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python setup_repo_labels.py --repo "$REPO"
    echo -e "${GREEN}✅ Labels created${NC}"
else
    echo "Skipping label setup"
fi

echo ""

# Step 3: Generate issues
echo -e "${YELLOW}Step 3: Generate Project Issues${NC}"
echo "This will create ~20 issues for a task management web app"
read -p "Generate issues? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python create_project_issues.py \
      --repo "$REPO" \
      --project-file test_queue_blocking_project.md
    echo -e "${GREEN}✅ Issues created${NC}"
else
    echo "Skipping issue generation"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}Your cluster will now start working on the issues.${NC}"
echo ""
echo "Monitor progress with these commands:"
echo ""
echo -e "${BLUE}1. Watch queue status:${NC}"
echo "   watch -n 5 'curl -s http://192.168.100.200:8000/health | jq \".pr_review\"'"
echo ""
echo -e "${BLUE}2. Check PR review status:${NC}"
echo "   curl http://192.168.100.200:8000/pr-review/status | jq"
echo ""
echo -e "${BLUE}3. List PRs needing review:${NC}"
echo "   python review_prs.py --repo $REPO --list"
echo ""
echo -e "${BLUE}4. Watch worker activity:${NC}"
echo "   watch -n 5 'curl -s http://192.168.100.200:8000/workers | jq'"
echo ""
echo -e "${BLUE}5. Check GitHub issues:${NC}"
echo "   gh issue list --repo $REPO --label ai-in-progress"
echo ""
echo "=========================================="
echo "Test Scenarios to Try"
echo "=========================================="
echo ""
echo -e "${YELLOW}Scenario 1: Threshold Blocking${NC}"
echo "  Wait for queue to block (MAX_PENDING_PRS=5 by default)"
echo "  Then approve some PRs:"
echo "  python review_prs.py --repo $REPO --approve 1,2,3 --merge"
echo ""
echo -e "${YELLOW}Scenario 2: Changes Requested${NC}"
echo "  Request changes on a PR:"
echo "  python review_prs.py --repo $REPO --request-changes 4 \\"
echo "    --comment \"Please add error handling\""
echo "  Watch everything BLOCK immediately"
echo "  Then approve to unblock:"
echo "  python review_prs.py --repo $REPO --approve 4"
echo ""
echo -e "${YELLOW}Scenario 3: Monitor Queue Health${NC}"
echo "  curl http://192.168.100.200:8000/health | jq '.pr_review'"
echo ""
echo "Happy testing! 🚀"
echo ""
