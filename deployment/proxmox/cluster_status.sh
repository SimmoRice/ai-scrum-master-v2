#!/bin/bash
# AI Scrum Master Cluster Status Dashboard
# Shows real-time status of orchestrator and all workers
# Auto-refreshes every 5 seconds (press Ctrl+C to exit)

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Refresh interval in seconds
REFRESH_INTERVAL=5

# Function to check service status
get_service_status() {
    local id=$1
    local service=$2

    if pct exec $id -- systemctl is-active --quiet $service 2>/dev/null; then
        echo -e "${GREEN}●${NC}"
    else
        echo -e "${RED}●${NC}"
    fi
}

# Function to get worker current task
get_worker_task() {
    local id=$1

    # Get last 50 lines and look for "Starting workflow for issue"
    local task=$(pct exec $id -- journalctl -u ai-worker -n 50 --no-pager 2>/dev/null | \
        grep "Starting workflow for issue" | \
        tail -1 | \
        sed -n 's/.*issue #\([0-9]*\): \(.*\)/Issue #\1: \2/p')

    if [ -z "$task" ]; then
        # Check if worker just completed something
        local completed=$(pct exec $id -- journalctl -u ai-worker -n 20 --no-pager 2>/dev/null | \
            grep "Issue #.* completed" | \
            tail -1 | \
            sed -n 's/.*Issue #\([0-9]*\) completed.*/Recently completed #\1/p')

        if [ -n "$completed" ]; then
            echo "$completed"
        else
            echo "Idle"
        fi
    else
        echo "$task"
    fi
}

# Function to display the dashboard
display_dashboard() {
    clear

    # Get current timestamp
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}        ${CYAN}${BOLD}AI Scrum Master Cluster Status Dashboard${NC}           ${BLUE}║${NC}"
    echo -e "${BLUE}║${NC}        ${NC}Last updated: $timestamp                      ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

# Orchestrator Status
echo -e "${YELLOW}━━━ Orchestrator (Container 200) ━━━${NC}"
orch_status=$(get_service_status 200 "ai-orchestrator")
echo -e "  Service: $orch_status ai-orchestrator"

# Get orchestrator info
if pct exec 200 -- systemctl is-active --quiet ai-orchestrator 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} Service running"

    # Get uptime
    uptime=$(pct exec 200 -- systemctl show ai-orchestrator -p ActiveEnterTimestamp --value 2>/dev/null | cut -d' ' -f1-2)
    echo -e "  Started: $uptime"

    # Get queue stats from API
    queue_json=$(curl -s http://192.168.100.200:8000/queue 2>/dev/null || echo '{}')
    pending=$(echo "$queue_json" | grep -o '"pending":\[[^]]*\]' | grep -o '#[0-9]*' | wc -l)
    in_progress=$(echo "$queue_json" | grep -o '"in_progress":\[[^]]*\]' | grep -o '#[0-9]*' | wc -l)
    completed=$(echo "$queue_json" | grep -o '"completed":\[[^]]*\]' | grep -o '#[0-9]*' | wc -l)

    echo -e "  Queue: ${YELLOW}${pending} pending${NC}, ${BLUE}${in_progress} in progress${NC}, ${GREEN}${completed} completed${NC}"
else
    echo -e "  ${RED}✗${NC} Service not running"
fi

echo ""

# Workers Status
echo -e "${YELLOW}━━━ Workers ━━━${NC}"
echo ""

for id in 201 202 203 204 205; do
    worker_num=$((id-200))
    worker_status=$(get_service_status $id "ai-worker")

    echo -e "${CYAN}Worker $worker_num${NC} (Container $id)"
    echo -e "  Service: $worker_status ai-worker"

    if pct exec $id -- systemctl is-active --quiet ai-worker 2>/dev/null; then
        task=$(get_worker_task $id)

        if [ "$task" = "Idle" ]; then
            echo -e "  Status: ${GREEN}Idle${NC} - waiting for work"
        elif [[ "$task" == "Recently completed"* ]]; then
            echo -e "  Status: ${GREEN}$task${NC}"
        else
            echo -e "  Status: ${BLUE}Working${NC}"
            echo -e "  Task: ${YELLOW}$task${NC}"
        fi
    else
        echo -e "  Status: ${RED}Service stopped${NC}"
    fi

    echo ""
done

# GitHub Status
echo -e "${YELLOW}━━━ GitHub Repository ━━━${NC}"
health_json=$(curl -s http://192.168.100.200:8000/health 2>/dev/null || echo '{}')
repo=$(echo "$health_json" | grep -o '"repositories":\[[^]]*\]' | sed 's/"repositories":\["\([^"]*\)".*/\1/')
if [ -n "$repo" ]; then
    echo -e "  Monitoring: ${CYAN}$repo${NC}"
else
    echo -e "  ${RED}Unable to fetch repository info${NC}"
fi

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to exit${NC} • Refreshing every ${REFRESH_INTERVAL}s"
    echo ""
    echo "Commands:"
    echo "  • Full queue details:    curl http://192.168.100.200:8000/queue | jq"
    echo "  • Health check:          curl http://192.168.100.200:8000/health | jq"
    echo "  • Monitor orchestrator:  pct exec 200 -- journalctl -u ai-orchestrator -f"
    echo "  • Monitor worker 1:      pct exec 201 -- journalctl -u ai-worker -f"
    echo ""
}

# Trap Ctrl+C to exit cleanly
trap 'echo -e "\n${GREEN}Dashboard stopped.${NC}"; exit 0' INT

# Main loop
while true; do
    display_dashboard
    sleep $REFRESH_INTERVAL
done
