<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/apiService'; // <-- Import the new service

const vms = ref([])
const snapshots = ref({})
const newSnapshotNames = ref({})
const isLoading = ref(true)
const error = ref(null)

onMounted(async () => {
  await fetchVMs()
})

async function fetchVMs() {
  isLoading.value = true
  error.value = null
  try {
    const allVms = await api.get('/vms');
    vms.value = allVms.filter(vm => !vm.hardware_details || vm.hardware_details.template !== 1)
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

async function fetchSnapshots(vmid) {
  try {
    snapshots.value[vmid] = await api.get(`/vms/${vmid}/snapshots`);
  } catch (e) {
    error.value = e.message
  }
}

async function createSnapshot(vmid) {
  const snapName = newSnapshotNames.value[vmid]
  if (!snapName || snapName.trim() === '') {
    alert('Please enter a snapshot name.')
    return
  }
  
  try {
    await api.post(`/vms/${vmid}/snapshots`, { name: snapName.trim() });
    alert(`Successfully created snapshot: ${snapName}`);
    newSnapshotNames.value[vmid] = '';
    await fetchSnapshots(vmid);
  } catch (e) {
    error.value = e.message
  }
}

async function rollbackSnapshot(vmid, snapname) {
  if (!confirm(`Are you sure you want to roll back this VM to the snapshot "${snapname}"?`)) {
    return
  }

  try {
    await api.post(`/vms/${vmid}/snapshots/${snapname}/rollback`, {});
    alert(`Successfully rolled back to snapshot: ${snapname}`);
    await fetchVMs();
  } catch (e) {
    error.value = e.message
  }
}
</script>

<template>
  <header>
    <h1>Snapshot Manager</h1>
    <p>Create and restore snapshots for your virtual machines.</p>
  </header>

  <main>
    <div v-if="isLoading">Loading VMs...</div>
    <div v-if="error" class="error-box">
      <p><strong>Error:</strong> {{ error }}</p>
    </div>

    <div class="vm-list">
      <div v-for="vm in vms" :key="vm.proxmox_id" class="vm-snapshot-card">
        <h3>{{ vm.name }} (ID: {{ vm.proxmox_id }})</h3>
        
        <div class="snapshot-actions">
          <input type="text" v-model="newSnapshotNames[vm.proxmox_id]" placeholder="New snapshot name...">
          <button @click="createSnapshot(vm.proxmox_id)">Create Snapshot</button>
        </div>

        <div class="snapshot-list">
          <button class="list-button" @click="fetchSnapshots(vm.proxmox_id)">Load Snapshots</button>
          <ul v-if="snapshots[vm.proxmox_id]">
            <li v-if="snapshots[vm.proxmox_id].length === 0">No snapshots exist.</li>
            <li v-for="snap in snapshots[vm.proxmox_id]" :key="snap.name">
              <span>{{ snap.name }} - {{ snap.description }}</span>
              <button class="rollback-button" @click="rollbackSnapshot(vm.proxmox_id, snap.name)">Rollback</button>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
header { text-align: center; margin-bottom: 2rem; }
.error-box { padding: 1rem; background-color: #ffebee; color: #c62828; border-radius: 5px; text-align: center; }
.vm-snapshot-card {
  background-color: var(--bg-light);
  border: 1px solid var(--border-color);
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}
.vm-snapshot-card h3 { margin-top: 0; color: var(--accent-color); }
.snapshot-actions { display: flex; gap: 1rem; margin-bottom: 1rem; }
.snapshot-actions input {
  flex-grow: 1;
  background-color: var(--bg-dark);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  padding: 10px;
  border-radius: 5px;
}
button {
  background-color: var(--accent-color);
  color: var(--bg-dark);
  font-weight: 700;
  border: none;
  padding: 10px 20px;
  font-size: 14px;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.2s;
}
.list-button { background-color: #6c757d; color: white; }
.rollback-button { background-color: #ffc107; color: #1a1a1a; font-size: 12px; padding: 5px 10px; }
.snapshot-list ul { list-style: none; padding: 0; margin-top: 1rem; }
.snapshot-list li { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border-bottom: 1px solid var(--border-color); }
.snapshot-list li:last-child { border-bottom: none; }
</style>
