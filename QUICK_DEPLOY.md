# 🚀 Quick Deployment Commands

## On Your Digital Ocean Server (159.89.170.85)

### 1️⃣ First Time Setup

```bash
# SSH to server
ssh root@159.89.170.85

# Clone repository
git clone https://github.com/coingraphai/bitscrunch-x402.git /root/bitscrunch-x402
cd /root/bitscrunch-x402

# Run deployment
./deploy_production.sh

# Edit environment variables
nano .env
# Add your private keys and API keys
# Save: Ctrl+X, Y, Enter
```

### 2️⃣ Quick Deploy/Update

```bash
ssh root@159.89.170.85
cd /root/bitscrunch-x402
git pull origin main
./deploy_production.sh
```

### 3️⃣ Test Everything Works

```bash
# Test APIs
curl http://159.89.170.85/api/facilitator/health
curl http://159.89.170.85/api/resource/health

# Open in browser
# http://159.89.170.85
```

---

## 📊 Port Configuration

| Service | Port | Public URL |
|---------|------|------------|
| Facilitator | 3001 | http://159.89.170.85/api/facilitator |
| Resource | 3000 | http://159.89.170.85/api/resource |
| Streamlit | 4000 | http://159.89.170.85 |

**✅ These ports are FREE on your server**

---

## 🔄 Service Management

### Manual Control
```bash
# Start
./start_servers_production.sh

# Stop
pkill -f facilitator_server && pkill -f resource_server && pkill -f streamlit

# View logs
tail -f logs/facilitator.log
tail -f logs/resource.log
tail -f logs/streamlit.log
```

### Systemd (Recommended)
```bash
# Start
systemctl start x402-facilitator x402-resource x402-streamlit

# Stop
systemctl stop x402-facilitator x402-resource x402-streamlit

# Restart
systemctl restart x402-facilitator x402-resource x402-streamlit

# Status
systemctl status x402-facilitator x402-resource x402-streamlit

# Logs
journalctl -u x402-facilitator -f
```

---

## ⚙️ Important Files to Edit

### `.env` - Your Configuration
```bash
nano /root/bitscrunch-x402/.env
```

**Must update these:**
- `FACILITATOR_PRIVATE_KEY` - Your facilitator wallet key
- `CLIENT_PRIVATE_KEY` - Your client wallet key
- `BITSCRUNCH_API_KEY` - UnleashNFTs API key

**Keep these as-is (production URLs):**
- `FACILITATOR_URL=http://159.89.170.85/api/facilitator`
- `RESOURCE_URL=http://159.89.170.85/api/resource`

---

## 🐛 Quick Troubleshooting

### Services not accessible?
```bash
# Check if running
ps aux | grep -E "(facilitator|resource|streamlit)"

# Check nginx
systemctl status nginx
nginx -t

# Check ports
netstat -tulpn | grep -E ":(3000|3001|4000)"
```

### Port conflicts?
```bash
# See what's using a port
lsof -i :3000
lsof -i :3001
lsof -i :4000

# Kill process
kill <PID>
```

### View errors?
```bash
# Check logs
tail -100 logs/facilitator.log
tail -100 logs/resource.log
tail -100 logs/streamlit.log

# Search for errors
grep -i error logs/*.log
```

---

## 📚 Full Documentation

See `PRODUCTION_DEPLOYMENT.md` for complete guide

---

**🎯 Your Production URLs:**
- Frontend: http://159.89.170.85
- API: http://159.89.170.85/api/facilitator & /api/resource
