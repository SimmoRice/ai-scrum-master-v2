# Proxmox Deployment Guide - Distributed AI Scrum Master

## Architecture

```
Proxmox Cluster (pve6.lab.int.as152738.net)
├── Orchestrator Container (LXC)
│   └── IP: 10.x.x.10
│   └── Ports: 8000 (API), 3000 (Dashboard)
│
├── Worker Container #1 (LXC)
│   └── IP: 10.x.x.11
├── Worker Container #2 (LXC)
│   └── IP: 10.x.x.12
├── Worker Container #3 (LXC)
│   └── IP: 10.x.x.13
├── Worker Container #4 (LXC)
│   └── IP: 10.x.x.14
└── Worker Container #5 (LXC)
    └── IP: 10.x.x.15
```

## Prerequisites

- Proxmox VE 7.0+ installed
- Ubuntu 22.04 LXC template available
- GitHub repository for AI Scrum Master
- Anthropic API key
- GitHub Personal Access Token

## Step 1: Create LXC Containers in Proxmox

### Container Specifications

**Orchestrator Container:**
- **Template:** Ubuntu 22.04
- **Hostname:** ai-scrum-orchestrator
- **Cores:** 2
- **RAM:** 4 GB
- **Disk:** 32 GB
- **Network:** Static IP (e.g., 10.0.0.10)

**Worker Containers (x5):**
- **Template:** Ubuntu 22.04
- **Hostname:** ai-scrum-worker-[1-5]
- **Cores:** 2
- **RAM:** 4 GB
- **Disk:** 32 GB
- **Network:** Static IP (e.g., 10.0.0.11-15)

###  Manual Container Creation (Proxmox Web UI)

1. Navigate to Proxmox web interface: https://pve6.lab.int.as152738.net:8006/
2. Click **Create CT** (top right)
3. Configure:
   - **General:**
     - Node: (select your node)
     - CT ID: 100 (orchestrator), 101-105 (workers)
     - Hostname: as above
     - Password: Set strong password
   - **Template:**
     - Storage: local
     - Template: ubuntu-22.04-standard
   - **Root Disk:**
     - Storage: local-lvm
     - Size: 32 GB
   - **CPU:**
     - Cores: 2
   - **Memory:**
     - RAM: 4096 MB
     - Swap: 512 MB
   - **Network:**
     - Bridge: vmbr0
     - IPv4: Static
     - IPv4/CIDR: 10.0.0.10/24 (adjust for each container)
     - Gateway: 10.0.0.1
4. Click **Finish**
5. Start the container

### Automated Container Creation (Proxmox CLI)

```bash
# SSH into Proxmox host
ssh root@pve6.lab.int.as152738.net

# Create orchestrator container
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname ai-scrum-orchestrator \
  --cores 2 \
  --memory 4096 \
  --swap 512 \
  --rootfs local-lvm:32 \
  --net0 name=eth0,bridge=vmbr0,ip=10.0.0.10/24,gw=10.0.0.1 \
  --password \
  --unprivileged 1 \
  --features nesting=1

# Create worker containers
for i in {1..5}; do
  pct create $((100 + i)) local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
    --hostname ai-scrum-worker-$i \
    --cores 2 \
    --memory 4096 \
    --swap 512 \
    --rootfs local-lvm:32 \
    --net0 name=eth0,bridge=vmbr0,ip=10.0.0.$((10 + i))/24,gw=10.0.0.1 \
    --password \
    --unprivileged 1 \
    --features nesting=1
done

# Start all containers
pct start 100
for i in {1..5}; do pct start $((100 + i)); done
```

## Step 2: Setup Orchestrator Container

```bash
# Enter orchestrator container
pct enter 100

# Download setup script
curl -o /root/orchestrator_setup.sh https://raw.githubusercontent.com/YOUR_ORG/ai-scrum-master-v2/main/deployment/orchestrator_setup.sh

# Make executable
chmod +x /root/orchestrator_setup.sh

# Run setup (pass API keys as environment variables)
ANTHROPIC_API_KEY="your-key-here" \
GITHUB_TOKEN="your-token-here" \
/root/orchestrator_setup.sh
```

## Step 3: Setup Worker Containers

```bash
# For each worker container
for i in {1..5}; do
  echo "Setting up worker $i..."
  pct enter $((100 + i)) << 'EOF'
    # Download setup script
    curl -o /root/proxmox_setup.sh https://raw.githubusercontent.com/YOUR_ORG/ai-scrum-master-v2/main/deployment/proxmox_setup.sh

    # Make executable
    chmod +x /root/proxmox_setup.sh

    # Run setup
    WORKER_ID="worker-$i" \
    ORCHESTRATOR_URL="http://10.0.0.10:8000" \
    ANTHROPIC_API_KEY="your-key-here" \
    GITHUB_TOKEN="your-token-here" \
    /root/proxmox_setup.sh

    exit
EOF
done
```

## Step 4: Configure SSH Access

### Generate SSH Key on Orchestrator

```bash
# On orchestrator container
pct enter 100
ssh-keygen -t ed25519 -C "orchestrator@ai-scrum" -f /root/.ssh/id_orchestrator -N ""

# View public key
cat /root/.ssh/id_orchestrator.pub
```

### Add Public Key to Workers

```bash
# For each worker
for i in {1..5}; do
  pct enter $((100 + i))
  mkdir -p /root/.ssh
  echo "PASTE_PUBLIC_KEY_HERE" >> /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
  exit
done
```

## Step 5: Start Services

### Start Orchestrator

```bash
pct enter 100
systemctl start ai-scrum-orchestrator
systemctl status ai-scrum-orchestrator

# View logs
journalctl -u ai-scrum-orchestrator -f
```

### Start Workers

```bash
for i in {1..5}; do
  pct enter $((100 + i))
  systemctl start ai-scrum-worker
  systemctl status ai-scrum-worker
  exit
done
```

## Step 6: Verify Deployment

### Check Orchestrator API

```bash
curl http://10.0.0.10:8000/health
# Expected: {"status": "healthy", "workers": 5, "active_tasks": 0}
```

### Check Worker Connectivity

```bash
# From orchestrator
ssh -i /root/.ssh/id_orchestrator root@10.0.0.11 "echo 'Worker 1 connected'"
ssh -i /root/.ssh/id_orchestrator root@10.0.0.12 "echo 'Worker 2 connected'"
# ... repeat for all workers
```

### Access Dashboard

Open browser: http://10.0.0.10:3000

## Step 7: Test with Sample Issue

### Create Test GitHub Issue

```bash
# Use GitHub CLI from orchestrator
gh issue create \
  --title "[Test] Create simple calculator function" \
  --body "Create a Python function that adds two numbers" \
  --label "ai-ready,priority:high,complexity:small"
```

### Monitor Worker Activity

```bash
# Watch orchestrator logs
journalctl -u ai-scrum-orchestrator -f

# Watch specific worker
pct enter 101
journalctl -u ai-scrum-worker -f
```

## Monitoring & Management

### Container Resource Usage

```bash
# On Proxmox host
pct list
pct status 100  # Orchestrator
pct status 101  # Worker 1
# ... etc
```

### Stop All Services

```bash
# Stop workers
for i in {1..5}; do
  pct exec $((100 + i)) systemctl stop ai-scrum-worker
done

# Stop orchestrator
pct exec 100 systemctl stop ai-scrum-orchestrator
```

### Restart All Services

```bash
# Restart orchestrator
pct exec 100 systemctl restart ai-scrum-orchestrator

# Restart workers
for i in {1..5}; do
  pct exec $((100 + i)) systemctl restart ai-scrum-worker
done
```

## Backup Strategy

```bash
# Backup orchestrator
vzdump 100 --mode snapshot --storage backup-storage

# Backup all workers
for i in {1..5}; do
  vzdump $((100 + i)) --mode snapshot --storage backup-storage
done
```

## Troubleshooting

### Worker Not Connecting to Orchestrator

```bash
# Check network connectivity
pct enter 101
ping 10.0.0.10
curl http://10.0.0.10:8000/health
```

### Worker Failing to Execute Tasks

```bash
# Check worker logs
pct enter 101
journalctl -u ai-scrum-worker -n 100

# Check Claude Code installation
claude --version

# Check API key
env | grep ANTHROPIC_API_KEY
```

### High Memory Usage

```bash
# Monitor container memory
pct exec 101 free -h

# Restart worker to clear memory
pct exec 101 systemctl restart ai-scrum-worker
```

## Scaling

### Add More Workers

1. Create new LXC container (CT ID 106+)
2. Run setup script
3. Add SSH key
4. Orchestrator auto-discovers new workers

### Remove Workers

1. Stop worker service
2. Remove from orchestrator configuration
3. Destroy container: `pct destroy 101`

## Security Considerations

1. **Firewall Rules:** Only allow necessary ports
   - Orchestrator: 8000 (API), 3000 (Dashboard)
   - Workers: 22 (SSH from orchestrator only)

2. **API Keys:** Store securely in .env files with restricted permissions
   ```bash
   chmod 600 /opt/ai-scrum-master/.env
   ```

3. **SSH Keys:** Use separate keys for orchestrator-worker communication

4. **Network Isolation:** Consider VLAN for AI Scrum Master infrastructure

## Performance Tuning

### Increase Worker Count
- Current: 5 workers
- Recommended max: 10 workers per Proxmox node
- Requires: 2 cores + 4GB RAM per worker

### Adjust Timeouts
Edit `/opt/ai-scrum-master/config.py`:
```python
CLAUDE_CLI_CONFIG = {
    "timeout": 3600,  # Increase for complex features
}
```

### Enable Caching
Ensure cache is enabled in config:
```python
CACHE_CONFIG = {
    "enabled": True,
    "ttl_days": 7,
}
```

## Cost Analysis

**Infrastructure Costs (Proxmox):**
- Hardware: One-time cost (already owned)
- Power: ~$20-40/month for dedicated server
- **Total: ~$30/month**

**API Costs (Claude):**
- Simple feature: $3-5
- Complex feature: $10-15
- 100 features/month: ~$500-1500/month

**Total Cost: ~$530-1540/month**

**vs. Human Developers:**
- 1 developer: $8,000-15,000/month
- **Savings: 90-95%**

## Next Steps

1. ✅ Deploy to Proxmox cluster
2. ✅ Test with sample issues
3. ✅ Monitor for 24 hours
4. ⬜ Integrate with production GitHub repository
5. ⬜ Scale to 10 workers
6. ⬜ Add monitoring dashboard (Grafana)
