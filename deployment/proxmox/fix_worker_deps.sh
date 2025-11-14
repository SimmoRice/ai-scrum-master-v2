#!/bin/bash
# fix_worker_deps.sh - Install missing worker dependencies
#
# Usage: ./fix_worker_deps.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Installing Worker Dependencies"
echo "=========================================="
echo ""

# Function to update a worker container
update_worker() {
    local id=$1
    local worker_num=$((id - 200))

    echo ""
    echo -e "${BLUE}Updating worker $worker_num (container $id)...${NC}"

    # Stop service first
    echo "  Stopping worker service..."
    pct exec $id -- systemctl stop ai-worker 2>/dev/null || true

    # Pull latest code (to get worker/requirements.txt)
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

    # Install worker requirements
    echo "  Installing worker requirements..."
    pct exec $id -- su - aimaster -c "
        cd ai-scrum-master-v2
        source env/bin/activate
        pip install --upgrade pip
        if [ -f worker/requirements.txt ]; then
            pip install -r worker/requirements.txt
        else
            echo 'Warning: worker/requirements.txt not found'
            exit 1
        fi
    " || {
        echo -e "${YELLOW}Warning: Failed to install dependencies on container $id${NC}"
        return 1
    }

    echo -e "${GREEN}✅ Worker $worker_num updated successfully${NC}"
}

# Update all workers
for id in {201..205}; do
    update_worker $id
done

echo ""
echo "=========================================="
echo -e "${GREEN}✅ All workers updated!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start workers:   ./start_cluster.sh"
echo "  2. Check status:    ./status_cluster.sh"
echo "  3. View logs:       ./view_logs.sh worker1"
echo ""