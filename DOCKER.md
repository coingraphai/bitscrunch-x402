# Docker Deployment Guide

This guide explains how to run the x402 Protocol application using Docker.

## Prerequisites

- Docker Engine 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- Docker Compose 2.0+ ([Install Compose](https://docs.docker.com/compose/install/))
- 2GB free disk space
- Ports 8001, 8002, 8501 available

## Quick Start

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env
```

**Required variables to update:**
- `CLIENT_PRIVATE_KEY` - Your wallet private key (without 0x)
- `FACILITATOR_PRIVATE_KEY` - Facilitator wallet private key (without 0x)
- `BITSCRUNCH_API_KEY` - Your UnleashNFTs API key
- `RPC_URL` - Base Sepolia RPC endpoint

### 2. Deploy with One Command

```bash
./docker-deploy.sh
```

That's it! The script will:
- Build Docker images
- Start all 3 services
- Show access URLs
- Display service status

### 3. Access Application

- **Frontend UI**: http://localhost:8501
- **Resource API**: http://localhost:8001
- **Facilitator API**: http://localhost:8002

## Manual Docker Commands

### Build Images

```bash
docker-compose build
```

### Start Services

```bash
# Start in background
docker-compose up -d

# Start with logs visible
docker-compose up
```

### Stop Services

```bash
docker-compose down
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f facilitator
docker-compose logs -f resource
docker-compose logs -f frontend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart facilitator
```

### Check Service Status

```bash
docker-compose ps
```

### Health Checks

```bash
# Facilitator health
curl http://localhost:8002/health

# Resource server health
curl http://localhost:8001/health
```

## Architecture

The Docker setup creates 3 containers:

```
┌─────────────────────┐
│  x402-frontend      │  Port 8501 (Streamlit UI)
│  (Container)        │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
┌───▼────────┐ ┌─▼──────────────┐
│x402-       │ │ x402-resource  │  Port 8001 (Flask API)
│facilitator │ │ (Container)    │
│(Container) │ └────────────────┘
└────────────┘    Port 8002 (FastAPI)
     │
     │ (Blockchain)
     ▼
```

All containers are connected via `x402-network` bridge network.

## Container Details

### Facilitator Container
- **Image**: Based on Python 3.11-slim
- **Command**: `uvicorn backend.facilitator_server:app`
- **Port**: 8002
- **Purpose**: Payment verification and blockchain settlement

### Resource Container
- **Image**: Based on Python 3.11-slim
- **Command**: `flask --app backend.resource_server run`
- **Port**: 8001
- **Purpose**: Protected UnleashNFTs API endpoints

### Frontend Container
- **Image**: Based on Python 3.11-slim
- **Command**: `streamlit run frontend/app_coingecko.py`
- **Port**: 8501
- **Purpose**: User interface for testing endpoints

## Volumes

Logs are persisted using Docker volumes:
- `./logs:/app/logs` - Maps host logs directory to container

## Environment Variables

All containers use `.env` file. Key variables:

```bash
# Blockchain
RPC_URL=https://base-sepolia-rpc.publicnode.com
CHAIN_ID=84532
TOKEN_CONTRACT_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e

# Wallets
CLIENT_PRIVATE_KEY=your_key_here
FACILITATOR_PRIVATE_KEY=your_key_here

# APIs
BITSCRUNCH_API_KEY=your_api_key_here
```

## Troubleshooting

### Port Already in Use

```bash
# Check what's using the port
lsof -ti:8501 | xargs kill -9  # Frontend
lsof -ti:8001 | xargs kill -9  # Resource
lsof -ti:8002 | xargs kill -9  # Facilitator
```

### Container Won't Start

```bash
# Check logs
docker-compose logs <service-name>

# Rebuild without cache
docker-compose build --no-cache
```

### Service Unhealthy

```bash
# Check health status
docker-compose ps

# View specific container logs
docker logs x402-facilitator
docker logs x402-resource
docker logs x402-frontend
```

### Clear Everything and Restart

```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Rebuild and restart
./docker-deploy.sh
```

### Network Issues

```bash
# Inspect network
docker network inspect bitscrunch-x402_x402-network

# Check container connectivity
docker exec x402-frontend ping facilitator
docker exec x402-resource ping facilitator
```

## Production Deployment

### Using Docker Compose Override

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  facilitator:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  resource:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  frontend:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

Deploy:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml x402

# Check services
docker stack services x402

# Remove stack
docker stack rm x402
```

### Using Kubernetes

Convert to Kubernetes manifests:
```bash
# Install kompose
brew install kompose  # macOS
# or download from https://kompose.io/

# Convert
kompose convert -f docker-compose.yml

# Deploy
kubectl apply -f .
```

## Resource Requirements

### Minimum
- **CPU**: 2 cores
- **RAM**: 2GB
- **Disk**: 1GB

### Recommended
- **CPU**: 4 cores
- **RAM**: 4GB
- **Disk**: 5GB

## Security Best Practices

1. **Never commit `.env` file** - Contains private keys
2. **Use Docker secrets** - For production deployments
3. **Run as non-root** - Add USER directive in Dockerfile
4. **Scan images** - Use `docker scan` for vulnerabilities
5. **Update regularly** - Keep base images updated

## Monitoring

### Container Stats

```bash
docker stats
```

### Container Inspect

```bash
docker inspect x402-facilitator
```

### Export Logs

```bash
docker-compose logs > logs/docker-logs.txt
```

## Backup and Restore

### Backup

```bash
# Backup .env
cp .env .env.backup

# Backup logs
tar -czf logs-backup.tar.gz logs/

# Export database (if using)
docker exec x402-db pg_dump -U user db > backup.sql
```

### Restore

```bash
# Restore .env
cp .env.backup .env

# Restore logs
tar -xzf logs-backup.tar.gz

# Restart services
docker-compose restart
```

## Advanced Usage

### Build Specific Service

```bash
docker-compose build facilitator
```

### Scale Services (if stateless)

```bash
docker-compose up -d --scale resource=3
```

### Execute Commands Inside Container

```bash
# Open shell
docker exec -it x402-facilitator /bin/bash

# Run Python command
docker exec x402-facilitator python -c "print('Hello')"

# Check Python version
docker exec x402-facilitator python --version
```

### Update Code Without Rebuilding

```bash
# Only if code changes, no dependency changes
docker-compose restart
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker images
        run: docker-compose build
      
      - name: Run tests
        run: docker-compose up -d && sleep 10 && curl http://localhost:8002/health
```

## Support

For issues:
1. Check logs: `docker-compose logs`
2. Verify `.env` configuration
3. Ensure ports are available
4. Check Docker daemon is running: `docker ps`

---

**Note**: This is a development/testnet setup. For production, implement proper security measures, use orchestration (Kubernetes), and set up monitoring/alerting.
