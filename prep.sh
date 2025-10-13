#!/bin/bash

# A script to interactively create the backend .env file.

echo "Welcome! This script will set up the configuration for your Proxmox application."
echo "----------------------------------------------------------------------------"

# --- NEW: Check for the secret in the environment ---
if [ -z "$PROXMOX_TOKEN_VALUE_ENV" ]; then
    echo "❌ Error: Proxmox token secret not found."
    echo "Before running this script, please set the secret using:"
    echo "export PROXMOX_TOKEN_VALUE_ENV='your_secret_token_value'"
    echo "(Add a space before the command to help prevent it from saving in history)"
    exit 1
fi
# ---------------------------------------------------

echo ""
echo "--- Backend Configuration ---"

# Ask for the Proxmox details (excluding the secret)
read -p "Enter your Proxmox Host IP (e.g., 192.168.1.100): " PROXMOX_HOST
read -p "Enter your Proxmox User (e.g., root@pam): " PROXMOX_USER
read -p "Enter your Proxmox API Token Name (e.g., myapp-token): " PROXMOX_TOKEN_NAME

# Auto-generate the SECRET_KEY
echo "Generating a secure SECRET_KEY..."
SECRET_KEY=$(openssl rand -hex 32)

# Auto-detect the VM's primary IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

# Check if IP address was found
if [ -z "$IP_ADDR" ]; then
    echo "❌ Error: Could not automatically detect IP address."
    read -p "Please enter the IP address for this VM manually: " IP_ADDR
fi

# Create the log file
cat << EOF > app.log
"Creating logging file"
EOF

# Create the backend .env file
# It now reads the token value from the environment variable
cat << EOF > .env
PROXMOX_HOST=${PROXMOX_HOST}
PROXMOX_USER=${PROXMOX_USER}
PROXMOX_TOKEN_NAME=${PROXMOX_TOKEN_NAME}
PROXMOX_TOKEN_VALUE=${PROXMOX_TOKEN_VALUE_ENV}
VITE_API_TARGET=http://${IP_ADDR}:8000
SECRET_KEY=${SECRET_KEY}
EOF

echo ""
echo "✅ Success! Your .env file has been created."
echo "Backend .env is ready."
echo "A new SECRET_KEY has been generated and added."
echo "Vite IP has been set with API target: http://${IP_ADDR}:8000"
echo ""

# --- Clean up the environment variable ---
unset PROXMOX_TOKEN_VALUE_ENV
echo "Secrets have been cleared from the environment."
# ----------------------------------------
