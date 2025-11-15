#!/bin/bash
# Check Git Status on All Containers
# Diagnoses why updates might not be pulling new files

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=========================================="
echo "Git Status Check - All Containers"
echo -e "==========================================${NC}"
echo ""

check_container() {
    local id=$1
    local name=$2

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$name (Container $id)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Check if repository exists
    if ! pct exec $id -- su - aimaster -c "test -d ai-scrum-master-v2/.git"; then
        echo -e "${RED}❌ Repository not found${NC}"
        echo ""
        return
    fi

    # Get current branch
    branch=$(pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git branch --show-current" 2>/dev/null || echo "unknown")
    echo "  Branch: $branch"

    # Get current commit
    commit=$(pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git rev-parse --short HEAD" 2>/dev/null || echo "unknown")
    echo "  Commit: $commit"

    # Get commit message
    msg=$(pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git log -1 --pretty=%B" 2>/dev/null | head -1 || echo "unknown")
    echo "  Message: $msg"
    echo ""

    # Check for uncommitted changes
    status=$(pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git status --porcelain" 2>/dev/null || echo "")
    if [ -n "$status" ]; then
        echo -e "${YELLOW}  ⚠️  Uncommitted changes:${NC}"
        echo "$status" | head -5
        echo ""
    else
        echo -e "${GREEN}  ✅ No uncommitted changes${NC}"
        echo ""
    fi

    # Check if behind remote
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git fetch origin" 2>/dev/null || true
    behind=$(pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git rev-list --count HEAD..origin/main" 2>/dev/null || echo "0")
    ahead=$(pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git rev-list --count origin/main..HEAD" 2>/dev/null || echo "0")

    if [ "$behind" -gt 0 ]; then
        echo -e "${YELLOW}  ⚠️  Behind origin/main by $behind commit(s)${NC}"
    elif [ "$ahead" -gt 0 ]; then
        echo -e "${YELLOW}  ⚠️  Ahead of origin/main by $ahead commit(s)${NC}"
    else
        echo -e "${GREEN}  ✅ Up to date with origin/main${NC}"
    fi

    # Check if distributed_worker.py has the fix
    if pct exec $id -- su - aimaster -c "grep -q 'Create the feature branch from current branch' ai-scrum-master-v2/worker/distributed_worker.py 2>/dev/null"; then
        echo -e "${GREEN}  ✅ Has latest git push fix${NC}"
    else
        echo -e "${RED}  ❌ Missing git push fix${NC}"
    fi

    echo ""
}

# Check Orchestrator
check_container 200 "Orchestrator"

# Check Workers
for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    check_container $id "Worker $worker_num"
done

echo -e "${BLUE}=========================================="
echo "Summary"
echo -e "==========================================${NC}"
echo ""
echo "Latest commit on GitHub main:"
echo "  Commit: 67fbf5f"
echo "  Message: Fix: Create feature branch before git push"
echo ""
echo "If containers are behind, run:"
echo "  ./deployment/proxmox/update_cluster.sh"
echo ""
echo "If containers have uncommitted changes, run:"
echo "  ./deployment/proxmox/update_cluster.sh --hard-reset"
echo ""
