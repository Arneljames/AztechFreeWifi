#!/bin/bash

# Aztech Free WiFi Setup Script for Orange Pi (Armbian)

echo "Setting up Aztech Free WiFi Captive Portal..."

# 1. Update and install dependencies
sudo apt update
sudo apt install -y python3 python3-flask python3-pip sqlite3 iproute2 iptables-persistent

# 2. Initialize Database if not exists
if [ ! -f wifi_users.db ]; then
    echo "Initializing database..."
    sqlite3 wifi_users.db < schema.sql
fi

# 3. iptables setup (Enable IP Forwarding)
echo "Enabling IP Forwarding..."
sudo sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf

# 4. Default iptables rules for captive portal (Block all FORWARD traffic by default)
# IMPORTANT: Adjust 'wlan0' to your actual WiFi interface
WIFI_IF="wlan0"
echo "Setting up default firewall rules on $WIFI_IF..."
sudo iptables -P FORWARD DROP
sudo iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# 5. Instructions to run
echo "------------------------------------------------"
echo "Setup Complete!"
echo "Steps to run:"
echo "1. Ensure you have sudo privileges."
echo "2. Run: sudo python3 app.py"
echo "3. The portal will be available on http://<OrangePi-IP>:8080"
echo "------------------------------------------------"
