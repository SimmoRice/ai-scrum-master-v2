#!/bin/bash
# Fix GitHub Token Issues on Workers and Orchestrator

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "GitHub Token Fix for Proxmox Cluster"
echo -e "==========================================${NC}"
echo ""

# Check if token provided
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: GitHub token not provided${NC}"
    echo ""
    echo "Usage: ./fix_github_tokens.sh YOUR_GITHUB_TOKEN"
    echo ""
    echo "Generate a new token at: https://github.com/settings/tokens/new"
    echo ""
    echo "Required scopes:"
    echo "  ✓ repo (full control of private repositories)"
    echo ""
    echo "This gives access to:"
    echo "  - Clone repositories"
    echo "  - Push branches"
    echo "  - Create pull requests"
    echo "  - Manage issues and labels"
    exit 1
fi

GITHUB_TOKEN="$1"

echo -e "${YELLOW}Token received: ${GITHUB_TOKEN:0:10}...${NC}"
echo ""

# Validate token format
if [[ ! "$GITHUB_TOKEN" =~ ^(ghp_|github_pat_) ]]; then
    echo -e "${RED}WARNING: Token doesn't start with 'ghp_' or 'github_pat_'${NC}"
    echo "Are you sure this is a valid GitHub token?"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Test token on local machine first
echo -e "${YELLOW}Testing token on local machine...${NC}"
if curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -q "login"; then
    echo -e "${GREEN}✅ Token is valid${NC}"
    USERNAME=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -o '"login":"[^"]*"' | cut -d'"' -f4)
    echo -e "   Token belongs to: ${GREEN}$USERNAME${NC}"
else
    echo -e "${RED}❌ Token is invalid or expired${NC}"
    exit 1
fi
echo ""

# Check token scopes
echo -e "${YELLOW}Checking token scopes...${NC}"
SCOPES=$(curl -s -I -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | grep -i "x-oauth-scopes:" | cut -d' ' -f2-)
echo "   Scopes: $SCOPES"

if [[ "$SCOPES" == *"repo"* ]]; then
    echo -e "${GREEN}✅ Has 'repo' scope (full access)${NC}"
else
    echo -e "${RED}❌ Missing 'repo' scope${NC}"
    echo "   This token may not work for cloning/pushing to repositories"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Update orchestrator (container 200)
echo -e "${YELLOW}Updating orchestrator (container 200)...${NC}"
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    sed -i '/^GITHUB_TOKEN=/d' .env
    echo 'GITHUB_TOKEN=$GITHUB_TOKEN' >> .env
"

# Verify orchestrator token
echo "Verifying orchestrator token..."
ORCH_TOKEN=$(pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && grep GITHUB_TOKEN .env | cut -d'=' -f2")
if [ "$ORCH_TOKEN" = "$GITHUB_TOKEN" ]; then
    echo -e "${GREEN}✅ Orchestrator token updated${NC}"
else
    echo -e "${RED}❌ Orchestrator token mismatch${NC}"
    echo "   Expected: ${GITHUB_TOKEN:0:10}..."
    echo "   Got: ${ORCH_TOKEN:0:10}..."
fi
echo ""

# Update all workers (containers 201-205)
echo -e "${YELLOW}Updating workers (containers 201-205)...${NC}"
for id in 201 202 203 204 205; do
    echo "  Updating worker $id..."

    # Update .env file
    pct exec $id -- su - aimaster -c "
        cd ai-scrum-master-v2
        sed -i '/^GITHUB_TOKEN=/d' .env
        echo 'GITHUB_TOKEN=$GITHUB_TOKEN' >> .env
    "

    # Update systemd service file
    pct exec $id -- sed -i "s|Environment=GITHUB_TOKEN=.*|Environment=GITHUB_TOKEN=$GITHUB_TOKEN|" /etc/systemd/system/ai-worker.service

    # Verify
    WORKER_TOKEN=$(pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && grep GITHUB_TOKEN .env | cut -d'=' -f2")
    if [ "$WORKER_TOKEN" = "$GITHUB_TOKEN" ]; then
        echo -e "    ${GREEN}✅ Worker $id token updated${NC}"
    else
        echo -e "    ${RED}❌ Worker $id token mismatch${NC}"
    fi
done
echo ""

# Restart services to pick up new tokens
echo -e "${YELLOW}Restarting services...${NC}"

echo "  Restarting orchestrator..."
pct exec 200 -- systemctl daemon-reload
pct exec 200 -- systemctl restart ai-orchestrator
sleep 5

for id in 201 202 203 204 205; do
    echo "  Restarting worker $id..."
    pct exec $id -- systemctl daemon-reload
    pct exec $id -- systemctl restart ai-worker
    sleep 2
done
echo ""

# Verify services are running
echo -e "${YELLOW}Verifying services...${NC}"

echo "  Checking orchestrator..."
if pct exec 200 -- systemctl is-active ai-orchestrator >/dev/null 2>&1; then
    echo -e "    ${GREEN}✅ Orchestrator running${NC}"
else
    echo -e "    ${RED}❌ Orchestrator not running${NC}"
    pct exec 200 -- journalctl -u ai-orchestrator -n 20 --no-pager
fi

for id in 201 202 203 204 205; do
    echo "  Checking worker $id..."
    if pct exec $id -- systemctl is-active ai-worker >/dev/null 2>&1; then
        echo -e "    ${GREEN}✅ Worker $id running${NC}"
    else
        echo -e "    ${RED}❌ Worker $id not running${NC}"
    fi
done
echo ""

# Test GitHub access from a worker
echo -e "${YELLOW}Testing GitHub access from worker...${NC}"
echo "  Testing repository clone on worker 201..."

TEST_RESULT=$(pct exec 201 -- su - aimaster -c "
    cd /tmp
    rm -rf test-clone 2>/dev/null || true
    GIT_ASKPASS=true GIT_TERMINAL_PROMPT=0 git clone https://$GITHUB_TOKEN@github.com/SimmoRice/taskmaster-app.git test-clone 2>&1
    if [ -d test-clone/.git ]; then
        echo 'SUCCESS'
        rm -rf test-clone
    else
        echo 'FAILED'
    fi
" | tail -1)

if [ "$TEST_RESULT" = "SUCCESS" ]; then
    echo -e "${GREEN}✅ Worker can clone repositories${NC}"
else
    echo -e "${RED}❌ Worker cannot clone repositories${NC}"
    echo "   This may indicate token permissions issues"
fi
echo ""

echo -e "${GREEN}=========================================="
echo "GitHub Token Update Complete!"
echo -e "==========================================${NC}"
echo ""
echo "Summary:"
echo "  Token: ${GITHUB_TOKEN:0:10}...${GITHUB_TOKEN: -4}"
echo "  User: $USERNAME"
echo "  Scopes: $SCOPES"
echo ""
echo "Next steps:"
echo "1. Monitor logs: pct exec 200 -- journalctl -u ai-orchestrator -f"
echo "2. Check worker logs: pct exec 201 -- journalctl -u ai-worker -f"
echo "3. Reset failed issues to ai-ready"
echo ""
