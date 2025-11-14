#!/bin/bash
# start_cluster.sh - Start all AI Scrum Master services
#
# Usage: ./start_cluster.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Starting AI Scrum Master Cluster"
echo "=========================================="
echo ""

# Start orchestrator
echo -e "${BLUE}Starting orchestrator (container 200)...${NC}"
if pct exec 200 -- systemctl is-active --quiet ai-orchestrator; then
    echo "  Orchestrator already running"
else
    pct exec 200 -- systemctl start ai-orchestrator
    echo -e "${GREEN}  ✅ Orchestrator started${NC}"
fi

# Wait for orchestrator to be ready
echo ""
echo "Waiting for orchestrator to be ready..."
for i in {1..30}; do
    if pct exec 200 -- curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}  ✅ Orchestrator is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "  ⚠️  Orchestrator not responding after 30s"
    fi
    sleep 1
done

# Start workers
echo ""
echo -e "${BLUE}Starting workers (containers 201-205)...${NC}"
for id in {201..205}; do
    worker_num=$((id - 200))
    if pct exec $id -- systemctl is-active --quiet ai-worker; then
        echo "  Worker $worker_num already running"
    else
        pct exec $id -- systemctl start ai-worker
        echo -e "${GREEN}  ✅ Worker $worker_num started${NC}"
    fi
    sleep 2
done

# Display status
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Cluster Started${NC}"
echo "=========================================="
echo ""
echo "Service Status:"
echo ""

# Check orchestrator
status=$(pct exec 200 -- systemctl is-active ai-orchestrator || echo "inactive")
echo "  Orchestrator: $status"

# Check workers
for id in {201..205}; do
    worker_num=$((id - 200))
    status=$(pct exec $id -- systemctl is-active ai-worker || echo "inactive")
    echo "  Worker $worker_num:    $status"
done

echo ""
echo "Access Points:"
echo "  • Orchestrator API: http://192.168.100.200:8000"
echo "  • Health Check:     http://192.168.100.200:8000/health"
echo "  • Worker Status:    http://192.168.100.200:8000/workers"
echo ""
echo "View Logs:"
echo "  • Orchestrator: pct exec 200 -- journalctl -u ai-orchestrator -f"
echo "  • Worker 1:     pct exec 201 -- journalctl -u ai-worker -f"
echo ""
