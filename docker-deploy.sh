#!/bin/bash

# Docker Deployment Script for x402 Protocol
# This script builds and runs the Dockerized application

set -e  # Exit on error

echo "======================================"
echo "x402 Protocol - Docker Deployment"
echo "======================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[ERROR] Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo ""
    echo "Please create .env file from template:"
    echo "  cp .env.example .env"
    echo ""
    echo "Then edit .env with your configuration:"
    echo "  - CLIENT_PRIVATE_KEY"
    echo "  - FACILITATOR_PRIVATE_KEY"
    echo "  - BITSCRUNCH_API_KEY"
    echo "  - RPC_URL"
    echo ""
    exit 1
fi

echo "[INFO] Environment file found ✓"
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs
echo "[INFO] Logs directory ready ✓"
echo ""

# Stop existing containers
echo "[INFO] Stopping existing containers..."
docker-compose down 2>/dev/null || true
echo ""

# Build Docker images
echo "[INFO] Building Docker images..."
docker-compose build
echo ""

# Start services
echo "[INFO] Starting services..."
docker-compose up -d
echo ""

# Wait for services to be healthy
echo "[INFO] Waiting for services to start..."
sleep 5

# Check service status
echo ""
echo "======================================"
echo "Service Status"
echo "======================================"
docker-compose ps
echo ""

# Display access information
echo "======================================"
echo "Services are running!"
echo "======================================"
echo ""
echo "Access URLs:"
echo "  - Frontend (Streamlit):  http://localhost:8501"
echo "  - Resource Server:       http://localhost:8001"
echo "  - Facilitator Server:    http://localhost:8002"
echo ""
echo "Health Checks:"
echo "  curl http://localhost:8002/health"
echo "  curl http://localhost:8001/health"
echo ""
echo "View Logs:"
echo "  docker-compose logs -f                 # All services"
echo "  docker-compose logs -f facilitator     # Facilitator only"
echo "  docker-compose logs -f resource        # Resource only"
echo "  docker-compose logs -f frontend        # Frontend only"
echo ""
echo "Stop Services:"
echo "  docker-compose down"
echo ""
echo "Restart Services:"
echo "  docker-compose restart"
echo ""
echo "======================================"
