<script setup>
import { ref, onMounted, computed } from 'vue';
import VmCard from '../components/VmCard.vue';
import VmDetailModal from '../components/VmDetailModal.vue';

const vms = ref([]);
const isLoading = ref(true);
const error = ref(null);
const selectedVm = ref(null);
const actionStatus = ref(null);

const labPlaygroundGroups = computed(() => {
  const groups = {};
  for (const vm of vms.value) {
    const description = vm.hardware_details?.description || '';
    const match = description.match(/Lab: (.*?) \| Instance: (\d+)/);
    
    if (match && match[1] && match[2]) {
      const labName = match[1];
      const instanceNum = match[2];
      const groupName = `${labName}_cloned${instanceNum}`;
      
      if (!groups[groupName]) {
        groups[groupName] = { vms: [], state: 'stopped' };
      }
      groups[groupName].vms.push(vm);
      if (vm.status === 'running') {
        groups[groupName].state = 'running';
      }
    }
  }
  return groups;
});

onMounted(async () => {
  await fetchVMs();
});

async function fetchVMs() {
  isLoading.value = true;
  error.value = null;
  vms.value = [];
  try {
    const response = await fetch('/api/vms');
    if (!response.ok) throw new Error(`Server responded with status: ${response.status}`);
    vms.value = await response.json();
  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}

async function deleteLab(vnetName) {
  if (!confirm(`Are you sure you want to delete the entire lab on network "${vnetName}"? All VMs in this lab will be permanently destroyed.`)) {
    return;
  }
  isLoading.value = true;
  error.value = null;
  actionStatus.value = null;
  try {
    const response = await fetch(`/api/labs/${vnetName}`, { method: 'DELETE' });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || 'Failed to delete lab.');
    }
    actionStatus.value = result.message;
    setTimeout(() => {
      fetchVMs();
    }, 5000); // Wait 5 seconds for all delete tasks to finish
  } catch(e) {
    error.value = e.message;
    isLoading.value = false;
  }
}


async function startLab(groupName) {
  isLoading.value = true;
  error.value = null;
  actionStatus.value = null;
  try {
    const response = await fetch(`/api/labs/${groupName}/start`, { method: 'POST' });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Failed to start lab.');
    actionStatus.value = result.message;
    setTimeout(() => { fetchVMs() }, 3000);
  } catch(e) {
    error.value = e.message;
    isLoading.value = false;
  }
}

async function stopLab(groupName) {
  isLoading.value = true;
  error.value = null;
  actionStatus.value = null;
  try {
    const response = await fetch(`/api/labs/${groupName}/stop`, { method: 'POST' });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Failed to stop lab.');
    actionStatus.value = result.message;
    setTimeout(() => { fetchVMs() }, 3000);
  } catch(e) {
    error.value = e.message;
    isLoading.value = false;
  }
}

function toggleLabPower(groupName, currentState) {
  if (currentState === 'running') {
    stopLab(groupName);
  } else {
    startLab(groupName);
  }
}

function handleViewVm(vmToShow) {
  selectedVm.value = vmToShow;
}
</script>

<template>
  <header>
    <h1>Lab Playground</h1>
    <p>View and manage active lab environments.</p>
     <button @click="fetchVMs" :disabled="isLoading">
      {{ isLoading ? 'Loading...' : 'Refresh Environments' }}
    </button>
  </header>
  <main>
    <div v-if="isLoading">Loading Environments...</div>
    <div v-if="actionStatus" class="status-box success"><p>{{ actionStatus }}</p></div>
    <div v-if="error" class="status-box error"><p><strong>Error:</strong> {{ error }}</p></div>
    
    <div v-if="Object.keys(labPlaygroundGroups).length === 0 && !isLoading" class="placeholder">
      <p>No active labs found. Use the Lab Builder to launch a new lab.</p>
    </div>

    <div v-else class="dashboard-layout">
      <div v-for="(group, groupName) in labPlaygroundGroups" :key="groupName" class="vm-group-column">
        <div class="group-header">
          <h2 class="group-title">{{ groupName }}</h2>
          <div class="button-group">
            <button 
              :class="group.state === 'running' ? 'stop-button' : 'start-button'"
              @click="toggleLabPower(groupName, group.state)">
              {{ group.state === 'running' ? 'Stop Lab' : 'Start Lab' }}
            </button>
            <button class="delete-button" @click="deleteLab(groupName)">Delete Lab</button>
          </div>
        </div>
        <div class="vm-grid">
          <VmCard v-for="vm in group.vms" :key="vm.proxmox_id" :vm="vm" @view="handleViewVm" />
        </div>
      </div>
    </div>
  </main>

  <VmDetailModal v-if="selectedVm" :vm="selectedVm" @close="selectedVm = null" />
</template>

<style scoped>
header { text-align: center; margin-bottom: 2rem; }
button { font-weight: 700; border: none; padding: 12px 24px; font-size: 16px; border-radius: 5px; cursor: pointer; }
.status-box { padding: 1rem; margin: 1rem 0; border-radius: 5px; }
.status-box.error { background-color: #ffebee; color: #c62828; }
.status-box.success { background-color: #e8f5e9; color: #2e7d32; }
.placeholder { text-align: center; color: var(--text-muted); padding: 2rem; background-color: var(--bg-light); border-radius: 8px; }

/* --- CORRECTED LAYOUT STYLES --- */
.dashboard-layout {
  display: flex;
  flex-direction: row;
  gap: 2rem;
  overflow-x: auto;
  padding-bottom: 1rem;
}
.vm-group-column {
  background-color: var(--bg-light);
  border: 1px solid var(--border-color);
  padding: 1.5rem;
  border-radius: 8px;
  min-width: 340px;
  flex-shrink: 0;
}
.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 1rem;
  margin-bottom: 1.5rem;
}
.group-title {
  color: var(--accent-color);
  margin: 0;
  font-size: 1.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.vm-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}
.button-group {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}
.start-button, .stop-button, .delete-button {
  font-size: 12px;
  padding: 5px 10px;
}
.start-button {
  background-color: var(--status-running);
  color: white;
}
.stop-button, .delete-button {
  background-color: var(--status-stopped);
  color: white;
}
</style>
