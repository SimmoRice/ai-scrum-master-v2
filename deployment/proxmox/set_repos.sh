#!/bin/bash
# Set GitHub Repositories for AI Scrum Master Cluster (Multi-Repo Mode)
# Updates all containers to monitor specified repositories
#
# Usage: ./set_repos.sh <repo1> [repo2] [repo3] ...
# Example: ./set_repos.sh SimmoRice/hello-world-test
# Example: ./set_repos.sh SimmoRice/hello-world-test SimmoRice/taskmaster-app

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ $# -eq 0 ]; then
    echo "Usage: $0 <repo1> [repo2] [repo3] ..."
    echo ""
    echo "Examples:"
    echo "  $0 SimmoRice/hello-world-test"
    echo "  $0 SimmoRice/hello-world-test SimmoRice/taskmaster-app"
    exit 1
fi

# Join all arguments with commas
REPOS_LIST=$(IFS=,; echo "$*")

echo -e "${BLUE}=========================================="
echo "Set GitHub Repositories (Multi-Repo Mode)"
echo -e "==========================================${NC}"
echo ""
echo "Repositories: $REPOS_LIST"
echo ""

# Update Orchestrator
echo -e "${YELLOW}Step 1: Updating Orchestrator Configuration${NC}"
echo ""

echo "  Stopping orchestrator service..."
pct exec 200 -- systemctl stop ai-orchestrator

echo "  Updating .env file..."
# Remove old GITHUB_REPO and GITHUB_REPOS lines
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^GITHUB_REPO=/d' .env"
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^GITHUB_REPOS=/d' .env"
# Add new GITHUB_REPOS line
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && echo 'GITHUB_REPOS=$REPOS_LIST' >> .env"

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
    pct exec 200 -- journalctl -u ai-orchestrator -n 20 --no-pager
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
    # Remove old GITHUB_REPO and GITHUB_REPOS lines
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^GITHUB_REPO=/d' .env"
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^GITHUB_REPOS=/d' .env"
    # Add new GITHUB_REPOS line
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && echo 'GITHUB_REPOS=$REPOS_LIST' >> .env"

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
echo "Repository Configuration Complete!"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}✅ All services updated to monitor:${NC}"
for repo in "$@"; do
    echo "   • $repo"
done
echo ""
echo "Verify configuration:"
echo "  pct exec 200 -- su - aimaster -c 'cd ai-scrum-master-v2 && grep GITHUB_REPOS .env'"
echo ""
echo "Check queue status:"
echo "  curl http://192.168.100.200:8000/queue"
echo ""
echo "Monitor orchestrator:"
echo "  pct exec 200 -- journalctl -u ai-orchestrator -f"
echo ""
