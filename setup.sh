#!/bin/bash
# Setup script for AI Scrum Master v2.0

echo "🚀 Setting up AI Scrum Master v2.0..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Check if Claude Code is installed
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code is not installed"
    echo "   Please install Claude Code from: https://claude.com/code"
    exit 1
fi

echo "✅ Claude Code found: $(claude --version)"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  No .env file found"
    echo "   Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your ANTHROPIC_API_KEY"
    echo "   Get your API key from: https://console.anthropic.com/"
    echo ""
else
    echo "✅ .env file exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your ANTHROPIC_API_KEY (if not already done)"
echo "  2. Run: python3 main.py"
echo "  3. Type 'help' for available commands"
echo ""
echo "Example usage:"
echo "  > task Build a simple calculator web app with HTML, CSS, and JavaScript"
echo ""
