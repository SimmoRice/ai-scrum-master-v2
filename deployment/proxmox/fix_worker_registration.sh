#!/bin/bash
# fix_worker_registration.sh - Configure worker IPs in orchestrator
#
# Usage: ./fix_worker_registration.sh

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Configuring Worker Registration"
echo "=========================================="
echo ""

echo -e "${BLUE}Updating orchestrator container 200...${NC}"

# Add WORKER_IPS to .env
pct exec 200 -- su - aimaster -c '
    cd ai-scrum-master-v2

    # Remove old WORKER_IPS if exists
    sed -i "/^WORKER_IPS=/d" .env

    # Add worker IPs (192.168.100.201-205)
    echo "WORKER_IPS=192.168.100.201,192.168.100.202,192.168.100.203,192.168.100.204,192.168.100.205" >> .env

    echo "Worker IPs configured in .env"
'

# Restart orchestrator to pick up changes
echo ""
echo "Restarting orchestrator service..."
pct exec 200 -- systemctl restart ai-orchestrator

echo ""
echo "Waiting for orchestrator to restart (5s)..."
sleep 5

echo ""
echo -e "${GREEN}✅ Worker registration configured${NC}"
echo ""
echo "Check worker registration:"
echo "  curl http://192.168.100.200:8000/workers"
echo "  curl http://192.168.100.200:8000/health"
echo ""