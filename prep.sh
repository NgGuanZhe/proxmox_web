#!/bin/bash

# A script to interactively create the backend .env file and set up frontend SSL.

echo "Welcome! This script will set up the configuration for your Proxmox application."
echo "----------------------------------------------------------------------------"

# --- Backend Configuration ---

if [ -z "$PROXMOX_TOKEN_VALUE_ENV" ]; then
    echo "❌ Error: Proxmox token secret not found in environment."
    echo "Before running this script, please set the secret using:"
    echo " export PROXMOX_TOKEN_VALUE_ENV='your_secret_token_value'"
    echo "(Add a space before the command to help prevent it from saving in history)"
    exit 1
fi

echo ""
echo "--- Backend .env Setup ---"

read -p "Enter your Proxmox Host IP (e.g., 192.168.1.100): " PROXMOX_HOST
read -p "Enter your Proxmox User (e.g., root@pam): " PROXMOX_USER
read -p "Enter your Proxmox API Token Name (e.g., myapp-token): " PROXMOX_TOKEN_NAME

echo "Generating a secure SECRET_KEY..."
SECRET_KEY=$(openssl rand -hex 32)

IP_ADDR=$(hostname -I | awk '{print $1}')
if [ -z "$IP_ADDR" ]; then
    echo "❌ Error: Could not automatically detect IP address."
    read -p "Please enter the IP address for this VM manually: " IP_ADDR
fi

cat << EOF > app.log
"Creating logging file"
EOF

cat << EOF > .env
PROXMOX_HOST=${PROXMOX_HOST}
PROXMOX_USER=${PROXMOX_USER}
PROXMOX_TOKEN_NAME=${PROXMOX_TOKEN_NAME}
PROXMOX_TOKEN_VALUE=${PROXMOX_TOKEN_VALUE_ENV}
VITE_API_TARGET=http://${IP_ADDR}:8000
SECRET_KEY=${SECRET_KEY}
EOF

echo "✅ Backend .env file created successfully."
unset PROXMOX_TOKEN_VALUE_ENV
echo "Secrets have been cleared from the environment."
echo ""

# --- Frontend SSL Configuration ---

echo "--- Frontend SSL Setup ---"

command_exists () {
    type "$1" &> /dev/null ;
}

# Check if mkcert is installed
if command_exists mkcert ; then
    echo "✅ mkcert is already installed."
else
    echo "mkcert not found. Attempting to install it..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get ; then
            echo "You will be prompted for your password to install packages."
            sudo apt-get update
            sudo apt-get install -y libnss3-tools wget
            
            # Automate finding the latest version and downloading it
            MKCERT_LATEST=$(curl -s "https://api.github.com/repos/FiloSottile/mkcert/releases/latest" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/')
            MKCERT_FILENAME="mkcert-${MKCERT_LATEST}-linux-amd64"
            
            echo "Downloading ${MKCERT_FILENAME}..."
            wget "https://github.com/FiloSottile/mkcert/releases/download/${MKCERT_LATEST}/${MKCERT_FILENAME}"
            
            chmod +x "${MKCERT_FILENAME}"
            sudo mv "${MKCERT_FILENAME}" /usr/local/bin/mkcert
            echo "✅ mkcert has been installed."
        else
            echo "Error: 'apt-get' not found. Please install mkcert manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command_exists brew ; then
            echo "Attempting to install with Homebrew..."
            brew install mkcert
        else
            echo "Error: Homebrew not found. Please install mkcert manually."
            exit 1
        fi
    else
        echo "Unsupported OS for automatic installation. Please install mkcert manually."
        exit 1
    fi
fi

# Run mkcert -install to create the local CA
echo "Setting up local Certificate Authority (CA). You may be prompted for your password."
mkcert -install

# Generate the certificate files in the correct directory
echo "Generating local SSL certificates for the frontend..."
(cd prox_frontend && mkcert localhost)

echo "✅ Frontend SSL certificates generated in 'prox_frontend/'."
echo ""
echo "----------------------------------------------------------------------------"
echo "🎉 Setup complete! You can now run the frontend and backend."
