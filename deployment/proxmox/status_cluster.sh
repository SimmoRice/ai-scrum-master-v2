#!/bin/bash
# status_cluster.sh - Show status of all containers and services
#
# Usage: ./status_cluster.sh

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "AI Scrum Master Cluster Status"
echo "=========================================="
echo ""

# Check container status
echo -e "${BLUE}Container Status:${NC}"
echo "  ID  | Hostname           | IP Address      | Status   | CPU    | Memory"
echo "------|--------------------|-----------------|-----------|---------|---------"

for id in {200..205}; do
    if [ $id -eq 200 ]; then
        name="Orchestrator"
    else
        name="Worker $((id - 200))"
    fi

    ip="192.168.100.$id"

    # Get container status
    if pct status $id &> /dev/null; then
        status=$(pct status $id | awk '{print $2}')

        if [ "$status" = "running" ]; then
            # Get resource usage
            cpu=$(pct exec $id -- top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
            mem=$(pct exec $id -- free -h | awk '/^Mem:/ {print $3"/"$2}')

            status_color=$GREEN
        else
            cpu="-"
            mem="-"
            status_color=$RED
        fi
    else
        status="not found"
        cpu="-"
        mem="-"
        status_color=$RED
    fi

    printf "  %-3s | %-18s | %-15s | %b%-9s%b | %-7s | %s\n" \
        "$id" "$name" "$ip" "$status_color" "$status" "$NC" "$cpu%" "$mem"
done

# Check service status
echo ""
echo -e "${BLUE}Service Status:${NC}"

# Orchestrator service
if pct exec 200 -- systemctl is-active --quiet ai-orchestrator 2>/dev/null; then
    orch_status="${GREEN}active${NC}"
else
    orch_status="${RED}inactive${NC}"
fi
echo -e "  Orchestrator: $orch_status"

# Worker services
for id in {201..205}; do
    worker_num=$((id - 200))
    if pct exec $id -- systemctl is-active --quiet ai-worker 2>/dev/null; then
        worker_status="${GREEN}active${NC}"
    else
        worker_status="${RED}inactive${NC}"
    fi
    echo -e "  Worker $worker_num:    $worker_status"
done

# Check orchestrator health
echo ""
echo -e "${BLUE}Orchestrator Health:${NC}"
if pct exec 200 -- curl -s http://localhost:8000/health 2>/dev/null | grep -q "ok"; then
    echo -e "  API Status: ${GREEN}healthy${NC}"

    # Get worker registration
    registered=$(pct exec 200 -- curl -s http://localhost:8000/workers 2>/dev/null | grep -o "worker-" | wc -l || echo "0")
    echo "  Workers Registered: $registered / 5"
else
    echo -e "  API Status: ${RED}not responding${NC}"
fi

# Resource Summary
echo ""
echo -e "${BLUE}Resource Summary:${NC}"
total_cpu=0
total_mem=0
for id in {200..205}; do
    if pct status $id | grep -q "running"; then
        cpu=$(pct config $id | grep "cores:" | awk '{print $2}')
        mem=$(pct config $id | grep "memory:" | awk '{print $2}')
        total_cpu=$((total_cpu + cpu))
        total_mem=$((total_mem + mem))
    fi
done
echo "  Total CPU Cores: $total_cpu"
echo "  Total Memory: $((total_mem / 1024))GB"

echo ""
echo "Quick Commands:"
echo "  # Start all:    ./start_cluster.sh"
echo "  # Stop all:     ./stop_cluster.sh"
echo "  # View logs:    ./view_logs.sh"
echo "  # Restart all:  ./restart_cluster.sh"
echo ""
