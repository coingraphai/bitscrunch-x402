#!/bin/bash
# Complete Deployment Script for Digital Ocean Server
# Server: 143.110.181.93
# Ports: 3000 (resource), 3001 (facilitator), 4000 (streamlit)

set -e

echo "=============================================="
echo "x402 Protocol Production Deployment"
echo "Digital Ocean Droplet: 143.110.181.93"
echo "=============================================="
echo ""

# Check if running on server
if [ ! -d "/root/bitscrunch-x402" ]; then
    echo "⚠️  This script should be run on the production server"
    echo ""
    echo "First, SSH to your server:"
    echo "  ssh root@143.110.181.93"
    echo ""
    echo "Then clone the repository:"
    echo "  git clone https://github.com/coingraphai/bitscrunch-x402.git /root/bitscrunch-x402"
    echo "  cd /root/bitscrunch-x402"
    echo "  ./deploy_production.sh"
    exit 1
fi

cd /root/bitscrunch-x402

# 1. Update code
echo "📦 Step 1: Updating code from GitHub..."
git pull origin main
echo "✅ Code updated"
echo ""

# 2. Setup environment
echo "🔧 Step 2: Setting up environment..."
if [ ! -f ".env" ]; then
    echo "Creating .env from production template..."
    cp .env.production .env
    echo "⚠️  IMPORTANT: Edit .env file with your actual keys:"
    echo "  nano .env"
    echo ""
    echo "Update these values:"
    echo "  - FACILITATOR_PRIVATE_KEY"
    echo "  - CLIENT_PRIVATE_KEY"
    echo "  - BITSCRUNCH_API_KEY"
    echo "  - COINGECKO_API_KEY"
    echo "  - OPENROUTER_API_KEY"
    echo ""
    read -p "Press Enter after updating .env or Ctrl+C to exit..."
else
    echo "✅ .env file exists"
fi
echo ""

# 3. Check Python
echo "🐍 Step 3: Checking Python installation..."
if ! command -v python3.11 &> /dev/null; then
    echo "Installing Python 3.11..."
    apt-get update
    apt-get install -y python3.11 python3.11-venv python3.11-dev
fi
echo "✅ Python 3.11 ready"
echo ""

# 4. Setup virtual environment
echo "📚 Step 4: Setting up virtual environment..."
if [ ! -d "venv-py311" ]; then
    python3.11 -m venv venv-py311
fi
source venv-py311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# 5. Create logs directory
echo "📝 Step 5: Creating logs directory..."
mkdir -p logs
echo "✅ Logs directory ready"
echo ""

# 6. Check ports availability
echo "🔍 Step 6: Checking port availability..."
for port in 3000 3001 4000; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo "⚠️  Port $port is in use"
        echo "   Run: sudo lsof -i :$port"
        echo "   To free it: kill <PID>"
    else
        echo "✅ Port $port is available"
    fi
done
echo ""

# 7. Stop existing services
echo "🛑 Step 7: Stopping existing x402 services..."
pkill -f "facilitator_server:app" 2>/dev/null || true
pkill -f "resource_server.py" 2>/dev/null || true
pkill -f "streamlit run.*app_coingecko" 2>/dev/null || true
sleep 3
echo "✅ Old services stopped"
echo ""

# 8. Start backend services
echo "🚀 Step 8: Starting backend services..."
chmod +x start_servers_production.sh
./start_servers_production.sh
echo ""

# 9. Start Streamlit
echo "🌐 Step 9: Starting Streamlit frontend..."
nohup ./venv-py311/bin/streamlit run frontend/app_coingecko.py \
    --server.port 4000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "   Streamlit PID: $STREAMLIT_PID"
echo ""

# 10. Wait and test
echo "⏳ Step 10: Waiting for services to start..."
sleep 5
echo ""

echo "🧪 Step 11: Testing endpoints..."
echo ""
echo "Facilitator Health:"
curl -s http://localhost:3001/health && echo " ✅" || echo " ❌"

echo ""
echo "Resource Health:"
curl -s http://localhost:3000/health && echo " ✅" || echo " ❌"

echo ""
echo "Streamlit:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000 && echo " ✅ Streamlit is running"
echo ""

# 11. Nginx configuration
echo "🔧 Step 12: Nginx configuration..."
if [ -f "/etc/nginx/sites-available/x402-bitscrunch" ]; then
    echo "✅ Nginx configuration already exists"
else
    echo "Installing nginx configuration..."
    apt-get install -y nginx
    cp nginx-x402.conf /etc/nginx/sites-available/x402-bitscrunch
    ln -sf /etc/nginx/sites-available/x402-bitscrunch /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
    echo "✅ Nginx configured and restarted"
fi
echo ""

# 12. Systemd services (optional but recommended)
echo "🔧 Step 13: Setting up systemd services (optional)..."
read -p "Setup systemd services for auto-restart? (y/n): " setup_systemd

if [ "$setup_systemd" = "y" ]; then
    # Facilitator service
    cat > /etc/systemd/system/x402-facilitator.service << EOF
[Unit]
Description=x402 Facilitator Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bitscrunch-x402
Environment="PATH=/root/bitscrunch-x402/venv-py311/bin"
ExecStart=/root/bitscrunch-x402/venv-py311/bin/uvicorn backend.facilitator_server:app --host 0.0.0.0 --port 3001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Resource service
    cat > /etc/systemd/system/x402-resource.service << EOF
[Unit]
Description=x402 Resource Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bitscrunch-x402
Environment="PATH=/root/bitscrunch-x402/venv-py311/bin"
Environment="FLASK_APP=backend/resource_server.py"
ExecStart=/root/bitscrunch-x402/venv-py311/bin/flask run --host 0.0.0.0 --port 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # Streamlit service
    cat > /etc/systemd/system/x402-streamlit.service << EOF
[Unit]
Description=x402 Streamlit Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bitscrunch-x402
Environment="PATH=/root/bitscrunch-x402/venv-py311/bin"
ExecStart=/root/bitscrunch-x402/venv-py311/bin/streamlit run frontend/app_coingecko.py --server.port 4000 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable x402-facilitator x402-resource x402-streamlit
    echo "✅ Systemd services configured"
    echo ""
    echo "To use systemd services instead of manual start:"
    echo "  systemctl start x402-facilitator x402-resource x402-streamlit"
    echo "  systemctl status x402-facilitator x402-resource x402-streamlit"
fi
echo ""

# Final summary
echo "=============================================="
echo "🎉 Deployment Complete!"
echo "=============================================="
echo ""
echo "📊 Service URLs:"
echo "  Frontend:    http://143.110.181.93"
echo "  Facilitator: http://143.110.181.93/api/facilitator"
echo "  Resource:    http://143.110.181.93/api/resource"
echo ""
echo "🔍 Local endpoints (for debugging):"
echo "  Facilitator: http://localhost:3001"
echo "  Resource:    http://localhost:3000"
echo "  Streamlit:   http://localhost:4000"
echo ""
echo "📝 View logs:"
echo "  tail -f logs/facilitator.log"
echo "  tail -f logs/resource.log"
echo "  tail -f logs/streamlit.log"
echo ""
echo "🔄 Restart services:"
echo "  ./start_servers_production.sh"
echo "  pkill -f streamlit && ./venv-py311/bin/streamlit run frontend/app_coingecko.py --server.port 4000 --server.address 0.0.0.0 &"
echo ""
echo "🛑 Stop services:"
echo "  pkill -f facilitator_server"
echo "  pkill -f resource_server"
echo "  pkill -f streamlit"
echo ""
