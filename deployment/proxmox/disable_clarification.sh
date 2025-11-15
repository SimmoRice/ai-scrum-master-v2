#!/bin/bash
# Disable Sprint Planning Q&A clarification check on all workers

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Disabling clarification check on all workers...${NC}"
echo ""

for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    echo "Worker $worker_num (Container $id)..."

    # Add SKIP_CLARIFICATION_CHECK to .env if not already there
    pct exec $id -- su - aimaster -c "
        cd ai-scrum-master-v2
        if grep -q 'SKIP_CLARIFICATION_CHECK' .env; then
            sed -i 's/SKIP_CLARIFICATION_CHECK=.*/SKIP_CLARIFICATION_CHECK=true/' .env
        else
            echo 'SKIP_CLARIFICATION_CHECK=true' >> .env
        fi
    "

    echo "  ✅ Clarification check disabled"
done

echo ""
echo -e "${YELLOW}Restarting workers to apply changes...${NC}"

for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    pct exec $id -- systemctl restart ai-worker
    echo "  Restarted worker $worker_num"
done

echo ""
echo -e "${GREEN}✅ Clarification check disabled on all workers${NC}"
echo ""
echo "Workers will now skip the clarification check and proceed directly to implementation."
echo "To re-enable, set SKIP_CLARIFICATION_CHECK=false in worker .env files."
echo ""
