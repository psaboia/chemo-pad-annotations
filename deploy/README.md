# Deployment Guide for Ubuntu 22.04 LTS

## VM Requirements
- Ubuntu 22.04 LTS
- 2 CPU cores (minimum)
- 2 GB RAM (minimum, 4 GB recommended)
- 25 GB disk space
- Private/Public IP address

## Deployment Steps

### 1. Connect to your VM
```bash
ssh ubuntu@<your-vm-ip>
```

### 2. Clone the repository
```bash
cd /home/ubuntu
git clone <your-repo-url> chemopad
cd chemopad
```

### 3. Upload CSV data files
You need to upload your data files to the `data/` directory:
- `chemoPAD-student-annotations.csv`
- `chemoPAD-student-annotations-with-flags.csv`
- `chemoPAD-dataset.csv`
- `project_cards.csv`

Using SCP from your local machine:
```bash
scp data/*.csv ubuntu@<your-vm-ip>:/home/ubuntu/chemopad/data/
```

### 4. Run the setup script
```bash
cd /home/ubuntu/chemopad
chmod +x deploy/setup.sh
./deploy/setup.sh
```

### 5. Access the application
Open your browser and navigate to:
```
http://<your-vm-ip-address>
```

## Manual Installation (if setup script fails)

### Install dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx supervisor -y
```

### Create Python virtual environment
```bash
cd /home/ubuntu/chemopad
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure Nginx
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/chemopad
sudo ln -s /etc/nginx/sites-available/chemopad /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Configure Supervisor
```bash
sudo cp deploy/supervisor.conf /etc/supervisor/conf.d/chemopad.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start chemopad
```

## Management Commands

### Check application status
```bash
sudo supervisorctl status chemopad
```

### Restart application
```bash
sudo supervisorctl restart chemopad
```

### View application logs
```bash
sudo tail -f /var/log/supervisor/chemopad.log
```

### View nginx error logs
```bash
sudo tail -f /var/log/nginx/error.log
```

### Stop application
```bash
sudo supervisorctl stop chemopad
```

## Troubleshooting

### Port already in use
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
```

### Permission errors
```bash
sudo chown -R ubuntu:ubuntu /home/ubuntu/chemopad
sudo chmod -R 755 /home/ubuntu/chemopad
```

### Memory issues (2GB RAM)
If you experience memory issues with 2GB RAM:
1. Reduce gunicorn workers to 1 in `gunicorn_config.py`
2. Consider adding swap space:
```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

## Security Considerations

1. **Change the secret key** in supervisor.conf:
   ```bash
   FLASK_SECRET_KEY="your-unique-secret-key-here"
   ```

2. **Configure firewall**:
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 22/tcp
   sudo ufw enable
   ```

3. **Consider HTTPS** with Let's Encrypt:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

## Backup

To backup your matches:
```bash
cp /home/ubuntu/chemopad/data/matches.json ~/matches_backup_$(date +%Y%m%d).json
```

## Performance Tuning

For 2GB RAM VM, optimize settings:

1. Edit `/home/ubuntu/chemopad/deploy/gunicorn_config.py`:
   - Set `workers = 1` (instead of 2)
   - Set `threads = 4`

2. Edit nginx config for caching:
   Add to `/etc/nginx/sites-available/chemopad`:
   ```nginx
   location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```