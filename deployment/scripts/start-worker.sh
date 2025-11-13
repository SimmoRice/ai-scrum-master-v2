#!/bin/bash
set -e

echo "Starting AI Scrum Master Worker..."

# Activate virtual environment
source /opt/ai-scrum-master/venv/bin/activate

# Authenticate GitHub CLI if token provided
if [ -n "$GITHUB_TOKEN" ]; then
    echo "$GITHUB_TOKEN" | gh auth login --with-token
fi

# Start SSH daemon in background
/usr/sbin/sshd

echo "Worker ID: $WORKER_ID"
echo "Orchestrator URL: $ORCHESTRATOR_URL"
echo "Workspace: $WORKSPACE_DIR"
echo ""

# Start worker process
echo "Starting distributed worker..."
exec python /opt/ai-scrum-master/worker/distributed_worker.py
