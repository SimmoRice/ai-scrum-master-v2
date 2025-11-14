#!/bin/bash
# setup_containers.sh - Configure all LXC containers with AI Scrum Master
#
# Usage:
#   ./setup_containers.sh
#
# Prerequisites:
#   - Containers created with deploy_lxc_cluster.sh
#   - ANTHROPIC_API_KEY and GITHUB_TOKEN environment variables set

set -e

# Configuration
REPO_URL="${REPO_URL:-https://github.com/SimmoRice/ai-scrum-master-v2.git}"
ANTHROPIC_KEY="${ANTHROPIC_API_KEY}"
GITHUB_TOKEN="${GITHUB_TOKEN}"
ORCHESTRATOR_URL="http://192.168.100.200:8000"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "AI Scrum Master Container Setup"
echo "=========================================="
echo ""

# Check API keys
if [ -z "$ANTHROPIC_KEY" ]; then
    echo -e "${YELLOW}Warning: ANTHROPIC_API_KEY not set${NC}"
    echo "Please set it before running: export ANTHROPIC_API_KEY=your_key"
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}Warning: GITHUB_TOKEN not set${NC}"
    echo "Please set it before running: export GITHUB_TOKEN=your_token"
fi

# Function to setup a container
setup_container() {
    local id=$1
    local worker_id=$2
    local is_orchestrator=$3

    echo ""
    echo -e "${BLUE}Setting up container $id ($worker_id)...${NC}"

    # Check if container is running
    if ! pct status $id | grep -q "running"; then
        echo -e "${RED}Error: Container $id is not running${NC}"
        return 1
    fi

    # Install system dependencies
    echo "  Installing system dependencies..."
    pct exec $id -- bash -c "
        export DEBIAN_FRONTEND=noninteractive
        apt-get update
        apt-get upgrade -y
        apt-get install -y \
            python3.11 \
            python3-pip \
            python3-venv \
            git \
            curl \
            wget \
            build-essential \
            ca-certificates \
            gnupg
    " || {
        echo -e "${RED}Failed to install system dependencies${NC}"
        return 1
    }

    # Install Node.js
    echo "  Installing Node.js..."
    pct exec $id -- bash -c "
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash
        apt-get install -y nodejs
    " || {
        echo -e "${RED}Failed to install Node.js${NC}"
        return 1
    }

    # Install Claude Code CLI
    echo "  Installing Claude Code CLI..."
    pct exec $id -- bash -c "
        npm install -g @anthropic-ai/claude-code
    " || {
        echo -e "${YELLOW}Warning: Failed to install Claude Code CLI${NC}"
    }

    # Create user
    echo "  Creating aimaster user..."
    pct exec $id -- bash -c "
        if ! id aimaster &>/dev/null; then
            useradd -m -s /bin/bash aimaster
        fi
    "

    # Setup application
    echo "  Setting up application..."
    pct exec $id -- su - aimaster -c "
        # Clone repository
        if [ ! -d ai-scrum-master-v2 ]; then
            git clone $REPO_URL ai-scrum-master-v2
        else
            cd ai-scrum-master-v2
            git pull
            cd ..
        fi

        cd ai-scrum-master-v2

        # Setup Python environment
        if [ ! -d env ]; then
            python3 -m venv env
        fi

        source env/bin/activate
        pip install --upgrade pip

        # Install base requirements
        pip install -r requirements.txt

        # Install role-specific requirements
        if [ \"$is_orchestrator\" = \"true\" ]; then
            pip install -r orchestrator_service/requirements.txt
        else
            # Install worker requirements if they exist
            if [ -f worker/requirements.txt ]; then
                pip install -r worker/requirements.txt
            fi
        fi

        # Create .env file
        cat > .env << EOF
ANTHROPIC_API_KEY=$ANTHROPIC_KEY
GITHUB_TOKEN=$GITHUB_TOKEN
ORCHESTRATOR_URL=$ORCHESTRATOR_URL
WORKER_ID=$worker_id
WORKSPACE_DIR=/home/aimaster/workspace
LOG_LEVEL=INFO
EOF

        # Create workspace directory
        mkdir -p /home/aimaster/workspace

        # Create logs directory
        mkdir -p logs
    " || {
        echo -e "${RED}Failed to setup application${NC}"
        return 1
    }

    # Create systemd service
    echo "  Creating systemd service..."
    if [ "$is_orchestrator" = "true" ]; then
        pct exec $id -- bash -c "
cat > /etc/systemd/system/ai-orchestrator.service << 'EOF'
[Unit]
Description=AI Scrum Master Orchestrator Service
After=network.target

[Service]
Type=simple
User=aimaster
WorkingDirectory=/home/aimaster/ai-scrum-master-v2
Environment=\"PATH=/home/aimaster/ai-scrum-master-v2/env/bin:/usr/local/bin:/usr/bin:/bin\"
Environment=\"PYTHONPATH=/home/aimaster/ai-scrum-master-v2\"
Environment=\"VIRTUAL_ENV=/home/aimaster/ai-scrum-master-v2/env\"
ExecStart=/home/aimaster/ai-scrum-master-v2/env/bin/python orchestrator_service/server.py
EnvironmentFile=/home/aimaster/ai-scrum-master-v2/.env
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-orchestrator
"
    else
        pct exec $id -- bash -c "
cat > /etc/systemd/system/ai-worker.service << 'EOF'
[Unit]
Description=AI Scrum Master Worker Service
After=network.target

[Service]
Type=simple
User=aimaster
WorkingDirectory=/home/aimaster/ai-scrum-master-v2
Environment=\"PATH=/home/aimaster/ai-scrum-master-v2/env/bin:/usr/local/bin:/usr/bin:/bin\"
Environment=\"PYTHONPATH=/home/aimaster/ai-scrum-master-v2\"
Environment=\"VIRTUAL_ENV=/home/aimaster/ai-scrum-master-v2/env\"
ExecStart=/home/aimaster/ai-scrum-master-v2/env/bin/python worker/distributed_worker.py
EnvironmentFile=/home/aimaster/ai-scrum-master-v2/.env
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-worker
"
    fi

    echo -e "${GREEN}✅ Container $id configured successfully${NC}"
}

# Setup orchestrator
setup_container 200 "orchestrator" true

# Setup workers
for id in {201..205}; do
    worker_num=$((id - 200))
    worker_id=$(printf 'worker-%02d' $worker_num)
    setup_container $id $worker_id false
done

# Display summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "All containers configured with:"
echo "  • Ubuntu 22.04"
echo "  • Python 3.11"
echo "  • Node.js 20"
echo "  • Claude Code CLI"
echo "  • AI Scrum Master v2"
echo "  • Systemd services"
echo ""

if [ -z "$ANTHROPIC_KEY" ] || [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  Important: Update API keys before starting services${NC}"
    echo ""
    echo "To update keys on each container:"
    echo "  pct exec 200 -- su - aimaster -c 'cd ai-scrum-master-v2 && nano .env'"
    echo ""
fi

echo "Next Steps:"
echo "  1. Verify API keys are set in .env files"
echo "  2. Start orchestrator:  pct exec 200 -- systemctl start ai-orchestrator"
echo "  3. Start workers:       for id in {201..205}; do pct exec \$id -- systemctl start ai-worker; done"
echo "  4. Check status:        pct exec 200 -- systemctl status ai-orchestrator"
echo "  5. View logs:           pct exec 200 -- journalctl -u ai-orchestrator -f"
echo ""
echo "Quick Management:"
echo "  # Start all:   ./start_cluster.sh"
echo "  # Stop all:    ./stop_cluster.sh"
echo "  # Check logs:  ./view_logs.sh"
echo ""
