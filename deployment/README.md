# Deployment Scripts for Distributed AI Scrum Master

This directory contains everything needed to deploy the AI Scrum Master system to a Proxmox cluster with 5 parallel worker containers.

## Quick Links

- **[Quick Start Guide](QUICKSTART.md)** - Deploy in 30 minutes
- **[Full Deployment Guide](PROXMOX_DEPLOYMENT.md)** - Comprehensive documentation
- **[Architecture Overview](../DISTRIBUTED_ARCHITECTURE.md)** - System design details

## Files

### Setup Scripts

| File | Purpose | Run On |
|------|---------|--------|
| [`orchestrator_setup.sh`](orchestrator_setup.sh) | Setup orchestrator container | Orchestrator CT (100) |
| [`proxmox_setup.sh`](proxmox_setup.sh) | Setup worker containers | Worker CTs (101-105) |

### Documentation

| File | Purpose |
|------|---------|
| [`QUICKSTART.md`](QUICKSTART.md) | 30-minute deployment guide |
| [`PROXMOX_DEPLOYMENT.md`](PROXMOX_DEPLOYMENT.md) | Full deployment documentation |

## Architecture Summary

```
┌─────────────────────────────────────────┐
│  Proxmox Cluster (pve6.lab.int)         │
│                                          │
│  ┌────────────────┐                     │
│  │ Orchestrator   │  (CT 100)           │
│  │ 10.0.0.10      │  ← API Server       │
│  │ - FastAPI      │  ← GitHub Monitor   │
│  │ - Dashboard    │  ← Work Dispatcher  │
│  └────────┬───────┘                     │
│           │                              │
│     ┌─────┴──────────────┐              │
│     │  │   │    │   │                   │
│  ┌──▼┐┌─▼┐┌▼─┐┌─▼┐┌─▼┐                 │
│  │W1 ││W2││W3││W4││W5│   (CT 101-105)  │
│  └───┘└──┘└──┘└──┘└──┘                  │
│   ↓    ↓   ↓   ↓   ↓                    │
│  [Feature Implementations]               │
│                                          │
└─────────────────────────────────────────┘
```

## Prerequisites

Before starting deployment:

- ✅ Proxmox VE 7.0+ access
- ✅ Ubuntu 22.04 LXC template downloaded
- ✅ Anthropic API key
- ✅ GitHub Personal Access Token
- ✅ Network configuration (IPs, gateway)

## Deployment Options

### Option 1: Docker Compose (Recommended for Testing)
Quick deployment using Docker containers. Perfect for testing and development.

**Prerequisites:**
- Docker Engine 20.10+
- Docker Compose 2.0+

**Deploy:**
```bash
cd deployment
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

See [Docker Deployment](#docker-deployment) section below for details.

### Option 2: Proxmox LXC Containers (Recommended for Production)
Production-ready deployment on Proxmox with 5 parallel worker containers.

**Quick Start:**
Follow [QUICKSTART.md](QUICKSTART.md) for a rapid deployment in ~30 minutes.

**Production Deploy:**
Follow [PROXMOX_DEPLOYMENT.md](PROXMOX_DEPLOYMENT.md) for a comprehensive production-ready deployment with monitoring, backups, and security hardening.

## Container Specifications

### Orchestrator Container
- **CT ID:** 100
- **Hostname:** ai-scrum-orchestrator
- **IP:** 10.0.0.10/24 (adjust to your network)
- **Resources:** 2 cores, 4GB RAM, 32GB disk
- **Services:** FastAPI API, Nginx reverse proxy, SSH

### Worker Containers (x5)
- **CT IDs:** 101-105
- **Hostnames:** ai-scrum-worker-1 through ai-scrum-worker-5
- **IPs:** 10.0.0.11-15/24 (adjust to your network)
- **Resources:** 2 cores, 4GB RAM, 32GB disk each
- **Services:** AI Scrum Master worker, SSH

## Total Resource Requirements

- **CPU:** 12 cores (2 per container × 6 containers)
- **RAM:** 24 GB (4 GB per container × 6 containers)
- **Disk:** 192 GB (32 GB per container × 6 containers)
- **Network:** 1 Gbps recommended

## Post-Deployment

After deployment:

1. **Verify System Health**
   ```bash
   curl http://10.0.0.10:8000/health
   ```

2. **Test with Sample Issue**
   ```bash
   gh issue create --title "[Test] Simple function" \
     --body "Create a hello world function" \
     --label "ai-ready"
   ```

3. **Monitor Execution**
   ```bash
   # Watch orchestrator
   pct exec 100 journalctl -u ai-scrum-orchestrator -f

   # Watch worker
   pct exec 101 journalctl -u ai-scrum-worker -f
   ```

## Performance Expectations

### With 5 Workers

- **Throughput:** 5-10 features per hour
- **Daily Capacity:** 50-100 features
- **Simple Feature:** 10-15 minutes
- **Medium Feature:** 20-40 minutes
- **Complex Feature:** 40-90 minutes

### Cost Per Feature

- **Simple:** $3-5
- **Medium:** $7-12
- **Complex:** $12-20

### Monthly Estimates

- **Infrastructure:** ~$30 (power for Proxmox server)
- **API Costs:** $500-1500 (100 features/month)
- **Total:** ~$530-1530/month

**vs Human Developer:** $8,000-15,000/month
**Savings:** 90-95%

## Scaling

### Add More Workers

```bash
# Create worker 6
pct create 106 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname ai-scrum-worker-6 \
  --cores 2 --memory 4096 --rootfs local-lvm:32 \
  --net0 name=eth0,bridge=vmbr0,ip=10.0.0.16/24,gw=10.0.0.1
```

### Remove Workers

```bash
pct stop 101
pct destroy 101
```

## Monitoring

### Container Status
```bash
pct list
pct status 100
```

### Resource Usage
```bash
pct exec 100 htop
pct exec 101 free -h
```

### Service Logs
```bash
pct exec 100 journalctl -u ai-scrum-orchestrator -f
pct exec 101 journalctl -u ai-scrum-worker -f
```

## Backup & Recovery

### Backup All Containers
```bash
# Orchestrator
vzdump 100 --mode snapshot --storage backup-storage

# Workers
for i in {1..5}; do
  vzdump $((100 + i)) --mode snapshot --storage backup-storage
done
```

### Restore Container
```bash
pct restore 100 /path/to/backup/vzdump-lxc-100.tar.zst
```

## Troubleshooting

### Common Issues

**Worker can't connect to orchestrator:**
```bash
pct exec 101 ping 10.0.0.10
pct exec 101 curl http://10.0.0.10:8000/health
```

**Service won't start:**
```bash
pct exec 100 systemctl status ai-scrum-orchestrator
pct exec 100 journalctl -u ai-scrum-orchestrator -n 50
```

**High memory usage:**
```bash
pct exec 101 free -h
pct exec 101 systemctl restart ai-scrum-worker
```

## Security

### Firewall Rules

Configure Proxmox firewall:

```bash
# Orchestrator (CT 100)
- Port 8000 (API) - Internal only
- Port 80/443 (Dashboard) - Internal only
- Port 22 (SSH) - Admin only

# Workers (CT 101-105)
- Port 22 (SSH) - Orchestrator only
```

### API Keys

Store securely:
```bash
chmod 600 /opt/ai-scrum-master/.env
```

## Support

- **Documentation:** See [PROXMOX_DEPLOYMENT.md](PROXMOX_DEPLOYMENT.md)
- **Architecture:** See [../DISTRIBUTED_ARCHITECTURE.md](../DISTRIBUTED_ARCHITECTURE.md)
- **Issues:** https://github.com/YOUR_ORG/ai-scrum-master-v2/issues

## Docker Deployment

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Anthropic API key
- GitHub Personal Access Token

### Quick Start

1. **Clone Repository**
```bash
git clone https://github.com/YOUR_ORG/ai-scrum-master-v2.git
cd ai-scrum-master-v2/deployment
```

2. **Create Environment File**
```bash
cat > .env << EOF
# API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
GITHUB_TOKEN=ghp_your-token-here

# GitHub Configuration
GITHUB_REPO=YOUR_ORG/YOUR_REPO
GITHUB_ISSUE_LABELS=ai-ready
GITHUB_POLL_INTERVAL=60

# Worker Configuration
WORKER_IPS=worker-1,worker-2,worker-3,worker-4,worker-5
LOG_LEVEL=INFO
EOF
```

3. **Build and Start**
```bash
docker-compose up -d
```

4. **Verify Deployment**
```bash
# Check orchestrator health
curl http://localhost:8000/health

# View logs
docker-compose logs -f orchestrator
docker-compose logs -f worker
```

### Docker Architecture

```
┌─────────────────────────────────────────┐
│  Docker Host                             │
│                                          │
│  ┌────────────────┐                     │
│  │ Orchestrator   │  :8000              │
│  │ Container      │  ← API Server       │
│  │                │  ← GitHub Monitor   │
│  └────────┬───────┘                     │
│           │                              │
│     ┌─────┴──────────────┐              │
│     │  │   │    │   │                   │
│  ┌──▼┐┌─▼┐┌▼─┐┌─▼┐┌─▼┐                 │
│  │W1 ││W2││W3││W4││W5│   (5 replicas)  │
│  └───┘└──┘└──┘└──┘└──┘                  │
│                                          │
│  ai-scrum-network (bridge)              │
└─────────────────────────────────────────┘
```

### Container Details

**Orchestrator Container:**
- Image: `ai-scrum-orchestrator:latest`
- Ports: 8000 (API), 3000 (Dashboard)
- Volumes:
  - `orchestrator-data` - Task queue database
  - `orchestrator-logs` - Application logs
- Networks: `ai-scrum-network`

**Worker Containers (5 replicas):**
- Image: `ai-scrum-worker:latest`
- Volumes:
  - `worker-workspace` - Shared workspace for git operations
- Networks: `ai-scrum-network`
- Depends on: `orchestrator`

### Management Commands

**View Status:**
```bash
docker-compose ps
```

**Scale Workers:**
```bash
# Increase to 10 workers
docker-compose up -d --scale worker=10

# Decrease to 3 workers
docker-compose up -d --scale worker=3
```

**View Logs:**
```bash
# All services
docker-compose logs -f

# Orchestrator only
docker-compose logs -f orchestrator

# Specific worker
docker logs -f ai-scrum-master-v2-worker-1
```

**Restart Services:**
```bash
# Restart all
docker-compose restart

# Restart orchestrator
docker-compose restart orchestrator

# Restart workers
docker-compose restart worker
```

**Stop Services:**
```bash
docker-compose down
```

**Clean Up (remove volumes):**
```bash
docker-compose down -v
```

### Updating Deployment

**Pull Latest Code:**
```bash
git pull origin main
docker-compose build
docker-compose up -d
```

**Update Single Service:**
```bash
docker-compose build orchestrator
docker-compose up -d orchestrator
```

### Troubleshooting

**Container won't start:**
```bash
docker-compose logs orchestrator
docker-compose logs worker
```

**Worker can't connect to orchestrator:**
```bash
# Check network
docker network inspect ai-scrum-master-v2_ai-scrum-network

# Test connectivity from worker
docker exec ai-scrum-master-v2-worker-1 curl http://orchestrator:8000/health
```

**View orchestrator SSH key:**
```bash
docker exec ai-scrum-orchestrator cat /root/.ssh/id_orchestrator.pub
```

**Add orchestrator key to workers:**
```bash
# Get public key
PUBKEY=$(docker exec ai-scrum-orchestrator cat /root/.ssh/id_orchestrator.pub)

# Add to each worker (already handled in start script)
docker exec ai-scrum-master-v2-worker-1 bash -c "echo '$PUBKEY' >> /root/.ssh/authorized_keys"
```

### Performance Tuning

**Resource Limits:**

Edit `docker-compose.yml` to adjust resources:

```yaml
services:
  worker:
    deploy:
      replicas: 5
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

**Persistent Storage:**

Volumes are automatically created. To use specific paths:

```yaml
volumes:
  orchestrator-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /path/to/data
```

## License

MIT License - See LICENSE file in project root
