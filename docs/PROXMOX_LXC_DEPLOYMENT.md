# Proxmox LXC Deployment Guide

Complete guide for deploying AI Scrum Master v2 across multiple LXC containers on Proxmox.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     Proxmox Cluster                              │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   LXC 100    │  │   LXC 101    │  │   LXC 102    │          │
│  │ Orchestrator │  │  Worker #1   │  │  Worker #2   │          │
│  │   Service    │  │              │  │              │          │
│  │  (FastAPI)   │  │  Python 3.13 │  │  Python 3.13 │          │
│  │              │  │  Claude Code │  │  Claude Code │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐          │
│  │   LXC 103    │  │   LXC 104    │  │   LXC 105    │          │
│  │  Worker #3   │  │  Worker #4   │  │  Worker #5   │          │
│  │              │  │              │  │              │          │
│  │  Python 3.13 │  │  Python 3.13 │  │  Python 3.13 │          │
│  │  Claude Code │  │  Claude Code │  │  Claude Code │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│                    Network: 10.0.0.0/24                          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    GitHub     │
                    │  Repository   │
                    └───────────────┘
```

## Prerequisites

### On Proxmox Host

1. Proxmox VE 7.0+ installed
2. At least 20GB RAM available (4GB per container)
3. 100GB storage available
4. Network bridge configured (vmbr0)

### Access Requirements

- SSH access to Proxmox host
- Root or sudo privileges
- GitHub account with Personal Access Token
- Anthropic API key

## Container Specifications

### Orchestrator Container (LXC 100)

- **OS**: Ubuntu 22.04
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 20GB
- **IP**: 10.0.0.100
- **Services**: FastAPI orchestrator, monitoring dashboard

### Worker Containers (LXC 101-105)

- **OS**: Ubuntu 22.04
- **CPU**: 2 cores each
- **RAM**: 4GB each
- **Disk**: 20GB each
- **IPs**: 10.0.0.101 - 10.0.0.105
- **Services**: AI Scrum Master worker process

## Step-by-Step Deployment

### 1. Create LXC Template

First, create a base template that will be cloned:

```bash
# On Proxmox host
ssh root@proxmox

# Download Ubuntu 22.04 template
pveam update
pveam available | grep ubuntu-22
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

### 2. Create Orchestrator Container

```bash
# Create container
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname ai-orchestrator \
  --cores 2 \
  --memory 4096 \
  --swap 2048 \
  --storage local-lvm \
  --rootfs 20 \
  --net0 name=eth0,bridge=vmbr0,ip=10.0.0.100/24,gw=10.0.0.1 \
  --nameserver 8.8.8.8 \
  --features nesting=1

# Start container
pct start 100

# Enter container
pct enter 100
```

### 3. Configure Orchestrator Container

```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y \
  python3.11 \
  python3-pip \
  python3-venv \
  git \
  curl \
  wget \
  build-essential

# Install Node.js (for Claude Code)
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install -y nodejs

# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Create app user
useradd -m -s /bin/bash aimaster
su - aimaster

# Clone repository
git clone https://github.com/YOUR_ORG/ai-scrum-master-v2.git
cd ai-scrum-master-v2

# Setup Python environment
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Create environment file
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
ORCHESTRATOR_URL=http://10.0.0.100:8000
EOF

# Install orchestrator service dependencies
pip install fastapi uvicorn

# Exit back to root
exit
```

### 4. Create Worker Containers

Create 5 worker containers (101-105):

```bash
# Script to create all workers
for id in {101..105}; do
  worker_num=$((id - 100))
  ip="10.0.0.$id"

  pct create $id local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
    --hostname ai-worker-$worker_num \
    --cores 2 \
    --memory 4096 \
    --swap 2048 \
    --storage local-lvm \
    --rootfs 20 \
    --net0 name=eth0,bridge=vmbr0,ip=$ip/24,gw=10.0.0.1 \
    --nameserver 8.8.8.8 \
    --features nesting=1

  pct start $id

  echo "Created worker container $id at $ip"
done
```

### 5. Configure Worker Containers

Run this for each worker (or use the automation script below):

```bash
# Enter container
pct enter 101

# Update and install dependencies
apt update && apt upgrade -y
apt install -y python3.11 python3-pip python3-venv git curl nodejs npm

# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Create app user
useradd -m -s /bin/bash aimaster
su - aimaster

# Clone repository
git clone https://github.com/YOUR_ORG/ai-scrum-master-v2.git
cd ai-scrum-master-v2

# Setup environment
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Configure worker
cat > .env << 'EOF'
ANTHROPIC_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
ORCHESTRATOR_URL=http://10.0.0.100:8000
WORKER_ID=worker-01
WORKSPACE_DIR=/home/aimaster/workspace
EOF

exit
exit
```

## Automation Scripts

### Deploy All Containers Script

Save as `deploy_lxc_cluster.sh`:

```bash
#!/bin/bash
# deploy_lxc_cluster.sh - Deploy AI Scrum Master cluster on Proxmox

set -e

# Configuration
PROXMOX_HOST="proxmox.local"
TEMPLATE="local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
STORAGE="local-lvm"
BRIDGE="vmbr0"
GATEWAY="10.0.0.1"
NAMESERVER="8.8.8.8"

# GitHub configuration
REPO_URL="https://github.com/YOUR_ORG/ai-scrum-master-v2.git"
ANTHROPIC_KEY="${ANTHROPIC_API_KEY}"
GITHUB_TOKEN="${GITHUB_TOKEN}"

echo "=========================================="
echo "AI Scrum Master LXC Cluster Deployment"
echo "=========================================="
echo ""

# Create orchestrator
echo "Creating orchestrator container (100)..."
pct create 100 $TEMPLATE \
  --hostname ai-orchestrator \
  --cores 2 \
  --memory 4096 \
  --swap 2048 \
  --storage $STORAGE \
  --rootfs 20 \
  --net0 name=eth0,bridge=$BRIDGE,ip=10.0.0.100/24,gw=$GATEWAY \
  --nameserver $NAMESERVER \
  --features nesting=1 \
  --unprivileged 1 \
  --start 1

sleep 5

# Create workers
for id in {101..105}; do
  worker_num=$((id - 100))
  ip="10.0.0.$id"

  echo "Creating worker container ($id) at $ip..."

  pct create $id $TEMPLATE \
    --hostname ai-worker-$worker_num \
    --cores 2 \
    --memory 4096 \
    --swap 2048 \
    --storage $STORAGE \
    --rootfs 20 \
    --net0 name=eth0,bridge=$BRIDGE,ip=$ip/24,gw=$GATEWAY \
    --nameserver $NAMESERVER \
    --features nesting=1 \
    --unprivileged 1 \
    --start 1

  sleep 5
done

echo ""
echo "✅ All containers created!"
echo ""
echo "Container IDs:"
echo "  100 - Orchestrator (10.0.0.100)"
echo "  101 - Worker 1 (10.0.0.101)"
echo "  102 - Worker 2 (10.0.0.102)"
echo "  103 - Worker 3 (10.0.0.103)"
echo "  104 - Worker 4 (10.0.0.104)"
echo "  105 - Worker 5 (10.0.0.105)"
echo ""
echo "Next: Run setup_containers.sh to configure all containers"
```

### Setup Containers Script

Save as `setup_containers.sh`:

```bash
#!/bin/bash
# setup_containers.sh - Configure all LXC containers

set -e

REPO_URL="https://github.com/YOUR_ORG/ai-scrum-master-v2.git"
ANTHROPIC_KEY="${ANTHROPIC_API_KEY:-your_key_here}"
GITHUB_TOKEN="${GITHUB_TOKEN:-your_token_here}"

setup_container() {
  local id=$1
  local worker_id=$2
  local orchestrator_url="http://10.0.0.100:8000"

  echo "Setting up container $id ($worker_id)..."

  pct exec $id -- bash -c "
    # Update system
    export DEBIAN_FRONTEND=noninteractive
    apt update && apt upgrade -y

    # Install dependencies
    apt install -y python3.11 python3-pip python3-venv git curl wget \
      build-essential nodejs npm

    # Install Claude Code
    npm install -g @anthropic-ai/claude-code

    # Create user
    useradd -m -s /bin/bash aimaster || true

    # Setup as aimaster user
    su - aimaster -c '
      # Clone repo
      if [ ! -d ai-scrum-master-v2 ]; then
        git clone $REPO_URL
      fi

      cd ai-scrum-master-v2

      # Setup Python environment
      python3 -m venv env
      source env/bin/activate
      pip install --upgrade pip
      pip install -r requirements.txt

      # Create .env file
      cat > .env << EOF
ANTHROPIC_API_KEY=$ANTHROPIC_KEY
GITHUB_TOKEN=$GITHUB_TOKEN
ORCHESTRATOR_URL=$orchestrator_url
WORKER_ID=$worker_id
WORKSPACE_DIR=/home/aimaster/workspace
LOG_LEVEL=INFO
EOF

      # Create workspace
      mkdir -p /home/aimaster/workspace
    '
  "

  echo "✅ Container $id configured"
}

# Setup orchestrator
echo "Setting up orchestrator (100)..."
setup_container 100 "orchestrator"

# Setup workers
for id in {101..105}; do
  worker_num=$((id - 100))
  setup_container $id "worker-$(printf '%02d' $worker_num)"
done

echo ""
echo "✅ All containers configured!"
echo ""
echo "Next steps:"
echo "  1. Update .env files with real API keys"
echo "  2. Start orchestrator service"
echo "  3. Start worker services"
```

### Create Systemd Services

Create systemd service files for automatic startup:

```bash
#!/bin/bash
# create_services.sh - Create systemd services for all containers

# Orchestrator service
pct exec 100 -- bash -c "
cat > /etc/systemd/system/ai-orchestrator.service << 'EOF'
[Unit]
Description=AI Scrum Master Orchestrator Service
After=network.target

[Service]
Type=simple
User=aimaster
WorkingDirectory=/home/aimaster/ai-scrum-master-v2
Environment=PATH=/home/aimaster/ai-scrum-master-v2/env/bin:/usr/bin
ExecStart=/home/aimaster/ai-scrum-master-v2/env/bin/python orchestrator_service/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-orchestrator
"

# Worker services
for id in {101..105}; do
  worker_num=$((id - 100))
  worker_id=$(printf 'worker-%02d' $worker_num)

  pct exec $id -- bash -c "
cat > /etc/systemd/system/ai-worker.service << 'EOF'
[Unit]
Description=AI Scrum Master Worker Service
After=network.target

[Service]
Type=simple
User=aimaster
WorkingDirectory=/home/aimaster/ai-scrum-master-v2
Environment=PATH=/home/aimaster/ai-scrum-master-v2/env/bin:/usr/bin
Environment=WORKER_ID=$worker_id
ExecStart=/home/aimaster/ai-scrum-master-v2/env/bin/python worker/distributed_worker.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ai-worker
"
done

echo "✅ Systemd services created!"
```

## Starting the Cluster

### 1. Start Orchestrator

```bash
# Start orchestrator service
pct exec 100 -- systemctl start ai-orchestrator

# Check status
pct exec 100 -- systemctl status ai-orchestrator

# View logs
pct exec 100 -- journalctl -u ai-orchestrator -f
```

### 2. Start Workers

```bash
# Start all workers
for id in {101..105}; do
  echo "Starting worker in container $id..."
  pct exec $id -- systemctl start ai-worker
done

# Check status of all workers
for id in {101..105}; do
  echo "Status of container $id:"
  pct exec $id -- systemctl status ai-worker
done
```

### 3. Verify Cluster Health

```bash
# Check orchestrator health
curl http://10.0.0.100:8000/health

# Check worker registration
curl http://10.0.0.100:8000/workers
```

## Monitoring and Management

### View Logs

```bash
# Orchestrator logs
pct exec 100 -- journalctl -u ai-orchestrator -f

# Worker logs (container 101)
pct exec 101 -- journalctl -u ai-worker -f

# All worker logs
for id in {101..105}; do
  echo "=== Worker $id ==="
  pct exec $id -- journalctl -u ai-worker -n 20
done
```

### Container Management

```bash
# Stop all containers
for id in {100..105}; do pct stop $id; done

# Start all containers
for id in {100..105}; do pct start $id; done

# Restart all containers
for id in {100..105}; do pct reboot $id; done

# Stop worker services
for id in {101..105}; do pct exec $id -- systemctl stop ai-worker; done

# Restart orchestrator
pct exec 100 -- systemctl restart ai-orchestrator
```

### Resource Monitoring

```bash
# Check CPU/memory usage
for id in {100..105}; do
  echo "=== Container $id ==="
  pct status $id
  pct exec $id -- free -h
  pct exec $id -- top -bn1 | head -20
done
```

## Networking Configuration

### Port Forwarding (Optional)

Forward orchestrator port to external access:

```bash
# On Proxmox host, forward port 8000 to orchestrator
iptables -t nat -A PREROUTING -p tcp --dport 8000 \
  -j DNAT --to-destination 10.0.0.100:8000

# Save rules
iptables-save > /etc/iptables/rules.v4
```

### Firewall Rules

```bash
# Allow orchestrator access from workers
pct exec 100 -- ufw allow from 10.0.0.0/24 to any port 8000

# Enable UFW
pct exec 100 -- ufw --force enable
```

## Backup and Recovery

### Backup Containers

```bash
# Backup orchestrator
vzdump 100 --mode snapshot --compress zstd --storage local

# Backup all workers
for id in {101..105}; do
  vzdump $id --mode snapshot --compress zstd --storage local
done
```

### Restore Container

```bash
# List backups
pvesm list local

# Restore from backup
pct restore 100 /var/lib/vz/dump/vzdump-lxc-100-*.tar.zst --storage local-lvm
```

## Performance Tuning

### CPU Pinning (Optional)

```bash
# Pin orchestrator to cores 0-1
pct set 100 --cores 2 --cpulimit 2

# Pin workers to specific cores
pct set 101 --cores 2 --cpulimit 2 --cpuunits 1024
pct set 102 --cores 2 --cpulimit 2 --cpuunits 1024
# etc...
```

### Memory Optimization

```bash
# Adjust swap
for id in {100..105}; do
  pct set $id --swap 4096
done
```

## Troubleshooting

### Worker Can't Connect to Orchestrator

```bash
# Check network connectivity
pct exec 101 -- ping -c 4 10.0.0.100

# Check orchestrator is running
pct exec 100 -- systemctl status ai-orchestrator

# Check firewall
pct exec 100 -- ufw status
```

### High Memory Usage

```bash
# Check memory usage
pct exec 101 -- free -h

# Restart worker if needed
pct exec 101 -- systemctl restart ai-worker
```

### Container Won't Start

```bash
# Check container status
pct status 101

# View container errors
pct start 101 --debug

# Check system logs
pct exec 101 -- journalctl -xe
```

## Cost Estimation

### Resource Usage

- **Orchestrator**: ~2GB RAM, 1 CPU (idle)
- **Worker (idle)**: ~1GB RAM, 0.5 CPU
- **Worker (active)**: ~3GB RAM, 1.5 CPU

### API Costs

- **Per feature**: $0.05 - $0.15
- **5 workers active**: ~$0.25 - $0.75/hour
- **Daily (8 hours)**: ~$2 - $6/day
- **Monthly**: ~$60 - $180/month

## Next Steps

1. Deploy containers using automation scripts
2. Configure API keys and tokens
3. Test with small number of issues
4. Scale up to production workload
5. Setup monitoring dashboard
6. Configure automated backups

## Support

For issues with:
- **Proxmox/LXC**: Check Proxmox documentation
- **AI Scrum Master**: GitHub issues or docs
- **Networking**: Verify bridge and firewall configuration

---

**Last Updated**: 2025-11-14
**Version**: 2.4.0
