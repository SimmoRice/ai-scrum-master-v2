#!/bin/bash
# Complete Cluster Update Script
# Updates code and installs dependencies on orchestrator and all workers

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "AI Scrum Master Cluster Update"
echo -e "==========================================${NC}"
echo ""

# Step 1: Update Orchestrator
echo -e "${YELLOW}Step 1: Updating Orchestrator (Container 200)${NC}"
echo ""

echo "Pulling latest code..."
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && git pull origin main"

echo "Installing dependencies..."
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && pip3 install -r requirements.txt"

echo "Restarting orchestrator..."
pct exec 200 -- systemctl restart ai-orchestrator

echo -e "${GREEN}✅ Orchestrator updated${NC}"
echo ""

# Step 2: Update Workers
echo -e "${YELLOW}Step 2: Updating Workers (Containers 201-205)${NC}"
echo ""

for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    echo -e "${BLUE}Worker $worker_num (Container $id)${NC}"

    echo "  Pulling latest code..."
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git pull origin main"

    echo "  Installing dependencies..."
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && pip3 install -r requirements.txt"

    echo "  Restarting worker..."
    pct exec $id -- systemctl restart ai-worker

    echo -e "${GREEN}  ✅ Worker $worker_num updated${NC}"
    echo ""
done

# Step 3: Verify All Services
echo -e "${YELLOW}Step 3: Verifying Services${NC}"
echo ""

echo "Orchestrator:"
pct exec 200 -- systemctl status ai-orchestrator --no-pager | head -3
echo ""

for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    echo "Worker $worker_num:"
    pct exec $id -- systemctl status ai-worker --no-pager | head -3
    echo ""
done

# Step 4: Check for errors
echo -e "${YELLOW}Step 4: Checking for Recent Errors${NC}"
echo ""

echo "Checking worker logs for errors..."
for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    errors=$(pct exec $id -- journalctl -u ai-worker --since "1 minute ago" --no-pager | grep -i "error\|traceback\|failed" | wc -l)

    if [ "$errors" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Worker $worker_num: Found $errors error(s) in last minute${NC}"
        pct exec $id -- journalctl -u ai-worker --since "1 minute ago" --no-pager | grep -i "error\|traceback" | tail -5
        echo ""
    else
        echo -e "${GREEN}✅ Worker $worker_num: No errors${NC}"
    fi
done

echo ""
echo -e "${BLUE}=========================================="
echo "Update Complete!"
echo -e "==========================================${NC}"
echo ""

# Final status
echo -e "${GREEN}All services updated and restarted.${NC}"
echo ""
echo "Next steps:"
echo "  1. Monitor orchestrator: pct exec 200 -- journalctl -u ai-orchestrator -f"
echo "  2. Monitor worker 1:     pct exec 201 -- journalctl -u ai-worker -f"
echo "  3. Check queue status:   curl http://192.168.100.200:8000/queue"
echo ""
