#!/bin/bash
# configure_multi_repo.sh - Configure orchestrator for multi-repo support
#
# Usage: ./configure_multi_repo.sh "repo1,repo2,repo3"
# Example: ./configure_multi_repo.sh "SimmoRice/ai-scrum-master-v2,SimmoRice/another-repo"

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo "Usage: ./configure_multi_repo.sh \"owner/repo1,owner/repo2,owner/repo3\""
    echo ""
    echo "Example:"
    echo "  ./configure_multi_repo.sh \"SimmoRice/ai-scrum-master-v2,SimmoRice/my-app\""
    echo ""
    exit 1
fi

REPOS="$1"

echo "=========================================="
echo "Configuring Multi-Repository Support"
echo "=========================================="
echo ""
echo "Repositories: $REPOS"
echo ""

echo -e "${BLUE}Updating orchestrator container 200...${NC}"

# Update .env with GITHUB_REPOS
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2

    # Remove old GITHUB_REPO and GITHUB_REPOS if they exist
    sed -i '/^GITHUB_REPO=/d' .env
    sed -i '/^GITHUB_REPOS=/d' .env

    # Add GITHUB_REPOS
    echo \"GITHUB_REPOS=$REPOS\" >> .env

    echo \"Multi-repo configuration updated in .env\"
"

# Restart orchestrator to pick up changes
echo ""
echo "Restarting orchestrator service..."
pct exec 200 -- systemctl restart ai-orchestrator

echo ""
echo "Waiting for orchestrator to restart (5s)..."
sleep 5

echo ""
echo -e "${GREEN}✅ Multi-repo configuration complete${NC}"
echo ""
echo "Verify configuration:"
echo "  curl http://192.168.100.200:8000/health"
echo ""
echo "The orchestrator will now monitor all configured repositories for 'ai-ready' issues."
echo ""
