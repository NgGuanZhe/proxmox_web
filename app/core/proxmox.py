import os
from fastapi import HTTPException
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
PROXMOX_HOST = os.getenv("PROXMOX_HOST")
PROXMOX_USER = os.getenv("PROXMOX_USER")
PROXMOX_TOKEN_NAME = os.getenv("PROXMOX_TOKEN_NAME")
PROXMOX_TOKEN_VALUE = os.getenv("PROXMOX_TOKEN_VALUE")

def get_proxmox_connection():
    """Helper function to connect to the Proxmox API."""
    try:
        full_user_string = "{}!{}".format(PROXMOX_USER, PROXMOX_TOKEN_NAME)
        proxmox = ProxmoxAPI(
            PROXMOX_HOST,
            user=PROXMOX_USER,
	    token_name=PROXMOX_TOKEN_NAME,
            token_value=PROXMOX_TOKEN_VALUE,
            verify_ssl=False
        )
        return proxmox
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
