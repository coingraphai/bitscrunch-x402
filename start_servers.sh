#!/bin/bash

# Script to start both backend servers for production

cd /Users/ajayprashanth/Documents/bitsCrunch/bitsCrunch-x402

# Use Python 3.11 virtual environment for proper OpenSSL support
VENV_PATH="./venv-py311"

# Kill any existing servers
echo "[STOP] Stopping existing servers..."
pkill -f "flask run" 2>/dev/null || true
pkill -f "uvicorn.*facilitator" 2>/dev/null || true
sleep 2

# Start Facilitator Server (port 8002)
echo "[START] Starting Facilitator Server on port 8002..."
$VENV_PATH/bin/uvicorn backend.facilitator_server:app --port 8002 --host 0.0.0.0 > logs/facilitator.log 2>&1 &
FACILITATOR_PID=$!
echo "   PID: $FACILITATOR_PID"

sleep 3

# Start Resource Server (port 8001)
echo "[START] Starting Resource Server on port 8001..."
FLASK_APP=backend/resource_server.py $VENV_PATH/bin/flask run --port 8001 --host 127.0.0.1 > logs/resource.log 2>&1 &
RESOURCE_PID=$!
echo "   PID: $RESOURCE_PID"

sleep 3

# Check if servers are running
echo ""
echo "[CHECK] Verifying server status..."
if curl -s http://localhost:8002/health > /dev/null; then
    echo "[OK] Facilitator Server: ONLINE (http://localhost:8002)"
else
    echo "[ERROR] Facilitator Server: OFFLINE"
fi

if curl -s http://localhost:8001/health > /dev/null; then
    echo "[OK] Resource Server: ONLINE (http://localhost:8001)"
else
    echo "[ERROR] Resource Server: OFFLINE"
fi

echo ""
echo "[INFO] Process IDs:"
echo "   Facilitator: $FACILITATOR_PID"
echo "   Resource: $RESOURCE_PID"
echo ""
echo "[INFO] View logs:"
echo "   tail -f logs/facilitator.log"
echo "   tail -f logs/resource.log"
echo ""
echo "[INFO] To stop servers:"
echo "   kill $FACILITATOR_PID $RESOURCE_PID"
