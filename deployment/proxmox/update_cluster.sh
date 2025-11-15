#!/bin/bash
# Complete Cluster Update Script
# Updates code and installs dependencies on orchestrator and all workers
#
# Options:
#   --no-restart    Don't restart services (for manual restart later)
#   --hard-reset    Use git reset --hard (discards local changes)

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse arguments
NO_RESTART=false
HARD_RESET=false

for arg in "$@"; do
    case $arg in
        --no-restart)
            NO_RESTART=true
            ;;
        --hard-reset)
            HARD_RESET=true
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --no-restart    Don't restart services after update"
            echo "  --hard-reset    Use git reset --hard (discards local changes)"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}=========================================="
echo "AI Scrum Master Cluster Update"
echo -e "==========================================${NC}"
echo ""

if [ "$HARD_RESET" = true ]; then
    echo -e "${YELLOW}⚠️  Hard reset enabled - local changes will be discarded${NC}"
    echo ""
fi

if [ "$NO_RESTART" = true ]; then
    echo -e "${YELLOW}ℹ️  Services will NOT be restarted automatically${NC}"
    echo ""
fi

# Function to update a container
update_container() {
    local id=$1
    local name=$2
    local service_name=$3

    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Updating $name (Container $id)${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Stop service first
    echo "  Stopping $service_name service..."
    pct exec $id -- systemctl stop $service_name 2>/dev/null || true

    # Update repository
    echo "  Pulling latest code..."
    if [ "$HARD_RESET" = true ]; then
        pct exec $id -- su - aimaster -c "
            cd ai-scrum-master-v2
            git fetch origin
            git reset --hard origin/main
            git pull origin main
        " || {
            echo -e "${RED}❌ Failed to update repository on container $id${NC}"
            return 1
        }
    else
        pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git pull origin main" || {
            echo -e "${RED}❌ Failed to update repository on container $id${NC}"
            return 1
        }
    fi

    # Install dependencies
    echo "  Installing dependencies..."

    if [ "$name" = "Orchestrator" ]; then
        # Orchestrator has additional requirements
        pct exec $id -- su - aimaster -c "
            cd ai-scrum-master-v2
            env/bin/pip install --upgrade pip
            env/bin/pip install -r requirements.txt
            if [ -f orchestrator_service/requirements.txt ]; then
                env/bin/pip install -r orchestrator_service/requirements.txt
            fi
        " || {
            echo -e "${RED}❌ Failed to install dependencies on container $id${NC}"
            return 1
        }
    else
        # Worker dependencies
        pct exec $id -- su - aimaster -c "
            cd ai-scrum-master-v2
            env/bin/pip install --upgrade pip
            env/bin/pip install -r requirements.txt
            if [ -f worker/requirements.txt ]; then
                env/bin/pip install -r worker/requirements.txt
            fi
        " || {
            echo -e "${RED}❌ Failed to install dependencies on container $id${NC}"
            return 1
        }
    fi

    # Restart service (if not disabled)
    if [ "$NO_RESTART" = false ]; then
        echo "  Restarting $service_name service..."
        pct exec $id -- systemctl restart $service_name

        # Wait a moment for service to start
        sleep 2

        # Check if service started successfully
        if pct exec $id -- systemctl is-active --quiet $service_name; then
            echo -e "${GREEN}  ✅ $name updated and restarted${NC}"
        else
            echo -e "${YELLOW}  ⚠️  $name updated but service may have issues${NC}"
        fi
    else
        echo -e "${GREEN}  ✅ $name updated (service not restarted)${NC}"
    fi

    echo ""
}

# Update Orchestrator
echo -e "${YELLOW}Step 1: Updating Orchestrator${NC}"
echo ""
update_container 200 "Orchestrator" "ai-orchestrator"

# Update Workers
echo -e "${YELLOW}Step 2: Updating Workers${NC}"
echo ""

for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    update_container $id "Worker $worker_num" "ai-worker"
done

# Verify All Services (if services were restarted)
if [ "$NO_RESTART" = false ]; then
    echo -e "${YELLOW}Step 3: Verifying Services${NC}"
    echo ""

    echo "Orchestrator:"
    pct exec 200 -- systemctl status ai-orchestrator --no-pager | head -3
    echo ""

    for id in 201 202 203 204 205; do
        worker_num=$((id-200))
        echo "Worker $worker_num:"
        pct exec $id -- systemctl status ai-worker --no-pager | head -3
        echo ""
    done

    # Check for errors
    echo -e "${YELLOW}Step 4: Checking for Recent Errors${NC}"
    echo ""

    echo "Checking orchestrator logs..."
    orch_errors=$(pct exec 200 -- journalctl -u ai-orchestrator --since "30 seconds ago" --no-pager | grep -i "error\|traceback\|failed" | wc -l)
    if [ "$orch_errors" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  Orchestrator: Found $orch_errors error(s) in last 30 seconds${NC}"
        pct exec 200 -- journalctl -u ai-orchestrator --since "30 seconds ago" --no-pager | grep -i "error\|traceback" | tail -5
        echo ""
    else
        echo -e "${GREEN}✅ Orchestrator: No errors${NC}"
    fi

    echo ""
    echo "Checking worker logs..."
    for id in 201 202 203 204 205; do
        worker_num=$((id-200))
        errors=$(pct exec $id -- journalctl -u ai-worker --since "30 seconds ago" --no-pager | grep -i "error\|traceback\|failed" | wc -l)

        if [ "$errors" -gt 0 ]; then
            echo -e "${YELLOW}⚠️  Worker $worker_num: Found $errors error(s) in last 30 seconds${NC}"
            pct exec $id -- journalctl -u ai-worker --since "30 seconds ago" --no-pager | grep -i "error\|traceback" | tail -5
            echo ""
        else
            echo -e "${GREEN}✅ Worker $worker_num: No errors${NC}"
        fi
    done
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Update Complete!"
echo -e "==========================================${NC}"
echo ""

if [ "$NO_RESTART" = false ]; then
    echo -e "${GREEN}✅ All services updated and restarted${NC}"
else
    echo -e "${YELLOW}⚠️  Services updated but NOT restarted${NC}"
    echo ""
    echo "To restart services, run:"
    echo "  deployment/proxmox/start_cluster.sh"
fi

echo ""
echo "Monitoring commands:"
echo "  • Monitor orchestrator: pct exec 200 -- journalctl -u ai-orchestrator -f"
echo "  • Monitor worker 1:     pct exec 201 -- journalctl -u ai-worker -f"
echo "  • Check queue status:   curl http://192.168.100.200:8000/queue"
echo "  • Check health:         curl http://192.168.100.200:8000/health"
echo ""
