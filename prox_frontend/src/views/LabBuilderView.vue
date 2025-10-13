<script setup>
import { ref, onMounted, computed } from 'vue';
import { api } from '@/services/apiService'; 

const allVms = ref([]);
const isLoading = ref(true);
const error = ref(null);
const newLabGroupName = ref('');
const selectedLabGroup = ref(null);

const launchVlanZone = ref('');
const launchVlanTag = ref('');
const isLaunching = ref(false);
const launchStatus = ref(null);
const allSdnZones = ref([]);

const labGroups = computed(() => {
  const allGroups = new Set();
  if (newLabGroupName.value.trim()) {
    allGroups.add(newLabGroupName.value.trim());
  }
  allVms.value.forEach(vm => {
    const tags = parseTagsFromDescription(vm.hardware_details.description);
    tags.forEach(tag => allGroups.add(tag));
  });
  return Array.from(allGroups).sort();
});

const vmsInGroup = computed(() => {
  if (!selectedLabGroup.value) return [];
  return allVms.value.filter(vm => 
    parseTagsFromDescription(vm.hardware_details.description).includes(selectedLabGroup.value)
  );
});

const vmsNotInGroup = computed(() => {
    if (!selectedLabGroup.value) return [];
    return allVms.value.filter(vm => {
        const description = vm.hardware_details?.description || '';
        const tags = parseTagsFromDescription(description);

        // A VM is NOT in the group if it doesn't have the selected lab group tag.
        const isNotInCurrentGroup = !tags.includes(selectedLabGroup.value);

        // Additionally, for non-templates, it should not be part of any other active lab instance.
        if (!vm.hardware_details?.template) {
            const isInAnotherLab = /Lab:.*?\| Instance:/.test(description);
            return isNotInCurrentGroup && !isInAnotherLab;
        }

        // For templates, just check if it's not in the current group.
        return isNotInCurrentGroup;
    });
});


onMounted(async () => {
  await fetchInitialData();
});

function parseTagsFromDescription(description) {
  const match = (description || '').match(/LabGroups:\[(.*?)\]/);
  return match && match[1] ? match[1].split(',') : [];
}

async function fetchInitialData() {
  isLoading.value = true;
  error.value = null;
  try {
    const [fetchedVms, allZones] = await Promise.all([
      api.get('/vms'),
      api.get('/sdn/zones')
    ]);
    
    allVms.value = fetchedVms;
    allSdnZones.value = allZones.filter(z => z.type === 'vlan');

  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}

async function updateVmTags(vm, newTags) {
  try {
    const endpoint = vm.hardware_details.template ? `/templates/${vm.proxmox_id}/tag` : `/vms/${vm.proxmox_id}/tag`;
    await api.put(endpoint, { lab_groups: newTags });
    await fetchInitialData(); // Refresh data after update
  } catch (e) {
    error.value = e.message;
  }
}


function addVmToGroup(vm) {
  if (!selectedLabGroup.value) return;
  const currentTags = parseTagsFromDescription(vm.hardware_details.description);
  if (!currentTags.includes(selectedLabGroup.value)) {
    updateVmTags(vm, [...currentTags, selectedLabGroup.value]);
  }
}

function removeVmFromGroup(vm) {
  if (!selectedLabGroup.value) return;
  const currentTags = parseTagsFromDescription(vm.hardware_details.description);
  const newTags = currentTags.filter(tag => tag !== selectedLabGroup.value);
  updateVmTags(vm, newTags);
}

async function instantiateLab() {
  if (!selectedLabGroup.value || !launchVlanZone.value || !launchVlanTag.value) {
    alert('Please select a lab group, a VLAN zone, and provide a VLAN tag.');
    return;
  }
  isLaunching.value = true;
  error.value = null;
  launchStatus.value = null;
  try {
    const payload = { 
      lab_group: selectedLabGroup.value,
      vlan_zone: launchVlanZone.value,
      vlan_tag: parseInt(launchVlanTag.value)
    };
    launchStatus.value = await api.post('/labs/instantiate', payload);
  } catch (e) {
    error.value = e.message;
  } finally {
    isLaunching.value = false;
  }
}

</script>

<template>
  <header>
    <h1>Lab Builder</h1>
    <p>Design and launch isolated lab environments by grouping templates.</p>
  </header>
  <main>
    <div v-if="isLoading">Loading...</div>
    <div v-if="error" class="error-box"><p><strong>Error:</strong> {{ error }}</p></div>
    
    <div class="builder-layout" v-if="!isLoading">
      <div class="lab-group-panel">
        <h3>Lab Groups</h3>
        <div class="create-form">
          <input type="text" v-model="newLabGroupName" placeholder="New lab group name...">
          <button @click="newLabGroupName = ''">Create Group</button>
        </div>
        <ul>
          <li v-for="group in labGroups" :key="group" 
              @click="selectedLabGroup = group"
              :class="{ active: selectedLabGroup === group }">
            <span>{{ group }}</span>
          </li>
        </ul>
      </div>

      <div class="template-panel">
        <div v-if="selectedLabGroup" class="content-wrapper">
          <section class="action-section launch-section">
            <h3>Launch Lab: {{ selectedLabGroup }}</h3>
            <div class="launch-form">
              <select v-model="launchVlanZone">
                <option disabled value="">Select VLAN Zone</option>
                <option v-for="zone in allSdnZones" :key="zone.zone" :value="zone.zone">{{ zone.zone }}</option>
              </select>
              <input type="number" v-model="launchVlanTag" placeholder="VLAN Tag (e.g., 30)">
              <button @click="instantiateLab" :disabled="isLaunching">{{ isLaunching ? 'Launching...' : 'Launch Lab' }}</button>
            </div>
            <div v-if="launchStatus" class="status-box success">
              <p>{{ launchStatus.message }}</p>
              <div v-if="launchStatus.cloned_vms && launchStatus.cloned_vms.length > 0">
                <strong>New VMs Created:</strong>
                <ul>
                  <li v-for="vm in launchStatus.cloned_vms" :key="vm.id">
                    {{ vm.name }} (ID: {{ vm.id }})
                  </li>
                </ul>
              </div>
              <div v-if="launchStatus.added_vms && launchStatus.added_vms.length > 0">
                <strong>Existing VMs Added:</strong>
                <ul>
                  <li v-for="vm in launchStatus.added_vms" :key="vm.id">
                    {{ vm.name }} (ID: {{ vm.id }})
                  </li>
                </ul>
              </div>
              <div v-if="launchStatus.failed_to_add_vms && launchStatus.failed_to_add_vms.length > 0" class="status-box error">
                 <strong>Failed to Add VMs:</strong>
                <ul>
                  <li v-for="vm in launchStatus.failed_to_add_vms" :key="vm.name">
                    {{ vm.name }} (Reason: {{ vm.reason }})
                  </li>
                </ul>
              </div>
            </div>
          </section>

          <div class="assignment-layout">
            <div class="vm-column">
              <h4>VMs in this Lab</h4>
              <ul class="vm-list-box">
                <li v-for="vm in vmsInGroup" :key="vm.proxmox_id">
                  <span>{{ vm.name }} <span v-if="vm.hardware_details.template" class="template-badge">Template</span></span>
                  <button @click="removeVmFromGroup(vm)" class="remove-button">Remove</button>
                </li>
                 <li v-if="vmsInGroup.length === 0" class="empty-text">No VMs assigned.</li>
              </ul>
            </div>
            <div class="vm-column">
              <h4>Available VMs</h4>
              <ul class="vm-list-box">
                <li v-for="vm in vmsNotInGroup" :key="vm.proxmox_id">
                   <span>{{ vm.name }} <span v-if="vm.hardware_details.template" class="template-badge">Template</span></span>
                  <button @click="addVmToGroup(vm)" class="add-button">Add</button>
                </li>
                <li v-if="vmsNotInGroup.length === 0" class="empty-text">No available VMs.</li>
              </ul>
            </div>
          </div>
        </div>
        <div v-else class="placeholder">
          <p>Select or create a Lab Group to begin.</p>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
header { text-align: center; margin-bottom: 2rem; }
.error-box { padding: 1rem; background-color: #ffebee; color: #c62828; border-radius: 5px; text-align: center; }
.action-section { background-color: var(--bg-light); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-color); }
.create-form { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.create-form input { flex-grow: 1; }
.launch-form { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; align-items: center; }

input, select, button {
  background-color: var(--bg-dark);
  color: var(--text-color);
  border: 1px solid var(--border-color);
  padding: 10px;
  border-radius: 5px;
  font-family: inherit;
  font-size: 14px;
}
button {
  background-color: var(--accent-color);
  color: var(--bg-dark);
  font-weight: 700;
  cursor: pointer;
  transition: background-color 0.2s;
}
button:hover:not(:disabled) { background-color: var(--accent-hover); }
button:disabled { opacity: 0.6; cursor: not-allowed; }

.builder-layout { display: grid; grid-template-columns: 300px 1fr; gap: 2rem; align-items: flex-start; }
.lab-group-panel { background-color: var(--bg-light); padding: 1.5rem; border-radius: 8px; border: 1px solid var(--border-color); }
.lab-group-panel h3 { margin-top: 0; color: var(--accent-color); }
.lab-group-panel ul { list-style: none; padding: 0; margin-top: 1rem; }
.lab-group-panel li { padding: 0.75rem; border-radius: 5px; cursor: pointer; transition: background-color 0.2s; }
.lab-group-panel li.active { background-color: var(--accent-color); color: var(--bg-dark); font-weight: bold; }
.lab-group-panel li:not(.active):hover { background-color: rgba(255, 255, 255, 0.05); }

.template-panel { display: flex; flex-direction: column; gap: 2rem; }
.assignment-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
.vm-column h4 { margin-top: 0; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; }
.vm-list-box { background-color: var(--bg-light); border-radius: 8px; padding: 1rem; min-height: 200px; border: 1px solid var(--border-color); }
.vm-list-box li { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; }
.vm-list-box button { font-size: 12px; padding: 5px 10px; }
.add-button { background-color: var(--status-running); color: white; }
.remove-button { background-color: var(--status-stopped); color: white; }
.placeholder { text-align: center; color: var(--text-muted); padding: 4rem; background-color: var(--bg-light); border-radius: 8px; border: 1px dashed var(--border-color); }
.status-box { padding: 1rem; margin-top: 1.5rem; border-radius: 5px; text-align: left; }
.status-box.success { background-color: #e8f5e9; color: #2e7d32; }
.status-box.error { background-color: #ffebee; color: #c62828; margin-top: 1rem; }
.status-box ul { padding-left: 20px; margin-top: 0.5rem; }
.empty-text { color: var(--text-muted); font-style: italic; }
.template-badge {
  background-color: #ffc107;
  color: #1a1a1a;
  padding: 2px 6px;
  border-radius: 10px;
  font-size: 10px;
  font-weight: bold;
  margin-left: 8px;
}
</style>

