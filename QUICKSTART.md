# x402 Protocol Testing - Quick Reference

## Quick Start

1. **Setup Environment**:
   ```bash
   chmod +x setup.sh start.sh
   ./setup.sh
   ```

2. **Configure .env**:
   Edit `.env` file with your settings

3. **Start UI**:
   ```bash
   ./start.sh
   ```

## Manual Start

### Terminal 1 - Facilitator Server:
```bash
source venv/bin/activate
python backend/facilitator_server.py
```

### Terminal 2 - Resource Server:
```bash
source venv/bin/activate
python backend/resource_server.py
```

### Terminal 3 - Streamlit UI:
```bash
source venv/bin/activate
streamlit run frontend/app.py
```

## Test Without UI

```bash
source venv/bin/activate
python backend/test_client.py
```

## Run Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

## Configuration

Key environment variables in `.env`:

- `FACILITATOR_PRIVATE_KEY` - Private key for submitting transactions
- `CLIENT_PRIVATE_KEY` - Private key for client wallet
- `RESOURCE_SERVER_ADDRESS` - Address to receive payments
- `TOKEN_CONTRACT_ADDRESS` - ERC20 token contract (e.g., USDC)
- `RPC_URL` - Blockchain RPC endpoint
- `NETWORK` - Network name (e.g., base-sepolia)
- `CHAIN_ID` - Chain ID (e.g., 84532 for Base Sepolia)

## Endpoints

### Facilitator (Port 8000):
- `POST /verify` - Verify payment
- `POST /settle` - Settle payment
- `GET /supported` - Get supported schemes
- `GET /health` - Health check

### Resource Server (Port 8001):
- `GET /weather` - $0.01
- `GET /article` - $0.05
- `GET /data` - $0.10
- `GET /health` - Health check

## Getting Test Tokens

1. Get ETH for gas: [Base Sepolia Faucet](https://www.coinbase.com/faucets/base-ethereum-sepolia-faucet)
2. Get USDC: Use a test token faucet or swap on testnet DEX

## Troubleshooting

- **Import errors**: Run `./setup.sh` to install dependencies
- **Connection refused**: Check servers are running
- **Invalid signature**: Verify private keys in `.env`
- **Insufficient funds**: Get testnet tokens
- **Transaction reverted**: Check token approvals

## Architecture

```
Streamlit UI → Client → Resource Server → Facilitator → Blockchain
```

For detailed documentation, see README.md
