#!/bin/bash
# Launch AI Scrum Master v2.0 in a new terminal window

cd "/Users/simonrice/Library/Mobile Documents/com~apple~CloudDocs/Development/repos/ai-scrum-master-v2"

echo "🎬 AI Scrum Master v2.0 - Test Run"
echo "=================================="
echo ""

# Run the test directly with Python
python3 -c "
from orchestrator import Orchestrator

print('🚀 Starting AI Scrum Master Test')
print('You will see all Claude Code output in real-time!\n')

orch = Orchestrator()

# Simple test
result = orch.process_user_story('Create a simple calculator web app with HTML, CSS, and JavaScript')

print(f'\n\n✅ Test Complete!')
print(f'Status: {\"APPROVED\" if result.approved else \"NOT APPROVED\"}')
print(f'Revisions: {result.revision_count}')
"

echo ""
echo "Press Enter to close..."
read
