#!/bin/bash

# HTTPS Setup Script with Let's Encrypt for ChemoPAD Flask App
# Run this after the main setup.sh script

set -e

echo "HTTPS Setup with Let's Encrypt"
echo "=============================="
echo ""

# Check if domain is provided
if [ -z "$1" ]; then
    echo "Usage: ./setup-https.sh your-domain.com"
    echo "Example: ./setup-https.sh chemopad.example.com"
    exit 1
fi

DOMAIN=$1

echo "Setting up HTTPS for domain: $DOMAIN"
echo ""

# Install Certbot
echo "1. Installing Certbot..."
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Test if the domain points to this server
echo "2. Testing domain DNS..."
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short $DOMAIN | head -n1)

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    echo "WARNING: Domain $DOMAIN does not point to this server!"
    echo "  Server IP: $SERVER_IP"
    echo "  Domain points to: $DOMAIN_IP"
    echo ""
    echo "Please update your DNS records and wait for propagation."
    echo "You can continue anyway if you're sure the DNS will be updated soon."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update Nginx configuration with domain
echo "3. Updating Nginx configuration..."
sudo sed -i "s/server_name _;/server_name $DOMAIN;/" /etc/nginx/sites-available/chemopad
sudo nginx -t
sudo systemctl reload nginx

# Obtain SSL certificate
echo "4. Obtaining SSL certificate from Let's Encrypt..."
echo "   You will be prompted for an email address for renewal notifications."
echo ""

sudo certbot --nginx -d $DOMAIN

# Setup auto-renewal
echo "5. Setting up automatic certificate renewal..."
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Test renewal
echo "6. Testing certificate renewal..."
sudo certbot renew --dry-run

echo ""
echo "========================================="
echo "HTTPS Setup Complete!"
echo "========================================="
echo ""
echo "Your app is now accessible via:"
echo "  https://$DOMAIN"
echo ""
echo "Certificate will auto-renew before expiration."
echo ""
echo "To manually renew certificate:"
echo "  sudo certbot renew"
echo ""
echo "To check certificate status:"
echo "  sudo certbot certificates"
echo ""