import time
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.proxmox import get_proxmox_connection
from typing import Optional
from app.routers.auth import get_current_active_user

router = APIRouter()

class SdnZoneRequest(BaseModel):
    zone: str
    type: str
    bridge: Optional[str] = None
    peers: Optional[str] = None

class SdnVnetRequest(BaseModel):
    vnet: str
    zone: str
    tag: Optional[int] = None

@router.get("/sdn/zones", tags=["SDN"])
def list_sdn_zones(current_user: dict = Depends(get_current_active_user)):
    """Gets a list of all SDN zones."""
    proxmox = get_proxmox_connection()
    try:
        # The endpoint is /cluster/sdn/zones
        return proxmox.cluster.sdn.zones.get()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sdn/zones", tags=["SDN"])
def create_sdn_zone(request: SdnZoneRequest, current_user: dict = Depends(get_current_active_user)):
    """Creates a new SDN Zone."""
    proxmox = get_proxmox_connection()
    # Prepare the parameters to send to Proxmox
    params = {
        'zone': request.zone,
        'type': request.type
    }
    if request.type == 'vlan' and request.bridge:
        params['bridge'] = request.bridge
    if request.type == 'vxlan' and request.peers:
        params['peers'] = request.peers
        
    try:
        # Proxmox API call to create a new SDN Zone
        result = proxmox.cluster.sdn.zones.post(**params)
        time.sleep(2) # Give a moment for tasks to register
        proxmox.cluster.sdn.put()
        return {"message": "Successfully created SDN Zone '{}' of type '{}'".format(request.zone, request.type)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sdn/zones/{zone}", tags=["SDN"])
def delete_sdn_zone(zone: str, current_user: dict = Depends(get_current_active_user)):
    """Deletes an SDN Zone."""
    proxmox = get_proxmox_connection()
    try:
        # Proxmox API call to delete the zone
        result = proxmox.cluster.sdn.zones(zone).delete()
        time.sleep(2) # Give a moment for tasks to register
        proxmox.cluster.sdn.put()
        return {"message": "Successfully deleted SDN Zone '{}'".format(zone)}
    except Exception as e:
        # Provide a helpful error if the zone is not empty
        if 'is not empty' in str(e):
            raise HTTPException(status_code=400, detail="Cannot delete zone '{}' because it is not empty. Please remove all VNETs from it first.".format(zone))
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/sdn/vnets", tags=["SDN"])
def list_sdn_vnets(current_user: dict = Depends(get_current_active_user)):
    """Gets a list of all SDN VNETs."""
    proxmox = get_proxmox_connection()
    try:
        return proxmox.cluster.sdn.vnets.get()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sdn/vnets", tags=["SDN"])
def create_sdn_vnet(request: SdnVnetRequest, current_user: dict = Depends(get_current_active_user)):
    """Creates a new SDN VNET in a specific zone."""
    proxmox = get_proxmox_connection()
    params = {
        'vnet': request.vnet,
        'zone': request.zone
    }
    # Add the tag only if it's provided (required for VLAN zones)
    if request.tag is not None:
        params['tag'] = request.tag
    
    try:
        result = proxmox.cluster.sdn.vnets.post(**params)
        time.sleep(2) # Give a moment for tasks to register
        proxmox.cluster.sdn.put()
        return {"message": "Successfully created VNET '{}' in zone '{}'".format(request.vnet, request.zone)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
@router.delete("/sdn/vnets/{vnet}", tags=["SDN"])
def delete_sdn_vnet(vnet: str, current_user: dict = Depends(get_current_active_user)):
    """Deletes an SDN VNET."""
    proxmox = get_proxmox_connection()
    try:
        # Proxmox API call to delete the vnet
        result = proxmox.cluster.sdn.vnets(vnet).delete()
        time.sleep(2) # Give a moment for tasks to register
        proxmox.cluster.sdn.put()
        return {"message": "Successfully deleted SDN VNET '{}'".format(vnet)}
    except Exception as e:
        if 'in use' in str(e):
            raise HTTPException(status_code=400, detail="Cannot delete VNET '{}' because it is in use by a VM.".format(vnet))
        raise HTTPException(status_code=500, detail=str(e))
        
        
