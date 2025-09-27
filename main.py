import os
import sys
import re
from fastapi import FastAPI, HTTPException
from proxmoxer import ProxmoxAPI
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
PROXMOX_HOST = os.getenv("PROXMOX_HOST")
PROXMOX_USER = os.getenv("PROXMOX_USER")
PROXMOX_TOKEN_NAME = os.getenv("PROXMOX_TOKEN_NAME")
PROXMOX_TOKEN_VALUE = os.getenv("PROXMOX_TOKEN_VALUE")

# --- FastAPI Application ---
app = FastAPI()

def _format_vm_details(vm_config):
    """Helper function to parse the raw config into a clean format."""
    details = {
        # --- THIS IS THE NEW LINE ---
        "template": vm_config.get("template", 0),
        "cpu": {
            "cores": vm_config.get("cores"),
            "sockets": vm_config.get("sockets"),
            "type": vm_config.get("cpu")
        },
        "memory_mb": vm_config.get("memory"),
        "boot_order": vm_config.get("boot"),
        "disks": [],
        "network_interfaces": []
    }

    # Parse all disk and network keys
    for key, value in vm_config.items():
        if key.startswith(('scsi', 'sata', 'ide', 'virtio')):
            disk_match = re.match(r"(.+?):(.+?),size=(\d+G?)", str(value))
            if disk_match:
                details["disks"].append({
                    "device": key,
                    "storage": disk_match.group(1),
                    "file": disk_match.group(2),
                    "size_gb": int(disk_match.group(3).replace('G', ''))
                })
        
        if key.startswith('net'):
            # This regex is simplified to be more robust
            parts = str(value).split(',')
            nic_details = { "device": key }
            for part in parts:
                if '=' in part:
                    k, v = part.split('=', 1)
                    if k in ['virtio', 'e1000', 'rtl8139', 'vmxnet3']:
                        nic_details['model'] = k
                        nic_details['mac_address'] = v
                    else:
                        nic_details[k] = v
            details["network_interfaces"].append(nic_details)

    return details

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

@app.get("/")
def read_root():
    return {"message": "Proxmox API server is running!"}

@app.get("/vms")
def list_vms():
    """Endpoint to list all VMs with detailed, formatted specs."""
    proxmox = get_proxmox_connection()
    all_vms_list = []
    
    try:
        for node in proxmox.nodes.get():
            node_name = node['node']
            for vm_summary in proxmox.nodes(node_name).qemu.get():
                vmid = vm_summary.get('vmid')
                if not vmid:
                    continue
                
                vm_config = proxmox.nodes(node_name).qemu(vmid).config.get()
                
                formatted_details = _format_vm_details(vm_config)

                full_details = {
                    'proxmox_id': vmid,
                    'name': vm_summary.get('name'),
                    'status': vm_summary.get('status'),
                    'node': node_name,
                    'hardware_details': formatted_details
                }
                all_vms_list.append(full_details)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return all_vms_list
