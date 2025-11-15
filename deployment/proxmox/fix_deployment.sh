#!/bin/bash
# Fix Deployment Issues for Queue Blocking System
# Run this on your Proxmox host after exiting Python

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "Fixing AI Scrum Master Deployment"
echo -e "==========================================${NC}"
echo ""

# Step 1: Fix workspace configuration on all workers
echo -e "${YELLOW}Step 1: Fixing workspace directory on workers...${NC}"
for id in 201 202 203 204 205; do
    echo "Fixing worker container $id..."
    pct exec $id -- su - aimaster -c "
        cd ai-scrum-master-v2
        sed -i '/^WORKSPACE_DIR=/d' .env
        echo 'WORKSPACE_DIR=/opt/ai-scrum-master/workspace' >> .env
    "
done
echo -e "${GREEN}✅ Workspace directories fixed${NC}"
echo ""

# Step 2: Update GitHub token on orchestrator
echo -e "${YELLOW}Step 2: Updating GitHub token on orchestrator...${NC}"
echo -e "${RED}You need to create a new GitHub token with full 'repo' scope${NC}"
echo ""
echo "Visit: https://github.com/settings/tokens/new"
echo ""
echo "Required settings:"
echo "  - Description: AI Scrum Master Proxmox Cluster"
echo "  - Expiration: Choose your preference (90 days recommended)"
echo "  - Select scopes: CHECK 'repo' (full control)"
echo ""
read -p "Have you created the token? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    read -p "Enter your new GitHub token (ghp_...): " GITHUB_TOKEN

    pct exec 200 -- su - aimaster -c "
        cd ai-scrum-master-v2
        sed -i '/^GITHUB_TOKEN=/d' .env
        echo 'GITHUB_TOKEN=$GITHUB_TOKEN' >> .env
    "
    echo -e "${GREEN}✅ GitHub token updated${NC}"
else
    echo -e "${RED}Skipping GitHub token update${NC}"
fi
echo ""

# Step 3: Configure multi-repo mode
echo -e "${YELLOW}Step 3: Configuring multi-repo mode...${NC}"
pct exec 200 -- su - aimaster -c "
    cd ai-scrum-master-v2
    sed -i '/^GITHUB_REPOS=/d' .env
    echo 'GITHUB_REPOS=SimmoRice/ai-scrum-master-v2,SimmoRice/taskmaster-app' >> .env
    sed -i '/^GITHUB_REPO=/d' .env
"
echo -e "${GREEN}✅ Multi-repo mode configured${NC}"
echo ""

# Step 4: Restart all services
echo -e "${YELLOW}Step 4: Restarting services...${NC}"

# Restart orchestrator
echo "Restarting orchestrator..."
pct exec 200 -- systemctl restart ai-orchestrator
sleep 5

# Restart workers
for id in 201 202 203 204 205; do
    echo "Restarting worker $id..."
    pct exec $id -- systemctl restart ai-worker
done
sleep 10

echo -e "${GREEN}✅ All services restarted${NC}"
echo ""

# Step 5: Verify deployment
echo -e "${YELLOW}Step 5: Verifying deployment...${NC}"
echo ""

echo "Checking orchestrator health..."
curl -s http://192.168.100.200:8000/health | jq '.'
echo ""

echo "Checking PR review tracker..."
curl -s http://192.168.100.200:8000/pr-review/status | jq '.'
echo ""

echo "Checking worker registration..."
curl -s http://192.168.100.200:8000/workers | jq '.workers | length'
echo ""

echo -e "${GREEN}=========================================="
echo "Deployment Fix Complete!"
echo -e "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Monitor orchestrator logs: cd /root/ai-scrum-master-v2/deployment/proxmox && ./view_logs.sh orchestrator"
echo "2. Monitor worker logs: ./view_logs.sh worker1"
echo "3. Check queue status: watch -n 5 'curl -s http://192.168.100.200:8000/health | jq \".pr_review\"'"
echo ""
