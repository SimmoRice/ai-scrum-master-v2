#!/bin/bash
# Check if Claude Code CLI is installed on all workers

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Checking Claude Code CLI on all workers...${NC}"
echo ""

for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    echo -e "${YELLOW}Worker $worker_num (Container $id):${NC}"

    # Check if claude command exists
    if pct exec $id -- su - aimaster -c "which claude" >/dev/null 2>&1; then
        claude_path=$(pct exec $id -- su - aimaster -c "which claude")
        claude_version=$(pct exec $id -- su - aimaster -c "claude --version" 2>&1 || echo "Error getting version")
        echo -e "  ${GREEN}✅ Claude CLI found: $claude_path${NC}"
        echo -e "  ${GREEN}   Version: $claude_version${NC}"
    else
        echo -e "  ${RED}❌ Claude CLI NOT FOUND${NC}"
    fi

    # Check PATH
    path_value=$(pct exec $id -- su - aimaster -c "echo \$PATH")
    echo -e "  PATH: $path_value"

    # Check if running from correct directory works
    echo -n "  Testing claude from workspace: "
    if pct exec $id -- su - aimaster -c "cd /opt/ai-scrum-master/workspace && claude --version" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Works${NC}"
    else
        echo -e "${RED}❌ Fails${NC}"
    fi

    echo ""
done

echo -e "${YELLOW}Done!${NC}"
