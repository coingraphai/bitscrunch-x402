#!/bin/bash
# Server Check and Update Script
# Run this on your server at 143.110.181.93

echo "==================================="
echo "Checking Server Code Status"
echo "==================================="
echo ""

# Check current directory
echo "1. Current Location:"
pwd
echo ""

# Check if repository exists
echo "2. Repository Status:"
if [ -d "/root/bitscrunch-x402" ]; then
    cd /root/bitscrunch-x402
    echo "✓ Repository found at: /root/bitscrunch-x402"
else
    echo "✗ Repository not found at /root/bitscrunch-x402"
    echo "Run: git clone https://github.com/coingraphai/bitscrunch-x402.git /root/bitscrunch-x402"
    exit 1
fi
echo ""

# Check git status
echo "3. Git Status:"
git status
echo ""

# Check current branch
echo "4. Current Branch:"
git branch --show-current
echo ""

# Check latest commit
echo "5. Latest Local Commit:"
git log -1 --oneline
echo ""

# Fetch latest from remote
echo "6. Fetching Latest from GitHub:"
git fetch origin
echo ""

# Check if updates available
echo "7. Checking for Updates:"
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✓ Code is up to date!"
else
    echo "✗ Updates available on GitHub"
    echo "Local:  $LOCAL"
    echo "Remote: $REMOTE"
    echo ""
    echo "To update, run:"
    echo "  git pull origin main"
fi
echo ""

# Check .env file
echo "8. Environment Configuration:"
if [ -f ".env" ]; then
    echo "✓ .env file exists"
    echo ""
    echo "Current URLs configured:"
    grep "FACILITATOR_URL" .env
    grep "RESOURCE_URL" .env
else
    echo "✗ .env file not found"
    echo "Run: cp .env.example .env"
    echo "Then edit with your configuration"
fi
echo ""

# Check virtual environment
echo "9. Python Virtual Environment:"
if [ -d "venv-py311" ]; then
    echo "✓ venv-py311 exists"
else
    echo "✗ venv-py311 not found"
    echo "Run: python3.11 -m venv venv-py311"
fi
echo ""

# Check if services are running
echo "10. Running Services:"
if pgrep -f "facilitator_server" > /dev/null; then
    echo "✓ Facilitator server is running"
    pgrep -af "facilitator_server"
else
    echo "✗ Facilitator server is not running"
fi

if pgrep -f "resource_server" > /dev/null; then
    echo "✓ Resource server is running"
    pgrep -af "resource_server"
else
    echo "✗ Resource server is not running"
fi

if pgrep -f "streamlit" > /dev/null; then
    echo "✓ Streamlit is running"
    pgrep -af "streamlit"
else
    echo "✗ Streamlit is not running"
fi
echo ""

# Check ports
echo "11. Port Status:"
echo "Checking if services are listening..."
if command -v netstat &> /dev/null; then
    netstat -tuln | grep -E ":(8001|8002|8501)" || echo "No services listening on expected ports"
elif command -v ss &> /dev/null; then
    ss -tuln | grep -E ":(8001|8002|8501)" || echo "No services listening on expected ports"
else
    echo "netstat/ss not available"
fi
echo ""

# Test endpoints
echo "12. Testing Endpoints:"
echo "Testing Facilitator..."
curl -s http://localhost:8002/health || echo "✗ Facilitator not responding"

echo ""
echo "Testing Resource Server..."
curl -s http://localhost:8001/health || echo "✗ Resource server not responding"
echo ""

echo "==================================="
echo "Check Complete!"
echo "==================================="
