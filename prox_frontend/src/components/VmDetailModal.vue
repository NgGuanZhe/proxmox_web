<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  vm: Object
})

const snapshots = ref([])
const newSnapshotName = ref('')
const isLoadingSnapshots = ref(false)

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
  if (!confirm(`Are you sure you want to roll back this VM to the snapshot "${snapname}"? All current changes will be lost.`)) {
    return
  }
  try {
    const response = await fetch(`/api/vms/${props.vm.proxmox_id}/snapshots/${snapname}/rollback`, { method: 'POST' })
    const result = await response.json()
    if (!response.ok) throw new Error(result.detail || 'Failed to roll back snapshot.')
    alert(`Successfully rolled back to snapshot: ${snapname}. The main dashboard will refresh.`)
    // We emit 'close' to close the modal, the parent will refresh the main list
    emit('close')
  } catch (e) {
    alert(e.message)
  }
}

// Automatically load snapshots when the modal opens
onMounted(() => {
  fetchSnapshots()
})

// Define the 'close' event that the component can emit
const emit = defineEmits(['close'])
</script>

<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>{{ vm.name }}</h2>
        <button class="close-button" @click="$emit('close')">&times;</button>
      </div>
      <div class="modal-body">
        <p><strong>ID:</strong> {{ vm.proxmox_id }}</p>
        <p><strong>Status:</strong> {{ vm.status }}</p>
        <p><strong>Node:</strong> {{ vm.node }}</p>
        <hr>
        
        <div class="snapshot-manager">
          <h4>Snapshot Manager</h4>
          
          <div class="snapshot-actions">
            <input type="text" v-model="newSnapshotName" placeholder="New snapshot name...">
            <button @click="createSnapshot">Create</button>
          </div>
          
          <div class="snapshot-list">
            <p v-if="isLoadingSnapshots">Loading snapshots...</p>
            <ul v-else-if="snapshots.length > 0">
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
/* (Styles are mostly the same, with additions for the snapshot section) */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background-color: var(--bg-light); color: var(--text-color); padding: 2rem; border-radius: 8px; border: 1px solid var(--border-color); width: 90%; max-width: 700px; max-height: 90vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem; }
.modal-header h2 { margin: 0; color: #fff; }
.close-button { background: none; border: none; color: var(--text-color); font-size: 2.5rem; cursor: pointer; line-height: 1; }
hr { border-color: var(--border-color); margin: 1.5rem 0; }
.snapshot-manager h4 { margin-top: 0; }
.snapshot-actions { display: flex; gap: 1rem; margin-bottom: 1rem; }
.snapshot-actions input { flex-grow: 1; background-color: var(--bg-dark); color: var(--text-color); border: 1px solid var(--border-color); padding: 10px; border-radius: 5px; }
.snapshot-list ul { list-style: none; padding: 0; margin-top: 1rem; }
.snapshot-list li { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 0; border-bottom: 1px solid var(--border-color); }
.snapshot-list li:last-child { border-bottom: none; }
.snapshot-list small { color: var(--text-muted); }
button { background-color: var(--accent-color); color: var(--bg-dark); font-weight: 700; border: none; padding: 10px 20px; font-size: 14px; border-radius: 5px; cursor: pointer; }
.rollback-button { background-color: #ffc107; color: #1a1a1a; }
</style>
