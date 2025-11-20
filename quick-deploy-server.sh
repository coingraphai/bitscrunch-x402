#!/bin/bash
# Quick Copy-Paste Deployment Script
# Run this entire script on your server: 143.110.181.93

echo "========================================="
echo "Starting Deployment..."
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

# Step 4: Install Python 3.11 if needed
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    apt-get update
    apt-get install -y python3.11 python3.11-venv python3.11-dev build-essential
fi

# Step 5: Setup virtual environment
if [ ! -d "venv-py311" ]; then
    echo "Creating virtual environment..."
    python3.11 -m venv venv-py311
fi

source venv-py311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Step 6: Create logs directory
mkdir -p logs

# Step 7: Install nginx
if ! command -v nginx &> /dev/null; then
    echo "Installing nginx..."
    apt-get install -y nginx
fi

# Step 8: Configure nginx
cp nginx-x402.conf /etc/nginx/sites-available/x402-bitscrunch
ln -sf /etc/nginx/sites-available/x402-bitscrunch /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Step 9: Stop old services
echo "Stopping old services..."
pkill -f facilitator_server || true
pkill -f resource_server || true
pkill -f streamlit || true
sleep 2

# Step 10: Start backend services
echo "Starting backend services..."
chmod +x start_servers_production.sh
./start_servers_production.sh

# Step 11: Start Streamlit
echo "Starting Streamlit..."
nohup ./venv-py311/bin/streamlit run frontend/app_coingecko.py \
    --server.port 4000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    > logs/streamlit.log 2>&1 &

sleep 3

# Step 12: Test everything
echo ""
echo "========================================="
echo "Testing endpoints..."
echo "========================================="
curl http://localhost:3001/health && echo "✅ Facilitator OK"
curl http://localhost:3000/health && echo "✅ Resource OK"
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000 && echo " ✅ Streamlit OK"

echo ""
echo "========================================="
echo "🎉 Deployment Complete!"
echo "========================================="
echo ""
echo "Access your app:"
echo "  http://143.110.181.93"
echo ""
echo "API Endpoints:"
echo "  http://143.110.181.93/api/facilitator"
echo "  http://143.110.181.93/api/resource"
echo ""
echo "View logs:"
echo "  tail -f /root/bitscrunch-x402/logs/facilitator.log"
echo "  tail -f /root/bitscrunch-x402/logs/resource.log"
echo "  tail -f /root/bitscrunch-x402/logs/streamlit.log"
echo ""
