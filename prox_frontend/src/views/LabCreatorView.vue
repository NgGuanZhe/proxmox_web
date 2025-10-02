<script setup>
import { ref, onMounted, computed } from 'vue';
import VmCard from '../components/VmCard.vue';
import VmDetailModal from '../components/VmDetailModal.vue';

const zones = ref([]);
const vms = ref([]);
const isLoading = ref(true);
const error = ref(null);
const selectedVm = ref(null);
const selectedZone = ref('');
const newVlanTag = ref('');
const isCreating = ref(false);
const creationStatus = ref(null);

const groupedVms = computed(() => {
  const groups = {};
  for (const vm of vms.value) {
    const bridge = vm.hardware_details?.network_interfaces[0]?.bridge || 'Unassigned';
    if (bridge === 'vmbr0') {
      continue;
    }
    if (!groups[bridge]) {
      groups[bridge] = [];
    }
    groups[bridge].push(vm);
  }
  return groups;
});

onMounted(async () => {
  await fetchInitialData();
});

async function fetchInitialData() {
  isLoading.value = true;
  error.value = null;
  creationStatus.value = null;
  try {
    const [zoneResponse, vmResponse] = await Promise.all([
      fetch('/api/sdn/zones'),
      fetch('/api/vms')
    ]);
    if (!zoneResponse.ok) throw new Error('Failed to fetch SDN Zones');
    if (!vmResponse.ok) throw new Error('Failed to fetch VMs');
    const allZones = await zoneResponse.json();
    vms.value = await vmResponse.json();
    zones.value = allZones.filter(z => z.type === 'vlan');
  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}

async function createVlanLab() {
  if (!selectedZone.value || !newVlanTag.value) {
    alert('Please select a VLAN zone and provide a VLAN Tag.');
    return;
  }
  isCreating.value = true;
  error.value = null;
  creationStatus.value = null;
  try {
    const response = await fetch('/api/labs/create_vlan_lab', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ zone: selectedZone.value, tag: parseInt(newVlanTag.value) })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Failed to create lab.');
    creationStatus.value = result;
    await fetchInitialData();
  } catch (e) {
    error.value = e.message;
  } finally {
    isCreating.value = false;
  }
}

function handleViewVm(vmToShow) {
  selectedVm.value = vmToShow;
}

// --- NEW FUNCTIONS ADDED ---
async function handleDeleteVm(vmToDelete) {
  if (!confirm(`Are you sure you want to permanently delete the VM "${vmToDelete.name}"? This cannot be undone.`)) {
    return;
  }
  isLoading.value = true;
  error.value = null;
  try {
    const response = await fetch(`/api/vms/${vmToDelete.proxmox_id}`, { method: 'DELETE' });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || 'Delete action failed.');
    }
    setTimeout(() => {
      fetchInitialData();
    }, 2000);
  } catch(e) {
    error.value = e.message;
    isLoading.value = false;
  }
}

async function handleRenameVm(vmToRename) {
  const newName = prompt("Enter the new name for the VM:", vmToRename.name);
  if (!newName || newName.trim() === '') {
    return;
  }
  isLoading.value = true;
  error.value = null;
  try {
    const response = await fetch(`/api/vms/${vmToRename.proxmox_id}/rename`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ new_name: newName.trim() })
    });
    const result = await response.json();
    if (!response.ok) {
      throw new Error(result.detail || 'Rename action failed.');
    }
    await fetchInitialData();
  } catch(e) {
    error.value = e.message;
    isLoading.value = false;
  }
}
</script>

<template>
  <header>
    <h1>Create Isolated VLAN Lab</h1>
    <p>This will create a new VNET and clone all templates into it.</p>
  </header>
  <main>
    <section class="action-section">
      <h2>Lab Configuration</h2>
      <div class="create-form">
        <select v-model="selectedZone">
          <option disabled value="">Select a VLAN Zone</option>
          <option v-for="zone in zones" :key="zone.zone" :value="zone.zone">
            {{ zone.zone }}
          </option>
        </select>
        <input type="number" v-model="newVlanTag" placeholder="Enter a unique VLAN Tag (e.g., 20)">
        <button @click="createVlanLab" :disabled="isCreating">
          {{ isCreating ? 'Creating Lab...' : 'Create VLAN Lab' }}
        </button>
      </div>
      <div v-if="creationStatus" class="status-box success">
        <p>{{ creationStatus.message }}</p>
        <ul v-if="creationStatus.created_vms">
          <li v-for="vm in creationStatus.created_vms" :key="vm.id">
            Created '{{ vm.name }}' (ID: {{ vm.id }})
          </li>
        </ul>
      </div>
    </section>

    <hr class="divider" />

    <div v-if="isLoading">Loading VM Environments...</div>
    <div v-if="error" class="status-box error"><p><strong>Error:</strong> {{ error }}</p></div>

    <div class="dashboard-layout" v-if="!isLoading">
      <div v-for="(vmList, groupName) in groupedVms" :key="groupName" class="vm-group-column">
        <h2 class="group-title">Network: {{ groupName }}</h2>
        <div class="vm-grid">
          <VmCard 
            v-for="vm in vmList" 
            :key="vm.proxmox_id" 
            :vm="vm" 
            @view="handleViewVm"
            @delete="handleDeleteVm"
            @rename="handleRenameVm" 
          />
        </div>
      </div>
    </div>
  </main>

  <VmDetailModal v-if="selectedVm" :vm="selectedVm" @close="selectedVm = null" />
</template>

<style scoped>
/* (All styles are unchanged) */
header { text-align: center; margin-bottom: 2rem; }
.action-section { background-color: var(--bg-light); padding: 1.5rem 2rem; border-radius: 8px; text-align: center; margin-bottom: 2rem; border: 1px solid var(--border-color); }
.action-section h2 { margin-top: 0; }
.create-form { display: flex; gap: 1rem; justify-content: center; align-items: center; }
.create-form input, .create-form select { background-color: var(--bg-dark); color: var(--text-color); border: 1px solid var(--border-color); padding: 10px; border-radius: 5px; font-family: inherit; }
button { font-weight: 700; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
button:disabled { background-color: #555; color: #999; cursor: not-allowed; }
.status-box { padding: 1rem; margin-top: 1rem; border-radius: 5px; text-align: left; }
.status-box.error { background-color: #ffebee; color: #c62828; }
.status-box.success { background-color: #e8f5e9; color: #2e7d32; }
.divider { border: none; border-top: 1px solid var(--border-color); margin: 2rem 0; }
.dashboard-layout { display: flex; flex-direction: row; gap: 2rem; overflow-x: auto; padding-bottom: 1rem; }
.vm-group-column { background-color: var(--bg-light); border: 1px solid var(--border-color); padding: 1.5rem; border-radius: 8px; min-width: 340px; flex-shrink: 0; }
.group-title { color: var(--accent-color); border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; margin-top: 0; margin-bottom: 1.5rem; }
.vm-grid { display: grid; grid-template-columns: 1fr; gap: 1.5rem; }
</style>
