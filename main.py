import os
import sys
from fastapi import FastAPI, HTTPException
from proxmoxer import ProxmoxAPI

# --- Configuration ---
# It's best practice to get credentials from environment variables
# instead of writing them directly in the code.
PROXMOX_HOST = os.getenv("PROXMOX_HOST")
PROXMOX_USER = os.getenv("PROXMOX_USER")
PROXMOX_TOKEN_NAME = os.getenv("PROXMOX_TOKEN_NAME")
PROXMOX_TOKEN = os.getenv("PROXMOX_TOKEN")

# --- FastAPI Application ---
app = FastAPI()

def get_proxmox_connection():
    """Helper function to connect to the Proxmox API."""
    try:
        # Connect to Proxmox
        proxmox = ProxmoxAPI(
            PROXMOX_HOST,
            user=PROXMOX_USER,
            token_name=PROXMOX_TOKEN_NAME,
	    token_value=PROXMOX_TOKEN
            verify_ssl=False  # Set to False for self-signed certificates
        )
        return proxmox
    except Exception as e:
        # If connection fails, raise an HTTP exception
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    """Root endpoint to show the server is running."""
    return {"message": "Proxmox API server is running!"}

@app.get("/vms")
def list_vms():
    """New endpoint to list all VMs from all nodes."""
    proxmox = get_proxmox_connection()
    all_vms = []
    
    try:
        # Loop through all nodes in the cluster
        for node in proxmox.nodes.get():
            # Get all VMs on the current node
            for vm in proxmox.nodes(node['node']).qemu.get():
                all_vms.append(vm)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return all_vms
