#!/bin/bash
# Quick Server Setup Script for x402 on 159.89.170.85
# Run this on your server after cloning the repository

set -e

echo "=============================================="
echo "x402 Quick Server Setup"
echo "Server: 159.89.170.85"
echo "=============================================="
echo ""

# Check if we're in the right directory
if [ ! -f "deploy_production.sh" ]; then
    echo "❌ Error: Run this script from /root/bitscrunch-x402 directory"
    echo "   cd /root/bitscrunch-x402"
    echo "   ./quick-server-setup.sh"
    exit 1
fi

# 1. Stop default nginx site
echo "📝 Step 1: Configuring Nginx..."
if [ -L "/etc/nginx/sites-enabled/default" ]; then
    echo "   Removing default nginx site..."
    rm -f /etc/nginx/sites-enabled/default
fi

# 2. Install x402 nginx config
echo "   Installing x402 nginx configuration..."
cp nginx-x402.conf /etc/nginx/sites-available/x402-bitscrunch
ln -sf /etc/nginx/sites-available/x402-bitscrunch /etc/nginx/sites-enabled/

# 3. Test nginx config
echo "   Testing nginx configuration..."
nginx -t

# 4. Reload nginx
echo "   Reloading nginx..."
systemctl reload nginx
echo "✅ Nginx configured and running"
echo ""

# 5. Setup .env file
echo "📝 Step 2: Setting up environment file..."
if [ ! -f ".env" ]; then
    if [ -f ".env.production.template" ]; then
        cp .env.production.template .env
        echo "✅ Created .env from template"
        echo ""
        echo "⚠️  IMPORTANT: You need to edit .env with your actual keys:"
        echo "   nano .env"
        echo ""
        echo "   Update these values:"
        echo "   - FACILITATOR_PRIVATE_KEY=your_actual_key"
        echo "   - CLIENT_PRIVATE_KEY=your_actual_key"
        echo "   - RESOURCE_SERVER_ADDRESS=your_actual_address"
        echo "   - BITSCRUNCH_API_KEY=your_actual_key"
        echo "   - COINGECKO_API_KEY=your_actual_key"
        echo "   - OPENROUTER_API_KEY=your_actual_key"
        echo ""
        read -p "Press Enter after editing .env file, or Ctrl+C to exit and edit later..."
    else
        echo "❌ Error: .env.production.template not found"
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi
echo ""

# 6. Check Python
echo "🐍 Step 3: Checking Python..."
if command -v python3.11 &> /dev/null; then
    echo "✅ Python 3.11 found: $(python3.11 --version)"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+' | head -1)
    echo "✅ Python found: $(python3 --version)"
    # Create symlink for convenience
    ln -sf $(which python3) /usr/local/bin/python3.11 2>/dev/null || true
else
    echo "❌ Python 3.11+ not found. Installing..."
    apt-get update
    apt-get install -y python3 python3-pip python3-venv
fi
echo ""

# 7. Setup virtual environment
echo "📚 Step 4: Setting up Python virtual environment..."
if [ ! -d "venv-py311" ]; then
    python3.11 -m venv venv-py311
    echo "✅ Virtual environment created"
fi

source venv-py311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# 8. Create logs directory
mkdir -p logs
echo "✅ Logs directory created"
echo ""

# 9. Check if services are running
echo "🔍 Step 5: Checking running services..."
if pgrep -f "facilitator_server:app" > /dev/null; then
    echo "   ⚠️  Facilitator server is already running"
    echo "   Stopping it..."
    pkill -f "facilitator_server:app"
fi

if pgrep -f "resource_server.py" > /dev/null; then
    echo "   ⚠️  Resource server is already running"
    echo "   Stopping it..."
    pkill -f "resource_server.py"
fi

if pgrep -f "streamlit run" > /dev/null; then
    echo "   ⚠️  Streamlit is already running"
    echo "   Stopping it..."
    pkill -f "streamlit run"
fi
sleep 2
echo ""

# 10. Start services
echo "🚀 Step 6: Starting x402 services..."
chmod +x start_servers_production.sh
./start_servers_production.sh
echo ""

# 11. Wait and test
echo "⏳ Step 7: Waiting for services to start..."
sleep 8
echo ""

echo "🧪 Step 8: Testing services..."
echo ""
echo -n "Facilitator (port 3001): "
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

echo -n "Resource (port 3000): "
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

echo -n "Streamlit (port 4000): "
if curl -s http://localhost:4000 > /dev/null 2>&1; then
    echo "✅ Running"
else
    echo "❌ Not responding"
fi

echo ""
echo "=============================================="
echo "🎉 Setup Complete!"
echo "=============================================="
echo ""
echo "📊 Access your application:"
echo "   http://159.89.170.85"
echo ""
echo "📊 API Endpoints:"
echo "   http://159.89.170.85/api/facilitator"
echo "   http://159.89.170.85/api/resource"
echo ""
echo "📝 View logs:"
echo "   tail -f logs/facilitator.log"
echo "   tail -f logs/resource.log"
echo "   tail -f logs/streamlit.log"
echo ""
echo "🔄 To restart services:"
echo "   ./start_servers_production.sh"
echo ""

