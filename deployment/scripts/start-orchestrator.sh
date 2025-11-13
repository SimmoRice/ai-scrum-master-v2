#!/bin/bash
set -e

echo "Starting AI Scrum Master Orchestrator..."

# Activate virtual environment
source /opt/ai-scrum-master/venv/bin/activate

# Authenticate GitHub CLI if token provided
if [ -n "$GITHUB_TOKEN" ]; then
    echo "$GITHUB_TOKEN" | gh auth login --with-token
fi

# Start nginx in background
nginx

# Display SSH public key for worker configuration
echo ""
echo "=========================================="
echo "Orchestrator SSH Public Key:"
echo "=========================================="
cat /root/.ssh/id_orchestrator.pub
echo ""
echo "Add this key to worker containers' /root/.ssh/authorized_keys"
echo "=========================================="
echo ""

# Start orchestrator server
echo "Starting orchestrator API server on port 8000..."
exec python /opt/ai-scrum-master/orchestrator_service/server.py
