# Quick Server Commands

## On Your Server (159.89.170.85)

### 1. Check if Code is Updated

```bash
cd /root/bitscrunch-x402
./server-check.sh
```

This will show you:
- Current git status
- If updates are available
- Running services
- Port status
- Endpoint health

### 2. Update Code from GitHub

```bash
cd /root/bitscrunch-x402
./server-update.sh
```

This will:
- Stop running services
- Pull latest code
- Update dependencies
- Restart all services

### 3. Manual Commands

#### Pull Latest Code
```bash
cd /root/bitscrunch-x402
git pull origin main
```

#### Check Git Status
```bash
cd /root/bitscrunch-x402
git status
git log -1 --oneline
```

#### Update .env File
```bash
cd /root/bitscrunch-x402
nano .env
```

Make sure these lines are set:
```
FACILITATOR_URL=http://159.89.170.85/facilitator
RESOURCE_URL=http://159.89.170.85/resource
```

#### Start Services
```bash
cd /root/bitscrunch-x402
./start_servers.sh
```

#### Start Streamlit
```bash
cd /root/bitscrunch-x402
nohup ./venv-py311/bin/streamlit run frontend/app_coingecko.py --server.port 8501 --server.address 0.0.0.0 > logs/streamlit.log 2>&1 &
```

#### Stop Services
```bash
pkill -f "facilitator_server"
pkill -f "resource_server"
pkill -f "streamlit"
```

#### View Logs
```bash
# Backend logs
tail -f /root/bitscrunch-x402/logs/facilitator.log
tail -f /root/bitscrunch-x402/logs/resource.log

# Streamlit log
tail -f /root/bitscrunch-x402/logs/streamlit.log
```

#### Test Endpoints
```bash
# Test locally
curl http://localhost:8002/health
curl http://localhost:8001/health

# Test via public IP
curl http://159.89.170.85/facilitator/health
curl http://159.89.170.85/resource/health
```

## URLs

- **Frontend**: http://159.89.170.85:8501
- **Facilitator**: http://159.89.170.85/facilitator
- **Resource**: http://159.89.170.85/resource

## First Time Setup

If repository doesn't exist:

```bash
# Clone repository
git clone https://github.com/coingraphai/bitscrunch-x402.git /root/bitscrunch-x402
cd /root/bitscrunch-x402

# Setup environment
cp .env.example .env
nano .env  # Add your keys and update URLs

# Create virtual environment
python3.11 -m venv venv-py311
source venv-py311/bin/activate
pip install -r requirements.txt

# Run update script
./server-update.sh
```

## Nginx Configuration Required

Make sure nginx is configured to proxy to your services:

```bash
# Check nginx config
sudo nano /etc/nginx/sites-available/bitscrunch-x402

# Test nginx config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

See `SERVER_SETUP.md` for complete nginx configuration.
