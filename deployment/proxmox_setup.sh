#!/bin/bash
#
# Proxmox LXC Container Setup Script for AI Scrum Master Worker
#
# This script should be run INSIDE each LXC container after creation
#
# Usage:
#   1. Create LXC container in Proxmox (Ubuntu 22.04 template)
#   2. Copy this script to the container
#   3. Run: chmod +x proxmox_setup.sh && ./proxmox_setup.sh
#

set -e  # Exit on any error

echo "================================================"
echo "AI Scrum Master Worker - Container Setup"
echo "================================================"

# Configuration
WORKER_ID="${WORKER_ID:-worker-$(hostname)}"
ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-http://orchestrator.lab.int.as152738.net:8000}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"

echo "Worker ID: $WORKER_ID"
echo "Orchestrator URL: $ORCHESTRATOR_URL"

# Update system
echo ""
echo "[1/8] Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo ""
echo "[2/8] Installing dependencies..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    nodejs \
    npm \
    build-essential \
    sqlite3 \
    openssh-server \
    supervisor

# Install Claude Code CLI
echo ""
echo "[3/8] Installing Claude Code CLI..."
npm install -g @anthropic-ai/claude-code

# Verify Claude Code installation
if ! command -v claude &> /dev/null; then
    echo "ERROR: Claude Code installation failed"
    exit 1
fi
echo "Claude Code version: $(claude --version)"

# Create working directory
echo ""
echo "[4/8] Setting up working directory..."
mkdir -p /opt/ai-scrum-master
cd /opt/ai-scrum-master

# Clone AI Scrum Master repository
echo ""
echo "[5/8] Cloning AI Scrum Master repository..."
if [ ! -d ".git" ]; then
    git clone https://github.com/YOUR_ORG/ai-scrum-master-v2.git .
else
    echo "Repository already cloned, pulling latest..."
    git pull
fi

# Setup Python environment
echo ""
echo "[6/8] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file
echo ""
echo "[7/8] Creating environment configuration..."
cat > .env << EOF
# Worker Configuration
WORKER_ID=${WORKER_ID}
ORCHESTRATOR_URL=${ORCHESTRATOR_URL}

# API Keys
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
GITHUB_TOKEN=${GITHUB_TOKEN}

# Worker Settings
WORKER_MODE=distributed
WORKSPACE_DIR=/opt/ai-scrum-master/workspace
LOG_DIR=/opt/ai-scrum-master/logs
EOF

# Create workspace directories
mkdir -p workspace logs

# Install GitHub CLI
echo ""
echo "[8/10] Installing GitHub CLI..."
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
apt-get update
apt-get install -y gh

# Setup systemd service
echo ""
echo "[9/10] Creating systemd service..."
# Copy systemd service file
cp /opt/ai-scrum-master/deployment/systemd/ai-scrum-worker.service /etc/systemd/system/
chmod 644 /etc/systemd/system/ai-scrum-worker.service

# Enable worker service
systemctl daemon-reload
systemctl enable ai-scrum-worker

# Setup SSH access for orchestrator
echo ""
echo "[10/10] Configuring SSH access..."
mkdir -p /root/.ssh
chmod 700 /root/.ssh

# Enable SSH service
systemctl enable ssh
systemctl start ssh

echo ""
echo "================================================"
echo "Setup Complete!"
echo "================================================"
echo ""
echo "Worker ID: $WORKER_ID"
echo "SSH Port: 22"
echo "Container IP: $(hostname -I | awk '{print $1}')"
echo ""
echo "Next steps:"
echo "1. Add orchestrator SSH public key to /root/.ssh/authorized_keys"
echo "2. Start worker service: systemctl start ai-scrum-worker"
echo "3. Check logs: journalctl -u ai-scrum-worker -f"
echo ""
