import re
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from app.core.proxmox import get_proxmox_connection
from .vms import _find_vm_node_by_id

router = APIRouter()

class TemplateTagRequest(BaseModel):
    lab_groups: List[str]

class LabInstantiateRequest(BaseModel):
    lab_group: str
    vlan_zone: str
    vlan_tag: int

def _parse_tags_from_description(description: str) -> dict:
    tags = {}
    group_match = re.search(r"LabGroups:\[(.*?)\]", description)
    if group_match and group_match.group(1):
        tags['lab_groups'] = group_match.group(1).split(',')
    
    instance_match = re.search(r"Lab: (.*?) \| Instance: (\d+)", description)
    if instance_match:
        tags['lab_name'] = instance_match.group(1)
        tags['lab_instance'] = int(instance_match.group(2))
    return tags

def _build_description_with_tags(existing_desc: str, lab_groups: List[str]) -> str:
    new_desc = re.sub(r"LabGroups:\[.*?\]\n?", "", existing_desc).strip()
    if lab_groups:
        tag_str = "LabGroups:[{}]".format(','.join(lab_groups))
        new_desc = "{}\n{}".format(new_desc, tag_str).strip()
    return new_desc

@router.put("/templates/{vmid}/tag", tags=["Lab Builder"])
def tag_template(vmid: int, request: TemplateTagRequest):
    proxmox = get_proxmox_connection()
    try:
        node_name = _find_vm_node_by_id(proxmox, vmid)
        if not node_name:
            raise HTTPException(status_code=404, detail="Template not found.")
        current_config = proxmox.nodes(node_name).qemu(vmid).config.get()
        existing_desc = current_config.get('description', '')
        new_description = _build_description_with_tags(existing_desc, request.lab_groups)
        proxmox.nodes(node_name).qemu(vmid).config.put(description=new_description)
        return {"message": "Template tags updated successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/labs/instantiate", tags=["Lab Builder"])
def instantiate_lab(request: LabInstantiateRequest):
    proxmox = get_proxmox_connection()
    try:
        nodes = proxmox.nodes.get()
        if not nodes:
            raise HTTPException(status_code=500, detail="No Proxmox nodes found.")

        # 1. Create the new VNET
        all_vnets = proxmox.cluster.sdn.vnets.get()
        highest_num = 0
        for vnet in all_vnets:
            match = re.match(r"vnet(\d+)", vnet.get('vnet', ''))
            if match:
                num = int(match.group(1))
                if num > highest_num:
                    highest_num = num
        new_vnet_name = "vnet{}".format(highest_num + 1)
        
        try:
            proxmox.cluster.sdn.vnets.post(vnet=new_vnet_name, zone=request.vlan_zone, tag=request.vlan_tag)
        except Exception as vnet_error:
            raise Exception("Failed to create SDN VNET. Proxmox Error: {}".format(vnet_error))
        
        # 2. Find templates and calculate next VMID
        all_vms = []
        for node in nodes:
            all_vms.extend(proxmox.nodes(node['node']).qemu.get())
        existing_ids = {vm['vmid'] for vm in all_vms}
        
        highest_instance = 0
        for vm_summary in all_vms:
            node_name_check = _find_vm_node_by_id(proxmox, vm_summary.get('vmid'))
            if not node_name_check: continue
            config = proxmox.nodes(node_name_check).qemu(vm_summary['vmid']).config.get()
            tags = _parse_tags_from_description(config.get('description', ''))
            if tags.get('lab_name') == request.lab_group:
                if tags.get('lab_instance') > highest_instance:
                    highest_instance = tags.get('lab_instance')
        next_instance_num = highest_instance + 1
        
        vmid_prefix = next_instance_num * 1000
        next_vmid = vmid_prefix + 1

        # 3. Clone and reconfigure
        created_vms = []
        for node in nodes:
            node_name = node['node']
            for template_summary in proxmox.nodes(node_name).qemu.get():
                if template_summary.get('template') == 1:
                    config = proxmox.nodes(node_name).qemu(template_summary['vmid']).config.get()
                    tags = _parse_tags_from_description(config.get('description', ''))
                    
                    if request.lab_group in tags.get('lab_groups', []):
                        while next_vmid in existing_ids:
                            next_vmid += 1
                        
                        template_id = template_summary['vmid']
                        new_clone_name = "{}-{}-{}".format(request.lab_group.lower(), template_summary.get('name', 'vm'), next_vmid)
                        clone_description = "Lab: {} | Instance: {}".format(request.lab_group, next_instance_num)
                        
                        # Step A: Clone the VM
                        proxmox.nodes(node_name).qemu(template_id).clone.post(newid=next_vmid, name=new_clone_name, full=0, description=clone_description)
                        
                        time.sleep(2)
                        new_vm = proxmox.nodes(node_name).qemu(next_vmid)
                        
                        # Step B: Reconfigure the network
                        template_config = proxmox.nodes(node_name).qemu(template_id).config.get()
                        net0_config = template_config.get('net0', '')
                        if net0_config:
                            model_and_mac = net0_config.split(',')[0]
                            new_net_config_str = "{},bridge={}".format(model_and_mac, new_vnet_name)
                            new_vm.config.put(net0=new_net_config_str)

                        created_vms.append({"name": new_clone_name, "id": next_vmid})
                        next_vmid += 1

        if not created_vms:
            proxmox.cluster.sdn.vnets(new_vnet_name).delete()
            raise HTTPException(status_code=404, detail="No templates found in lab group '{}'.".format(request.lab_group))

        return {"message": "Lab '{}' instance {} instantiated successfully on VNET '{}'.".format(request.lab_group, next_instance_num, new_vnet_name), "created_vms": created_vms}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred: {}".format(e))
