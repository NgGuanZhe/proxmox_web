import re
import sys
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.proxmox import get_proxmox_connection

router = APIRouter()

class VmNetworkRequest(BaseModel):
    iface: str  # e.g., net0
    bridge: str # e.g., vmbr1

# Pydantic models to validate request bodies
class VmRenameRequest(BaseModel):
    new_name: str

class SnapshotRequest(BaseModel):
    name: str

class LabCreateRequest(BaseModel):
    lab_name: str
# Helper functions (_find_vm_node_by_id, _format_vm_details) are unchanged
def _find_vm_node_by_id(proxmox_conn, vmid):
    try:
        all_resources = proxmox_conn.cluster.resources.get(type='vm')
        for resource in all_resources:
            if resource.get('vmid') == vmid:
                return resource.get('node')
    except Exception:
        for node in proxmox_conn.nodes.get():
            for vm in proxmox_conn.nodes(node['node']).qemu.get():
                if vm['vmid'] == vmid:
                    return node['node']
    return None

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

@router.put("/vms/{vmid}/rename", tags=["Virtual Machines"])
def rename_vm(vmid: int, request: VmRenameRequest):
    proxmox = get_proxmox_connection()
    try:
        node_name = _find_vm_node_by_id(proxmox, vmid)
        if not node_name:
            raise HTTPException(status_code=404, detail="VM with ID {} not found.".format(vmid))
        proxmox.nodes(node_name).qemu(vmid).config.put(name=request.new_name)
        return {"message": "Successfully renamed VM {} to {}".format(vmid, request.new_name)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/vms/{vmid}", tags=["Virtual Machines"])
def delete_vm(vmid: int):
    proxmox = get_proxmox_connection()
    try:
        node_name = _find_vm_node_by_id(proxmox, vmid)
        if not node_name:
            raise HTTPException(status_code=404, detail="VM with ID {} not found.".format(vmid))
        vm = proxmox.nodes(node_name).qemu(vmid)
        if vm.status.current.get()['status'] == 'running':
            vm.status.stop.post()
            for i in range(20):
                time.sleep(3)
                if vm.status.current.get()['status'] == 'stopped': break
            else:
                raise Exception("Timed out waiting for VM to stop.")
        vm.delete()
        return {"message": "Successfully deleted VM {}".format(vmid)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vms/start_all", tags=["Virtual Machines"])
def start_all_vms():
    proxmox = get_proxmox_connection()
    started_vms = []
    try:
        for node in proxmox.nodes.get():
            node_name = node['node']
            for vm in proxmox.nodes(node_name).qemu.get():
                if vm.get('template') != 1 and vm.get('status') == 'stopped':
                    proxmox.nodes(node_name).qemu(vm['vmid']).status.start.post()
                    started_vms.append(vm.get('name'))
        return {"message": "Start command sent to all stopped VMs.", "started": started_vms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vms/stop_all", tags=["Virtual Machines"])
def stop_all_vms():
    proxmox = get_proxmox_connection()
    stopped_vms = []
    try:
        for node in proxmox.nodes.get():
            node_name = node['node']
            for vm in proxmox.nodes(node_name).qemu.get():
                if vm.get('template') != 1 and vm.get('status') == 'running':
                    proxmox.nodes(node_name).qemu(vm['vmid']).status.stop.post()
                    stopped_vms.append(vm.get('name'))
        return {"message": "Stop command sent to all running VMs.", "stopped": stopped_vms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@router.post("/vms/delete_clones", tags=["Virtual Machines"])
def delete_all_clones():
    proxmox = get_proxmox_connection()
    deleted_vms = []
    errors = []
    try:
        for node in proxmox.nodes.get():
            node_name = node['node']
            for vm_summary in proxmox.nodes(node_name).qemu.get():
                vmid = vm_summary.get('vmid')
                if not vmid: continue
                vm_config = proxmox.nodes(node_name).qemu(vmid).config.get()
                description = vm_config.get('description', '')
                if "Cloned from template:" in description:
                    try:
                        if vm_summary.get('status') == 'running':
                            proxmox.nodes(node_name).qemu(vmid).status.stop.post()
                            for i in range(20):
                                time.sleep(3)
                                if proxmox.nodes(node_name).qemu(vmid).status.current.get()['status'] == 'stopped': break
                            else:
                                raise Exception("Timed out waiting for VM to stop.")
                        proxmox.nodes(node_name).qemu(vmid).delete()
                        deleted_vms.append(vm_summary.get('name'))
                    except Exception as delete_error:
                        errors.append("Could not delete {}: {}".format(vm_summary.get('name'), delete_error))
        return {"message": "Cleanup process completed.", "deleted_vms": deleted_vms, "errors": errors}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred during cleanup: {}".format(e))

@router.get("/vms/{vmid}/snapshots", tags=["Snapshots"])
def list_snapshots(vmid: int):
    """Gets a list of all snapshots for a specific VM."""
    proxmox = get_proxmox_connection()
    try:
        node_name = _find_vm_node_by_id(proxmox, vmid)
        if not node_name:
            raise HTTPException(status_code=404, detail="VM with ID {} not found.".format(vmid))
        
        snapshots = proxmox.nodes(node_name).qemu(vmid).snapshot.get()
        return snapshots
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vms/{vmid}/snapshots", tags=["Snapshots"])
def create_snapshot(vmid: int, request: SnapshotRequest):
    """Creates a new snapshot for a VM."""
    proxmox = get_proxmox_connection()
    try:
        node_name = _find_vm_node_by_id(proxmox, vmid)
        if not node_name:
            raise HTTPException(status_code=404, detail="VM with ID {} not found.".format(vmid))
        
        # Proxmox API call to create a snapshot
        result = proxmox.nodes(node_name).qemu(vmid).snapshot.post(snapname=request.name)
        return {"message": "Successfully created snapshot '{}' for VM {}".format(request.name, vmid), "task_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/vms/{vmid}/snapshots/{snapname}/rollback", tags=["Snapshots"])
def rollback_snapshot(vmid: int, snapname: str):
    """Restores a VM to a previous snapshot."""
    proxmox = get_proxmox_connection()
    try:
        node_name = _find_vm_node_by_id(proxmox, vmid)
        if not node_name:
            raise HTTPException(status_code=404, detail="VM with ID {} not found.".format(vmid))
        
        # Proxmox API call to roll back to a snapshot
        result = proxmox.nodes(node_name).qemu(vmid).snapshot(snapname).rollback.post()
        return {"message": "Successfully initiated rollback to snapshot '{}' for VM {}".format(snapname, vmid), "task_id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/vms/{vmid}/reconfigure_network", tags=["Virtual Machines"])
def reconfigure_network(vmid: int, request: VmNetworkRequest):
    proxmox = get_proxmox_connection()
    try:
        node_name = _find_vm_node_by_id(proxmox, vmid)
        if not node_name:
            raise HTTPException(status_code=404, detail="VM with ID {} not found.".format(vmid))

        vm = proxmox.nodes(node_name).qemu(vmid)
        current_config = vm.config.get()
        net_config_str = current_config.get(request.iface)
        
        if not net_config_str:
            raise HTTPException(status_code=404, detail="Network device {} not found on VM {}.".format(request.iface, vmid))

        parts = net_config_str.split(',')
        model_and_mac = parts[0]
        new_config = "{},bridge={}".format(model_and_mac, request.bridge)
        update_data = {request.iface: new_config}

        vm.config.put(**update_data)
        
        return {"message": "Successfully moved {} on VM {} to bridge {}".format(request.iface, vmid, request.bridge)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# The full, correct create_lab function
@router.post("/labs/create", tags=["Labs"])
def create_lab(request: LabCreateRequest):
    proxmox = get_proxmox_connection()
    try:
        lab_name_clean = re.sub(r'[^a-zA-Z0-9]', '', request.lab_name).lower()
        if not lab_name_clean:
            raise HTTPException(status_code=400, detail="Invalid lab name.")

        nodes = proxmox.nodes.get()
        if not nodes:
            raise HTTPException(status_code=500, detail="No Proxmox nodes found.")
        
        # 1. Determine a valid, new bridge name
        existing_bridges = set()
        for node in nodes:
            for net in proxmox.nodes(node['node']).network.get():
                if net.get('type') == 'bridge':
                    existing_bridges.add(net.get('iface'))
        
        next_bridge_num = 0
        while True:
            bridge_name = "vmbr{}".format(next_bridge_num)
            if bridge_name not in existing_bridges:
                break
            next_bridge_num += 1

        # 2. Create the new bridge on ALL nodes
        for node in nodes:
            node_name = node['node']
            proxmox.nodes(node_name).network.post(type='bridge', iface=bridge_name, autostart=1, comments="Isolated network for lab: {}".format(request.lab_name))
            time.sleep(1)
            proxmox.nodes(node_name).network.put()

        # 3. Get all VMs to calculate next ID and find templates
        all_vms_and_templates = []
        for node in nodes:
            all_vms_and_templates.extend(proxmox.nodes(node['node']).qemu.get())
        
        existing_ids = {vm['vmid'] for vm in all_vms_and_templates}
        max_id = max([vmid for vmid in existing_ids if vmid >= 1000] or [999])
        next_vmid = max_id + 1

        created_vms = []
        # 4. Find and clone all templates, and reconfigure their network
        for node in nodes:
            node_name = node['node']
            for template_summary in proxmox.nodes(node_name).qemu.get():
                if template_summary.get('template') == 1:
                    template_id = template_summary['vmid']
                    
                    new_clone_name = "{}-{}-{}".format(lab_name_clean, template_summary.get('name', 'vm'), next_vmid)
                    clone_description = "Cloned from template: {}".format(template_summary.get('name', 'unknown'))
                    
                    # 5. Clone the VM
                    proxmox.nodes(node_name).qemu(template_id).clone.post(newid=next_vmid, name=new_clone_name, full=0, description=clone_description)
                    
                    time.sleep(2) # Give a moment for the clone to be created
                    new_vm = proxmox.nodes(node_name).qemu(next_vmid)
                    new_vm_config = new_vm.config.get()
                    
                    # 6. Reconfigure the network for net0
                    net0_config = new_vm_config.get('net0', '')
                    if net0_config:
                        model_and_mac = net0_config.split(',')[0]
                        new_net0_config = "{},bridge={}".format(model_and_mac, bridge_name)
                        new_vm.config.put(net0=new_net0_config)

                    created_vms.append({"name": new_clone_name, "id": next_vmid})
                    next_vmid += 1

        return {"message": "Lab '{}' created successfully on network '{}'.".format(request.lab_name, bridge_name), "created_vms": created_vms}
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred: {}".format(e))
