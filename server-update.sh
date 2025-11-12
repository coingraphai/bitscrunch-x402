#!/bin/bash
# Server Update and Deployment Script
# Run this on your server at 143.110.181.93

set -e

echo "==================================="
echo "Updating and Deploying Application"
echo "==================================="
echo ""

# Navigate to repository
cd /root/bitscrunch-x402 || exit 1

# Stop existing services
echo "1. Stopping existing services..."
pkill -f "facilitator_server" || true
pkill -f "resource_server" || true
pkill -f "streamlit" || true
sleep 2
echo "✓ Services stopped"
echo ""

# Pull latest code
echo "2. Pulling latest code from GitHub..."
git pull origin main
echo "✓ Code updated"
echo ""

# Check if .env needs updating
echo "3. Checking environment configuration..."
if ! grep -q "RESOURCE_URL=http://143.110.181.93/resource" .env 2>/dev/null; then
    echo "⚠ .env file needs to be updated with server URLs"
    echo ""
    echo "Update these lines in .env:"
    echo "  FACILITATOR_URL=http://143.110.181.93/facilitator"
    echo "  RESOURCE_URL=http://143.110.181.93/resource"
    echo ""
    read -p "Press Enter after updating .env or Ctrl+C to exit..."
fi
echo "✓ Environment configuration checked"
echo ""

# Activate virtual environment and update dependencies
echo "4. Updating Python dependencies..."
source venv-py311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies updated"
echo ""

# Create logs directory
echo "5. Setting up logs directory..."
mkdir -p logs
echo "✓ Logs directory ready"
echo ""

# Start services
echo "6. Starting services..."
./start_servers.sh
echo "✓ Backend services started"
echo ""

# Start Streamlit
echo "7. Starting Streamlit frontend..."
nohup ./venv-py311/bin/streamlit run frontend/app_coingecko.py --server.port 8501 --server.address 0.0.0.0 > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "✓ Streamlit started (PID: $STREAMLIT_PID)"
echo ""

# Wait and test
echo "8. Waiting for services to start..."
sleep 5
echo ""

echo "9. Testing endpoints..."
echo ""
echo "Facilitator Health:"
curl -s http://localhost:8002/health && echo "" || echo "✗ Failed"

echo ""
echo "Resource Health:"
curl -s http://localhost:8001/health && echo "" || echo "✗ Failed"

echo ""
echo "Streamlit (check browser):"
echo "  http://143.110.181.93:8501"
echo ""

echo "==================================="
echo "Deployment Complete!"
echo "==================================="
echo ""
echo "Access your application:"
echo "  Frontend: http://143.110.181.93:8501"
echo "  Facilitator: http://143.110.181.93/facilitator"
echo "  Resource: http://143.110.181.93/resource"
echo ""
echo "View logs:"
echo "  tail -f logs/facilitator.log"
echo "  tail -f logs/resource.log"
echo "  tail -f logs/streamlit.log"
echo ""
