#!/bin/bash

# Define the interfaces
WIFI_INTERFACE="wlan0"  # This is the interface for the hotspot
ETH_INTERFACE="eth0"    # Ethernet interface providing internet
WIFI_INTERNET_INTERFACE="wlan1"  # Wi-Fi interface providing internet

# Install necessary packages
echo "Installing required packages..."
sudo apt update
sudo apt install -y hostapd dnsmasq

# Stop services if they're running
echo "Stopping hostapd and dnsmasq services..."
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq

# Configure a static IP for the hotspot interface (wlan0)
echo "Configuring static IP for the wireless hotspot interface..."
sudo bash -c "cat > /etc/dhcpcd.conf" <<EOL
interface $WIFI_INTERFACE
static ip_address=192.168.50.1/24
denyinterfaces $WIFI_INTERFACE
EOL

# Restart dhcpcd to apply changes
sudo systemctl restart dhcpcd

# Configure dnsmasq for DHCP service
echo "Configuring dnsmasq..."
sudo bash -c "cat > /etc/dnsmasq.conf" <<EOL
interface=$WIFI_INTERFACE
dhcp-range=192.168.50.10,192.168.50.100,12h
EOL

# Configure hostapd for the access point
echo "Configuring hostapd..."
sudo bash -c "cat > /etc/hostapd/hostapd.conf" <<EOL
interface=$WIFI_INTERFACE
driver=nl80211
ssid=MyRPiHotspot    # Change this to your preferred SSID
hw_mode=g
channel=7
ieee80211n=1
wmm_enabled=1
ht_capab=[HT40][SHORT-GI-20][DSSS_CCK-40]
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=raspberrypi  # Change this to your preferred Wi-Fi password
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
EOL

# Point hostapd to its config file
sudo bash -c "cat > /etc/default/hostapd" <<EOL
DAEMON_CONF="/etc/hostapd/hostapd.conf"
EOL

# Enable IP forwarding for internet sharing
echo "Enabling IP forwarding..."
sudo bash -c "echo 'net.ipv4.ip_forward=1' > /etc/sysctl.conf"
sudo sysctl -p

# Set up NAT between the hotspot and both internet interfaces (eth0 and wlan1)
echo "Configuring NAT between $ETH_INTERFACE, $WIFI_INTERNET_INTERFACE, and $WIFI_INTERFACE..."

# Configure iptables for Ethernet (eth0)
sudo iptables -t nat -A POSTROUTING -o $ETH_INTERFACE -j MASQUERADE
sudo iptables -A FORWARD -i $ETH_INTERFACE -o $WIFI_INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i $WIFI_INTERFACE -o $ETH_INTERFACE -j ACCEPT

# Configure iptables for Wi-Fi internet interface (wlan1)
sudo iptables -t nat -A POSTROUTING -o $WIFI_INTERNET_INTERFACE -j MASQUERADE
sudo iptables -A FORWARD -i $WIFI_INTERNET_INTERFACE -o $WIFI_INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i $WIFI_INTERFACE -o $WIFI_INTERNET_INTERFACE -j ACCEPT

# Save iptables rules
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
sudo bash -c "cat >> /etc/rc.local" <<EOL
iptables-restore < /etc/iptables.ipv4.nat
exit 0
EOL

# Enable and start the services
echo "Starting hostapd and dnsmasq services..."
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
sudo systemctl start hostapd
sudo systemctl start dnsmasq

echo "Hotspot setup completed successfully!"
