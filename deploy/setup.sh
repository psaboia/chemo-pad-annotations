#!/bin/bash

# Deployment script for ChemoPAD Flask App on Ubuntu 22.04
# Run this after cloning the repository

set -e

echo "ChemoPAD Flask App Deployment Script"
echo "====================================="

# Variables
APP_DIR="/home/ubuntu/chemopad"
VENV_DIR="$APP_DIR/venv"

# Create necessary directories
echo "1. Creating directories..."
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/log/supervisor
sudo mkdir -p /var/run/gunicorn
sudo chown ubuntu:ubuntu /var/log/gunicorn
sudo chown ubuntu:ubuntu /var/run/gunicorn

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
    echo "ERROR: Missing data/chemoPAD-student-annotations-with-flags.csv"
    echo "Please upload your CSV data files to the data/ directory"
    exit 1
fi

if [ ! -f "data/project_cards.csv" ]; then
    echo "ERROR: Missing data/project_cards.csv"
    echo "Please upload your CSV data files to the data/ directory"
    exit 1
fi

# Setup Nginx
echo "5. Setting up Nginx..."
sudo cp deploy/nginx.conf /etc/nginx/sites-available/chemopad
sudo ln -sf /etc/nginx/sites-available/chemopad /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# Setup Supervisor
echo "6. Setting up Supervisor..."
sudo cp deploy/supervisor.conf /etc/supervisor/conf.d/chemopad.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start chemopad

# Setup firewall
echo "7. Setting up firewall..."
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