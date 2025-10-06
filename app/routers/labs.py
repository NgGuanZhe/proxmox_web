import re
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.proxmox import get_proxmox_connection
from .vms import _find_vm_node_by_id

router = APIRouter()

class VlanLabRequest(BaseModel):
    zone: str
    tag: int

@router.post("/labs/create_vlan_lab", tags=["Labs"])
def create_vlan_lab(request: VlanLabRequest):
    proxmox = get_proxmox_connection()
    try:
        # ... (VNET and VMID naming logic is unchanged)
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

        all_vms = []
        nodes = proxmox.nodes.get()
        for node in nodes:
            all_vms.extend(proxmox.nodes(node['node']).qemu.get())
        existing_ids = {vm['vmid'] for vm in all_vms}
        vmid_prefix = (highest_num + 1) * 1000
        next_vmid = vmid_prefix

        created_vms = []
        clone_index = 1
        # Find templates and clone with the correct network
        for node in nodes:
            node_name = node['node']
            for template_summary in proxmox.nodes(node_name).qemu.get():
                if template_summary.get('template') == 1:
                    template_id = template_summary['vmid']
                    
                    while next_vmid in existing_ids:
                        next_vmid += 1
                    
                    new_clone_name = "{}-{}".format(template_summary.get('name', 'vm'), next_vmid)
                    clone_description = "Lab VNET: {}".format(new_vnet_name)

                    # --- THIS IS THE CORRECTED LOGIC ---
                    # Get the template's network config to preserve its MAC and model
                    template_config = proxmox.nodes(node_name).qemu(template_id).config.get()
                    net0_config = template_config.get('net0', '')
                    new_net_config = ""
                    if net0_config:
                        model_and_mac = net0_config.split(',')[0]
                        new_net_config = "{},bridge={}".format(model_and_mac, new_vnet_name)

                    # Clone the VM and set the network config at the same time
                    proxmox.nodes(node_name).qemu(template_id).clone.post(
                        newid=next_vmid, 
                        name=new_clone_name, 
                        full=0, 
                        description=clone_description,
                        net0=new_net_config # Set the network during the clone
                    )
                    # --- END OF CORRECTED LOGIC ---

                    created_vms.append({"name": new_clone_name, "id": next_vmid})
                    clone_index += 1
        
        return {"message": "Lab created successfully.", "vnet": new_vnet_name, "created_vms": created_vms}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred: {}".format(e))

@router.delete("/labs/{vnet_name}", tags=["Labs"])
def delete_lab(vnet_name: str):
    """
    Deletes all VMs connected to a VNET, and then deletes the VNET itself.
    """
    proxmox = get_proxmox_connection()
    deleted_vms = []
    try:
        nodes = proxmox.nodes.get()
        # Loop through each node to find and delete VMs
        for node in nodes:
            node_name = node['node']
            for vm_summary in proxmox.nodes(node_name).qemu.get():
                vmid = vm_summary.get('vmid')
                if not vmid: continue

                # Now we have the correct node_name
                vm_config = proxmox.nodes(node_name).qemu(vmid).config.get()
                net0_config = vm_config.get('net0', '')

                if "bridge={}".format(vnet_name) in net0_config:
                    # This VM is in our lab, so delete it
                    vm = proxmox.nodes(node_name).qemu(vmid)
                    if vm.status.current.get()['status'] == 'running':
                        vm.status.stop.post()
                        # Wait for it to stop
                        for _ in range(20):
                            time.sleep(3)
                            if vm.status.current.get()['status'] == 'stopped': break
                        else:
                            raise Exception("Timed out waiting for VM {} to stop.".format(vmid))
                    
                    vm.delete()
                    deleted_vms.append(vm_summary.get('name'))
                    time.sleep(2)

        # After all VMs are deleted, delete the VNET itself
        proxmox.cluster.sdn.vnets(vnet_name).delete()

        return {"message": "Successfully deleted lab and VNET '{}'.".format(vnet_name), "deleted_vms": deleted_vms}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during lab deletion: {}".format(e))
