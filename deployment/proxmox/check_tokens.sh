#!/bin/bash
# Check GitHub Token Status on All Containers

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "GitHub Token Status Check"
echo -e "==========================================${NC}"
echo ""

# Check orchestrator
echo -e "${YELLOW}Orchestrator (Container 200):${NC}"
ORCH_TOKEN=$(pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && grep GITHUB_TOKEN .env 2>/dev/null | cut -d'=' -f2" 2>/dev/null || echo "NOT_FOUND")

if [ "$ORCH_TOKEN" = "NOT_FOUND" ]; then
    echo -e "  ${RED}❌ No GITHUB_TOKEN in .env${NC}"
elif [ -z "$ORCH_TOKEN" ]; then
    echo -e "  ${RED}❌ GITHUB_TOKEN is empty${NC}"
else
    echo -e "  ${GREEN}✅ Token found: ${ORCH_TOKEN:0:10}...${ORCH_TOKEN: -4}${NC}"

    # Test token
    if curl -s -H "Authorization: token $ORCH_TOKEN" https://api.github.com/user | grep -q "login"; then
        USERNAME=$(curl -s -H "Authorization: token $ORCH_TOKEN" https://api.github.com/user | grep -o '"login":"[^"]*"' | cut -d'"' -f4)
        echo -e "  ${GREEN}✅ Token is valid (user: $USERNAME)${NC}"

        # Check scopes
        SCOPES=$(curl -s -I -H "Authorization: token $ORCH_TOKEN" https://api.github.com/user 2>/dev/null | grep -i "x-oauth-scopes:" | cut -d' ' -f2- | tr -d '\r\n')
        echo -e "  📋 Scopes: $SCOPES"

        if [[ "$SCOPES" == *"repo"* ]]; then
            echo -e "  ${GREEN}✅ Has 'repo' scope${NC}"
        else
            echo -e "  ${RED}❌ Missing 'repo' scope${NC}"
        fi
    else
        echo -e "  ${RED}❌ Token is invalid or expired${NC}"
    fi
fi
echo ""

# Check workers
for id in 201 202 203 204 205; do
    echo -e "${YELLOW}Worker $id (Container $id):${NC}"

    # Check .env
    ENV_TOKEN=$(pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && grep GITHUB_TOKEN .env 2>/dev/null | cut -d'=' -f2" 2>/dev/null || echo "NOT_FOUND")

    if [ "$ENV_TOKEN" = "NOT_FOUND" ]; then
        echo -e "  .env: ${RED}❌ Not found${NC}"
    elif [ -z "$ENV_TOKEN" ]; then
        echo -e "  .env: ${RED}❌ Empty${NC}"
    else
        echo -e "  .env: ${GREEN}✅ ${ENV_TOKEN:0:10}...${ENV_TOKEN: -4}${NC}"
    fi

    # Check systemd service
    SERVICE_TOKEN=$(pct exec $id -- grep "Environment=GITHUB_TOKEN=" /etc/systemd/system/ai-worker.service 2>/dev/null | cut -d'=' -f3 || echo "NOT_FOUND")

    if [ "$SERVICE_TOKEN" = "NOT_FOUND" ]; then
        echo -e "  systemd: ${RED}❌ Not found${NC}"
    elif [ -z "$SERVICE_TOKEN" ]; then
        echo -e "  systemd: ${RED}❌ Empty${NC}"
    else
        echo -e "  systemd: ${GREEN}✅ ${SERVICE_TOKEN:0:10}...${SERVICE_TOKEN: -4}${NC}"
    fi

    # Check if service is running
    if pct exec $id -- systemctl is-active ai-worker >/dev/null 2>&1; then
        echo -e "  Status: ${GREEN}✅ Running${NC}"
    else
        echo -e "  Status: ${RED}❌ Not running${NC}"
    fi

    echo ""
done

echo -e "${BLUE}=========================================="
echo "Summary"
echo -e "==========================================${NC}"
echo ""

if [ "$ORCH_TOKEN" != "NOT_FOUND" ] && [ -n "$ORCH_TOKEN" ]; then
    echo -e "${GREEN}✅ Orchestrator has token${NC}"
else
    echo -e "${RED}❌ Orchestrator missing token${NC}"
fi

WORKERS_OK=0
for id in 201 202 203 204 205; do
    ENV_TOKEN=$(pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && grep GITHUB_TOKEN .env 2>/dev/null | cut -d'=' -f2" 2>/dev/null || echo "NOT_FOUND")
    if [ "$ENV_TOKEN" != "NOT_FOUND" ] && [ -n "$ENV_TOKEN" ]; then
        ((WORKERS_OK++))
    fi
done

echo -e "${GREEN}✅ $WORKERS_OK/5 workers have tokens${NC}"

if [ $WORKERS_OK -eq 5 ]; then
    echo ""
    echo -e "${GREEN}All systems have tokens configured!${NC}"
else
    echo ""
    echo -e "${RED}Some systems are missing tokens!${NC}"
    echo ""
    echo "Fix with:"
    echo "  ./fix_github_tokens.sh YOUR_GITHUB_TOKEN"
fi
echo ""
