#!/bin/bash

# Production Deployment Script for x402 Protocol + UnleashNFTs API

set -e  # Exit on error

echo "[DEPLOY] Starting x402 Protocol deployment..."
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "[ERROR] .env file not found!"
    echo "[INFO] Copy .env.example to .env and configure your values:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Check Python version
echo "[CHECK] Verifying Python 3.11 installation..."
if command -v python3.11 &> /dev/null; then
    echo "[OK] Python 3.11 found"
else
    echo "[ERROR] Python 3.11 not found. Please install:"
    echo "   brew install python@3.11"
    exit 1
fi

# Create Python 3.11 virtual environment if it doesn't exist
if [ ! -d "venv-py311" ]; then
    echo "[SETUP] Creating Python 3.11 virtual environment..."
    python3.11 -m venv venv-py311
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment exists"
fi

# Install dependencies
echo "[SETUP] Installing dependencies..."
./venv-py311/bin/pip install --upgrade pip > /dev/null
./venv-py311/bin/pip install -r requirements.txt > /dev/null
echo "[OK] Dependencies installed"

# Create logs directory
mkdir -p logs
echo "[OK] Logs directory ready"

# Start servers
echo ""
echo "[DEPLOY] Starting backend servers..."
./start_servers.sh

echo ""
echo "[SUCCESS] Deployment complete!"
echo ""
echo "[INFO] Access the application:"
echo "   Facilitator API: http://localhost:8002"
echo "   Resource API: http://localhost:8001"
echo "   Frontend: streamlit run frontend/app_coingecko.py"
echo ""
echo "[INFO] Monitor logs:"
echo "   tail -f logs/facilitator.log"
echo "   tail -f logs/resource.log"
