#!/bin/bash

# A script to interactively create the backend .env file
# and automatically create the frontend .env file.

echo "Welcome! This script will set up the configuration for your Proxmox application."
echo "----------------------------------------------------------------------------"
echo ""
echo "--- Backend Configuration ---"

# Ask for the Proxmox details
read -p "Enter your Proxmox User (e.g., root@pam): " PROXMOX_USER
read -p "Enter your Proxmox API Token Name (e.g., myapp-token): " PROXMOX_TOKEN_NAME

# -s flag hides the input for security
read -sp "Enter your Proxmox API Token Secret/Value: " PROXMOX_TOKEN_VALUE
echo "" # Move to a new line after the hidden input

# --- THIS IS THE NEW PART ---
# Auto-detect the VM's primary IP address
# hostname -I gets all IPs, awk '{print $1}' grabs the first one.
IP_ADDR=$(hostname -I | awk '{print $1}')

# Check if IP address was found
if [ -z "$IP_ADDR" ]; then
    echo "❌ Error: Could not automatically detect IP address."
    read -p "Please enter the IP address for this VM manually: " IP_ADDR
fi

# ----------------------------

# --- Create the backend .env file ---
cat << EOF > .env
PROXMOX_HOST=${IP_ADDR}
PROXMOX_USER=${PROXMOX_USER}
PROXMOX_TOKEN_NAME=${PROXMOX_TOKEN_NAME}
PROXMOX_TOKEN_VALUE=${PROXMOX_TOKEN_VALUE}
EOF

# --- Create the frontend .env file ---
cat << EOF > frontend/.env
VITE_API_TARGET=http://${IP_ADDR}:8000
EOF

echo ""
echo "✅ Success! Your .env files have been created."
echo "Backend .env is ready."
echo "Frontend .env has been set with API target: http://${IP_ADDR}:8000"
echo ""
