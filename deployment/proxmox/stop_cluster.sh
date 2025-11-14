#!/bin/bash
# stop_cluster.sh - Stop all AI Scrum Master services
#
# Usage: ./stop_cluster.sh

set -e

RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Stopping AI Scrum Master Cluster"
echo "=========================================="
echo ""

# Stop workers first
echo -e "${BLUE}Stopping workers (containers 201-205)...${NC}"
for id in {201..205}; do
    worker_num=$((id - 200))
    if pct exec $id -- systemctl is-active --quiet ai-worker; then
        pct exec $id -- systemctl stop ai-worker
        echo -e "${YELLOW}  ⏸️  Worker $worker_num stopped${NC}"
    else
        echo "  Worker $worker_num already stopped"
    fi
done

# Wait for workers to finish
echo ""
echo "Waiting for workers to finish tasks (10s)..."
sleep 10

# Stop orchestrator
echo ""
echo -e "${BLUE}Stopping orchestrator (container 200)...${NC}"
if pct exec 200 -- systemctl is-active --quiet ai-orchestrator; then
    pct exec 200 -- systemctl stop ai-orchestrator
    echo -e "${YELLOW}  ⏸️  Orchestrator stopped${NC}"
else
    echo "  Orchestrator already stopped"
fi

# Display status
echo ""
echo "=========================================="
echo -e "${YELLOW}⏸️  Cluster Stopped${NC}"
echo "=========================================="
echo ""
echo "All services stopped. To start again:"
echo "  ./start_cluster.sh"
echo ""
