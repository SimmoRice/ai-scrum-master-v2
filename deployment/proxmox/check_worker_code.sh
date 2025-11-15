#\!/bin/bash
# Check what version of code workers have
for id in 201 202 203 204 205; do
    echo "=== Worker $((id-200)) (Container $id) ==="
    pct exec $id -- su - aimaster -c "cd ai-scrum-master-v2 && git log --oneline -1"
    echo ""
done
