#!/bin/bash
# fix_github_repo.sh - Add GITHUB_REPO to orchestrator .env
#
# Usage: ./fix_github_repo.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Adding GITHUB_REPO to Orchestrator .env"
echo "=========================================="
echo ""

echo -e "${BLUE}Updating orchestrator container 200...${NC}"

# Add GITHUB_REPO to .env if not already present
pct exec 200 -- su - aimaster -c '
    cd ai-scrum-master-v2
    if ! grep -q "GITHUB_REPO=" .env; then
        echo "GITHUB_REPO=SimmoRice/ai-scrum-master-v2" >> .env
        echo "Added GITHUB_REPO to .env"
    else
        echo "GITHUB_REPO already exists in .env"
    fi
'

echo ""
echo -e "${GREEN}✅ GITHUB_REPO added to orchestrator .env${NC}"
echo ""
echo "Next steps:"
echo "  1. Test orchestrator manually:"
echo "     pct exec 200 -- su - aimaster -c 'cd ai-scrum-master-v2 && source env/bin/activate && python -m orchestrator_service.server'"
echo "  2. If successful, start with systemd:"
echo "     pct exec 200 -- systemctl start ai-orchestrator"
echo ""
