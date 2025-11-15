#!/bin/bash
# Fetch workflow log from a worker

WORKER_ID="${1:-201}"
LOG_FILE="${2}"

if [ -z "$LOG_FILE" ]; then
    echo "Usage: $0 <worker_id> <log_file>"
    echo "Example: $0 201 workflow_20251115_123711.log"
    exit 1
fi

echo "Fetching log from Worker $((WORKER_ID-200)) (Container $WORKER_ID)..."
echo ""

pct exec $WORKER_ID -- su - aimaster -c "cat ai-scrum-master-v2/logs/$LOG_FILE"
