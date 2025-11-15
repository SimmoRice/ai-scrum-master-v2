#!/bin/bash
# Quick restart of all worker services
# Use this after updating code to load new changes

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "Restarting All Workers"
echo -e "==========================================${NC}"
echo ""

for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    echo -e "${BLUE}Restarting Worker $worker_num (Container $id)...${NC}"

    pct exec $id -- systemctl restart ai-worker

    # Wait a moment
    sleep 1

    # Check status
    if pct exec $id -- systemctl is-active --quiet ai-worker; then
        echo -e "${GREEN}✅ Worker $worker_num restarted successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Worker $worker_num may have issues${NC}"
        pct exec $id -- systemctl status ai-worker --no-pager | head -5
    fi
    echo ""
done

echo -e "${GREEN}All workers restarted!${NC}"
echo ""
echo "Monitor logs with:"
echo "  pct exec 201 -- journalctl -u ai-worker -f"
echo ""
