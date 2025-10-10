<script setup>
import { ref, onMounted, computed } from 'vue';
import { api } from '@/services/apiService';
import VmCard from '../components/VmCard.vue';
import VmDetailModal from '../components/VmDetailModal.vue';

// Main state
const vms = ref([]);
const isLoading = ref(true);
const error = ref(null);
const selectedVm = ref(null);
const actionStatus = ref(null);
const collapsedGroups = ref(new Set());

// State for inline editing
const editingGroupName = ref(null);
const vmsInEditLab = ref([]);
const isSaving = ref(false);

const labPlaygroundGroups = computed(() => {
  const groups = {};
  for (const vm of vms.value) {
    const description = vm.hardware_details?.description || '';
    const match = description.match(/Lab: (.*?) \| Instance: (\d+)/);
    
    if (match && match[1] && match[2]) {
      const labName = match[1].replace(' clone', '').replace(' added', '');
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

const sortedLabGroups = computed(() => {
  const groups = labPlaygroundGroups.value;
  const sortedKeys = Object.keys(groups).sort((a, b) => {
    const numA = parseInt((a.match(/_cloned(\d+)$/) || [])[1] || 0);
    const numB = parseInt((b.match(/_cloned(\d+)$/) || [])[1] || 0);
    return numA - numB;
  });
  return sortedKeys.map(key => ({
    name: key,
    data: groups[key]
  }));
});


const availableVmsForEdit = computed(() => {
    if (!editingGroupName.value) return [];
    return vms.value.filter(vm => {
        // Exclude templates
        if (vm.hardware_details?.template === 1) return false;
        
        // Exclude VMs already in the group being edited
        if (vmsInEditLab.value.some(labVm => labVm.proxmox_id === vm.proxmox_id)) return false;

        // Exclude VMs that were part of an original lab clone by checking description
        const description = vm.hardware_details?.description || '';
        if (/Lab:.*? clone \|/.test(description)) {
            return false;
        }

        return true;
    });
});


onMounted(async () => {
  await fetchVMs();
});

async function fetchVMs() {
  isLoading.value = true;
  error.value = null;
  actionStatus.value = null;
  vms.value = [];
  try {
    const fetchedVms = await api.get('/vms');
    vms.value = fetchedVms;

    const groupNames = new Set(Object.keys(labPlaygroundGroups.value));
    collapsedGroups.value = new Set(groupNames);

  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}

async function deleteLab(groupName) {
  if (!confirm(`Are you sure you want to delete the entire lab "${groupName}"?`)) return;
  isLoading.value = true;
  try {
    const result = await api.delete(`/labs/${groupName}`);
    actionStatus.value = result.message;
    setTimeout(() => { fetchVMs() }, 5000);
  } catch(e) {
    error.value = e.message;
    isLoading.value = false;
  }
}

async function startLab(groupName) {
  isLoading.value = true;
  try {
    const result = await api.post(`/labs/${groupName}/start`, {});
    actionStatus.value = result.message;
    setTimeout(() => { fetchVMs() }, 3000);
  } catch(e) {
    error.value = e.message;
    isLoading.value = false;
  }
}

async function stopLab(groupName) {
  isLoading.value = true;
  try {
    const result = await api.post(`/labs/${groupName}/stop`, {});
    actionStatus.value = result.message;
    setTimeout(() => { fetchVMs() }, 3000);
  } catch(e) {
    error.value = e.message;
    isLoading.value = false;
  }
}

function toggleLabPower(groupName, currentState) {
  if (currentState === 'running') stopLab(groupName);
  else startLab(groupName);
}

function toggleGroup(groupName) {
  if (editingGroupName.value === groupName) return; // Don't collapse while editing
  if (collapsedGroups.value.has(groupName)) {
    collapsedGroups.value.delete(groupName);
  } else {
    collapsedGroups.value.add(groupName);
  }
}

function handleViewVm(vmToShow) {
  selectedVm.value = vmToShow;
}

// --- Inline Editing Functions ---

function startEditing(groupName) {
  editingGroupName.value = groupName;
  vmsInEditLab.value = [...labPlaygroundGroups.value[groupName].vms];
  collapsedGroups.value.delete(groupName); // Ensure group is expanded
}

function cancelEditing() {
  editingGroupName.value = null;
  vmsInEditLab.value = [];
}

async function saveLabChanges() {
  if (!editingGroupName.value) return;
  isSaving.value = true;
  error.value = null;
  try {
    const vm_ids = vmsInEditLab.value.map(vm => vm.proxmox_id);
    await api.put(`/labs/${editingGroupName.value}/members`, { vm_ids });
    cancelEditing();
    await fetchVMs();
  } catch (e) {
    error.value = e.message;
  } finally {
    isSaving.value = false;
  }
}

function addToLab(vm) {
    vmsInEditLab.value.push(vm);
}

function removeFromLab(vmId) {
    vmsInEditLab.value = vmsInEditLab.value.filter(vm => vm.proxmox_id !== vmId);
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
    
    <div v-if="sortedLabGroups.length === 0 && !isLoading" class="placeholder">
      <p>No active labs found. Use the Lab Builder to launch a new lab.</p>
    </div>

    <div v-else class="dashboard-layout">
      <div v-for="group in sortedLabGroups" :key="group.name" class="vm-group-column">
        <div class="group-header">
           <div class="button-group" @click.stop>
            <button 
              :class="group.data.state === 'running' ? 'stop-button' : 'start-button'"
              @click="toggleLabPower(group.name, group.data.state)">
              {{ group.data.state === 'running' ? 'Stop Lab' : 'Start Lab' }}
            </button>

            <button v-if="editingGroupName !== group.name" class="edit-button" @click="startEditing(group.name)">Edit</button>
            <button v-if="editingGroupName === group.name" class="save-button" @click="saveLabChanges" :disabled="isSaving">{{ isSaving ? 'Saving...' : 'Save' }}</button>
            <button v-if="editingGroupName === group.name" class="cancel-button" @click="cancelEditing">Cancel</button>

            <button class="delete-button" @click="deleteLab(group.name)">Delete Lab</button>
          </div>
          <div class="group-title-wrapper" @click="toggleGroup(group.name)">
            <h2 class="group-title">
              <span class="collapse-icon" :class="{ collapsed: collapsedGroups.has(group.name) && editingGroupName !== group.name }">▼</span>
              {{ group.name }}
            </h2>
          </div>
        </div>

        <!-- REGULAR VIEW -->
        <div v-if="!collapsedGroups.has(group.name) && editingGroupName !== group.name" class="vm-grid">
          <VmCard v-for="vm in group.data.vms" :key="vm.proxmox_id" :vm="vm" @view="handleViewVm" />
        </div>

        <!-- EDITING VIEW -->
        <div v-if="editingGroupName === group.name" class="edit-mode-container">
          <div class="assignment-layout">
            <div class="vm-column">
              <h4>VMs in this Lab</h4>
              <ul class="vm-list-box">
                <li v-for="vm in vmsInEditLab" :key="vm.proxmox_id">
                  <span>{{ vm.name }}</span>
                  <button @click="removeFromLab(vm.proxmox_id)" class="remove-button">Remove</button>
                </li>
                <li v-if="vmsInEditLab.length === 0" class="empty-text">No VMs assigned.</li>
              </ul>
            </div>
            <div class="vm-column">
              <h4>Available VMs</h4>
              <ul class="vm-list-box">
                <li v-for="vm in availableVmsForEdit" :key="vm.proxmox_id">
                  <span>{{ vm.name }}</span>
                  <button @click="addToLab(vm)" class="add-button">Add</button>
                </li>
                <li v-if="availableVmsForEdit.length === 0" class="empty-text">No available VMs.</li>
              </ul>
            </div>
          </div>
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

.dashboard-layout { display: flex; flex-direction: column; gap: 1.5rem; }
.vm-group-column { background-color: var(--bg-light); border: 1px solid var(--border-color); padding: 1.5rem; border-radius: 8px; }
.group-header { border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem; }
.group-title-wrapper { cursor: pointer; }
.group-title { color: var(--accent-color); margin: 0; font-size: 1.1rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; min-width: 0; }
.collapse-icon { margin-right: 0.75rem; display: inline-block; transition: transform 0.2s ease-in-out; }
.collapse-icon.collapsed { transform: rotate(-90deg); }

.vm-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; padding-top: 1rem; }
.button-group { display: flex; gap: 0.5rem; justify-content: flex-end; margin-bottom: 1rem; }
.start-button, .stop-button, .delete-button, .edit-button, .save-button, .cancel-button { font-size: 12px; padding: 5px 10px; }
.start-button { background-color: var(--status-running); color: white; }
.stop-button, .delete-button { background-color: var(--status-stopped); color: white; }
.edit-button { background-color: #ffc107; color: #1a1a1a; }
.save-button { background-color: var(--accent-color); color: var(--bg-dark); }
.cancel-button { background-color: #6c757d; color: white; }

/* Edit Mode Styles */
.edit-mode-container { padding-top: 1rem; }
.assignment-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
.vm-column h4 { margin-top: 0; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; }
.vm-list-box { background-color: var(--bg-dark); border-radius: 8px; padding: 1rem; min-height: 200px; max-height: 400px; overflow-y: auto; border: 1px solid var(--border-color); list-style: none; }
.vm-list-box li { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; }
.vm-list-box li:not(:last-child) { border-bottom: 1px solid var(--border-color); }
.vm-list-box button { font-size: 12px; padding: 5px 10px; font-weight: 700; border: none; border-radius: 5px; cursor: pointer; }
.add-button { background-color: var(--status-running); color: white; }
.remove-button { background-color: var(--status-stopped); color: white; }
.empty-text { color: var(--text-muted); font-style: italic; justify-content: center; }
</style>


