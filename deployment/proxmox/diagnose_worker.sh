#!/bin/bash
# Diagnose worker Python environment issues

WORKER_ID=${1:-205}

echo "=========================================="
echo "Diagnosing Worker $WORKER_ID"
echo "=========================================="
echo ""

echo "1. Checking Python version used by systemd service:"
pct exec $WORKER_ID -- grep "ExecStart" /etc/systemd/system/ai-worker.service
echo ""

echo "2. Checking which Python is in PATH for aimaster user:"
pct exec $WORKER_ID -- su - aimaster -c "which python3"
pct exec $WORKER_ID -- su - aimaster -c "python3 --version"
echo ""

echo "3. Checking if anthropic is installed for aimaster user:"
pct exec $WORKER_ID -- su - aimaster -c "python3 -m pip list | grep anthropic"
echo ""

echo "4. Checking if anthropic is installed system-wide:"
pct exec $WORKER_ID -- python3 -m pip list | grep anthropic
echo ""

echo "5. Checking Python path:"
pct exec $WORKER_ID -- su - aimaster -c "python3 -c 'import sys; print(sys.path)'"
echo ""

echo "6. Attempting to import anthropic:"
pct exec $WORKER_ID -- su - aimaster -c "python3 -c 'import anthropic; print(anthropic.__version__)'" 2>&1
echo ""

echo "7. Checking site-packages directories:"
pct exec $WORKER_ID -- su - aimaster -c "python3 -m site"
echo ""
