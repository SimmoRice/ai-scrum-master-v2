#!/bin/bash
# Enable Sequential Processing Mode
# Configures the orchestrator to process one PR at a time to avoid merge conflicts

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "Enable Sequential Processing Mode"
echo -e "==========================================${NC}"
echo ""
echo "This will configure the orchestrator to:"
echo "  • Process only 1 PR at a time (MAX_PENDING_PRS=1)"
echo "  • Block queue until PR is merged"
echo "  • Prevent merge conflicts"
echo ""

# Check if orchestrator is running
if ! pct exec 200 -- systemctl is-active --quiet ai-orchestrator 2>/dev/null; then
    echo -e "${RED}❌ Orchestrator is not running${NC}"
    exit 1
fi

echo -e "${YELLOW}Step 1: Updating orchestrator configuration${NC}"

# Remove any existing PR review settings
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^MAX_PENDING_PRS=/d' .env"
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^BLOCK_ON_CHANGES_REQUESTED=/d' .env"
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^ALLOW_PARALLEL_PRS=/d' .env"

# Add sequential processing settings
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && cat >> .env << 'EOF'

# Sequential Processing Mode (to avoid merge conflicts)
MAX_PENDING_PRS=1
BLOCK_ON_CHANGES_REQUESTED=true
ALLOW_PARALLEL_PRS=false
EOF
"

echo -e "${GREEN}✓${NC} Configuration updated"
echo ""

echo -e "${YELLOW}Step 2: Restarting orchestrator${NC}"
pct exec 200 -- systemctl restart ai-orchestrator

sleep 3

if pct exec 200 -- systemctl is-active --quiet ai-orchestrator; then
    echo -e "${GREEN}✓${NC} Orchestrator restarted successfully"
else
    echo -e "${RED}✗${NC} Orchestrator failed to start"
    echo "Check logs: pct exec 200 -- journalctl -u ai-orchestrator -n 50"
    exit 1
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Sequential Mode Enabled!"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}✓${NC} Orchestrator will now:"
echo "  • Create one PR at a time"
echo "  • Block queue when PR is pending"
echo "  • Wait for you to merge before processing next issue"
echo ""
echo "Workflow:"
echo "  1. Worker creates PR #1"
echo "  2. Queue blocks"
echo "  3. You review and merge PR #1"
echo "  4. Queue unblocks"
echo "  5. Worker creates PR #2 (based on updated main)"
echo "  6. Repeat..."
echo ""
echo "To disable sequential mode and allow parallel PRs:"
echo "  Set MAX_PENDING_PRS to a higher number (e.g., 5)"
echo ""
