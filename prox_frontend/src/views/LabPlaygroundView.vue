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
    const bridge = vm.hardware_details?.network_interfaces[0]?.bridge || 'Unassigned';
    if (bridge.startsWith('vnet')) {
      if (!groups[bridge]) {
        groups[bridge] = [];
      }
      groups[bridge].push(vm);
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

function handleViewVm(vmToShow) {
  selectedVm.value = vmToShow;
}
</script>

<template>
  <header>
    <h1>Lab Playground</h1>
    <p>View all active lab environments grouped by their network.</p>
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
      <div v-for="(vmList, groupName) in labPlaygroundGroups" :key="groupName" class="vm-group-column">
        <div class="group-header">
          <h2 class="group-title">Network: {{ groupName }}</h2>
          <button class="delete-button" @click="deleteLab(groupName)">Delete Lab</button>
        </div>
        <div class="vm-grid">
          <VmCard v-for="vm in vmList" :key="vm.proxmox_id" :vm="vm" @view="handleViewVm" />
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
.dashboard-layout { display: flex; flex-direction: row; gap: 2rem; overflow-x: auto; padding-bottom: 1rem; }
.vm-group-column { background-color: var(--bg-light); border: 1px solid var(--border-color); padding: 1.5rem; border-radius: 8px; min-width: 340px; flex-shrink: 0; }
.group-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; margin-bottom: 1.5rem; }
.group-title { color: var(--accent-color); margin: 0; }
.delete-button { background-color: var(--status-stopped); color: white; font-size: 12px; padding: 5px 10px; }
.vm-grid { display: grid; grid-template-columns: 1fr; gap: 1.5rem; }
</style>
