#!/bin/bash
# deploy_lxc_cluster.sh - Deploy AI Scrum Master cluster on Proxmox
#
# Usage:
#   ./deploy_lxc_cluster.sh
#
# Prerequisites:
#   - Run on Proxmox host as root
#   - Ubuntu 22.04 template downloaded
#   - Network bridge configured (vmbr0)

set -e

# Configuration
TEMPLATE="local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst"
STORAGE="zfs-store"
BRIDGE="vmbr0"
GATEWAY="192.168.100.254"
NAMESERVER="192.168.100.251"
BASE_IP="192.168.100"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "AI Scrum Master LXC Cluster Deployment"
echo "=========================================="
echo ""

# Check if running on Proxmox
if ! command -v pct &> /dev/null; then
    echo -e "${RED}Error: pct command not found. Are you running on Proxmox?${NC}"
    exit 1
fi

# Check if template exists
if ! pveam list local | grep -q "ubuntu-22.04-standard"; then
    echo -e "${YELLOW}Warning: Ubuntu 22.04 template not found${NC}"
    echo "Downloading template..."
    pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.zst
fi

# Function to create container
create_container() {
    local id=$1
    local hostname=$2
    local ip=$3
    local cores=$4
    local memory=$5

    echo -e "${GREEN}Creating container $id ($hostname) at $ip...${NC}"

    # Check if container already exists
    if pct status $id &> /dev/null; then
        echo -e "${YELLOW}Container $id already exists. Skipping...${NC}"
        return
    fi

    pct create $id $TEMPLATE \
        --hostname $hostname \
        --cores $cores \
        --memory $memory \
        --swap $((memory / 2)) \
        --storage $STORAGE \
        --rootfs 20 \
        --net0 name=eth0,bridge=$BRIDGE,ip=$ip/24,gw=$GATEWAY \
        --nameserver $NAMESERVER \
        --features nesting=1 \
        --unprivileged 1 \
        --onboot 1

    echo -e "${GREEN}✅ Container $id created${NC}"
}

# Create orchestrator container
echo ""
echo "Creating orchestrator container..."
create_container 200 "ai-orchestrator" "$BASE_IP.200" 2 4096

# Create worker containers
echo ""
echo "Creating worker containers..."
for id in {201..205}; do
    worker_num=$((id - 200))
    ip="$BASE_IP.$id"
    create_container $id "ai-worker-$worker_num" "$ip" 2 4096
done

# Start all containers
echo ""
echo "Starting all containers..."
for id in {200..205}; do
    if pct status $id | grep -q "stopped"; then
        echo "Starting container $id..."
        pct start $id
        sleep 3
    else
        echo "Container $id already running"
    fi
done

# Wait for containers to boot
echo ""
echo "Waiting for containers to boot (30s)..."
sleep 30

# Display summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Container Summary:"
echo "  ID  | Hostname           | IP Address      | Status"
echo "------|--------------------|-----------------|---------"

for id in {200..205}; do
    if [ $id -eq 200 ]; then
        name="Orchestrator"
    else
        name="Worker $((id - 200))"
    fi

    ip="$BASE_IP.$id"
    status=$(pct status $id | awk '{print $2}')

    printf "  %-3s | %-18s | %-15s | %s\n" "$id" "$name" "$ip" "$status"
done

echo ""
echo "Next Steps:"
echo "  1. Run setup_containers.sh to configure software"
echo "  2. Update .env files with your API keys"
echo "  3. Start the services"
echo ""
echo "Quick commands:"
echo "  # Enter orchestrator: pct enter 200"
echo "  # Enter worker 1:     pct enter 201"
echo "  # Check logs:         pct exec 201 -- journalctl -u ai-worker -f"
echo ""
