#!/bin/bash

# Deployment script for ChemoPAD Flask App on Ubuntu 22.04
# This version automatically detects the current user

set -e

echo "ChemoPAD Flask App Deployment Script"
echo "====================================="

# Detect current user and home directory
CURRENT_USER=$(whoami)
USER_HOME=$HOME
APP_DIR="$USER_HOME/chemopad"
VENV_DIR="$APP_DIR/venv"

echo "Detected user: $CURRENT_USER"
echo "Home directory: $USER_HOME"
echo "App directory: $APP_DIR"
echo ""

# Create necessary directories
echo "1. Creating directories..."
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/log/supervisor
sudo mkdir -p /var/run/gunicorn
sudo chown $CURRENT_USER:$CURRENT_USER /var/log/gunicorn
sudo chown $CURRENT_USER:$CURRENT_USER /var/run/gunicorn

# Setup Python virtual environment
echo "2. Setting up Python virtual environment..."
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "3. Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy data files
echo "4. Checking data files..."
if [ ! -f "data/chemoPAD-student-annotations-with-flags.csv" ]; then
    echo "WARNING: Missing data/chemoPAD-student-annotations-with-flags.csv"
    echo "Please upload your CSV data files to the data/ directory"
    echo "Continuing anyway..."
fi

if [ ! -f "data/project_cards.csv" ]; then
    echo "WARNING: Missing data/project_cards.csv"
    echo "Please upload your CSV data files to the data/ directory"
    echo "Continuing anyway..."
fi

# Create updated config files with correct paths
echo "5. Creating configuration files..."

# Create updated supervisor config
cat > /tmp/chemopad-supervisor.conf <<EOF
[program:chemopad]
command=$APP_DIR/venv/bin/gunicorn -c $APP_DIR/deploy/gunicorn_config.py app_production:app
directory=$APP_DIR/flask-app
user=$CURRENT_USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/chemopad.log
environment=PATH="$APP_DIR/venv/bin",FLASK_SECRET_KEY="your-secret-key-here"
EOF

# Create updated nginx config
cat > /tmp/chemopad-nginx.conf <<EOF
server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }

    location /static {
        alias $APP_DIR/flask-app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Setup Nginx
echo "6. Setting up Nginx..."
sudo cp /tmp/chemopad-nginx.conf /etc/nginx/sites-available/chemopad
sudo ln -sf /etc/nginx/sites-available/chemopad /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Setup Supervisor
echo "7. Setting up Supervisor..."
sudo cp /tmp/chemopad-supervisor.conf /etc/supervisor/conf.d/chemopad.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start chemopad

# Setup firewall
echo "8. Setting up firewall..."
sudo ufw allow 80/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Your app should now be accessible at:"
echo "http://<your-vm-ip-address>"
echo ""
echo "Useful commands:"
echo "  Check status:  sudo supervisorctl status chemopad"
echo "  Restart app:   sudo supervisorctl restart chemopad"
echo "  View logs:     sudo tail -f /var/log/supervisor/chemopad.log"
echo "  Nginx logs:    sudo tail -f /var/log/nginx/error.log"
echo ""