#!/bin/bash
# Fix persistent workspace issue on workers

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Fixing persistent workspace directory issue...${NC}"
echo ""

# Fix each worker
for id in 201 202 203 204 205; do
    echo -e "${YELLOW}Fixing worker container $id...${NC}"

    # Stop the service first
    echo "  Stopping service..."
    pct exec $id -- systemctl stop ai-worker

    # Check and update .env
    echo "  Updating .env..."
    pct exec $id -- su - aimaster -c "
        cd ai-scrum-master-v2

        # Remove any existing WORKSPACE_DIR lines
        sed -i '/^WORKSPACE_DIR=/d' .env

        # Add correct workspace dir
        echo 'WORKSPACE_DIR=/opt/ai-scrum-master/workspace' >> .env

        # Verify it's there
        echo '  Current .env WORKSPACE_DIR:'
        grep WORKSPACE_DIR .env || echo '  NOT FOUND!'
    "

    # Check systemd service file for hardcoded paths
    echo "  Checking systemd service..."
    pct exec $id -- cat /etc/systemd/system/ai-worker.service | grep -i workspace || echo "  No workspace in service file"

    # Create the workspace directory if it doesn't exist
    echo "  Creating workspace directory..."
    pct exec $id -- mkdir -p /opt/ai-scrum-master/workspace
    pct exec $id -- chown -R aimaster:aimaster /opt/ai-scrum-master/workspace

    # Reload systemd in case service changed
    echo "  Reloading systemd..."
    pct exec $id -- systemctl daemon-reload

    # Start the service
    echo "  Starting service..."
    pct exec $id -- systemctl start ai-worker

    sleep 2

    # Verify the service is running
    if pct exec $id -- systemctl is-active ai-worker >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅ Worker $id running${NC}"
    else
        echo -e "  ${RED}❌ Worker $id failed to start${NC}"
        pct exec $id -- journalctl -u ai-worker -n 20 --no-pager
    fi

    echo ""
done

echo -e "${YELLOW}Waiting 10 seconds for workers to initialize...${NC}"
sleep 10

echo ""
echo -e "${YELLOW}Checking worker logs for workspace paths...${NC}"
echo ""

for id in 201 202 203 204 205; do
    echo -e "${YELLOW}Worker $id:${NC}"
    pct exec $id -- journalctl -u ai-worker -n 5 --no-pager | grep -i workspace || echo "  No recent workspace logs"
    echo ""
done

echo ""
echo -e "${GREEN}=========================================="
echo "Fix Complete!"
echo -e "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Monitor logs: ./view_logs.sh worker1"
echo "2. Should see: 'Workspace: /opt/ai-scrum-master/workspace'"
echo "3. NOT: 'Workspace: /home/aimaster/workspace'"
