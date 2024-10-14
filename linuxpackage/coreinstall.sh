#!/bin/bash

# MQTT and Docker Installation Script
# This script installs Mosquitto MQTT Broker, Client, and Docker on a Debian-based system

# Update package list
echo "Updating package list..."
sudo apt update

# Install Mosquitto broker and clients
echo "Installing Mosquitto broker and clients..."
sudo apt install -y mosquitto mosquitto-clients

# Enable Mosquitto service to start on boot
echo "Enabling Mosquitto service to start on boot..."
sudo systemctl enable mosquitto

# Start Mosquitto service
echo "Starting Mosquitto service..."
sudo systemctl start mosquitto

# Check Mosquitto service status
echo "Checking Mosquitto service status..."
sudo systemctl status mosquitto

# Installing Docker
echo "Installing Docker..."

# Remove any old versions of Docker
sudo apt remove -y docker docker-engine docker.io containerd runc

# Install required packages
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker’s official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Set up the stable repository
echo "Adding Docker repository..."
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update package list again
sudo apt update

# Install Docker
echo "Installing Docker and Docker Compose..."
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Check Docker installation
echo "Checking Docker status..."
sudo systemctl status docker

# Final confirmation
echo "Mosquitto MQTT broker, clients, and Docker installed successfully!"
