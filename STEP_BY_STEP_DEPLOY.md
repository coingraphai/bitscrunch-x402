# Step-by-Step Server Deployment Commands
# Digital Ocean Server: 143.110.181.93

## 🚀 Complete Deployment Steps

### Step 1: SSH to Your Server
```bash
ssh root@143.110.181.93
```

---

### Step 2: Clone Repository (First Time Only)
```bash
# Clone the repository
git clone https://github.com/coingraphai/bitscrunch-x402.git /root/bitscrunch-x402

# Navigate to directory
cd /root/bitscrunch-x402
```

**Note**: If repository already exists, skip to Step 3

---

### Step 3: Pull Latest Code
```bash
cd /root/bitscrunch-x402
git pull origin main
```

---

### Step 4: Copy Production Environment File
```bash
# Copy production config to .env
cp .env.production .env

# Verify it was copied
ls -la .env
```

---

### Step 5: Install Python 3.11 (if not installed)
```bash
# Check if Python 3.11 is installed
python3.11 --version

# If not installed, run:
apt-get update
apt-get install -y python3.11 python3.11-venv python3.11-dev build-essential
```

---

### Step 6: Create Virtual Environment
```bash
cd /root/bitscrunch-x402

# Create virtual environment
python3.11 -m venv venv-py311

# Activate it
source venv-py311/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

### Step 7: Create Logs Directory
```bash
mkdir -p /root/bitscrunch-x402/logs
```

---

### Step 8: Check Port Availability
```bash
# Check if ports 3000, 3001, 4000 are free
lsof -i :3000
lsof -i :3001
lsof -i :4000

# If any port is in use, kill the process:
# kill <PID>
```

---

### Step 9: Install and Configure Nginx
```bash
# Install nginx
apt-get update
apt-get install -y nginx

# Copy nginx configuration
cp /root/bitscrunch-x402/nginx-x402.conf /etc/nginx/sites-available/x402-bitscrunch

# Create symbolic link
ln -sf /etc/nginx/sites-available/x402-bitscrunch /etc/nginx/sites-enabled/

# Remove default site if exists
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Restart nginx
systemctl restart nginx

# Check nginx status
systemctl status nginx
```

---

### Step 10: Start Backend Services
```bash
cd /root/bitscrunch-x402

# Make script executable
chmod +x start_servers_production.sh

# Start facilitator and resource servers
./start_servers_production.sh
```

**Expected Output:**
```
[START] Starting Facilitator Server on port 3001...
   PID: XXXXX
[START] Starting Resource Server on port 3000...
   PID: XXXXX
[OK] Facilitator Server: ONLINE (http://localhost:3001)
[OK] Resource Server: ONLINE (http://localhost:3000)
```

---

### Step 11: Start Streamlit Frontend
```bash
cd /root/bitscrunch-x402

# Activate virtual environment
source venv-py311/bin/activate

# Start Streamlit in background
nohup ./venv-py311/bin/streamlit run frontend/app_coingecko.py \
    --server.port 4000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    > logs/streamlit.log 2>&1 &

# Note the PID
echo $!
```

---

### Step 12: Verify All Services Running
```bash
# Check processes
ps aux | grep -E "(facilitator|resource|streamlit)" | grep -v grep

# Check ports
netstat -tulpn | grep -E ":(3000|3001|4000)"
```

---

### Step 13: Test Endpoints Locally
```bash
# Test Facilitator
curl http://localhost:3001/health

# Test Resource
curl http://localhost:3000/health

# Test Streamlit
curl http://localhost:4000
```

---

### Step 14: Test Public URLs
```bash
# Test through Nginx (from server)
curl http://143.110.181.93/api/facilitator/health
curl http://143.110.181.93/api/resource/health

# Access frontend
curl http://143.110.181.93
```

---

### Step 15: Open in Browser
```
Open your browser and go to:
http://143.110.181.93

You should see the Streamlit frontend!
```

---

## 🔧 Optional: Setup Systemd Services (Recommended)

### Create Facilitator Service
```bash
cat > /etc/systemd/system/x402-facilitator.service << 'EOF'
[Unit]
Description=x402 Facilitator Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bitscrunch-x402
Environment="PATH=/root/bitscrunch-x402/venv-py311/bin"
ExecStart=/root/bitscrunch-x402/venv-py311/bin/uvicorn backend.facilitator_server:app --host 0.0.0.0 --port 3001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Create Resource Service
```bash
cat > /etc/systemd/system/x402-resource.service << 'EOF'
[Unit]
Description=x402 Resource Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bitscrunch-x402
Environment="PATH=/root/bitscrunch-x402/venv-py311/bin"
Environment="FLASK_APP=backend/resource_server.py"
ExecStart=/root/bitscrunch-x402/venv-py311/bin/flask run --host 0.0.0.0 --port 3000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Create Streamlit Service
```bash
cat > /etc/systemd/system/x402-streamlit.service << 'EOF'
[Unit]
Description=x402 Streamlit Frontend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/bitscrunch-x402
Environment="PATH=/root/bitscrunch-x402/venv-py311/bin"
ExecStart=/root/bitscrunch-x402/venv-py311/bin/streamlit run frontend/app_coingecko.py --server.port 4000 --server.address 0.0.0.0 --server.headless true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Enable and Start Systemd Services
```bash
# Reload systemd
systemctl daemon-reload

# Enable services to start on boot
systemctl enable x402-facilitator x402-resource x402-streamlit

# Stop manual processes first
pkill -f facilitator_server
pkill -f resource_server
pkill -f streamlit

# Start systemd services
systemctl start x402-facilitator x402-resource x402-streamlit

# Check status
systemctl status x402-facilitator
systemctl status x402-resource
systemctl status x402-streamlit
```

---

## 📝 View Logs

### Application Logs
```bash
# View logs in real-time
tail -f /root/bitscrunch-x402/logs/facilitator.log
tail -f /root/bitscrunch-x402/logs/resource.log
tail -f /root/bitscrunch-x402/logs/streamlit.log

# View last 100 lines
tail -n 100 /root/bitscrunch-x402/logs/facilitator.log
```

### Systemd Logs (if using systemd)
```bash
journalctl -u x402-facilitator -f
journalctl -u x402-resource -f
journalctl -u x402-streamlit -f
```

### Nginx Logs
```bash
tail -f /var/log/nginx/x402-access.log
tail -f /var/log/nginx/x402-error.log
```

---

## 🔄 Restart Services

### Manual Restart
```bash
# Stop all
pkill -f facilitator_server
pkill -f resource_server
pkill -f streamlit

# Start all
cd /root/bitscrunch-x402
./start_servers_production.sh

# Start Streamlit
nohup ./venv-py311/bin/streamlit run frontend/app_coingecko.py --server.port 4000 --server.address 0.0.0.0 --server.headless true > logs/streamlit.log 2>&1 &
```

### Systemd Restart
```bash
systemctl restart x402-facilitator x402-resource x402-streamlit
```

---

## 🐛 Troubleshooting

### If services won't start:
```bash
# Check what's using the ports
lsof -i :3000
lsof -i :3001
lsof -i :4000

# Kill processes
kill <PID>
```

### If nginx errors:
```bash
# Test configuration
nginx -t

# Restart nginx
systemctl restart nginx

# Check logs
tail -50 /var/log/nginx/error.log
```

### If payment fails:
```bash
# Check RPC connection
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  https://base-sepolia-rpc.publicnode.com
```

---

## ✅ Verification Checklist

- [ ] Repository cloned to `/root/bitscrunch-x402`
- [ ] `.env` file exists with production config
- [ ] Python 3.11 installed
- [ ] Virtual environment created (`venv-py311`)
- [ ] Dependencies installed
- [ ] Nginx configured and running
- [ ] Facilitator running on port 3001
- [ ] Resource server running on port 3000
- [ ] Streamlit running on port 4000
- [ ] Can access http://143.110.181.93 in browser
- [ ] API endpoints working
- [ ] Systemd services enabled (optional)

---

## 🎯 Your Production URLs

Once deployed:
- **Frontend**: http://143.110.181.93
- **Facilitator API**: http://143.110.181.93/api/facilitator
- **Resource API**: http://143.110.181.93/api/resource

**Ports Used:**
- 3000 → Resource Server
- 3001 → Facilitator Server
- 4000 → Streamlit Frontend
- 80 → Nginx (proxies to above)

---

## 📞 Need Help?

View full documentation:
- `PRODUCTION_DEPLOYMENT.md` - Complete guide
- `QUICK_DEPLOY.md` - Quick reference

Repository: https://github.com/coingraphai/bitscrunch-x402
