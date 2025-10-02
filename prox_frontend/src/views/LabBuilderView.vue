<script setup>
import { ref, onMounted, computed } from 'vue';

const templates = ref([]);
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
  templates.value.forEach(template => {
    const tags = parseTagsFromDescription(template.hardware_details.description);
    tags.forEach(tag => allGroups.add(tag));
  });
  return Array.from(allGroups).sort();
});

const templatesInGroup = computed(() => {
  if (!selectedLabGroup.value) return [];
  return templates.value.filter(t => 
    parseTagsFromDescription(t.hardware_details.description).includes(selectedLabGroup.value)
  );
});
const templatesNotInGroup = computed(() => {
  if (!selectedLabGroup.value) return [];
  return templates.value.filter(t => 
    !parseTagsFromDescription(t.hardware_details.description).includes(selectedLabGroup.value)
  );
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
    const [vmResponse, zoneResponse] = await Promise.all([
      fetch('/api/vms'),
      fetch('/api/sdn/zones')
    ]);
    if (!vmResponse.ok) throw new Error('Failed to fetch VMs/Templates');
    if (!zoneResponse.ok) throw new Error('Failed to fetch SDN Zones');
    
    const allVms = await vmResponse.json();
    templates.value = allVms.filter(vm => vm.hardware_details?.template === 1);

    const allZones = await zoneResponse.json();
    allSdnZones.value = allZones.filter(z => z.type === 'vlan');

  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}

async function updateTemplateTags(template, newTags) {
  try {
    const response = await fetch(`/api/templates/${template.proxmox_id}/tag`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lab_groups: newTags })
    });
    if (!response.ok) throw new Error('Failed to update template tags.');
    await fetchInitialData();
  } catch (e) {
    error.value = e.message;
  }
}

function addTemplateToGroup(template) {
  if (!selectedLabGroup.value) return;
  const currentTags = parseTagsFromDescription(template.hardware_details.description);
  if (!currentTags.includes(selectedLabGroup.value)) {
    updateTemplateTags(template, [...currentTags, selectedLabGroup.value]);
  }
}

function removeTemplateFromGroup(template) {
  if (!selectedLabGroup.value) return;
  const currentTags = parseTagsFromDescription(template.hardware_details.description);
  const newTags = currentTags.filter(tag => tag !== selectedLabGroup.value);
  updateTemplateTags(template, newTags);
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
    const response = await fetch('/api/labs/instantiate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        lab_group: selectedLabGroup.value,
        vlan_zone: launchVlanZone.value,
        vlan_tag: parseInt(launchVlanTag.value)
      })
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Failed to launch lab.');
    launchStatus.value = result;
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
            </div>
          </section>

          <div class="assignment-layout">
            <div class="vm-column">
              <h4>Templates in this Lab</h4>
              <ul class="vm-list-box">
                <li v-for="vm in templatesInGroup" :key="vm.proxmox_id">
                  <span>{{ vm.name }}</span>
                  <button @click="removeTemplateFromGroup(vm)" class="remove-button">Remove</button>
                </li>
                 <li v-if="templatesInGroup.length === 0" class="empty-text">No templates assigned.</li>
              </ul>
            </div>
            <div class="vm-column">
              <h4>Available Templates</h4>
              <ul class="vm-list-box">
                <li v-for="vm in templatesNotInGroup" :key="vm.proxmox_id">
                  <span>{{ vm.name }}</span>
                  <button @click="addTemplateToGroup(vm)" class="add-button">Add</button>
                </li>
                <li v-if="templatesNotInGroup.length === 0" class="empty-text">No available templates.</li>
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
.empty-text { color: var(--text-muted); font-style: italic; }
</style>
