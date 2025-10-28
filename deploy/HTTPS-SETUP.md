# HTTPS Setup with Let's Encrypt

## Prerequisites

1. **You need a domain name** pointing to your VM's IP address
   - Can be a subdomain like `chemopad.yourdomain.com`
   - Free options: [DuckDNS](https://www.duckdns.org/), [No-IP](https://www.noip.com/)

2. **DNS must be configured** before running the setup
   - Your domain must resolve to your VM's public IP
   - Test with: `nslookup your-domain.com`

## Option 1: Automated Setup (Recommended)

```bash
cd /home/ubuntu/chemopad
chmod +x deploy/setup-https.sh
./deploy/setup-https.sh your-domain.com
```

Follow the prompts:
- Enter your email for renewal notifications
- Agree to Let's Encrypt terms
- Choose whether to redirect HTTP to HTTPS (recommended: yes)

## Option 2: Manual Setup

### Step 1: Install Certbot
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

### Step 2: Update Nginx config with your domain
```bash
sudo nano /etc/nginx/sites-available/chemopad
```

Change `server_name _;` to `server_name your-domain.com;`

### Step 3: Obtain SSL certificate
```bash
sudo certbot --nginx -d your-domain.com
```

### Step 4: Setup auto-renewal
```bash
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## Option 3: Using Private IP Only (No Public Domain)

If you only have a private IP and no domain, you can:

### A. Self-Signed Certificate (Not recommended for production)
```bash
# Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/chemopad.key \
    -out /etc/ssl/certs/chemopad.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-private-ip"

# Update Nginx config
sudo nano /etc/nginx/sites-available/chemopad
```

Add to the server block:
```nginx
listen 443 ssl;
ssl_certificate /etc/ssl/certs/chemopad.crt;
ssl_certificate_key /etc/ssl/private/chemopad.key;
```

### B. Use SSH Tunnel (Recommended for private networks)
No HTTPS needed. From your local machine:
```bash
ssh -L 8080:localhost:80 ubuntu@your-vm-ip
```
Then access at: `http://localhost:8080`

### C. Use VPN Access
If your VM is on a private network, use VPN to access it securely without HTTPS.

## Free Domain Options

If you don't have a domain:

### 1. DuckDNS (Easiest)
1. Go to https://www.duckdns.org/
2. Sign in with GitHub/Google
3. Create subdomain: `yourname.duckdns.org`
4. Point it to your VM's public IP
5. Use automated script:
```bash
# Install DuckDNS updater
echo "url=\"https://www.duckdns.org/update?domains=yourname&token=your-token&ip=\" | curl -k -o ~/duck.log -K-" > ~/duck.sh
chmod 700 ~/duck.sh
# Add to crontab for auto-update
(crontab -l ; echo "*/5 * * * * ~/duck.sh") | crontab -
```

### 2. No-IP
1. Sign up at https://www.noip.com/
2. Create hostname
3. Install dynamic update client:
```bash
cd /tmp
wget https://www.noip.com/client/linux/noip-duc-linux.tar.gz
tar xzf noip-duc-linux.tar.gz
cd noip-2.1.9-1/
sudo make install
```

### 3. Cloudflare (if you own a domain)
1. Add domain to Cloudflare (free plan)
2. Point A record to your VM IP
3. Enable proxy for DDoS protection
4. Use Cloudflare Origin Certificate:
```bash
# Instead of Let's Encrypt, use Cloudflare Origin Certificate
# Download from Cloudflare dashboard → SSL/TLS → Origin Server
```

## Testing HTTPS

After setup, test your HTTPS configuration:

### Check certificate
```bash
sudo certbot certificates
```

### Test SSL configuration
```bash
# Online test
curl -I https://your-domain.com

# SSL Labs test (best)
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=your-domain.com
```

### Test auto-renewal
```bash
sudo certbot renew --dry-run
```

## Troubleshooting

### Certificate fails to obtain
- **Port 80 must be accessible** from internet
- Check firewall: `sudo ufw status`
- Check DNS: `nslookup your-domain.com`
- Check Nginx: `sudo nginx -t`

### Too many certificates error
Let's Encrypt has rate limits. Wait 1 week or use staging:
```bash
sudo certbot --nginx -d your-domain.com --staging
```

### Mixed content warnings
Update Flask app to use HTTPS URLs:
```python
# In app_production.py, add:
@app.before_request
def force_https():
    if not request.is_secure:
        return redirect(request.url.replace('http://', 'https://'))
```

## Security Headers (Optional)

Add security headers to Nginx config:
```nginx
# In /etc/nginx/sites-available/chemopad
server {
    # ... existing config ...

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

## Monitoring

### Check certificate expiration
```bash
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Setup expiration alerts
```bash
# Add to crontab
0 0 * * 1 certbot renew --post-hook "systemctl reload nginx"
```

## Important Notes

1. **Let's Encrypt certificates expire after 90 days** but auto-renew with certbot timer
2. **Rate limits**: Max 50 certificates per domain per week
3. **Wildcard certificates** require DNS validation (more complex)
4. **Private IP only**: Can't use Let's Encrypt, use self-signed or SSH tunnel instead