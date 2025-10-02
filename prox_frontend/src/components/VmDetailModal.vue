<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  vm: Object
})
const emit = defineEmits(['close'])

// State for snapshots
const snapshots = ref([])
const newSnapshotName = ref('')
const isLoadingSnapshots = ref(false)

// State for network management
const availableNetworks = ref([])
const isEditingNic = ref(null) // Holds the device name, e.g., 'net0'
const selectedBridge = ref('')


// --- Lifecycle Hook ---
onMounted(async () => {
  // When the modal opens, fetch snapshots and available networks
  if (props.vm && (!props.vm.hardware_details || props.vm.hardware_details.template !== 1)) {
    await fetchSnapshots()
    await fetchNetworks()
  }
})

// --- Snapshot Functions ---
async function fetchSnapshots() {
  if (!props.vm) return
  isLoadingSnapshots.value = true
  try {
    const response = await fetch(`/api/vms/${props.vm.proxmox_id}/snapshots`)
    if (!response.ok) throw new Error('Failed to fetch snapshots.')
    snapshots.value = await response.json()
  } catch (e) {
    alert(e.message)
  } finally {
    isLoadingSnapshots.value = false
  }
}

async function createSnapshot() {
  if (!newSnapshotName.value || newSnapshotName.value.trim() === '') {
    alert('Please enter a snapshot name.')
    return
  }
  try {
    const response = await fetch(`/api/vms/${props.vm.proxmox_id}/snapshots`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newSnapshotName.value.trim() })
    })
    const result = await response.json()
    if (!response.ok) throw new Error(result.detail || 'Failed to create snapshot.')
    alert(`Successfully created snapshot: ${newSnapshotName.value}`)
    newSnapshotName.value = ''
    await fetchSnapshots()
  } catch (e) {
    alert(e.message)
  }
}

async function rollbackSnapshot(snapname) {
  if (!confirm(`Are you sure you want to roll back this VM to the snapshot "${snapname}"? This cannot be undone.`)) {
    return
  }
  try {
    const response = await fetch(`/api/vms/${props.vm.proxmox_id}/snapshots/${snapname}/rollback`, { method: 'POST' })
    const result = await response.json()
    if (!response.ok) throw new Error(result.detail || 'Failed to roll back snapshot.')
    alert(`Successfully rolled back to snapshot: ${snapname}. The main dashboard will refresh.`)
    emit('close')
  } catch (e) {
    alert(e.message)
  }
}

// --- Network Functions ---
async function fetchNetworks() {
  try {
    const response = await fetch('/api/networks')
    if (!response.ok) throw new Error('Failed to fetch networks.')
    const networkData = await response.json()
    const bridges = []
    for (const node in networkData) {
      for (const iface of networkData[node]) {
        if (iface.type === 'bridge' && !bridges.includes(iface.iface)) {
          bridges.push(iface.iface)
        }
      }
    }
    availableNetworks.value = bridges
  } catch (e) {
    alert(e.message)
  }
}

function startEditing(nic) {
  isEditingNic.value = nic.device
  selectedBridge.value = nic.bridge
}

async function saveNetworkChange() {
  if (!isEditingNic.value || !selectedBridge.value) return;
  try {
    const response = await fetch(`/api/vms/${props.vm.proxmox_id}/reconfigure_network`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ iface: isEditingNic.value, bridge: selectedBridge.value })
    })
    const result = await response.json()
    if (!response.ok) throw new Error(result.detail || 'Failed to update network.')
    alert('Network updated successfully! The dashboard will refresh.')
    emit('close')
  } catch (e) {
    alert(e.message)
  } finally {
    isEditingNic.value = null
  }
}

</script>

<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>{{ vm.name }}</h2>
        <button class="close-button" @click="$emit('close')">&times;</button>
      </div>
      <div class="modal-body">
        <h4>Hardware Details:</h4>
        <ul class="details-list">
          <li><strong>ID:</strong> {{ vm.proxmox_id }}</li>
          <li><strong>Status:</strong> {{ vm.status }}</li>
          <li><strong>Node:</strong> {{ vm.node }}</li>
          <li v-if="vm.hardware_details"><strong>CPU:</strong> {{ vm.hardware_details.cpu.sockets }} Socket(s), {{ vm.hardware_details.cpu.cores }} Core(s)</li>
          <li v-if="vm.hardware_details"><strong>Memory:</strong> {{ vm.hardware_details.memory_mb }} MB</li>
        </ul>
        <hr>

        <div class="feature-section" v-if="!vm.hardware_details.template">
          <h4>Network Interfaces</h4>
          <ul class="item-list">
            <li v-for="nic in vm.hardware_details.network_interfaces" :key="nic.device">
              <div>
                <strong>{{ nic.device.toUpperCase() }}:</strong> 
                <span> {{ nic.mac_address }} on bridge <strong>'{{ nic.bridge }}'</strong></span>
              </div>
              <div v-if="isEditingNic === nic.device" class="edit-form">
                <select v-model="selectedBridge">
                  <option v-for="net in availableNetworks" :key="net" :value="net">{{ net }}</option>
                </select>
                <button @click="saveNetworkChange">Save</button>
                <button @click="isEditingNic = null" class="cancel-button">Cancel</button>
              </div>
              <button v-else class="change-button" @click="startEditing(nic)">Change</button>
            </li>
          </ul>
        </div>
        <hr v-if="!vm.hardware_details.template">
        
        <div class="feature-section" v-if="!vm.hardware_details.template">
          <h4>Snapshot Manager</h4>
          <div class="snapshot-actions">
            <input type="text" v-model="newSnapshotName" placeholder="New snapshot name...">
            <button @click="createSnapshot">Create</button>
          </div>
          <div class="snapshot-list">
            <p v-if="isLoadingSnapshots">Loading snapshots...</p>
            <ul v-else-if="snapshots.length > 0" class="item-list">
              <li v-for="snap in snapshots" :key="snap.name">
                <span>{{ snap.name }} <small>({{ snap.description }})</small></span>
                <button class="rollback-button" @click="rollbackSnapshot(snap.name)">Rollback</button>
              </li>
            </ul>
            <p v-else>No snapshots exist.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background-color: var(--bg-light); color: var(--text-color); padding: 2rem; border-radius: 8px; border: 1px solid var(--border-color); width: 90%; max-width: 700px; max-height: 90vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem; }
.modal-header h2 { margin: 0; color: #fff; }
.close-button { background: none; border: none; color: var(--text-color); font-size: 2.5rem; cursor: pointer; line-height: 1; }
hr { border-color: var(--border-color); margin: 1.5rem 0; }

.details-list, .item-list { list-style: none; padding: 0; margin-top: 1rem; }
.details-list > li { margin-bottom: 0.5rem; }

.feature-section h4 { margin-top: 0; color: var(--text-muted); }
.item-list li { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid var(--border-color); }
.item-list li:last-child { border-bottom: none; }
.item-list small { color: var(--text-muted); }

.snapshot-actions { display: flex; gap: 1rem; margin-bottom: 1rem; }
.snapshot-actions input { flex-grow: 1; background-color: var(--bg-dark); color: var(--text-color); border: 1px solid var(--border-color); padding: 10px; border-radius: 5px; }

button { background-color: var(--accent-color); color: var(--bg-dark); font-weight: 700; border: none; padding: 10px 20px; font-size: 14px; border-radius: 5px; cursor: pointer; }
.change-button, .rollback-button { font-size: 12px; padding: 5px 10px; }
.rollback-button { background-color: #ffc107; color: #1a1a1a; }
.cancel-button { background-color: #6c757d; color: white; }

.edit-form { display: flex; gap: 0.5rem; align-items: center; }
.edit-form select { background-color: var(--bg-dark); color: var(--text-color); border: 1px solid var(--border-color); padding: 5px; border-radius: 5px; }
</style>
