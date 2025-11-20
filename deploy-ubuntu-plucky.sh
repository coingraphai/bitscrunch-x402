#!/bin/bash
# Fixed Deployment Script for Ubuntu Plucky (24.10)
# Works with system Python 3.12 instead of requiring Python 3.11

set -e

echo "========================================="
echo "Starting Deployment (Ubuntu Plucky Fix)..."
echo "========================================="

# Step 1: Navigate or clone
if [ ! -d "/root/bitscrunch-x402" ]; then
    echo "Cloning repository..."
    git clone https://github.com/coingraphai/bitscrunch-x402.git /root/bitscrunch-x402
fi

cd /root/bitscrunch-x402

# Step 2: Pull latest
echo "Pulling latest code..."
git pull origin main

# Step 3: Copy production config
echo "Setting up environment..."
cp .env.production .env

# Step 4: Remove deadsnakes PPA if it exists (causes issues on Plucky)
echo "Cleaning up repository lists..."
rm -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-plucky.list
rm -f /etc/apt/sources.list.d/deadsnakes-ubuntu-ppa-plucky.sources

# Step 5: Use system Python (3.12 on Ubuntu Plucky)
echo "Checking Python installation..."
apt-get update
apt-get install -y python3 python3-venv python3-dev python3-pip build-essential

PYTHON_VERSION=$(python3 --version)
echo "Using: $PYTHON_VERSION"

# Step 6: Setup virtual environment with system Python
VENV_DIR="venv-py311"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 7: Create logs directory
mkdir -p logs

# Step 8: Install nginx
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    apt-get install -y nginx
fi

# Step 9: Configure nginx
echo "Configuring nginx..."
cp nginx-x402.conf /etc/nginx/sites-available/x402-bitscrunch
ln -sf /etc/nginx/sites-available/x402-bitscrunch /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Step 10: Stop old services
echo "Stopping old services..."
pkill -f facilitator_server || true
pkill -f resource_server || true
pkill -f streamlit || true
sleep 2

# Step 11: Start backend services
echo "Starting backend services..."
chmod +x start_servers_production.sh

# Update the script to use our venv
sed -i 's/venv-py311/venv-py311/g' start_servers_production.sh

./start_servers_production.sh

# Step 12: Start Streamlit
echo "Starting Streamlit..."
nohup ./$VENV_DIR/bin/streamlit run frontend/app_coingecko.py \
    --server.port 4000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    > logs/streamlit.log 2>&1 &

sleep 3

# Step 13: Test everything
echo ""
echo "========================================="
echo "Testing endpoints..."
echo "========================================="

echo -n "Facilitator: "
curl -s http://localhost:3001/health && echo " ✅" || echo " ❌"

echo -n "Resource: "
curl -s http://localhost:3000/health && echo " ✅" || echo " ❌"

echo -n "Streamlit: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "✅"
else
    echo "❌ (HTTP $HTTP_CODE)"
fi

echo ""
echo "========================================="
echo "🎉 Deployment Complete!"
echo "========================================="
echo ""
echo "Access your app:"
echo "  http://143.110.181.93"
echo ""
echo "API Endpoints:"
echo "  http://143.110.181.93/api/facilitator/health"
echo "  http://143.110.181.93/api/resource/health"
echo ""
echo "View logs:"
echo "  tail -f /root/bitscrunch-x402/logs/facilitator.log"
echo "  tail -f /root/bitscrunch-x402/logs/resource.log"
echo "  tail -f /root/bitscrunch-x402/logs/streamlit.log"
echo ""
echo "Python version used: $PYTHON_VERSION"
echo ""
