#!/bin/bash
# restart_cluster.sh - Restart all AI Scrum Master services
#
# Usage: ./restart_cluster.sh

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "=========================================="
echo "Restarting AI Scrum Master Cluster"
echo "=========================================="
echo ""

# Stop all services
./stop_cluster.sh

echo ""
echo "Waiting 5 seconds before restart..."
sleep 5

# Start all services
./start_cluster.sh

echo ""
echo -e "${GREEN}✅ Cluster Restarted${NC}"
echo ""
