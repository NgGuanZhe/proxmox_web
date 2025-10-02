import re
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.proxmox import get_proxmox_connection

router = APIRouter()

class VlanLabRequest(BaseModel):
    zone: str
    tag: int

@router.post("/labs/create_vlan_lab", tags=["Labs"])
def create_vlan_lab(request: VlanLabRequest):
    """
    Creates a new VNET in a VLAN zone, then clones all templates
    and connects them to the new VNET with a unique ID scheme.
    """
    proxmox = get_proxmox_connection()
    try:
        # --- 1. Determine New VNET and VMID names ---
        all_vnets = proxmox.cluster.sdn.vnets.get()
        vnet_count = len(all_vnets)
        new_vnet_name = "vnet{}".format(request.tag)
        
        vmid_prefix = (vnet_count + 1) * 1000
        
        all_vms = []
        for node in proxmox.nodes.get():
            all_vms.extend(proxmox.nodes(node['node']).qemu.get())
        existing_ids = {vm['vmid'] for vm in all_vms}

        # --- 2. Create the new SDN VNET ---
        proxmox.cluster.sdn.vnets.post(
            vnet=new_vnet_name,
            zone=request.zone,
            tag=request.tag
        )

        created_vms = []
        clone_index = 1
        # --- 3. Find templates, clone, and reconfigure network ---
        for node in proxmox.nodes.get():
            node_name = node['node']
            for template_summary in proxmox.nodes(node_name).qemu.get():
                if template_summary.get('template') == 1:
                    template_id = template_summary['vmid']
                    
                    # Calculate new VMID
                    next_vmid = vmid_prefix + clone_index
                    while next_vmid in existing_ids:
                        next_vmid += 1
                    
                    new_clone_name = "{}-{}".format(template_summary.get('name', 'vm'), next_vmid)
                    clone_description = "Lab VNET: {}".format(new_vnet_name)

                    # 4. Clone the VM
                    proxmox.nodes(node_name).qemu(template_id).clone.post(
                        newid=next_vmid, 
                        name=new_clone_name, 
                        full=0, 
                        description=clone_description
                    )
                    
                    time.sleep(2) # Give a moment for the clone to be created
                    new_vm = proxmox.nodes(node_name).qemu(next_vmid)
                    
                    # 5. Reconfigure the network to use the new VNET
                    net0_config_str = new_vm.config.get().get('net0', '')
                    if net0_config_str:
                        model_and_mac = net0_config_str.split(',')[0]
                        # The bridge for an SDN VNET is the VNET name itself
                        new_net0_config = "{},bridge={}".format(model_and_mac, new_vnet_name)
                        new_vm.config.put(net0=new_net0_config)

                    created_vms.append({"name": new_clone_name, "id": next_vmid})
                    clone_index += 1
                    
                    # 6. Convert the new clone to a template
                    time.sleep(1) # Give a moment for config to apply
                    new_vm.template.post()

                    created_vms.append({"name": new_clone_name, "id": next_vmid})
                    clone_index += 1
        
        return {"message": "Lab created successfully.", "vnet": new_vnet_name, "created_vms": created_vms}

    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred: {}".format(e))
