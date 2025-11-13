# Quick Start: Deploy to Proxmox in 30 Minutes

## Prerequisites
- Proxmox cluster access: https://pve6.lab.int.as152738.net:8006/
- Anthropic API key
- GitHub Personal Access Token
- Ubuntu 22.04 LXC template downloaded

## Step 1: Create Containers (5 minutes)

SSH into your Proxmox host:

```bash
ssh root@pve6.lab.int.as152738.net
```

Run this script to create all 6 containers:

```bash
# Create orchestrator + 5 workers
# Adjust IP range to match your network (currently using 10.0.0.x)

# Orchestrator
pct create 100 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname ai-scrum-orchestrator \
  --cores 2 --memory 4096 --swap 512 --rootfs local-lvm:32 \
  --net0 name=eth0,bridge=vmbr0,ip=10.0.0.10/24,gw=10.0.0.1 \
  --password --unprivileged 1 --features nesting=1

# 5 Workers
for i in {1..5}; do
  pct create $((100 + i)) local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
    --hostname ai-scrum-worker-$i \
    --cores 2 --memory 4096 --swap 512 --rootfs local-lvm:32 \
    --net0 name=eth0,bridge=vmbr0,ip=10.0.0.$((10 + i))/24,gw=10.0.0.1 \
    --password --unprivileged 1 --features nesting=1
done

# Start all containers
pct start 100
for i in {1..5}; do pct start $((100 + i)); done
```

## Step 2: Setup Orchestrator (10 minutes)

```bash
# Enter orchestrator container
pct enter 100

# Download and run setup script
curl -o /root/orchestrator_setup.sh \
  https://raw.githubusercontent.com/YOUR_ORG/ai-scrum-master-v2/main/deployment/orchestrator_setup.sh

chmod +x /root/orchestrator_setup.sh

# Run setup with your API keys
ANTHROPIC_API_KEY="sk-ant-..." \
GITHUB_TOKEN="ghp_..." \
/root/orchestrator_setup.sh
```

## Step 3: Setup SSH Keys (2 minutes)

Still in orchestrator container:

```bash
# Generate SSH key for worker communication
ssh-keygen -t ed25519 -C "orchestrator" -f /root/.ssh/id_orchestrator -N ""

# Copy public key (you'll need this for workers)
cat /root/.ssh/id_orchestrator.pub
```

## Step 4: Setup Workers (10 minutes)

For each worker, run:

```bash
# Worker 1
pct enter 101

curl -o /root/proxmox_setup.sh \
  https://raw.githubusercontent.com/YOUR_ORG/ai-scrum-master-v2/main/deployment/proxmox_setup.sh

chmod +x /root/proxmox_setup.sh

WORKER_ID="worker-1" \
ORCHESTRATOR_URL="http://10.0.0.10:8000" \
ANTHROPIC_API_KEY="sk-ant-..." \
GITHUB_TOKEN="ghp_..." \
/root/proxmox_setup.sh

# Add orchestrator's public key
mkdir -p /root/.ssh
echo "PASTE_PUBLIC_KEY_FROM_STEP3" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

exit
```

Repeat for workers 2-5 (containers 102-105).

## Step 5: Start Services (3 minutes)

### Start Orchestrator
```bash
pct enter 100
systemctl start ai-scrum-orchestrator
systemctl status ai-scrum-orchestrator
```

### Start Workers
```bash
for i in {1..5}; do
  pct exec $((100 + i)) systemctl start ai-scrum-worker
done
```

## Step 6: Verify (2 minutes)

### Check Orchestrator Health
```bash
curl http://10.0.0.10:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "workers": 5,
  "active_tasks": 0,
  "uptime": "5m"
}
```

### Check Worker Connectivity
```bash
pct enter 100
for ip in 10.0.0.{11..15}; do
  ssh -i /root/.ssh/id_orchestrator root@$ip "echo 'Worker $ip: OK'"
done
```

## Step 7: Test with Sample Task

### Create GitHub Issue
From orchestrator container:

```bash
gh issue create \
  --repo YOUR_ORG/YOUR_REPO \
  --title "[Test] Create hello world function" \
  --body "Create a simple Python function that returns 'Hello, World!'" \
  --label "ai-ready,priority:high"
```

### Monitor Execution
```bash
# Watch orchestrator logs
journalctl -u ai-scrum-orchestrator -f

# Or watch specific worker
pct enter 101
journalctl -u ai-scrum-worker -f
```

## Troubleshooting

### Container won't start
```bash
# Check container status
pct status 100

# View container logs
pct enter 100
journalctl -xe
```

### Service fails to start
```bash
# Check service logs
systemctl status ai-scrum-orchestrator
journalctl -u ai-scrum-orchestrator -n 50
```

### Worker can't connect to orchestrator
```bash
# From worker container
ping 10.0.0.10
curl http://10.0.0.10:8000/health
```

### Claude Code not working
```bash
# Verify installation
claude --version

# Check API key
echo $ANTHROPIC_API_KEY

# Test CLI
claude "Write a hello world function"
```

## What's Next?

1. **Scale Up**: Add more workers as needed
2. **Monitor**: Setup Grafana dashboard for monitoring
3. **Production**: Point to production GitHub repository
4. **Automate**: Setup cron jobs for maintenance tasks

## Useful Commands

```bash
# View all containers
pct list

# Stop all services
for i in {1..5}; do pct exec $((100 + i)) systemctl stop ai-scrum-worker; done
pct exec 100 systemctl stop ai-scrum-orchestrator

# Restart all services
pct exec 100 systemctl restart ai-scrum-orchestrator
for i in {1..5}; do pct exec $((100 + i)) systemctl restart ai-scrum-worker; done

# View resource usage
pct exec 100 top
pct exec 101 htop
```

## Expected Performance

- Simple feature (50-100 LOC): 10-15 minutes
- Medium feature (200-500 LOC): 20-40 minutes
- Complex feature (500+ LOC): 40-90 minutes

With 5 parallel workers:
- **Throughput**: 5-10 features per hour
- **Daily capacity**: 50-100 features
- **Cost**: $5-15 per feature

## Support

For issues:
- Check logs: `journalctl -u ai-scrum-orchestrator -f`
- Review documentation: `deployment/PROXMOX_DEPLOYMENT.md`
- GitHub: https://github.com/YOUR_ORG/ai-scrum-master-v2/issues
