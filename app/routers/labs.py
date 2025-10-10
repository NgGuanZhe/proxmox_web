import re
import time
import logging
from app.logging_helper import save_error
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.proxmox import get_proxmox_connection
from .vms import _find_vm_node_by_id
from app.routers.auth import get_current_active_user
from filelock import FileLock, Timeout
from typing import List

logger = logging.getLogger("proxmox_api")
router = APIRouter()
creation_lock = FileLock("/tmp/lab_creation.lock")
deletion_lock = FileLock("/tmp/lab_deletion.lock")

class VlanLabRequest(BaseModel):
    zone: str
    tag: int

class LabMemberUpdateRequest(BaseModel):
    vm_ids: List[int]

def _clear_lab_description(existing_desc: str) -> str:
    """Removes any 'Lab: ...' line from a description."""
    return re.sub(r"Lab: .*? \| Instance: \d+\n?", "", existing_desc).strip()

@router.put("/labs/{lab_group_name}/members", tags=["Labs"])
def update_lab_members(lab_group_name: str, request: LabMemberUpdateRequest, current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user}' is requesting to edit Lab '{lab_group_name}'.")
    """
    Updates the list of VMs in a lab group.
    Adds specified VMs and removes any not in the list.
    """
    proxmox = get_proxmox_connection()
    try:
        # Extract lab name and instance number from the group name
        match = re.match(r"(.*?)_cloned(\d+)", lab_group_name)
        if not match:
            logger.error(f"Invalid lab group name format.")
            raise HTTPException(status_code=400, detail="Invalid lab group name format.")
        lab_name, instance_num = match.groups()
        instance_num = int(instance_num)

        # 1. Get all VMs to find the VNET
        vnet_name = None
        current_vms_in_group = []
        all_vms = []
        nodes = proxmox.nodes.get()
        for node in nodes:
            node_name = node['node']
            for vm_summary in proxmox.nodes(node_name).qemu.get():
                all_vms.append({**vm_summary, 'node': node_name})

        for vm_summary in all_vms:
            config = proxmox.nodes(vm_summary['node']).qemu(vm_summary['vmid']).config.get()
            desc = config.get('description', '')
            desc_match = re.search(r"Lab: (.*?) \| Instance: (\d+)", desc)
            if desc_match:
                lab_name_from_desc = desc_match.group(1).replace(' clone', '').replace(' added', '')
                instance_num_from_desc = desc_match.group(2)
                reconstructed_group_name = f"{lab_name_from_desc}_cloned{instance_num_from_desc}"
                
                if reconstructed_group_name == lab_group_name:
                    current_vms_in_group.append(vm_summary['vmid'])
                    if not vnet_name:
                        net0 = config.get('net0', '')
                        if 'bridge=' in net0:
                            vnet_name = net0.split('bridge=')[1].split(',')[0]
        
        if not vnet_name:
             logger.error(f"Could not determine the VNET for lab group {lab_group_name}.")
             raise HTTPException(status_code=404, detail=f"Could not determine the VNET for lab group {lab_group_name}.")

        # 2. Determine which VMs to add and remove
        current_vm_set = set(current_vms_in_group)
        requested_vm_set = set(request.vm_ids)
        
        vms_to_add = requested_vm_set - current_vm_set
        vms_to_remove = current_vm_set - requested_vm_set
        
        # 3. Add new VMs to the group
        for vmid in vms_to_add:
            node_name = _find_vm_node_by_id(proxmox, vmid)
            if node_name:
                vm = proxmox.nodes(node_name).qemu(vmid)
                current_config = vm.config.get()
                current_desc = current_config.get('description', '')
                
                # Set description to 'added'
                new_desc = f"{_clear_lab_description(current_desc)}\nLab: {lab_name} added | Instance: {instance_num}".strip()
                
                # Reconfigure network
                net0_config_str = current_config.get('net0', '')
                new_net_config = ""
                if net0_config_str:
                    model_and_mac = net0_config_str.split(',')[0]
                    new_net_config = f"{model_and_mac},bridge={vnet_name}"
                    vm.config.put(description=new_desc, net0=new_net_config)
                else:
                    vm.config.put(description=new_desc)

        # 4. Remove VMs from the group
        for vmid in vms_to_remove:
            node_name = _find_vm_node_by_id(proxmox, vmid)
            if node_name:
                vm = proxmox.nodes(node_name).qemu(vmid)
                current_desc = vm.config.get().get('description', '')
                new_desc = _clear_lab_description(current_desc)
                vm.config.put(description=new_desc)
        logger.info(f"Successfully updated members for lab {lab_group_name}.")
        return {"message": f"Successfully updated members for lab {lab_group_name}."}

    except Exception as e:
        logger.error(f"Error updating lab members for {lab_group_name}: {save_error(e)}.")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/labs/create_vlan_lab", tags=["Labs"])
def create_vlan_lab(request: VlanLabRequest, current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user.username}' requested to create vlan lab.")
    try:
        # This will wait up to 5 minutes (300 seconds) for other lab creations to finish
        with creation_lock.acquire(timeout=300):
            proxmox = get_proxmox_connection()
            
            # --- The rest of your lab creation logic goes here ---
            # It is now protected from race conditions
            all_vnets = proxmox.cluster.sdn.vnets.get()
            highest_num = 0
            for vnet in all_vnets:
                match = re.match(r"vnet(\d+)", vnet.get('vnet', ''))
                if match:
                    num = int(match.group(1))
                    if num > highest_num:
                        highest_num = num
            new_vnet_name = "vnet{}".format(highest_num + 1)
            
            proxmox.cluster.sdn.vnets.post(
                vnet=new_vnet_name,
                zone=request.zone,
                tag=request.tag
            )
            time.sleep(2)
            proxmox.cluster.sdn.put()

            all_vms = []
            nodes = proxmox.nodes.get()
            for node in nodes:
                all_vms.extend(proxmox.nodes(node['node']).qemu.get())
            existing_ids = {vm['vmid'] for vm in all_vms}
            vmid_prefix = (highest_num + 1) * 1000
            next_vmid = vmid_prefix
            created_vms = []
            clone_index = 1
            
            for node in nodes:
                node_name = node['node']
                for template_summary in proxmox.nodes(node_name).qemu.get():
                    if template_summary.get('template') == 1:
                        template_id = template_summary['vmid']
                        while next_vmid in existing_ids:
                            next_vmid += 1
                        new_clone_name = "{}-{}".format(template_summary.get('name', 'vm'), next_vmid)
                        clone_description = "Lab VNET: {}".format(new_vnet_name)
                        template_config = proxmox.nodes(node_name).qemu(template_id).config.get()
                        net0_config = template_config.get('net0', '')
                        new_net_config = ""
                        if net0_config:
                            model_and_mac = net0_config.split(',')[0]
                            new_net_config = "{},bridge={}".format(model_and_mac, new_vnet_name)

                        proxmox.nodes(node_name).qemu(template_id).clone.post(
                            newid=next_vmid, 
                            name=new_clone_name, 
                            full=0, 
                            description=clone_description,
                            net0=new_net_config
                        )
                        created_vms.append({"name": new_clone_name, "id": next_vmid})
                        clone_index += 1
            logger.info(f"Vlan Lab created successfully. Vnet: {new_vnet_name} Created VMs: {created_vms}")
            return {"message": "Vlan Lab created successfully.", "vnet": new_vnet_name, "created_vms": created_vms}

    except Timeout:
        logger.error(f"Another lab creation is already in progress. Please try again in a few moments.")
        raise HTTPException(status_code=503, detail="Another lab creation is already in progress. Please try again in a few moments.")
    except Exception as e:
        logger.error(f"Error creating Vlan Lab: {save_error(e)}.")
        raise HTTPException(status_code=500, detail="An error occurred: {}".format(e))


@router.delete("/labs/{lab_group_name}", tags=["Labs"])
def delete_lab(lab_group_name: str, current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user.username}' requested to delete vlan lab.")
    """
    Deletes all VMs in a lab group, and then deletes the VNET they are connected to.
    """
    try:
        # This will wait up to 5 minutes for other lab deletions to finish
        with deletion_lock.acquire(timeout=300):
            proxmox = get_proxmox_connection()
            deleted_vms = []
            vnet_to_delete = None
            
            nodes = proxmox.nodes.get()
            vms_to_delete = []

            # First, loop through all VMs on all nodes to identify which ones to delete
            for node in nodes:
                node_name = node['node']
                for vm_summary in proxmox.nodes(node_name).qemu.get():
                    vmid = vm_summary.get('vmid')
                    if not vmid: continue

                    config = proxmox.nodes(node_name).qemu(vmid).config.get()
                    desc = config.get('description', '')
                    match = re.search(r"Lab: (.*?) \| Instance: (\d+)", desc)

                    if match:
                        lab_name = match.group(1).replace(' clone', '').replace(' added', '')
                        instance_num = match.group(2)
                        current_group_name = "{}_cloned{}".format(lab_name, instance_num)

                        if current_group_name == lab_group_name:
                            vm_summary['node'] = node_name
                            vms_to_delete.append(vm_summary)
                            
                            if not vnet_to_delete:
                                net0 = config.get('net0', '')
                                if 'bridge=' in net0:
                                    vnet_to_delete = net0.split('bridge=')[1].split(',')[0]
            
            # Now, delete the VMs we found
            for vm_summary in vms_to_delete:
                vmid = vm_summary['vmid']
                node_name = vm_summary['node']
                vm = proxmox.nodes(node_name).qemu(vmid)

                if vm.status.current.get()['status'] == 'running':
                    vm.status.stop.post()
                    for _ in range(20):
                        time.sleep(3)
                        if vm.status.current.get()['status'] == 'stopped': break
                    else:
                        logger.error(f"Timed out waiting for VM {vmid} to stop.")
                        raise Exception("Timed out waiting for VM {} to stop.".format(vmid))
                
                vm.delete()
                deleted_vms.append(vm_summary.get('name'))
                time.sleep(2)
            
            # After all VMs are deleted, delete the VNET if we found one
            if vnet_to_delete:
                proxmox.cluster.sdn.vnets(vnet_to_delete).delete()
                time.sleep(2)
                proxmox.cluster.sdn.put()
            logger.info(f"Successfully deleted lab '{lab_group_name}' and VNET '{vnet_to_delete}'. Deleted VMs: {deleted_vms}")
            return {"message": "Successfully deleted lab '{}' and VNET '{}'.".format(lab_group_name, vnet_to_delete), "deleted_vms": deleted_vms}

    except Timeout:
        logger.error(f"Another lab deletion is already in progress. Please try again.")
        raise HTTPException(status_code=503, detail="Another lab deletion is already in progress. Please try again.")
    except Exception as e:
        logger.error(f"An error occurred during lab deletion: {save_error(e)}.")
        raise HTTPException(status_code=500, detail="An error occurred during lab deletion: {}".format(e))
        
@router.post("/labs/{lab_group_name}/start", tags=["Labs"])
def start_lab(lab_group_name: str, current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user.username}' requested to start vlan lab {lab_group_name}.")
    """
    Starts all VMs that belong to a specific lab group instance.
    """
    proxmox = get_proxmox_connection()
    started_vms = []
    try:
        nodes = proxmox.nodes.get()
        for node in nodes:
            node_name = node['node']
            for vm_summary in proxmox.nodes(node_name).qemu.get():
                vmid = vm_summary.get('vmid')
                if not vmid: continue

                config = proxmox.nodes(node_name).qemu(vmid).config.get()
                desc = config.get('description', '')
                match = re.search(r"Lab: (.*?) \| Instance: (\d+)", desc)

                if match:
                    lab_name = match.group(1).replace(' clone', '').replace(' added', '')
                    instance_num = match.group(2)
                    current_group_name = "{}_cloned{}".format(lab_name, instance_num)

                    # If this VM is part of the lab we want to start
                    if current_group_name == lab_group_name:
                        if vm_summary.get('status') == 'stopped':
                            proxmox.nodes(node_name).qemu(vmid).status.start.post()
                            started_vms.append(vm_summary.get('name'))
        logger.info(f"Start command sent to all VMs in lab '{lab_group_name}'. Started VMs: {started_vms}")
        return {"message": "Start command sent to all VMs in lab '{}'.".format(lab_group_name), "started_vms": started_vms}
    except Exception as e:
        logger.error(f"An error occurred while starting the lab: {save_error(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while starting the lab: {}".format(e))
        
@router.post("/labs/{lab_group_name}/stop", tags=["Labs"])
def stop_lab(lab_group_name: str, current_user: dict = Depends(get_current_active_user)):
    logger.info(f"User '{current_user.username}' requested to stop vlan lab {lab_group_name}.")
    """
    Stops all VMs that belong to a specific lab group instance.
    """
    proxmox = get_proxmox_connection()
    stopped_vms = []
    try:
        nodes = proxmox.nodes.get()
        for node in nodes:
            node_name = node['node']
            for vm_summary in proxmox.nodes(node_name).qemu.get():
                vmid = vm_summary.get('vmid')
                if not vmid: continue

                config = proxmox.nodes(node_name).qemu(vmid).config.get()
                desc = config.get('description', '')
                match = re.search(r"Lab: (.*?) \| Instance: (\d+)", desc)

                if match:
                    lab_name = match.group(1).replace(' clone', '').replace(' added', '')
                    instance_num = match.group(2)
                    current_group_name = "{}_cloned{}".format(lab_name, instance_num)

                    if current_group_name == lab_group_name:
                        if vm_summary.get('status') == 'running':
                            proxmox.nodes(node_name).qemu(vmid).status.stop.post()
                            stopped_vms.append(vm_summary.get('name'))
        logger.info(f"Stop command sent to all VMs in lab '{lab_group_name}'. Started VMs: {stopped_vms}")
        return {"message": "Stop command sent to all VMs in lab '{}'.".format(lab_group_name), "stopped_vms": stopped_vms}
    except Exception as e:
        logger.error(f"An error occurred while stopping the lab: {save_error(e)}.")
        raise HTTPException(status_code=500, detail="An error occurred while stopping the lab: {}".format(e))


