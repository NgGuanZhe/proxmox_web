import time
import logging
from app.logging_helper import save_error
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.proxmox import get_proxmox_connection
from typing import Optional
from app.routers.auth import get_current_active_user

logger = logging.getLogger("proxmox_api")
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
    logger.info(f"User '{current_user.username}' requested to list all SDN Zones.")
    """Gets a list of all SDN zones."""
    proxmox = get_proxmox_connection()
    try:
        # The endpoint is /cluster/sdn/zones
        logger.info(f"Retrieval of SDN Zones...........")
        return proxmox.cluster.sdn.zones.get()
    except Exception as e:
        logger.error(f"Error with obtaining all SDN Zones: {save_error(e)}.")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sdn/zones", tags=["SDN"])
def create_sdn_zone(request: SdnZoneRequest, current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user.username}' requested to create SDN Zones.")
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
        logger.info(f"Successfully created SDN Zone '{request.zone}' of type '{request.type}'")
        return {"message": "Successfully created SDN Zone '{}' of type '{}'".format(request.zone, request.type)}
    except Exception as e:
        logger.error(f"Error creating SDN Zone {request.zone}.", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sdn/zones/{zone}", tags=["SDN"])
def delete_sdn_zone(zone: str, current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user.username}' requested to delete SDN Zones '{zone}'.")
    """Deletes an SDN Zone."""
    proxmox = get_proxmox_connection()
    try:
        # Proxmox API call to delete the zone
        result = proxmox.cluster.sdn.zones(zone).delete()
        time.sleep(2) # Give a moment for tasks to register
        proxmox.cluster.sdn.put()
        logger.info(f"Successfully deleted SDN Zone '{zone}'.")
        return {"message": "Successfully deleted SDN Zone '{}'".format(zone)}
    except Exception as e:
        # Provide a helpful error if the zone is not empty
        if 'is not empty' in str(e):
            logger.error(f"Cannot Delete Zone '{zone}' because it is not empty. Please remove all VNETs from it!!")
            raise HTTPException(status_code=400, detail="Cannot delete zone '{}' because it is not empty. Please remove all VNETs from it first.".format(zone))
        logger.error(f"Error deleting SDN Zone '{zone}': {save_error(e)}.")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.get("/sdn/vnets", tags=["SDN"])
def list_sdn_vnets(current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user.username}' requested to list all SDN Vnets.")
    """Gets a list of all SDN VNETs."""
    proxmox = get_proxmox_connection()
    try:
        logger.info(f"Retreving SDN Vnets.......")
        return proxmox.cluster.sdn.vnets.get()
    except Exception as e:
        logger.error(f"Errror retrieving all the Vnets: {save_error(e)}.")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sdn/vnets", tags=["SDN"])
def create_sdn_vnet(request: SdnVnetRequest, current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user.username}' requested to create a SDN Vnets.")
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
        logger.info(f"Successfully created VNET '{request.vnet}' in zone '{request.zone}'.")
        return {"message": "Successfully created VNET '{}' in zone '{}'".format(request.vnet, request.zone)}
    except Exception as e:
        logger.error(f"Error creating Vnet '{request.vnet}'.: {save_error(e)}.")
        raise HTTPException(status_code=500, detail=str(e))
        
@router.delete("/sdn/vnets/{vnet}", tags=["SDN"])
def delete_sdn_vnet(vnet: str, current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user.username}' requested to delete a SDN Vnets.")
    """Deletes an SDN VNET."""
    proxmox = get_proxmox_connection()
    try:
        # Proxmox API call to delete the vnet
        result = proxmox.cluster.sdn.vnets(vnet).delete()
        time.sleep(2) # Give a moment for tasks to register
        proxmox.cluster.sdn.put()
        logger.info(f"Successfully deleted SDN VNET '{vnet}'.")
        return {"message": "Successfully deleted SDN VNET '{}'".format(vnet)}
    except Exception as e:
        if 'in use' in str(e):
            logger.error(f"Cannot delete VNET '{vnet}' because it is in use by a VM.")
            raise HTTPException(status_code=400, detail="Cannot delete VNET '{}' because it is in use by a VM.".format(vnet))
        logger.error(f"Error deleting SDN Vnet: {save_error(e)}.")
        raise HTTPException(status_code=500, detail=str(e))
        
        
