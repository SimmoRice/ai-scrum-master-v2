#!/bin/bash
# Install anthropic package on all workers

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Installing anthropic package on all workers...${NC}"
echo ""

for id in 201 202 203 204 205; do
    echo -e "${YELLOW}Worker $id (ai-worker-$((id-200)))${NC}"

    # Install anthropic package
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && pip3 install anthropic"

    # Restart worker
    pct exec $id -- systemctl restart ai-worker

    echo -e "${GREEN}✅ Worker $id updated${NC}"
    echo ""
done

echo -e "${GREEN}All workers updated! Checking status...${NC}"
echo ""

# Check status
for id in 201 202 203 204 205; do
    echo "Worker $id:"
    pct exec $id -- systemctl status ai-worker --no-pager | head -3
    echo ""
done
