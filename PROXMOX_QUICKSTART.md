# Proxmox Deployment - Quick Start Guide

Deploy AI Scrum Master v2 across 5 LXC containers on your Proxmox cluster in under 30 minutes.

## What You'll Get

```
┌─────────────────────────────────────────────────────┐
│              Your Proxmox Cluster                    │
│                                                      │
│  🖥️  Orchestrator (10.0.0.100)                      │
│       FastAPI coordination service                   │
│                                                      │
│  🤖 Worker 1 (10.0.0.101)  🤖 Worker 2 (10.0.0.102) │
│  🤖 Worker 3 (10.0.0.103)  🤖 Worker 4 (10.0.0.104) │
│  🤖 Worker 5 (10.0.0.105)                           │
│                                                      │
│  Total: 12 CPU cores, 24GB RAM                      │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

### Hardware Requirements
- **Proxmox VE**: 7.0+ (or 8.x)
- **CPU**: At least 12 cores available
- **RAM**: Minimum 24GB free (4GB per container)
- **Storage**: 120GB available on storage pool
- **Network**: Configured bridge (default: vmbr0)

### Software Requirements
- SSH access to Proxmox host (root or sudo user)
- Ubuntu 22.04 LXC template downloaded
- Git installed on your local machine

### API Keys
- **Anthropic API Key**: Get from https://console.anthropic.com/
- **GitHub Token**: Personal Access Token with repo permissions
  - Create at: https://github.com/settings/tokens
  - Required scopes: `repo`, `workflow`

### Network Planning
Default network configuration (adjust if needed):
- **Network Range**: 10.0.0.0/24
- **Gateway**: 10.0.0.1
- **Orchestrator**: 10.0.0.100
- **Workers**: 10.0.0.101-105
- **Bridge**: vmbr0

> ⚠️ **Important**: Ensure these IPs are not already in use on your network!

## Step 1: Prepare Proxmox Host

### 1.1 Download Ubuntu Template

First, SSH to your Proxmox host and download the Ubuntu 22.04 template:

```bash
# SSH to Proxmox
ssh root@your-proxmox-host

# Update template list
pveam update

# List available Ubuntu templates
pveam available | grep ubuntu-22

# Download Ubuntu 22.04 template
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
```

This will download the template to `/var/lib/vz/template/cache/` and make it available as `local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst`.

### 1.2 Verify Network Configuration

Check your network bridge configuration:

```bash
# List network bridges
ip addr show

# Verify vmbr0 exists and has IP configured
# If using different bridge, note the name for later
```

### 1.3 Check Available Resources

Verify you have enough resources:

```bash
# Check available memory
free -h

# Check available CPU cores
nproc

# Check storage
pvesm status

# You should see local-lvm or similar storage with 120GB+ free
```

### 1.4 Transfer Deployment Scripts

On your **local machine**, navigate to your AI Scrum Master repository and transfer the scripts:

```bash
# Navigate to your repository
cd /path/to/ai-scrum-master-v2

# Transfer deployment scripts to Proxmox
scp -r deployment/proxmox root@your-proxmox-host:/root/ai-scrum-deployment

# You should see:
# deploy_lxc_cluster.sh
# setup_containers.sh
# start_cluster.sh
# stop_cluster.sh
# restart_cluster.sh
# status_cluster.sh
# view_logs.sh
# README.md
```

### 1.5 Prepare on Proxmox

Back on your Proxmox host:

```bash
# Navigate to deployment directory
cd /root/ai-scrum-deployment

# Make scripts executable
chmod +x *.sh

# Verify scripts are there
ls -lh
```

## Step 2: Deploy Containers (5-10 minutes)

### 2.1 Review Configuration (Optional)

Before deploying, you may want to customize network settings:

```bash
# Edit deploy_lxc_cluster.sh if you need to change:
# - IP addresses (BASE_IP)
# - Gateway (GATEWAY)
# - Bridge name (BRIDGE)
# - Storage location (STORAGE)
nano deploy_lxc_cluster.sh
```

**Default configuration:**
- Template: `local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst`
- Storage: `local-lvm`
- Bridge: `vmbr0`
- Network: `10.0.0.0/24`
- Gateway: `10.0.0.1`

### 2.2 Run Deployment Script

```bash
# Create all 6 LXC containers
./deploy_lxc_cluster.sh
```

**What this does:**
1. Checks if Proxmox tools are available
2. Verifies Ubuntu template exists
3. Creates 6 unprivileged LXC containers:
   - Container 100: Orchestrator (10.0.0.100)
   - Containers 101-105: Workers 1-5 (10.0.0.101-105)
4. Configures each with:
   - 2 CPU cores
   - 4GB RAM
   - 2GB swap
   - 20GB root filesystem
   - Network interface with static IP
   - Nesting enabled (for Docker/containers if needed)
5. Starts all containers
6. Waits 30 seconds for boot

**Expected output:**
```
==========================================
AI Scrum Master LXC Cluster Deployment
==========================================

Creating orchestrator container...
✅ Container 100 created

Creating worker containers...
✅ Container 101 created
✅ Container 102 created
✅ Container 103 created
✅ Container 104 created
✅ Container 105 created

Starting all containers...
Starting container 100...
Starting container 101...
[...]

Waiting for containers to boot (30s)...

==========================================
✅ Deployment Complete!
==========================================

Container Summary:
  ID  | Hostname           | IP Address      | Status
------|--------------------|-----------------|---------
  100 | Orchestrator       | 10.0.0.100      | running
  101 | Worker 1           | 10.0.0.101      | running
  102 | Worker 2           | 10.0.0.102      | running
  103 | Worker 3           | 10.0.0.103      | running
  104 | Worker 4           | 10.0.0.104      | running
  105 | Worker 5           | 10.0.0.105      | running
```

### 2.3 Verify Containers

```bash
# Check container status
pct list | grep ai-

# Verify containers can be accessed
pct exec 100 -- hostname
pct exec 101 -- hostname

# Test network connectivity
pct exec 101 -- ping -c 2 10.0.0.100
```

**Troubleshooting:**
- If template not found: Run `pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst`
- If IP conflict: Edit `BASE_IP` in script
- If storage full: Check `pvesm status` and adjust `STORAGE` variable
- If container won't start: Check `pct start 100 --debug`

## Step 3: Configure Software (15-20 minutes)

### 3.1 Prepare API Keys

**Get your Anthropic API Key:**
1. Go to https://console.anthropic.com/
2. Navigate to API Keys
3. Create a new key or copy existing one
4. It should start with `sk-ant-`

**Get your GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`
4. Generate and copy the token (starts with `ghp_`)

### 3.2 Configure Repository URL

Edit the setup script to point to your repository:

```bash
nano setup_containers.sh

# Find this line:
# REPO_URL="${REPO_URL:-https://github.com/YOUR_ORG/ai-scrum-master-v2.git}"

# Change to your actual repository URL:
# REPO_URL="${REPO_URL:-https://github.com/yourusername/ai-scrum-master-v2.git}"

# Save and exit (Ctrl+X, Y, Enter)
```

### 3.3 Set Environment Variables

```bash
# Set your API keys (replace with your actual keys)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
export GITHUB_TOKEN="ghp_your-token-here"

# Optionally set repository URL
export REPO_URL="https://github.com/yourusername/ai-scrum-master-v2.git"

# Verify they're set
echo $ANTHROPIC_API_KEY
echo $GITHUB_TOKEN
```

> ⚠️ **Security Note**: These keys will be stored in `.env` files on each container. Consider using a secrets management system for production.

### 3.4 Run Setup Script

```bash
# Install and configure all software (takes 15-20 minutes)
./setup_containers.sh
```

**What this does for each container:**

1. **System Updates**
   - Updates apt package lists
   - Upgrades existing packages
   - Installs build tools

2. **Install Python 3.11**
   - Installs Python 3.11 and pip
   - Creates virtual environment
   - Installs Python dependencies

3. **Install Node.js 20**
   - Adds NodeSource repository
   - Installs Node.js 20.x and npm

4. **Install Claude Code CLI**
   - Installs `@anthropic-ai/claude-code` globally

5. **Setup Application**
   - Creates `aimaster` user
   - Clones repository
   - Creates Python virtual environment
   - Installs requirements
   - Creates `.env` file with API keys
   - Creates workspace directories

6. **Configure Services**
   - Creates systemd service files
   - Enables auto-start on boot
   - Configures logging

**Expected output:**
```
==========================================
AI Scrum Master Container Setup
==========================================

Setting up container 100 (orchestrator)...
  Installing system dependencies...
  Installing Node.js...
  Installing Claude Code CLI...
  Creating aimaster user...
  Setting up application...
  Creating systemd service...
✅ Container 100 configured successfully

Setting up container 101 (worker-01)...
  Installing system dependencies...
  [...]
✅ Container 101 configured successfully

[Continues for all containers...]

==========================================
✅ Setup Complete!
==========================================

All containers configured with:
  • Ubuntu 22.04
  • Python 3.11
  • Node.js 20
  • Claude Code CLI
  • AI Scrum Master v2
  • Systemd services

Next Steps:
  1. Verify API keys are set in .env files
  2. Start orchestrator:  pct exec 100 -- systemctl start ai-orchestrator
  3. Start workers:       for id in {101..105}; do pct exec $id -- systemctl start ai-worker; done
```

### 3.5 Verify Installation

```bash
# Check Python is installed
pct exec 100 -- python3 --version

# Check Node.js is installed
pct exec 100 -- node --version

# Check Claude Code is installed
pct exec 100 -- claude --version

# Check application files
pct exec 100 -- ls -la /home/aimaster/ai-scrum-master-v2/

# Check .env file was created
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && cat .env'
```

**Troubleshooting:**
- If apt update fails: Check container internet connectivity
- If Node.js install fails: Manually add NodeSource repo
- If Claude Code not found: Check npm global install path
- If repository clone fails: Verify repository URL and network access
- If .env empty: API keys not exported, re-run with export commands

## Step 4: Start the Cluster (2-3 minutes)

### 4.1 Start Services

```bash
# Start all services
./start_cluster.sh
```

**What this does:**
1. Starts orchestrator service (container 100)
2. Waits for orchestrator API to be ready
3. Starts all worker services (containers 101-105)
4. Verifies service status
5. Shows access information

**Expected output:**
```
==========================================
Starting AI Scrum Master Cluster
==========================================

Starting orchestrator (container 100)...
  ✅ Orchestrator started

Waiting for orchestrator to be ready...
  ✅ Orchestrator is ready

Starting workers (containers 101-105)...
  ✅ Worker 1 started
  ✅ Worker 2 started
  ✅ Worker 3 started
  ✅ Worker 4 started
  ✅ Worker 5 started

==========================================
✅ Cluster Started
==========================================

Service Status:

  Orchestrator: active
  Worker 1:     active
  Worker 2:     active
  Worker 3:     active
  Worker 4:     active
  Worker 5:     active

Access Points:
  • Orchestrator API: http://10.0.0.100:8000
  • Health Check:     http://10.0.0.100:8000/health
  • Worker Status:    http://10.0.0.100:8000/workers

View Logs:
  • Orchestrator: pct exec 100 -- journalctl -u ai-orchestrator -f
  • Worker 1:     pct exec 101 -- journalctl -u ai-worker -f
```

### 4.2 Verify Cluster Health

```bash
# Check orchestrator API
curl http://10.0.0.100:8000/health

# Should return:
# {"status":"ok","version":"2.4.0"}

# Check registered workers
curl http://10.0.0.100:8000/workers

# Should show all 5 workers registered

# Check service status on each container
pct exec 100 -- systemctl status ai-orchestrator
pct exec 101 -- systemctl status ai-worker
```

### 4.3 View Live Logs

```bash
# Watch orchestrator logs (Ctrl+C to exit)
pct exec 100 -- journalctl -u ai-orchestrator -f

# Watch worker 1 logs in another terminal
pct exec 101 -- journalctl -u ai-worker -f

# Or use the log viewer script
./view_logs.sh
```

**Troubleshooting:**
- **Orchestrator won't start**: Check logs with `pct exec 100 -- journalctl -u ai-orchestrator -n 50`
- **API not responding**: Verify port 8000 is listening: `pct exec 100 -- netstat -tlnp | grep 8000`
- **Worker can't connect**: Test connectivity: `pct exec 101 -- curl http://10.0.0.100:8000/health`
- **Service fails immediately**: Check API keys in .env file
- **Python errors**: Verify virtual environment: `pct exec 100 -- ls /home/aimaster/ai-scrum-master-v2/env/`

## Step 5: Verify Everything Works

### 5.1 Check Cluster Status

```bash
# Run status script
./status_cluster.sh
```

**Expected output:**
```
==========================================
AI Scrum Master Cluster Status
==========================================

Container Status:
  ID  | Hostname           | IP Address      | Status   | CPU    | Memory
------|--------------------|-----------------|-----------|---------|---------
  100 | Orchestrator       | 10.0.0.100      | running  | 5.2%   | 1.2G/4G
  101 | Worker 1           | 10.0.0.101      | running  | 3.1%   | 1.5G/4G
  102 | Worker 2           | 10.0.0.102      | running  | 3.4%   | 1.4G/4G
  103 | Worker 3           | 10.0.0.103      | running  | 2.8%   | 1.3G/4G
  104 | Worker 4           | 10.0.0.104      | running  | 3.2%   | 1.5G/4G
  105 | Worker 5           | 10.0.0.105      | running  | 3.0%   | 1.4G/4G

Service Status:
  Orchestrator: active
  Worker 1:     active
  Worker 2:     active
  Worker 3:     active
  Worker 4:     active
  Worker 5:     active

Orchestrator Health:
  API Status: healthy
  Workers Registered: 5 / 5

Resource Summary:
  Total CPU Cores: 12
  Total Memory: 24GB
```

### 5.2 Test Orchestrator API

```bash
# Health check
curl http://10.0.0.100:8000/health

# List workers
curl http://10.0.0.100:8000/workers | jq

# Check queue status
curl http://10.0.0.100:8000/queue/status | jq
```

### 5.3 Test with a GitHub Issue

**Create a test issue in your repository:**

```bash
# From your local machine with gh CLI installed
gh issue create \
  --repo yourusername/your-repo \
  --title "Test: Add hello world function" \
  --body "Create a simple hello world function in Python" \
  --label "ready-for-dev"
```

**Monitor the workers:**

```bash
# On Proxmox, watch logs
./view_logs.sh

# Or watch specific worker
pct exec 101 -- journalctl -u ai-worker -f
```

You should see:
1. Worker picks up the issue
2. Processes through all agents (Architect → Security → Tester → PO)
3. Creates a pull request
4. Reports completion

### 5.4 View All Logs

```bash
# Interactive log viewer with menu
./view_logs.sh

# Direct access to specific logs
./view_logs.sh orchestrator  # Live orchestrator logs
./view_logs.sh worker1       # Live worker 1 logs
./view_logs.sh all           # Summary of all workers
```

### 5.5 Check from Proxmox Web UI

1. Open Proxmox web interface
2. Navigate to each container (100-105)
3. Check "Summary" tab for resource usage
4. Check "Console" to access container directly
5. Verify all containers show green "running" status

## Managing Your Cluster

### Daily Operations

```bash
# Start cluster (after reboot)
./start_cluster.sh

# Check status
./status_cluster.sh

# View logs interactively
./view_logs.sh

# Stop cluster
./stop_cluster.sh

# Restart cluster
./restart_cluster.sh
```

### Monitoring

```bash
# Live orchestrator logs
pct exec 100 -- journalctl -u ai-orchestrator -f

# Live worker 1 logs
pct exec 101 -- journalctl -u ai-worker -f

# Check API health
curl http://10.0.0.100:8000/health

# See registered workers
curl http://10.0.0.100:8000/workers
```

### Troubleshooting

```bash
# Check service status
pct exec 100 -- systemctl status ai-orchestrator
pct exec 101 -- systemctl status ai-worker

# Restart a specific service
pct exec 101 -- systemctl restart ai-worker

# Enter a container
pct enter 100  # Orchestrator
pct enter 101  # Worker 1

# Check resource usage
./status_cluster.sh
```

## Configuration

### Update API Keys

If you need to update API keys after deployment:

```bash
# Edit orchestrator .env
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && nano .env'

# Edit worker 1 .env
pct exec 101 -- su - aimaster -c 'cd ai-scrum-master-v2 && nano .env'

# Restart services
./restart_cluster.sh
```

### Adjust Resources

```bash
# Increase worker 1 memory to 6GB
pct set 101 --memory 6144

# Add more CPU cores to orchestrator
pct set 100 --cores 4

# Increase swap
pct set 101 --swap 4096
```

## Usage Example

Once running, workers will automatically:
1. Poll GitHub for issues labeled `ready-for-dev`
2. Process issues concurrently (5 at a time)
3. Create pull requests when complete
4. Report status to orchestrator

### Create Test Issues

**Method 1: Using GitHub CLI (recommended)**

```bash
# Install gh CLI if not already installed
# macOS: brew install gh
# Linux: See https://cli.github.com/

# Authenticate
gh auth login

# Create a test issue
gh issue create \
  --repo yourusername/your-repo \
  --title "Test: Add calculator function" \
  --body "Create a simple calculator with add, subtract, multiply, divide operations" \
  --label "ready-for-dev"
```

**Method 2: Using GitHub Web Interface**

1. Go to your repository on GitHub
2. Click "Issues" → "New Issue"
3. Title: "Test: Add hello world function"
4. Body: "Create a simple hello world function"
5. Add label: `ready-for-dev`
6. Click "Submit new issue"

**Method 3: Using API**

```bash
curl -X POST https://api.github.com/repos/USERNAME/REPO/issues \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test: Add utility function",
    "body": "Create a utility function for string manipulation",
    "labels": ["ready-for-dev"]
  }'
```

### Monitor Worker Progress

**Watch in real-time:**

```bash
# Terminal 1: Watch orchestrator
pct exec 100 -- journalctl -u ai-orchestrator -f

# Terminal 2: Watch first available worker
pct exec 101 -- journalctl -u ai-worker -f

# Or use the interactive viewer
./view_logs.sh
```

**You should see:**
1. Worker fetches issue from GitHub
2. Architect agent writes code
3. Security agent reviews
4. Tester agent creates tests
5. Product Owner approves
6. PR created on GitHub

**Check queue status:**

```bash
# See what's being processed
curl http://10.0.0.100:8000/queue/status

# Check worker activity
./status_cluster.sh
```

**Expected timeline:**
- Simple feature: 10-15 minutes
- Medium feature: 20-30 minutes
- Complex feature: 30-60 minutes

## Performance

With 5 parallel workers, you can expect:

- **Throughput**: ~5 issues processed simultaneously
- **Simple feature**: ~10-15 minutes per worker
- **Daily capacity**: ~100-150 features (assuming 8-hour operation)
- **Cost**: ~$0.08 per simple feature
- **Monthly cost**: ~$60-180 (depending on usage)

## Network Access

### Access from Outside Proxmox

To access orchestrator API from external network:

```bash
# On Proxmox host, forward port 8000
iptables -t nat -A PREROUTING -p tcp --dport 8000 \
  -j DNAT --to-destination 10.0.0.100:8000

# Save rules
iptables-save > /etc/iptables/rules.v4

# Now access from anywhere
curl http://your-proxmox-ip:8000/health
```

## Backup

```bash
# Backup entire cluster
vzdump 100,101,102,103,104,105 \
  --mode snapshot \
  --compress zstd \
  --storage local

# Backups saved to /var/lib/vz/dump/
```

## Scaling

### Add More Workers

```bash
# Create worker 6
pct create 106 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname ai-worker-6 \
  --cores 2 \
  --memory 4096 \
  --rootfs 20 \
  --net0 name=eth0,bridge=vmbr0,ip=10.0.0.106/24,gw=10.0.0.1 \
  --features nesting=1

pct start 106

# Configure it (manually run setup steps)
```

### Scale Down

```bash
# Stop worker 5
pct exec 105 -- systemctl stop ai-worker
pct stop 105

# Remove if no longer needed
pct destroy 105
```

## Common Issues & Solutions

### Issue: Container Won't Start

**Symptoms:**
- `pct status 100` shows "stopped"
- Container won't start with `pct start 100`

**Solutions:**

```bash
# 1. Check detailed error
pct start 100 --debug

# 2. Check Proxmox logs
tail -f /var/log/pve/tasks/*.log

# 3. Verify template exists
pveam list local | grep ubuntu-22

# 4. Check if another container is using same ID
pct list

# 5. If corrupt, destroy and recreate
pct destroy 100
./deploy_lxc_cluster.sh  # Re-run deployment
```

### Issue: Service Won't Start

**Symptoms:**
- Service status shows "failed"
- `systemctl status ai-orchestrator` shows errors

**Solutions:**

```bash
# 1. Check service logs
pct exec 100 -- journalctl -u ai-orchestrator -n 100 --no-pager

# 2. Check Python environment
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && source env/bin/activate && python --version'

# 3. Verify API key is set
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && cat .env | grep ANTHROPIC'

# 4. Test manual startup
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && source env/bin/activate && python orchestrator_service/server.py'

# 5. Check for port conflicts
pct exec 100 -- netstat -tlnp | grep 8000

# 6. Reinstall dependencies
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && source env/bin/activate && pip install -r requirements.txt'
```

### Issue: Worker Can't Connect to Orchestrator

**Symptoms:**
- Worker logs show connection errors
- `curl http://10.0.0.100:8000/health` fails from worker

**Solutions:**

```bash
# 1. Test network connectivity
pct exec 101 -- ping -c 4 10.0.0.100

# 2. Check if orchestrator is listening
pct exec 100 -- netstat -tlnp | grep 8000
pct exec 100 -- ss -tlnp | grep 8000

# 3. Test from worker container
pct exec 101 -- curl -v http://10.0.0.100:8000/health

# 4. Check firewall on orchestrator
pct exec 100 -- ufw status
# If enabled, allow port 8000:
pct exec 100 -- ufw allow 8000

# 5. Verify orchestrator is actually running
pct exec 100 -- systemctl status ai-orchestrator

# 6. Check ORCHESTRATOR_URL in worker .env
pct exec 101 -- su - aimaster -c 'cd ai-scrum-master-v2 && cat .env | grep ORCHESTRATOR'
```

### Issue: API Keys Not Working

**Symptoms:**
- Authentication errors in logs
- "Invalid API key" messages

**Solutions:**

```bash
# 1. Verify keys are set in .env
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && cat .env'

# 2. Check for extra spaces or quotes
# Keys should be: ANTHROPIC_API_KEY=sk-ant-xxx (no quotes)

# 3. Update keys manually
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && nano .env'

# 4. Restart service after updating
pct exec 100 -- systemctl restart ai-orchestrator

# 5. Test API key from container
pct exec 100 -- su - aimaster -c 'cd ai-scrum-master-v2 && source env/bin/activate && python -c "import os; print(os.getenv(\"ANTHROPIC_API_KEY\"))"'
```

### Issue: High CPU/Memory Usage

**Symptoms:**
- Container using 100% CPU
- Out of memory errors
- System sluggish

**Solutions:**

```bash
# 1. Check resource usage
./status_cluster.sh

# 2. Check what's consuming resources
pct exec 101 -- top -bn1 | head -20

# 3. Increase container resources
pct set 101 --memory 6144  # Increase to 6GB
pct set 101 --cores 4      # Increase to 4 cores

# 4. Restart the container
pct reboot 101

# 5. Check for runaway processes
pct exec 101 -- ps aux | grep python
```

### Issue: "Template not found"

**Symptoms:**
- Deploy script fails with template error

**Solutions:**

```bash
# 1. Download template
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst

# 2. Verify download completed
ls -lh /var/lib/vz/template/cache/

# 3. Check available templates
pveam list local

# 4. If different template name, update script
nano deploy_lxc_cluster.sh
# Change TEMPLATE= line to match your template
```

### Issue: Network Connectivity Problems

**Symptoms:**
- Can't reach internet from containers
- Can't ping between containers

**Solutions:**

```bash
# 1. Check bridge configuration
ip addr show vmbr0

# 2. Test internet from container
pct exec 100 -- ping -c 4 8.8.8.8
pct exec 100 -- ping -c 4 google.com

# 3. Check DNS resolution
pct exec 100 -- cat /etc/resolv.conf

# 4. Verify gateway
pct exec 100 -- ip route

# 5. Check firewall rules on Proxmox host
iptables -L -n
```

### Issue: Repository Clone Fails

**Symptoms:**
- Setup script can't clone repository
- "Permission denied" or "Not found" errors

**Solutions:**

```bash
# 1. Test git from container
pct exec 100 -- git ls-remote https://github.com/yourusername/your-repo.git

# 2. Check if repository is private and token is needed
# For private repos, use token in URL:
export REPO_URL="https://$GITHUB_TOKEN@github.com/yourusername/repo.git"

# 3. Clone manually to debug
pct exec 100 -- su - aimaster -c 'git clone https://github.com/yourusername/repo.git test-clone'

# 4. Verify network access to GitHub
pct exec 100 -- curl -I https://github.com
```

### Getting More Help

If issues persist:

1. **Check comprehensive logs:**
   ```bash
   ./view_logs.sh
   ```

2. **Review full documentation:**
   - [docs/PROXMOX_LXC_DEPLOYMENT.md](docs/PROXMOX_LXC_DEPLOYMENT.md)
   - [deployment/proxmox/README.md](deployment/proxmox/README.md)

3. **Check Proxmox system logs:**
   ```bash
   journalctl -xe
   ```

4. **Verify Proxmox version:**
   ```bash
   pveversion
   ```

5. **Join our community or open an issue on GitHub**

## Next Steps

1. **Test with Real Issues**: Create GitHub issues with `ready-for-dev` label
2. **Monitor Performance**: Use `./status_cluster.sh` and logs
3. **Optimize**: Adjust worker count based on workload
4. **Automate**: Set up automated backups
5. **Scale**: Add more workers as needed

## Documentation

- **Full Deployment Guide**: [docs/PROXMOX_LXC_DEPLOYMENT.md](docs/PROXMOX_LXC_DEPLOYMENT.md)
- **Script Reference**: [deployment/proxmox/README.md](deployment/proxmox/README.md)
- **Parallel Architecture**: [DISTRIBUTED_ARCHITECTURE.md](DISTRIBUTED_ARCHITECTURE.md)

## Getting Help

If you encounter issues:

1. Check logs: `./view_logs.sh`
2. Verify status: `./status_cluster.sh`
3. Review documentation in `docs/`
4. Check Proxmox system logs
5. Open an issue on GitHub

---

**Estimated Setup Time**: 30 minutes
**Difficulty**: Intermediate
**Requirements**: Proxmox access, API keys

🚀 **Ready to deploy?** Start with Step 1!
