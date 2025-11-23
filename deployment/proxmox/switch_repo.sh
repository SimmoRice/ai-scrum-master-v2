#!/bin/bash
# Switch GitHub Repository for AI Scrum Master Cluster
# Updates all containers to monitor a different repository
#
# Usage: ./switch_repo.sh <owner/repo>
# Example: ./switch_repo.sh SimmoRice/hello-world-test

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ $# -ne 1 ]; then
    echo "Usage: $0 <owner/repo>"
    echo "Example: $0 SimmoRice/hello-world-test"
    exit 1
fi

NEW_REPO="$1"

echo -e "${BLUE}=========================================="
echo "Switch GitHub Repository"
echo -e "==========================================${NC}"
echo ""
echo "New repository: $NEW_REPO"
echo ""

# Update Orchestrator
echo -e "${YELLOW}Step 1: Updating Orchestrator Configuration${NC}"
echo ""

echo "  Stopping orchestrator service..."
pct exec 200 -- systemctl stop ai-orchestrator

echo "  Updating .env file..."
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i 's|^GITHUB_REPO=.*|GITHUB_REPO=$NEW_REPO|' .env"

echo "  Clearing work queue..."
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && rm -f work_queue.json"
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && echo '[]' > work_queue.json"

echo "  Starting orchestrator service..."
pct exec 200 -- systemctl start ai-orchestrator

sleep 2

if pct exec 200 -- systemctl is-active --quiet ai-orchestrator; then
    echo -e "${GREEN}  ✅ Orchestrator updated${NC}"
else
    echo -e "${RED}  ❌ Orchestrator failed to start${NC}"
    exit 1
fi

echo ""

# Update Workers
echo -e "${YELLOW}Step 2: Updating Workers${NC}"
echo ""

for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    echo -e "${BLUE}Worker $worker_num (Container $id)...${NC}"

    echo "  Stopping service..."
    pct exec $id -- systemctl stop ai-worker

    echo "  Updating .env file..."
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i 's|^GITHUB_REPO=.*|GITHUB_REPO=$NEW_REPO|' .env"

    echo "  Starting service..."
    pct exec $id -- systemctl start ai-worker

    sleep 1

    if pct exec $id -- systemctl is-active --quiet ai-worker; then
        echo -e "${GREEN}  ✅ Worker $worker_num updated${NC}"
    else
        echo -e "${YELLOW}  ⚠️  Worker $worker_num may have issues${NC}"
    fi

    echo ""
done

echo -e "${BLUE}=========================================="
echo "Repository Switch Complete!"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}✅ All services updated to monitor: $NEW_REPO${NC}"
echo ""
echo "Verify configuration:"
echo "  pct exec 200 -- su - aimaster -c 'cd ai-scrum-master-v2 && grep GITHUB_REPO .env'"
echo ""
echo "Check queue status:"
echo "  curl http://192.168.100.200:8000/queue"
echo ""
echo "Monitor orchestrator:"
echo "  pct exec 200 -- journalctl -u ai-orchestrator -f"
echo ""
