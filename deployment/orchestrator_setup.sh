#!/bin/bash
#
# Orchestrator Container Setup Script
#
# This script sets up the orchestrator service that manages worker containers
#

set -e

echo "================================================"
echo "AI Scrum Master Orchestrator - Setup"
echo "================================================"

# Configuration
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable not set"
    exit 1
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "WARNING: GITHUB_TOKEN not set - GitHub integration will be disabled"
fi

# Update system
echo ""
echo "[1/10] Updating system packages..."
apt-get update
apt-get upgrade -y

# Install dependencies
echo ""
echo "[2/10] Installing dependencies..."
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
    supervisor \
    nginx

# Install GitHub CLI
echo ""
echo "[3/10] Installing GitHub CLI..."
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
apt-get update
apt-get install -y gh

# Install Claude Code CLI (not needed on orchestrator, but useful for testing)
echo ""
echo "[4/10] Installing Claude Code CLI..."
npm install -g @anthropic-ai/claude-code

# Create working directory
echo ""
echo "[5/10] Setting up working directory..."
mkdir -p /opt/ai-scrum-master
cd /opt/ai-scrum-master

# Clone AI Scrum Master repository
echo ""
echo "[6/10] Cloning AI Scrum Master repository..."
if [ ! -d ".git" ]; then
    git clone https://github.com/YOUR_ORG/ai-scrum-master-v2.git .
else
    echo "Repository already cloned, pulling latest..."
    git pull
fi

# Setup Python environment
echo ""
echo "[7/10] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install orchestrator dependencies
pip install -r requirements.txt
pip install fastapi uvicorn python-multipart aiofiles psutil

# Create environment file
echo ""
echo "[8/10] Creating environment configuration..."
cat > .env << EOF
# Orchestrator Configuration
MODE=orchestrator
ORCHESTRATOR_HOST=0.0.0.0
ORCHESTRATOR_PORT=8000

# API Keys
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
GITHUB_TOKEN=${GITHUB_TOKEN}

# Worker Configuration
WORKER_IPS=10.0.0.11,10.0.0.12,10.0.0.13,10.0.0.14,10.0.0.15
WORKER_SSH_KEY=/root/.ssh/id_orchestrator
WORKER_SSH_USER=root

# GitHub Configuration
GITHUB_REPO=YOUR_ORG/YOUR_REPO
GITHUB_ISSUE_LABELS=ai-ready
GITHUB_POLL_INTERVAL=60

# Database
DATABASE_PATH=/opt/ai-scrum-master/orchestrator.db

# Logging
LOG_DIR=/opt/ai-scrum-master/logs
LOG_LEVEL=INFO
EOF

# Create directories
mkdir -p logs data

# Setup systemd service
echo ""
echo "[9/10] Creating systemd service..."
# Copy systemd service file
cp /opt/ai-scrum-master/deployment/systemd/ai-scrum-orchestrator.service /etc/systemd/system/
chmod 644 /etc/systemd/system/ai-scrum-orchestrator.service

# Setup nginx reverse proxy
echo ""
echo "[10/10] Configuring nginx..."
# Copy nginx configuration
cp /opt/ai-scrum-master/deployment/nginx/orchestrator.conf /etc/nginx/sites-available/orchestrator
ln -sf /etc/nginx/sites-available/orchestrator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

# Enable services
systemctl daemon-reload
systemctl enable ai-scrum-orchestrator
systemctl enable nginx
systemctl enable ssh

# Setup GitHub CLI authentication
if [ -n "$GITHUB_TOKEN" ]; then
    echo "$GITHUB_TOKEN" | gh auth login --with-token
fi

echo ""
echo "================================================"
echo "Orchestrator Setup Complete!"
echo "================================================"
echo ""
echo "Orchestrator API: http://$(hostname -I | awk '{print $1}'):8000"
echo "Nginx Reverse Proxy: http://$(hostname -I | awk '{print $1}')"
echo "SSH Access: ssh root@$(hostname -I | awk '{print $1}')"
echo ""
echo "Next steps:"
echo "1. Generate SSH key: ssh-keygen -t ed25519 -f /root/.ssh/id_orchestrator"
echo "2. Add public key to worker containers"
echo "3. Start orchestrator: systemctl start ai-scrum-orchestrator"
echo "4. Check status: systemctl status ai-scrum-orchestrator"
echo "5. View logs: journalctl -u ai-scrum-orchestrator -f"
echo ""
