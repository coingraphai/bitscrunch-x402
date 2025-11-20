#!/bin/bash
# Production Server Startup Script with Custom Ports
# Uses ports: 3000 (resource), 3001 (facilitator), 4000 (streamlit)

set -e

echo "========================================="
echo "Starting x402 Protocol Production Servers"
echo "Digital Ocean Droplet: 159.89.170.85"
echo "========================================="
echo ""

# Stop existing servers
echo "[STOP] Stopping existing servers..."
pkill -f "facilitator_server:app" 2>/dev/null || true
pkill -f "resource_server.py" 2>/dev/null || true
pkill -f "streamlit run" 2>/dev/null || true
sleep 2

# Ensure logs directory exists
mkdir -p logs

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ ! -d "venv-py311" ]; then
    echo "[ERROR] Virtual environment not found. Please run:"
    echo "  python3.11 -m venv venv-py311"
    echo "  source venv-py311/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

source venv-py311/bin/activate

# Start Facilitator Server on port 3001
echo "[START] Starting Facilitator Server on port 3001..."
FACILITATOR_SERVER_PORT=3001 nohup uvicorn backend.facilitator_server:app \
    --host 0.0.0.0 \
    --port 3001 \
    --log-level info \
    > logs/facilitator.log 2>&1 &
FACILITATOR_PID=$!
echo "   PID: $FACILITATOR_PID"

# Wait a moment
sleep 2

# Start Resource Server on port 3000
echo "[START] Starting Resource Server on port 3000..."
FLASK_APP=backend/resource_server.py \
RESOURCE_SERVER_PORT=3000 \
nohup flask run \
    --host 0.0.0.0 \
    --port 3000 \
    > logs/resource.log 2>&1 &
RESOURCE_PID=$!
echo "   PID: $RESOURCE_PID"

# Wait for servers to start
sleep 3

# Start Streamlit Frontend on port 4000
echo "[START] Starting Streamlit Frontend on port 4000..."
nohup streamlit run frontend/app_coingecko.py \
    --server.port 4000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    > logs/streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "   PID: $STREAMLIT_PID"

# Wait for Streamlit to start
sleep 5

# Check server health
echo ""
echo "[CHECK] Verifying server status..."

# Check Facilitator
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo "[OK] Facilitator Server: ONLINE (http://localhost:3001)"
else
    echo "[ERROR] Facilitator Server: OFFLINE"
fi

# Check Resource Server
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "[OK] Resource Server: ONLINE (http://localhost:3000)"
else
    echo "[ERROR] Resource Server: OFFLINE"
fi

# Check Streamlit
if curl -s http://localhost:4000 > /dev/null 2>&1; then
    echo "[OK] Streamlit Frontend: ONLINE (http://localhost:4000)"
else
    echo "[ERROR] Streamlit Frontend: OFFLINE"
    echo "        Check logs: tail -f logs/streamlit.log"
fi

echo ""
echo "[INFO] Process IDs:"
echo "   Facilitator: $FACILITATOR_PID"
echo "   Resource: $RESOURCE_PID"
echo "   Streamlit: $STREAMLIT_PID"

echo ""
echo "[INFO] View logs:"
echo "   tail -f logs/facilitator.log"
echo "   tail -f logs/resource.log"
echo "   tail -f logs/streamlit.log"

echo ""
echo "[INFO] To stop servers:"
echo "   kill $FACILITATOR_PID $RESOURCE_PID $STREAMLIT_PID"

echo ""
echo "[INFO] Access endpoints:"
echo "   Frontend: http://159.89.170.85"
echo "   Facilitator: http://159.89.170.85/api/facilitator"
echo "   Resource: http://159.89.170.85/api/resource"
echo ""
