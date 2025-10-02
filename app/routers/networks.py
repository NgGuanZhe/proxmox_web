import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.proxmox import get_proxmox_connection

router = APIRouter()

class NetworkCreateRequest(BaseModel):
    node: str
    iface: str
    comments: str = None

@router.get("/networks", tags=["Networks"])
def list_networks():
    proxmox = get_proxmox_connection()
    all_networks = {}
    try:
        for node in proxmox.nodes.get():
            node_name = node['node']
            all_networks[node_name] = [
                net for net in proxmox.nodes(node_name).network.get()
                if net.get('type') == 'bridge'
            ]
        return all_networks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/networks", tags=["Networks"])
def create_network(request: NetworkCreateRequest):
    proxmox = get_proxmox_connection()
    try:
        proxmox.nodes(request.node).network.post(
            type='bridge', 
            iface=request.iface,
            autostart=1,
            comments=request.comments or 'Created by Web App'
        )
        
        # After creating, we must apply the pending changes.
        time.sleep(1)
        proxmox.nodes(request.node).network.put() # This is the "apply" call
        
        return {"message": "Successfully created and applied bridge {} on node {}".format(request.iface, request.node)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/networks/{node}/{iface}", tags=["Networks"])
def delete_network(node: str, iface: str):
    proxmox = get_proxmox_connection()
    try:
        proxmox.nodes(node).network(iface).delete()
        
        # After deleting, we must also apply the pending changes.
        time.sleep(1)
        proxmox.nodes(node).network.put() # This is the "apply" call
        
        return {"message": "Successfully deleted bridge {} from node {}".format(iface, node)}
    except Exception as e:
        if 'device is busy' in str(e):
            raise HTTPException(status_code=400, detail="Cannot delete bridge '{}' because it is in use.".format(iface))
        raise HTTPException(status_code=500, detail=str(e))
