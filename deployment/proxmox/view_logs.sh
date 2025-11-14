#!/bin/bash
# view_logs.sh - View logs from containers
#
# Usage:
#   ./view_logs.sh              # Interactive menu
#   ./view_logs.sh orchestrator # View orchestrator logs
#   ./view_logs.sh worker1      # View worker 1 logs
#   ./view_logs.sh all          # View all logs

BLUE='\033[0;34m'
NC='\033[0m'

show_menu() {
    echo "=========================================="
    echo "AI Scrum Master - Log Viewer"
    echo "=========================================="
    echo ""
    echo "Select logs to view:"
    echo "  1) Orchestrator (live)"
    echo "  2) Worker 1 (live)"
    echo "  3) Worker 2 (live)"
    echo "  4) Worker 3 (live)"
    echo "  5) Worker 4 (live)"
    echo "  6) Worker 5 (live)"
    echo "  7) All workers (last 50 lines each)"
    echo "  8) Orchestrator (last 100 lines)"
    echo "  9) Exit"
    echo ""
    read -p "Enter choice [1-9]: " choice

    case $choice in
        1) pct exec 200 -- journalctl -u ai-orchestrator -f ;;
        2) pct exec 201 -- journalctl -u ai-worker -f ;;
        3) pct exec 202 -- journalctl -u ai-worker -f ;;
        4) pct exec 203 -- journalctl -u ai-worker -f ;;
        5) pct exec 204 -- journalctl -u ai-worker -f ;;
        6) pct exec 205 -- journalctl -u ai-worker -f ;;
        7) view_all_workers ;;
        8) pct exec 200 -- journalctl -u ai-orchestrator -n 100 --no-pager ;;
        9) exit 0 ;;
        *) echo "Invalid choice"; sleep 1; show_menu ;;
    esac
}

view_all_workers() {
    echo ""
    for id in {201..205}; do
        worker_num=$((id - 200))
        echo -e "${BLUE}=== Worker $worker_num (Container $id) ===${NC}"
        pct exec $id -- journalctl -u ai-worker -n 50 --no-pager | tail -20
        echo ""
    done
    echo "Press Enter to continue..."
    read
    show_menu
}

# Handle command line arguments
if [ "$1" = "orchestrator" ]; then
    pct exec 200 -- journalctl -u ai-orchestrator -f
elif [ "$1" = "worker1" ]; then
    pct exec 201 -- journalctl -u ai-worker -f
elif [ "$1" = "worker2" ]; then
    pct exec 202 -- journalctl -u ai-worker -f
elif [ "$1" = "worker3" ]; then
    pct exec 203 -- journalctl -u ai-worker -f
elif [ "$1" = "worker4" ]; then
    pct exec 204 -- journalctl -u ai-worker -f
elif [ "$1" = "worker5" ]; then
    pct exec 205 -- journalctl -u ai-worker -f
elif [ "$1" = "all" ]; then
    view_all_workers
else
    show_menu
fi
