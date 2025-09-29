<script setup>
import { ref, computed } from 'vue'
import VmCard from '../components/VmCard.vue'
import VmDetailModal from '../components/VmDetailModal.vue'

const vms = ref([])
const isLoading = ref(false)
const error = ref(null)
const selectedVm = ref(null)
const bulkActionStatus = ref(null)
const isBulkActionLoading = ref(false)

const groupedVms = computed(() => {
  const groups = {}
  const templates = []
  const otherVMs = []

  // First, separate templates from all other VMs
  for (const vm of vms.value) {
    if (vm.hardware_details && vm.hardware_details.template === 1) {
      templates.push(vm)
    } else {
      otherVMs.push(vm)
    }
  }

  // Create a group for each template, keyed by the template's name
  for (const template of templates) {
    groups[template.name] = {
      template: template,
      clones: []
    }
  }

  const unassignedVMs = []
  // Go through the non-template VMs and assign them to their parent group
  for (const vm of otherVMs) {
    const description = vm.hardware_details?.description || ''
    const match = description.match(/Cloned from template: (.*)/)
    
    if (match && match[1] && groups[match[1].trim()]) {
      groups[match[1].trim()].clones.push(vm)
    } else {
      unassignedVMs.push(vm)
    }
  }

  // Add the final group for any remaining, unassigned VMs
  if (unassignedVMs.length > 0) {
    groups['Other VMs'] = {
      template: null, // This group has no parent template
      clones: unassignedVMs
    }
  }
  
  return groups
})

async function fetchVMs() {
  isLoading.value = true; error.value = null; vms.value = []; bulkActionStatus.value = null;
  try {
    const response = await fetch('/api/vms');
    if (!response.ok) throw new Error(`Server responded with status: ${response.status}`);
    vms.value = await response.json()
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

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
    // Wait for 2 seconds before refreshing to give Proxmox time
    setTimeout(() => {
      fetchVMs();
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
    await fetchVMs();
  } catch(e) {
    error.value = e.message;
    isLoading.value = false;
  }
}

function handleViewVm(vmToShow) {
  selectedVm.value = vmToShow;
}

async function handleBulkAction(action) {
  isBulkActionLoading.value = true;
  error.value = null;
  bulkActionStatus.value = null;
  const endpoint = action === 'start' ? '/api/vms/start_all' : '/api/vms/stop_all';
  try {
    const response = await fetch(endpoint, { method: 'POST' });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Bulk action failed.');
    bulkActionStatus.value = result.message;
    setTimeout(() => { fetchVMs() }, 3000);
  } catch (e) {
    error.value = e.message;
  } finally {
    isBulkActionLoading.value = false;
  }
}
</script>

<template>
  <header>
    <h1>VM Dashboard</h1>
    <p>A simple interface to view and manage virtual machines.</p>
    <button @click="fetchVMs" :disabled="isLoading || isBulkActionLoading">
      {{ isLoading ? 'Loading...' : 'Refresh VM List' }}
    </button>
  </header>

  <main>
    <section class="bulk-actions">
      <h2>Bulk Actions</h2>
      <div class="button-group">
        <button @click="handleBulkAction('start')" :disabled="isBulkActionLoading || isLoading" class="start-button">Start All VMs</button>
        <button @click="handleBulkAction('stop')" :disabled="isBulkActionLoading || isLoading" class="stop-button">Stop All VMs</button>
      </div>
      <div v-if="bulkActionStatus" class="status-box success">
        <p>{{ bulkActionStatus }}</p>
      </div>
    </section>

    <hr class="divider" />
    
    <div v-if="error" class="status-box error">
      <p><strong>Error:</strong> {{ error }}</p>
    </div>

    <div class="dashboard-layout">
      <div v-for="(group, groupName) in groupedVms" :key="groupName" class="vm-group-column">
        <h2 class="group-title">{{ groupName }}</h2>
        
        <VmCard v-if="group.template" :vm="group.template" @view="handleViewVm" @delete="handleDeleteVm" @rename="handleRenameVm" class="golden-template-card" />
        
        <div class="vm-grid">
          <VmCard v-for="vm in group.clones" :key="vm.proxmox_id" :vm="vm" @view="handleViewVm" @delete="handleDeleteVm" @rename="handleRenameVm" />
        </div>
      </div>
    </div>
  </main>

  <VmDetailModal v-if="selectedVm" :vm="selectedVm" @close="selectedVm = null" />
</template>

<style scoped>
header { text-align: center; margin-bottom: 2rem; }
button { background-color: var(--accent-color); color: var(--bg-dark); font-weight: 700; border: none; padding: 12px 24px; font-size: 16px; border-radius: 5px; cursor: pointer; transition: background-color 0.2s; }
button:disabled { background-color: #555; color: #999; cursor: not-allowed; }
.status-box { padding: 1rem; margin-top: 1rem; border-radius: 5px; text-align: left; }
.status-box.error { background-color: #ffebee; color: #c62828; }
.status-box.success { background-color: #e8f5e9; color: #2e7d32; }
.divider { border: none; border-top: 1px solid var(--border-color); margin: 2rem 0; }

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
.group-title {
  color: var(--accent-color);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.5rem;
  margin-top: 0;
  margin-bottom: 1.5rem;
}
.golden-template-card {
  margin-bottom: 1.5rem;
  border: 2px solid #ffc107;
}
.vm-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.5rem;
}
.bulk-actions {
  background-color: var(--bg-light);
  padding: 1.5rem 2rem;
  border-radius: 8px;
  text-align: center;
  margin-bottom: 2rem;
  border: 1px solid var(--border-color);
}
.bulk-actions h2 { margin-top: 0; }
.button-group {
  display: flex;
  justify-content: center;
  gap: 1rem;
}
.start-button { background-color: var(--status-running); color: white; }
.stop-button { background-color: var(--status-stopped); color: white; }
</style>
