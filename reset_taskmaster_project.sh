#!/bin/bash
# Reset TaskMaster App Project - Start Fresh with Proper Phase Order

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "Reset TaskMaster App Project"
echo -e "==========================================${NC}"
echo ""

REPO="SimmoRice/taskmaster-app"

echo -e "${YELLOW}This will:${NC}"
echo "1. Stop all workers immediately"
echo "2. Reset all issues from ai-in-progress to ai-ready"
echo "3. Add phase labels to enforce order"
echo "4. Remove ai-ready from Phase 2-4 issues"
echo "5. Keep only Phase 1 issues (1-5) as ai-ready"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Step 1: Stop all workers on Proxmox (if you have SSH access)
echo -e "${YELLOW}Step 1: Stopping all workers...${NC}"
if command -v ssh &> /dev/null; then
    read -p "Enter Proxmox host IP (or press Enter to skip): " PROXMOX_HOST
    if [ -n "$PROXMOX_HOST" ]; then
        echo "Stopping workers on $PROXMOX_HOST..."
        ssh root@$PROXMOX_HOST "
            for id in 201 202 203 204 205; do
                pct exec \$id -- systemctl stop ai-worker
            done
            echo 'All workers stopped'
        "
        echo -e "${GREEN}✅ Workers stopped${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping worker stop - do this manually on Proxmox${NC}"
        echo "   Run: for id in 201 202 203 204 205; do pct exec \$id -- systemctl stop ai-worker; done"
    fi
else
    echo -e "${YELLOW}⚠️  SSH not available - stop workers manually on Proxmox${NC}"
fi
echo ""

# Step 2: Reset all issues from ai-in-progress to ai-ready
echo -e "${YELLOW}Step 2: Resetting all issues to ai-ready...${NC}"
gh issue list --repo $REPO --label ai-in-progress --json number --jq '.[].number' | while read num; do
    echo "  Resetting issue #$num..."
    gh issue edit $num --repo $REPO \
        --remove-label ai-in-progress \
        --add-label ai-ready
done
echo -e "${GREEN}✅ All issues reset to ai-ready${NC}"
echo ""

# Step 3: Add phase labels
echo -e "${YELLOW}Step 3: Adding phase labels...${NC}"

# Phase 1: Foundation & Backend (Issues 1-5)
echo "  Phase 1: Foundation (issues 1-5)..."
for num in 1 2 3 4 5; do
    gh issue edit $num --repo $REPO --add-label "phase:1-foundation" --add-label "priority:high"
done

# Phase 2: Frontend Core (Issues 6-9)
echo "  Phase 2: Frontend (issues 6-9)..."
for num in 6 7 8 9; do
    gh issue edit $num --repo $REPO --add-label "phase:2-frontend" --add-label "priority:medium"
done

# Phase 3: Advanced Features (Issues 10-15)
echo "  Phase 3: Features (issues 10-15)..."
for num in 10 11 12 13 14 15; do
    gh issue edit $num --repo $REPO --add-label "phase:3-features" --add-label "priority:medium"
done

# Phase 4: Polish & Testing (Issues 16-20)
echo "  Phase 4: Polish (issues 16-20)..."
for num in 16 17 18 19 20; do
    gh issue edit $num --repo $REPO --add-label "phase:4-polish" --add-label "priority:low"
done

echo -e "${GREEN}✅ Phase labels added${NC}"
echo ""

# Step 4: Remove ai-ready from Phase 2-4, keep only Phase 1
echo -e "${YELLOW}Step 4: Setting only Phase 1 as ai-ready...${NC}"
for num in 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
    echo "  Removing ai-ready from issue #$num..."
    gh issue edit $num --repo $REPO --remove-label ai-ready
done
echo -e "${GREEN}✅ Only Phase 1 issues are ai-ready${NC}"
echo ""

# Step 5: Summary
echo -e "${BLUE}=========================================="
echo "Reset Complete!"
echo -e "==========================================${NC}"
echo ""
echo -e "${GREEN}Current state:${NC}"
echo "  Phase 1 (Issues 1-5):  ai-ready + phase:1-foundation + priority:high"
echo "  Phase 2 (Issues 6-9):  phase:2-frontend + priority:medium (NOT ai-ready)"
echo "  Phase 3 (Issues 10-15): phase:3-features + priority:medium (NOT ai-ready)"
echo "  Phase 4 (Issues 16-20): phase:4-polish + priority:low (NOT ai-ready)"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Check issues on GitHub:"
echo "   gh issue list --repo $REPO --label ai-ready"
echo "   (Should show only issues 1-5)"
echo ""
echo "2. Restart workers on Proxmox:"
echo "   for id in 201 202 203 204 205; do"
echo "     pct exec \$id -- systemctl start ai-worker"
echo "   done"
echo ""
echo "3. Monitor progress:"
echo "   pct exec 201 -- journalctl -u ai-worker -f"
echo ""
echo "4. After Phase 1 PRs are merged, enable Phase 2:"
echo "   for num in 6 7 8 9; do"
echo "     gh issue edit \$num --repo $REPO --add-label ai-ready"
echo "   done"
echo ""
echo -e "${GREEN}Workers will now work on Phase 1 first! 🚀${NC}"
echo ""
