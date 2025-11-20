# Production Server Setup Guide

## Server Configuration

**Server IP**: http://159.89.170.85

### Service URLs

| Service | Path | Full URL |
|---------|------|----------|
| Facilitator Server | `/facilitator` | http://159.89.170.85/facilitator |
| Resource Server | `/resource` | http://159.89.170.85/resource |
| Frontend (Streamlit) | `/` or `/app` | http://159.89.170.85:8501 |

## Environment Configuration

Your `.env` file has been updated with production URLs:

```bash
# Facilitator URL (used by resource server)
FACILITATOR_URL=http://159.89.170.85/facilitator

# Resource URL (used by frontend)
RESOURCE_URL=http://159.89.170.85/resource
```

## Nginx/Reverse Proxy Setup

You'll need to configure your web server (nginx/apache) to proxy requests:

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name 159.89.170.85;

    # Facilitator Server
    location /facilitator/ {
        proxy_pass http://localhost:8002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Resource Server
    location /resource/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Streamlit Frontend (optional)
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

## Deployment Steps

### 1. On Your Server (159.89.170.85)

```bash
# Clone the repository
cd ~
git clone https://github.com/coingraphai/bitscrunch-x402.git
cd bitscrunch-x402

# Copy and configure environment
cp .env.example .env
nano .env

# Update with production values:
# - FACILITATOR_URL=http://159.89.170.85/facilitator
# - RESOURCE_URL=http://159.89.170.85/resource
# - Your private keys and API keys
```

### 2. Deploy the Application

```bash
# Run deployment script
./deploy.sh

# Or manual setup:
python3.11 -m venv venv-py311
source venv-py311/bin/activate
pip install -r requirements.txt
./start_servers.sh
```

### 3. Configure Nginx

```bash
# Install nginx
sudo apt-get update
sudo apt-get install nginx

# Create configuration
sudo nano /etc/nginx/sites-available/bitscrunch-x402

# Add the nginx configuration from above

# Enable the site
sudo ln -s /etc/nginx/sites-available/bitscrunch-x402 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Start Services

```bash
cd ~/bitscrunch-x402
./start_servers.sh

# Start Streamlit (in background)
nohup ./venv-py311/bin/streamlit run frontend/app_coingecko.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
```

## Testing Production Setup

### Test Facilitator Server

```bash
curl http://159.89.170.85/facilitator/health
```

Expected response:
```json
{"status": "healthy"}
```

### Test Resource Server

```bash
curl http://159.89.170.85/resource/health
```

Expected response:
```json
{"status": "healthy", "server": "resource"}
```

### Test Frontend

Open browser: http://159.89.170.85:8501

## Process Management (systemd)

For production, use systemd to manage services:

### Facilitator Service

```bash
sudo nano /etc/systemd/system/x402-facilitator.service
```

```ini
[Unit]
Description=x402 Facilitator Server
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/bitscrunch-x402
Environment="PATH=/home/YOUR_USER/bitscrunch-x402/venv-py311/bin"
ExecStart=/home/YOUR_USER/bitscrunch-x402/venv-py311/bin/uvicorn backend.facilitator_server:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Resource Service

```bash
sudo nano /etc/systemd/system/x402-resource.service
```

```ini
[Unit]
Description=x402 Resource Server
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/home/YOUR_USER/bitscrunch-x402
Environment="PATH=/home/YOUR_USER/bitscrunch-x402/venv-py311/bin"
Environment="FLASK_APP=backend/resource_server.py"
ExecStart=/home/YOUR_USER/bitscrunch-x402/venv-py311/bin/flask run --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable x402-facilitator x402-resource
sudo systemctl start x402-facilitator x402-resource
sudo systemctl status x402-facilitator x402-resource
```

## Monitoring

### View Logs

```bash
# Service logs
sudo journalctl -u x402-facilitator -f
sudo journalctl -u x402-resource -f

# Application logs
tail -f logs/facilitator.log
tail -f logs/resource.log
```

### Check Service Status

```bash
sudo systemctl status x402-facilitator
sudo systemctl status x402-resource
```

## Security Considerations

1. **Firewall Rules**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 8501/tcp  # Streamlit (if direct access needed)
   sudo ufw enable
   ```

2. **SSL/TLS Certificate** (Recommended)
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

3. **Environment Variables**
   - Never commit `.env` to git
   - Protect private keys
   - Rotate keys regularly

4. **Updates**
   ```bash
   cd ~/bitscrunch-x402
   git pull
   sudo systemctl restart x402-facilitator x402-resource
   ```

## Troubleshooting

### Services Not Accessible

1. Check if services are running:
   ```bash
   sudo systemctl status x402-facilitator x402-resource
   curl http://localhost:8002/health
   curl http://localhost:8001/health
   ```

2. Check nginx configuration:
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

3. Check firewall:
   ```bash
   sudo ufw status
   ```

### Payment Failures

1. Check wallet balances (USDC and ETH for gas)
2. Verify RPC URL is accessible from server
3. Check facilitator logs for errors

### Frontend Connection Issues

1. Update `RESOURCE_URL` and `FACILITATOR_URL` in `.env`
2. Restart Streamlit application
3. Clear browser cache

## Support

For issues:
1. Check logs: `logs/facilitator.log`, `logs/resource.log`
2. Verify nginx configuration
3. Test endpoints with curl
4. Review GitHub repository: https://github.com/coingraphai/bitscrunch-x402

---

**Production Checklist:**
- ✅ Nginx configured with reverse proxy
- ✅ Services running on correct ports
- ✅ Environment variables set correctly
- ✅ SSL certificate installed (recommended)
- ✅ Firewall rules configured
- ✅ Systemd services enabled
- ✅ Monitoring and logs accessible
