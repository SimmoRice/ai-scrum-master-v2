# Fix Workspace Path Issue - Workers Still Using /home

## Problem
Workers showing: `Workspace: /home/aimaster/workspace`
Should be: `Workspace: /opt/ai-scrum-master/workspace`

## Root Cause
Systemd services cache environment variables. Updating `.env` isn't enough - need to:
1. Stop service
2. Update .env
3. Reload systemd daemon
4. Start service

## Quick Fix - Run These Commands on Proxmox

### Fix All Workers at Once

```bash
for id in 201 202 203 204 205; do
    echo "=== Fixing Worker $id ==="

    # Stop service
    pct exec $id -- systemctl stop ai-worker

    # Update .env
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && sed -i '/^WORKSPACE_DIR=/d' .env && echo 'WORKSPACE_DIR=/opt/ai-scrum-master/workspace' >> .env"

    # Create workspace directory
    pct exec $id -- mkdir -p /opt/ai-scrum-master/workspace
    pct exec $id -- chown -R aimaster:aimaster /opt/ai-scrum-master/workspace

    # Reload and start
    pct exec $id -- systemctl daemon-reload
    pct exec $id -- systemctl start ai-worker

    sleep 2
done
```

### Verify Fix

```bash
# Check logs for correct workspace path
for id in 201 202 203 204 205; do
    echo "=== Worker $id ==="
    pct exec $id -- journalctl -u ai-worker -n 3 --no-pager | grep -i workspace
done
```

You should see:
```
INFO - Workspace: /opt/ai-scrum-master/workspace
```

NOT:
```
INFO - Workspace: /home/aimaster/workspace
```

### If Still Not Working

Check if systemd service has hardcoded workspace:

```bash
pct exec 201 -- cat /etc/systemd/system/ai-worker.service
```

Look for any `Environment=WORKSPACE_DIR=` lines.

If found, remove them:

```bash
for id in 201 202 203 204 205; do
    pct exec $id -- sed -i '/Environment=WORKSPACE_DIR=/d' /etc/systemd/system/ai-worker.service
    pct exec $id -- systemctl daemon-reload
    pct exec $id -- systemctl restart ai-worker
done
```

### Alternative: Check Worker Code Default

The worker code might have a hardcoded default. Check:

```bash
pct exec 201 -- su - aimaster -c "cd ai-scrum-master-v2 && grep -n 'workspace' worker/distributed_worker.py | head -20"
```

If you see something like:
```python
workspace_dir = os.getenv("WORKSPACE_DIR", "/home/aimaster/workspace")
```

The second parameter is the default when WORKSPACE_DIR is not set.

## Full Diagnostic

Run this to see ALL places workspace might be defined:

```bash
echo "=== Checking Worker 201 ==="

echo "1. .env file:"
pct exec 201 -- su - aimaster -c "cd ai-scrum-master-v2 && cat .env | grep WORKSPACE"

echo ""
echo "2. Systemd service:"
pct exec 201 -- cat /etc/systemd/system/ai-worker.service | grep -i workspace || echo "Not in service"

echo ""
echo "3. Current running process:"
pct exec 201 -- ps aux | grep distributed_worker

echo ""
echo "4. Recent logs:"
pct exec 201 -- journalctl -u ai-worker -n 5 --no-pager | grep -i workspace
```
