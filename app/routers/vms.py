import re
import sys
import time
from fastapi import APIRouter, HTTPException
from app.core.proxmox import get_proxmox_connection

router = APIRouter()

def _format_vm_details(vm_config):
    details = { "description": vm_config.get("description", ""), "template": vm_config.get("template", 0), "cpu": { "cores": vm_config.get("cores"), "sockets": vm_config.get("sockets"), "type": vm_config.get("cpu") }, "memory_mb": vm_config.get("memory"), "boot_order": vm_config.get("boot"), "disks": [], "network_interfaces": [] }
    for key, value in vm_config.items():
        if key.startswith(('scsi', 'sata', 'ide', 'virtio')):
            disk_match = re.match(r"(.+?):(.+?),size=(\d+G?)", str(value));
            if disk_match: details["disks"].append({ "device": key, "storage": disk_match.group(1), "file": disk_match.group(2), "size_gb": int(disk_match.group(3).replace('G', '')) })
        if key.startswith('net'):
            parts = str(value).split(','); nic_details = { "device": key };
            for part in parts:
                if '=' in part:
                    k, v = part.split('=', 1)
                    if k in ['virtio', 'e1000', 'rtl8139', 'vmxnet3']: nic_details['model'] = k; nic_details['mac_address'] = v
                    else: nic_details[k] = v
            details["network_interfaces"].append(nic_details)
    return details

@router.get("/vms", tags=["Virtual Machines"])
def list_vms():
    proxmox = get_proxmox_connection(); all_vms_list = []
    try:
        for node in proxmox.nodes.get():
            node_name = node['node']
            for vm_summary in proxmox.nodes(node_name).qemu.get():
                vmid = vm_summary.get('vmid');
                if not vmid: continue
                vm_config = proxmox.nodes(node_name).qemu(vmid).config.get(); formatted_details = _format_vm_details(vm_config);
                full_details = { 'proxmox_id': vmid, 'name': vm_summary.get('name'), 'status': vm_summary.get('status'), 'node': node_name, 'hardware_details': formatted_details }; all_vms_list.append(full_details)
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
    return all_vms_list

@router.post("/clone_templates", tags=["Virtual Machines"])
def clone_all_templates():
    proxmox = get_proxmox_connection()
    try:
        all_vms_and_templates = [];
        for node in proxmox.nodes.get(): all_vms_and_templates.extend(proxmox.nodes(node['node']).qemu.get())
        existing_ids = {vm['vmid'] for vm in all_vms_and_templates}
        max_id = max([id for id in existing_ids if id >= 1000] or [999]); next_vmid = max_id + 1
        cloned_vms = []
        for node in proxmox.nodes.get():
            node_name = node['node']
            for template_summary in proxmox.nodes(node_name).qemu.get():
                if template_summary.get('template') == 1:
                    template_id = template_summary['vmid']
                    new_clone_name = "{}-clone-{}".format(template_summary.get('name', 'template'), next_vmid)
                    clone_description = "Cloned from template: {}".format(template_summary.get('name', 'unknown'))
                    proxmox.nodes(node_name).qemu(template_id).clone.post(newid=next_vmid, name=new_clone_name, full=0, description=clone_description)
                    cloned_vms.append({"template": template_summary.get('name'), "new_id": next_vmid, "new_name": new_clone_name})
                    next_vmid += 1
        if not cloned_vms: return {"message": "No templates found to clone."}
        return {"message": "Cloning process completed successfully.", "cloned_vms": cloned_vms}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during cloning: {}".format(e))

# --- THIS IS THE NEW FUNCTION ---
@router.post("/vms/delete_clones", tags=["Virtual Machines"])
def delete_all_clones():
    """
    Finds and deletes all VMs that have the 'Cloned from' tag in their description.
    It will attempt to stop running VMs before deleting.
    """
    proxmox = get_proxmox_connection()
    deleted_vms = []
    errors = []
    try:
        for node in proxmox.nodes.get():
            node_name = node['node']
            for vm_summary in proxmox.nodes(node_name).qemu.get():
                vmid = vm_summary.get('vmid')
                if not vmid: continue
                
                # Check the description for the tag
                vm_config = proxmox.nodes(node_name).qemu(vmid).config.get()
                description = vm_config.get('description', '')
                if "Cloned from template:" in description:
                    # This is a clone, let's delete it
                    try:
                        # If VM is running, try to stop it first
                        if vm_summary.get('status') == 'running':
                            proxmox.nodes(node_name).qemu(vmid).status.stop.post()
                            # Wait for it to stop (up to 30 seconds)
                            for i in range(10):
                                time.sleep(3)
                                current_status = proxmox.nodes(node_name).qemu(vmid).status.current.get()
                                if current_status.get('status') == 'stopped':
                                    break
                        
                        # Delete the VM
                        proxmox.nodes(node_name).qemu(vmid).delete()
                        deleted_vms.append(vm_summary.get('name'))
                    except Exception as delete_error:
                        errors.append("Could not delete {}: {}".format(vm_summary.get('name'), delete_error))

        return {"message": "Cleanup process completed.", "deleted_vms": deleted_vms, "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during cleanup: {}".format(e))
