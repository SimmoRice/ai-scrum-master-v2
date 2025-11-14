#!/bin/bash
# update_repo.sh - Update AI Scrum Master repository on all containers
#
# Usage: ./update_repo.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Updating AI Scrum Master Repository"
echo "=========================================="
echo ""

# Function to update a container
update_container() {
    local id=$1
    local name=$2

    echo ""
    echo -e "${BLUE}Updating container $id ($name)...${NC}"

    # Stop service first
    if [ "$name" = "orchestrator" ]; then
        echo "  Stopping orchestrator service..."
        pct exec $id -- systemctl stop ai-orchestrator 2>/dev/null || true
    else
        echo "  Stopping worker service..."
        pct exec $id -- systemctl stop ai-worker 2>/dev/null || true
    fi

    # Update repository
    echo "  Pulling latest code..."
    pct exec $id -- su - aimaster -c "
        cd ai-scrum-master-v2
        git fetch origin
        git reset --hard origin/main
        git pull origin main
    " || {
        echo -e "${YELLOW}Warning: Failed to update repository on container $id${NC}"
        return 1
    }

    # Reinstall dependencies
    echo "  Reinstalling dependencies..."
    if [ "$name" = "orchestrator" ]; then
        pct exec $id -- su - aimaster -c "
            cd ai-scrum-master-v2
            source env/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
            pip install -r orchestrator_service/requirements.txt
        " || {
            echo -e "${YELLOW}Warning: Failed to install dependencies on container $id${NC}"
            return 1
        }
    else
        pct exec $id -- su - aimaster -c "
            cd ai-scrum-master-v2
            source env/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
            # Install worker requirements if they exist
            if [ -f worker/requirements.txt ]; then
                pip install -r worker/requirements.txt
            fi
        " || {
            echo -e "${YELLOW}Warning: Failed to install dependencies on container $id${NC}"
            return 1
        }
    fi

    echo -e "${GREEN}✅ Container $id updated successfully${NC}"
}

# Update orchestrator
update_container 200 "orchestrator"

# Update workers
for id in {201..205}; do
    worker_num=$((id - 200))
    update_container $id "worker-$worker_num"
done

echo ""
echo "=========================================="
echo -e "${GREEN}✅ All containers updated!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start services:  ./start_cluster.sh"
echo "  2. Check status:    ./status_cluster.sh"
echo "  3. View logs:       ./view_logs.sh"
echo ""