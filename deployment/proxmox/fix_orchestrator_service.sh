#!/bin/bash
# fix_orchestrator_service.sh - Fix orchestrator systemd service
# Run this on Proxmox host to update the orchestrator service configuration

set -e

echo "Fixing orchestrator service configuration..."

# Stop the service
echo "Stopping orchestrator service..."
pct exec 200 -- systemctl stop ai-orchestrator 2>/dev/null || true

# Update the service file
echo "Updating service file..."
pct exec 200 -- bash -c 'cat > /etc/systemd/system/ai-orchestrator.service << '\''EOF'\''
[Unit]
Description=AI Scrum Master Orchestrator Service
After=network.target

[Service]
Type=simple
User=aimaster
WorkingDirectory=/home/aimaster/ai-scrum-master-v2
Environment="PATH=/home/aimaster/ai-scrum-master-v2/env/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=/home/aimaster/ai-scrum-master-v2"
Environment="VIRTUAL_ENV=/home/aimaster/ai-scrum-master-v2/env"
ExecStart=/home/aimaster/ai-scrum-master-v2/env/bin/python orchestrator_service/server.py
EnvironmentFile=/home/aimaster/ai-scrum-master-v2/.env
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF'

# Reload systemd
echo "Reloading systemd..."
pct exec 200 -- systemctl daemon-reload

# Install dependencies
echo "Installing orchestrator dependencies..."
pct exec 200 -- su - aimaster -c "cd ai-scrum-master-v2 && source env/bin/activate && pip install -r orchestrator_service/requirements.txt"

# Start the service
echo "Starting orchestrator service..."
pct exec 200 -- systemctl start ai-orchestrator

# Wait a moment
sleep 2

# Check status
echo ""
echo "Service status:"
pct exec 200 -- systemctl status ai-orchestrator --no-pager

echo ""
echo "Recent logs:"
pct exec 200 -- journalctl -u ai-orchestrator -n 20 --no-pager
