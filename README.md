# x402 Protocol - UnleashNFTs API Integration

Production-ready HTTP-native payment protocol with blockchain settlement, integrated with UnleashNFTs Analytics API.

## Overview

This application enables micropayments for NFT analytics endpoints using the x402 protocol. Each API request requires a blockchain payment (USDC on Base Sepolia testnet), providing:

- **HTTP-Native Payments**: 402 Payment Required status code integration
- **Blockchain Settlement**: EIP-3009 transferWithAuthorization on Base Sepolia
- **NFT Analytics**: 7 UnleashNFTs API endpoints with real-time data
- **Interactive UI**: Streamlit frontend with parameter configuration

## Architecture

```
┌─────────────────┐
│   Streamlit UI  │  (Port 8501)
│  Frontend       │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼────────────┐
│Client│  │ Resource API  │  (Port 8001)
│      │  │ UnleashNFTs   │
└───┬──┘  └──┬────────────┘
    │        │
    │   ┌────▼─────────┐
    └───► Facilitator  │  (Port 8002)
        │ Payment      │
        │ Verification │
        └────┬─────────┘
             │
        ┌────▼──────────┐
        │  Blockchain   │
        │ Base Sepolia  │
        │   (USDC)      │
        └───────────────┘
```

## Components

### Backend Services

1. **Facilitator Server** (`backend/facilitator_server.py`)
   - FastAPI application on port 8002
   - Verifies payment signatures
   - Settles transactions on blockchain
   - Endpoints: `/verify`, `/settle`, `/supported`, `/health`

2. **Resource Server** (`backend/resource_server.py`)
   - Flask application on port 8001
   - Protected UnleashNFTs API endpoints
   - Payment required for access (402 status code)
   - 7 analytics endpoints with real-time NFT data

### Frontend

- **Streamlit Application** (`frontend/app_coingecko.py`)
  - Interactive parameter configuration
  - Real-time URL building
  - Payment processing and transaction tracking
  - Response data visualization

### Core Modules

- `backend/client.py` - Payment client implementation
- `backend/protocol.py` - x402 protocol logic
- `backend/verification.py` - Payment signature verification
- `backend/settlement.py` - Blockchain settlement logic

## Prerequisites

- **For Docker** (Recommended): Docker & Docker Compose
- **For Manual Setup**: Python 3.11+ (required for OpenSSL 3.x support)
- Access to Base Sepolia testnet
- USDC tokens on Base Sepolia (for payments)
- ETH on Base Sepolia (for gas fees)
- UnleashNFTs API key

## Quick Start

### Option 1: Docker Deployment (Recommended) 🐳

**Easiest way to get started!**

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Add your API keys and private keys

# 2. Deploy with one command
./docker-deploy.sh

# 3. Access the application
# Frontend: http://localhost:8501
# Resource API: http://localhost:8001
# Facilitator API: http://localhost:8002
```

That's it! All services are now running in Docker containers.

**Docker Commands:**
```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart
```

📖 **[See detailed Docker documentation](DOCKER.md)**

---

### Option 2: Manual Setup

### 1. Clone and Setup

```bash
cd /path/to/bitsCrunch-x402

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Configure Environment Variables

Edit `.env` with your values:

```bash
# Blockchain Configuration
RPC_URL=https://base-sepolia-rpc.publicnode.com
CHAIN_ID=84532
NETWORK_ID=84532

# USDC Token Contract on Base Sepolia
TOKEN_CONTRACT_ADDRESS=0x036CbD53842c5426634e7929541eC2318f3dCF7e

# Wallet Private Keys (WITHOUT 0x prefix)
CLIENT_PRIVATE_KEY=your_client_private_key_here
FACILITATOR_PRIVATE_KEY=your_facilitator_private_key_here

# Server URLs
FACILITATOR_URL=http://localhost:8002
RESOURCE_URL=http://localhost:8001

# UnleashNFTs API
BITSCRUNCH_API_KEY=your_unleashnfts_api_key_here
BITSCRUNCH_API_URL=https://api.unleashnfts.com/api/v2
```

### 3. Deploy

```bash
# One-command deployment
./deploy.sh
```

This will:
- Create Python 3.11 virtual environment
- Install all dependencies
- Start Facilitator and Resource servers
- Display access URLs and logs

### 4. Start Frontend

```bash
# In a new terminal
./venv-py311/bin/streamlit run frontend/app_coingecko.py --server.port 8501
```

Access the UI at: http://localhost:8501

## UnleashNFTs API Endpoints

| Endpoint | Price | Description |
|----------|-------|-------------|
| Supported Blockchains | $0.02 | Get list of all supported blockchains |
| Market Insights | $0.05 | NFT market analytics (volume, sales, trends) |
| Supported Collections | $0.03 | Collections with AI valuation support |
| NFT Valuation | $0.08 | AI-powered price estimation for NFTs |
| Collection Scores | $0.04 | Comprehensive collection metrics |
| Washtrade Analysis | $0.06 | Detect suspicious trading activity |
| Floor Price | $0.03 | Real-time floor prices across 30+ marketplaces |

## Usage

### Testing an Endpoint

1. Go to **Test Endpoints** tab
2. Select an endpoint (e.g., "NFT Valuation")
3. Configure parameters:
   - Chain ID (Ethereum, Polygon, BSC)
   - Contract Address (default: BAYC)
   - Token ID
4. Click **Test** button
5. View payment transaction and API response

### Payment Flow

1. User selects endpoint and parameters
2. Client requests protected resource
3. Server responds with 402 Payment Required
4. Client creates payment signature
5. Facilitator verifies and settles payment
6. Resource server returns NFT data

## Server Management

### Start Servers

```bash
./start_servers.sh
```

### Stop Servers

```bash
# Get PIDs from start_servers.sh output
kill <FACILITATOR_PID> <RESOURCE_PID>

# Or kill all
pkill -f "flask run"
pkill -f "uvicorn.*facilitator"
```

### View Logs

```bash
# Facilitator logs
tail -f logs/facilitator.log

# Resource server logs
tail -f logs/resource.log
```

### Health Checks

```bash
# Facilitator
curl http://localhost:8002/health

# Resource Server
curl http://localhost:8001/health
```

## Production Deployment

### Security Considerations

1. **Environment Variables**
   - Never commit `.env` to version control
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Rotate private keys regularly

2. **API Keys**
   - Store UnleashNFTs API key securely
   - Monitor API usage and rate limits
   - Implement key rotation policy

3. **Network Security**
   - Use HTTPS in production (TLS/SSL certificates)
   - Configure firewall rules
   - Restrict access to backend servers

### Scaling

1. **Load Balancing**
   - Run multiple Resource Server instances
   - Use nginx or HAProxy for load balancing
   - Session affinity not required (stateless)

2. **Database**
   - Consider PostgreSQL for payment records
   - Implement caching (Redis) for frequently accessed data
   - Log all transactions for audit trail

3. **Monitoring**
   - Set up application monitoring (Datadog, New Relic)
   - Track payment success rates
   - Monitor blockchain gas prices
   - Alert on API errors

### Mainnet Deployment

To deploy on mainnet (Base):

1. Update `.env`:
   ```bash
   RPC_URL=https://mainnet.base.org
   CHAIN_ID=8453
   TOKEN_CONTRACT_ADDRESS=<USDC_MAINNET_ADDRESS>
   ```

2. Fund wallets with real USDC and ETH

3. Update endpoint prices as needed

4. Test thoroughly on testnet first!

## Troubleshooting

### Common Issues

1. **SSL/TLS Errors**
   - Ensure using Python 3.11+ with OpenSSL 3.x
   - Virtual environment: `venv-py311`

2. **Payment Failures**
   - Check USDC balance in wallet
   - Verify sufficient ETH for gas
   - Confirm private keys are correct (without 0x prefix)

3. **Server Offline**
   - Check logs for errors
   - Verify ports 8001/8002 not in use
   - Ensure RPC URL is accessible

4. **API Rate Limiting**
   - UnleashNFTs may have rate limits
   - Implement request queuing if needed
   - Contact UnleashNFTs for enterprise plans

## Development

### Project Structure

```
bitsCrunch-x402/
├── backend/
│   ├── client.py              # Payment client
│   ├── facilitator_server.py  # Payment verification server
│   ├── resource_server.py     # API endpoints server
│   ├── protocol.py            # x402 protocol logic
│   ├── verification.py        # Payment verification
│   └── settlement.py          # Blockchain settlement
├── frontend/
│   └── app_coingecko.py       # Streamlit UI
├── logs/                      # Server logs
├── .env                       # Environment variables (not in git)
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
├── deploy.sh                  # Deployment script
├── start_servers.sh           # Server startup script
└── README.md                  # This file
```

### Adding New Endpoints

1. Add endpoint to `backend/resource_server.py`:
```python
@app.route('/new-endpoint', methods=['GET'])
@require_payment("$0.05", "Description")
def new_endpoint():
    # Your logic here
    return {"data": "response"}
```

2. Add to frontend `frontend/app_coingecko.py`:
```python
{
    "name": "New Endpoint",
    "icon": "",
    "url_template": "http://localhost:8001/new-endpoint",
    "price": "$0.05",
    "description": "What it does",
    "key": "new_endpoint",
    "parameters": []
}
```

3. Restart servers and test

## Resources

- [x402 Protocol Documentation](https://x402.org)
- [EIP-3009 Specification](https://eips.ethereum.org/EIPS/eip-3009)
- [Base Network](https://base.org)
- [UnleashNFTs API](https://unleashnfts.com)
- [Streamlit Documentation](https://docs.streamlit.io)

## License

This project is for demonstration purposes. Ensure compliance with:
- UnleashNFTs API Terms of Service
- Base Network Terms
- USDC Terms

## Support

For issues or questions:
1. Check logs: `logs/facilitator.log`, `logs/resource.log`
2. Verify configuration in `.env`
3. Test on Base Sepolia testnet first
4. Review UnleashNFTs API documentation

---

**Note**: This is a testnet implementation. Always test thoroughly before deploying to mainnet with real funds.
