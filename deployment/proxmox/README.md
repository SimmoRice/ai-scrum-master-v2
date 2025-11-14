# Proxmox LXC Deployment Scripts

Automated deployment scripts for running AI Scrum Master v2 across multiple LXC containers on Proxmox.

## Quick Start

### 1. Deploy Containers

```bash
# SSH to Proxmox host
ssh root@proxmox

# Navigate to deployment directory
cd /path/to/deployment/proxmox

# Make scripts executable
chmod +x *.sh

# Deploy all containers
./deploy_lxc_cluster.sh
```

This creates 6 LXC containers:
- Container 100: Orchestrator (10.0.0.100)
- Containers 101-105: Workers 1-5 (10.0.0.101-105)

### 2. Setup Software

```bash
# Set your API keys
export ANTHROPIC_API_KEY="sk-ant-..."
export GITHUB_TOKEN="ghp_..."

# Configure all containers
./setup_containers.sh
```

This installs:
- Python 3.11
- Node.js 20
- Claude Code CLI
- AI Scrum Master application
- Systemd services

### 3. Start Cluster

```bash
# Start all services
./start_cluster.sh

# Check status
./status_cluster.sh

# View logs
./view_logs.sh
```

## Scripts Overview

### Deployment Scripts

| Script | Description |
|--------|-------------|
| `deploy_lxc_cluster.sh` | Create all LXC containers |
| `setup_containers.sh` | Install software and configure services |

### Management Scripts

| Script | Description |
|--------|-------------|
| `start_cluster.sh` | Start all services |
| `stop_cluster.sh` | Stop all services |
| `restart_cluster.sh` | Restart all services |
| `status_cluster.sh` | Show cluster status |
| `view_logs.sh` | Interactive log viewer |

## Container Layout

```
Proxmox Host
├── LXC 100 - Orchestrator
│   ├── Ubuntu 22.04
│   ├── 2 CPU cores, 4GB RAM
│   ├── IP: 10.0.0.100
│   └── Service: ai-orchestrator
│
├── LXC 101 - Worker 1
│   ├── Ubuntu 22.04
│   ├── 2 CPU cores, 4GB RAM
│   ├── IP: 10.0.0.101
│   └── Service: ai-worker
│
├── LXC 102 - Worker 2
│   └── (same as above, IP: 10.0.0.102)
│
├── LXC 103 - Worker 3
│   └── (same as above, IP: 10.0.0.103)
│
├── LXC 104 - Worker 4
│   └── (same as above, IP: 10.0.0.104)
│
└── LXC 105 - Worker 5
    └── (same as above, IP: 10.0.0.105)
```

## Configuration

### Network Settings

Default network configuration (edit in scripts if needed):
- Network: `10.0.0.0/24`
- Gateway: `10.0.0.1`
- Bridge: `vmbr0`

### Resource Allocation

Per container:
- **CPU**: 2 cores
- **RAM**: 4GB
- **Swap**: 2GB
- **Disk**: 20GB

Total cluster:
- **CPU**: 12 cores
- **RAM**: 24GB
- **Disk**: 120GB

### Repository

Update `REPO_URL` in `setup_containers.sh`:
```bash
REPO_URL="https://github.com/YOUR_ORG/ai-scrum-master-v2.git"
```

## Common Tasks

### Start/Stop Services

```bash
# Start all
./start_cluster.sh

# Stop all
./stop_cluster.sh

# Restart all
./restart_cluster.sh
```

### Check Status

```bash
./status_cluster.sh
```

Output shows:
- Container status
- Service status
- Resource usage
- API health

### View Logs

```bash
# Interactive menu
./view_logs.sh

# Direct access
./view_logs.sh orchestrator  # Orchestrator logs (live)
./view_logs.sh worker1       # Worker 1 logs (live)
./view_logs.sh all           # All workers (summary)
```

### Access Containers

```bash
# Enter orchestrator
pct enter 100

# Enter worker 1
pct enter 101

# Run command in container
pct exec 100 -- ls -la /home/aimaster/ai-scrum-master-v2
```

### Update API Keys

```bash
# Edit .env file on orchestrator
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && nano .env'

# Edit .env file on worker 1
pct exec 101 -- su - aimaster -c 'cd ai-scrum-master-v2 && nano .env'

# Restart services after update
./restart_cluster.sh
```

### Manual Service Control

```bash
# Start orchestrator
pct exec 100 -- systemctl start ai-orchestrator

# Stop worker 1
pct exec 101 -- systemctl stop ai-worker

# Check service status
pct exec 100 -- systemctl status ai-orchestrator

# View service logs
pct exec 100 -- journalctl -u ai-orchestrator -f
```

## Monitoring

### Check Orchestrator API

```bash
# Health check
curl http://10.0.0.100:8000/health

# List registered workers
curl http://10.0.0.100:8000/workers

# Get queue status
curl http://10.0.0.100:8000/queue/status
```

### Resource Usage

```bash
# All containers
for id in {100..105}; do
  echo "=== Container $id ==="
  pct status $id
  pct exec $id -- free -h
  pct exec $id -- df -h /
done
```

### Live Monitoring

```bash
# Container resource usage (Proxmox host)
watch -n 2 'for id in {100..105}; do echo "CT$id:"; pct status $id; done'

# Service logs (orchestrator)
pct exec 100 -- journalctl -u ai-orchestrator -f
```

## Backup & Recovery

### Backup Containers

```bash
# Backup orchestrator
vzdump 100 --mode snapshot --compress zstd --storage local

# Backup all workers
for id in {101..105}; do
  vzdump $id --mode snapshot --compress zstd --storage local
done

# Backup entire cluster
vzdump 100,101,102,103,104,105 --mode snapshot --compress zstd --storage local
```

### Restore Container

```bash
# List backups
ls -lh /var/lib/vz/dump/

# Restore from backup
pct restore 100 /var/lib/vz/dump/vzdump-lxc-100-*.tar.zst \
  --storage local-lvm
```

## Troubleshooting

### Container Won't Start

```bash
# Check container status
pct status 100

# View system logs
pct exec 100 -- journalctl -xe

# Try starting with debug
pct start 100 --debug
```

### Service Won't Start

```bash
# Check service status
pct exec 100 -- systemctl status ai-orchestrator

# View service logs
pct exec 100 -- journalctl -u ai-orchestrator -n 50

# Check Python environment
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && source env/bin/activate && python --version'
```

### Network Issues

```bash
# Test connectivity from worker to orchestrator
pct exec 101 -- ping -c 4 10.0.0.100

# Check if orchestrator API is responding
pct exec 101 -- curl http://10.0.0.100:8000/health

# Check firewall
pct exec 100 -- ufw status
```

### High Resource Usage

```bash
# Check CPU usage
pct exec 101 -- top -bn1 | head -20

# Check memory usage
pct exec 101 -- free -h

# Check disk usage
pct exec 101 -- df -h

# Restart service if needed
pct exec 101 -- systemctl restart ai-worker
```

## Scaling

### Add More Workers

To add worker 6 (container 106):

```bash
# Create container
pct create 106 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname ai-worker-6 \
  --cores 2 \
  --memory 4096 \
  --swap 2048 \
  --storage local-lvm \
  --rootfs 20 \
  --net0 name=eth0,bridge=vmbr0,ip=10.0.0.106/24,gw=10.0.0.1 \
  --nameserver 8.8.8.8 \
  --features nesting=1

# Start and configure
pct start 106
# Run setup steps from setup_containers.sh manually
```

### Remove Workers

```bash
# Stop service
pct exec 105 -- systemctl stop ai-worker

# Stop container
pct stop 105

# Remove container
pct destroy 105
```

## Performance Tuning

### CPU Pinning

```bash
# Pin orchestrator to specific cores
pct set 100 --cores 2 --cpulimit 2

# Distribute workers across cores
pct set 101 --cores 2 --cpulimit 2 --cpuunits 1024
pct set 102 --cores 2 --cpulimit 2 --cpuunits 1024
```

### Memory Limits

```bash
# Increase swap for heavy workloads
pct set 101 --swap 4096

# Adjust memory
pct set 101 --memory 6144
```

## Security

### Update Containers

```bash
# Update all containers
for id in {100..105}; do
  pct exec $id -- apt update
  pct exec $id -- apt upgrade -y
done
```

### Firewall Configuration

```bash
# On orchestrator, allow only workers
pct exec 100 -- ufw allow from 10.0.0.101 to any port 8000
pct exec 100 -- ufw allow from 10.0.0.102 to any port 8000
# ... repeat for all workers
pct exec 100 -- ufw enable
```

## Support

For issues:
- Proxmox: Check [Proxmox documentation](https://pve.proxmox.com/wiki)
- Application: See main [documentation](../../docs/)
- Scripts: Review script comments and error messages

---

**Version**: 2.4.0
**Last Updated**: 2025-11-14
