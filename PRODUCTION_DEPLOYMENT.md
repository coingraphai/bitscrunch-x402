# Digital Ocean Production Deployment Guide

## 🌐 Server Information

- **Server IP**: 159.89.170.85
- **Repository**: https://github.com/coingraphai/bitscrunch-x402

## 🔧 Port Configuration

### Ports Used (Avoiding Conflicts):

| Service | Port | Purpose | URL |
|---------|------|---------|-----|
| **Facilitator** | 3001 | Payment verification | http://159.89.170.85/api/facilitator |
| **Resource** | 3000 | UnleashNFTs APIs | http://159.89.170.85/api/resource |
| **Streamlit** | 4000 | Frontend UI | http://159.89.170.85 |

### Avoided Ports (Already in Use):
- 22: SSH
- 53: systemd-resolved (DNS)
- 80: Nginx (HTTP)
- 8001, 8002, 8501: Docker containers

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] SSH access to server: `ssh root@159.89.170.85`
- [ ] Private keys for wallets
- [ ] UnleashNFTs API key
- [ ] CoinGecko API key (optional)
- [ ] OpenRouter API key (optional)

## 🚀 Deployment Steps

### Step 1: SSH to Server

```bash
ssh root@159.89.170.85
```

### Step 2: Clone Repository (First Time Only)

```bash
# If repository doesn't exist
git clone https://github.com/coingraphai/bitscrunch-x402.git /root/bitscrunch-x402
cd /root/bitscrunch-x402
```

### Step 3: Run Deployment Script

```bash
cd /root/bitscrunch-x402
chmod +x deploy_production.sh
./deploy_production.sh
```

The script will:
1. ✅ Pull latest code from GitHub
2. ✅ Create `.env` from production template
3. ✅ Install Python 3.11 (if needed)
4. ✅ Setup virtual environment
5. ✅ Install dependencies
6. ✅ Check port availability
7. ✅ Stop old services
8. ✅ Start backend servers (ports 3000, 3001)
9. ✅ Start Streamlit (port 4000)
10. ✅ Test all endpoints
11. ✅ Configure Nginx
12. ✅ Setup systemd services (optional)

### Step 4: Configure Environment Variables

When prompted, edit the `.env` file:

```bash
nano /root/bitscrunch-x402/.env
```

**Update these required values:**

```bash
# Wallet private keys (WITHOUT 0x prefix)
FACILITATOR_PRIVATE_KEY=your_facilitator_private_key_here
CLIENT_PRIVATE_KEY=your_client_private_key_here

# API Keys
BITSCRUNCH_API_KEY=your_unleashnfts_api_key_here
COINGECKO_API_KEY=your_coingecko_api_key_here  # optional
OPENROUTER_API_KEY=your_openrouter_api_key_here  # optional
```

**Keep these production URLs as-is:**
```bash
FACILITATOR_URL=http://159.89.170.85/api/facilitator
RESOURCE_URL=http://159.89.170.85/api/resource
```

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

## 🔍 Verification

### Test Endpoints

```bash
# Test Facilitator (should return JSON)
curl http://159.89.170.85/api/facilitator/health

# Test Resource (should return JSON)
curl http://159.89.170.85/api/resource/health

# Test Frontend (should return HTML)
curl http://159.89.170.85
```

### Check Running Services

```bash
# Check processes
ps aux | grep -E "(facilitator|resource|streamlit)" | grep -v grep

# Check ports
netstat -tulpn | grep -E ":(3000|3001|4000)"
```

### View Logs

```bash
# Real-time log viewing
tail -f /root/bitscrunch-x402/logs/facilitator.log
tail -f /root/bitscrunch-x402/logs/resource.log
tail -f /root/bitscrunch-x402/logs/streamlit.log

# View last 50 lines
tail -n 50 /root/bitscrunch-x402/logs/facilitator.log
```

## 🌐 Access Your Application

### Public URLs:
- **Main App**: http://159.89.170.85
- **Facilitator API**: http://159.89.170.85/api/facilitator
- **Resource API**: http://159.89.170.85/api/resource

### Test in Browser:
1. Open http://159.89.170.85
2. Go to "Test Endpoints" tab
3. Select an endpoint
4. Configure parameters
5. Click "Test" button

## 🔄 Managing Services

### Manual Control

```bash
# Start services
cd /root/bitscrunch-x402
./start_servers_production.sh

# Start Streamlit
nohup ./venv-py311/bin/streamlit run frontend/app_coingecko.py --server.port 4000 --server.address 0.0.0.0 --server.headless true > logs/streamlit.log 2>&1 &

# Stop services
pkill -f "facilitator_server"
pkill -f "resource_server"
pkill -f "streamlit"
```

### Using Systemd (Recommended for Production)

```bash
# Start services
systemctl start x402-facilitator x402-resource x402-streamlit

# Stop services
systemctl stop x402-facilitator x402-resource x402-streamlit

# Restart services
systemctl restart x402-facilitator x402-resource x402-streamlit

# Check status
systemctl status x402-facilitator
systemctl status x402-resource
systemctl status x402-streamlit

# View logs
journalctl -u x402-facilitator -f
journalctl -u x402-resource -f
journalctl -u x402-streamlit -f

# Enable auto-start on boot
systemctl enable x402-facilitator x402-resource x402-streamlit
```

## 🔧 Nginx Configuration

The nginx configuration at `/etc/nginx/sites-available/x402-bitscrunch`:

- Routes `/api/facilitator/*` → `localhost:3001`
- Routes `/api/resource/*` → `localhost:3000`
- Routes `/` → `localhost:4000` (Streamlit)

### Test Nginx Configuration

```bash
# Test config syntax
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Restart nginx
sudo systemctl restart nginx

# Check nginx status
sudo systemctl status nginx
```

## 🔄 Updating Application

### Pull Latest Changes

```bash
cd /root/bitscrunch-x402

# Stop services
pkill -f "facilitator_server"
pkill -f "resource_server"
pkill -f "streamlit"

# Pull updates
git pull origin main

# Restart services
./deploy_production.sh
```

### Or Use Systemd

```bash
cd /root/bitscrunch-x402
git pull origin main

# Restart services
systemctl restart x402-facilitator x402-resource x402-streamlit
```

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check if ports are free
sudo lsof -i :3000
sudo lsof -i :3001
sudo lsof -i :4000

# Kill processes using ports
kill $(lsof -t -i:3000)
kill $(lsof -t -i:3001)
kill $(lsof -t -i:4000)
```

### Nginx Issues

```bash
# Check nginx error log
tail -f /var/log/nginx/x402-error.log

# Test configuration
nginx -t

# Restart nginx
systemctl restart nginx
```

### Check Firewall

```bash
# Check firewall status
ufw status

# Allow ports if needed
ufw allow 80/tcp
ufw allow 443/tcp
```

### Payment Failures

1. Check wallet has USDC tokens
2. Check wallet has ETH for gas
3. Verify private keys in `.env` (without 0x prefix)
4. Check RPC URL is accessible:
   ```bash
   curl -X POST -H "Content-Type: application/json" \
     --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
     https://base-sepolia-rpc.publicnode.com
   ```

### View Application Errors

```bash
# Check all logs
ls -lh /root/bitscrunch-x402/logs/

# View errors
grep -i error /root/bitscrunch-x402/logs/*.log
```

## 📊 Monitoring

### Resource Usage

```bash
# CPU and Memory
htop

# Disk space
df -h

# Process monitoring
watch -n 2 'ps aux | grep -E "(facilitator|resource|streamlit)" | grep -v grep'
```

### Log Size Management

```bash
# Check log sizes
du -sh /root/bitscrunch-x402/logs/*

# Rotate logs (if needed)
mv logs/facilitator.log logs/facilitator.log.old
mv logs/resource.log logs/resource.log.old
mv logs/streamlit.log logs/streamlit.log.old

# Restart services to create new logs
systemctl restart x402-facilitator x402-resource x402-streamlit
```

## 🔒 Security Recommendations

1. **SSL Certificate** (Recommended):
   ```bash
   apt-get install certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com
   ```

2. **Firewall**:
   ```bash
   ufw enable
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ```

3. **Environment Variables**:
   - Never commit `.env` to git
   - Keep private keys secure
   - Rotate keys regularly

4. **Updates**:
   ```bash
   apt-get update
   apt-get upgrade
   ```

## 📞 Support

For issues:
1. Check logs: `/root/bitscrunch-x402/logs/`
2. Review GitHub repository: https://github.com/coingraphai/bitscrunch-x402
3. Test endpoints with curl
4. Verify environment variables in `.env`

## ✅ Production Checklist

Before going live:

- [ ] All services running (check `systemctl status`)
- [ ] Nginx configured and running
- [ ] SSL certificate installed (optional but recommended)
- [ ] Firewall configured
- [ ] `.env` file has real API keys
- [ ] Wallets have USDC and ETH
- [ ] Tested all 7 UnleashNFTs endpoints
- [ ] Logs are being written
- [ ] Auto-restart configured (systemd)
- [ ] Monitoring setup
- [ ] Backup `.env` file stored securely

---

**Your Production Setup:**
- Free ports: 3000, 3001, 4000 ✅
- Nginx routing: `/api/facilitator`, `/api/resource`, `/` ✅
- Server IP: 159.89.170.85 ✅
- Repository: coingraphai/bitscrunch-x402 ✅
