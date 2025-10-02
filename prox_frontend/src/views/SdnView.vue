<script setup>
import { ref, onMounted, computed } from 'vue'

const zones = ref([])
const vnets = ref([])
const isLoading = ref(true)
const error = ref(null)

// State for creating zones
const newZoneName = ref('')
const newZoneType = ref('simple')
const newVlanBridge = ref('')
const newVxlanPeers = ref('')

// State for creating vnets
const newVnetName = ref('')
const newVnetZone = ref('')
const newVnetVlanTag = ref('')

// Determines if the selected zone for a new VNET is a 'vlan' type
const selectedZoneType = computed(() => {
  const zone = zones.value.find(z => z.zone === newVnetZone.value)
  return zone ? zone.type : ''
})

onMounted(async () => {
  await fetchInitialData()
})

async function fetchInitialData() {
  isLoading.value = true; error.value = null;
  try {
    const [zoneResponse, vnetResponse] = await Promise.all([
      fetch('/api/sdn/zones'),
      fetch('/api/sdn/vnets')
    ]);
    if (!zoneResponse.ok) throw new Error('Failed to fetch SDN Zones');
    if (!vnetResponse.ok) throw new Error('Failed to fetch SDN VNETs');
    zones.value = await zoneResponse.json();
    vnets.value = await vnetResponse.json();
  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}

async function createSdnZone() {
  if (!newZoneName.value || !newZoneType.value) {
    alert('Please provide a zone name and select a type.');
    return;
  }
  const payload = {
    zone: newZoneName.value, type: newZoneType.value,
    bridge: newVlanBridge.value, peers: newVxlanPeers.value
  };
  try {
    const response = await fetch('/api/sdn/zones', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Failed to create SDN Zone.');
    alert(`Successfully created zone: ${newZoneName.value}`);
    newZoneName.value = ''; newVlanBridge.value = ''; newVxlanPeers.value = '';
    await fetchInitialData();
  } catch (e) {
    error.value = e.message;
  }
}

async function deleteSdnZone(zoneName) {
  if (!confirm(`Are you sure you want to delete the SDN Zone "${zoneName}"?`)) return;
  try {
    const response = await fetch(`/api/sdn/zones/${zoneName}`, { method: 'DELETE' });
    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.detail || 'Failed to delete zone.');
    }
    alert(`Successfully deleted zone: ${zoneName}`);
    await fetchInitialData();
  } catch(e) {
    error.value = e.message;
  }
}

async function createSdnVnet() {
  if (!newVnetName.value || !newVnetZone.value) {
    alert('Please provide a VNET name and select a zone.');
    return;
  }
  const payload = {
    vnet: newVnetName.value,
    zone: newVnetZone.value,
    tag: selectedZoneType.value === 'vlan' ? newVnetVlanTag.value : undefined
  };
  try {
    const response = await fetch('/api/sdn/vnets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Failed to create SDN VNET.');
    alert(`Successfully created VNET: ${newVnetName.value}`);
    newVnetName.value = '';
    newVnetVlanTag.value = '';
    await fetchInitialData();
  } catch (e) {
    error.value = e.message;
  }
}

// --- THIS IS THE NEW FUNCTION ---
async function deleteSdnVnet(vnetName) {
  if (!confirm(`Are you sure you want to delete the SDN VNET "${vnetName}"?`)) {
    return;
  }
  try {
    const response = await fetch(`/api/sdn/vnets/${vnetName}`, { method: 'DELETE' });
    if (!response.ok) {
      const result = await response.json();
      throw new Error(result.detail || 'Failed to delete VNET.');
    }
    alert(`Successfully deleted VNET: ${vnetName}`);
    await fetchInitialData(); // Auto-refresh the list
  } catch(e) {
    error.value = e.message;
  }
}
</script>

<template>
  <header>
    <h1>SDN Manager</h1>
    <p>Manage Software-Defined Networking Zones and VNETs.</p>
  </header>
  <main>
    <div v-if="isLoading">Loading...</div>
    <div v-if="error" class="error-box"><p><strong>Error:</strong> {{ error }}</p></div>
    
    <div class="layout" v-if="!isLoading">
      <div class="column">
        <section class="action-section">
          <h2>Create New SDN Zone</h2>
          <div class="create-form">
            <input type="text" v-model="newZoneName" placeholder="New zone name...">
            <select v-model="newZoneType">
              <option value="simple">Simple</option>
              <option value="vlan">VLAN</option>
              <option value="vxlan">VXLAN</option>
            </select>
            <input v-if="newZoneType === 'vlan'" type="text" v-model="newVlanBridge" placeholder="Bridge (e.g., vmbr0)">
            <input v-if="newZoneType === 'vxlan'" type="text" v-model="newVxlanPeers" placeholder="Peer IPs (comma-separated)">
            <button @click="createSdnZone">Create Zone</button>
          </div>
        </section>

        <div class="table-container">
          <h2>Existing SDN Zones</h2>
          <table>
            <thead>
              <tr>
                <th>Zone</th>
                <th>Type</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="zones.length === 0">
                <td colspan="3">No SDN Zones found.</td>
              </tr>
              <tr v-for="zone in zones" :key="zone.zone">
                <td>{{ zone.zone }}</td>
                <td>{{ zone.type }}</td>
                <td><button class="delete-button" @click="deleteSdnZone(zone.zone)">Delete</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div class="column">
        <section class="action-section">
          <h2>Create New VNET</h2>
          <div class="create-form">
            <input type="text" v-model="newVnetName" placeholder="New VNET name...">
            <select v-model="newVnetZone">
              <option disabled value="">Select Zone to Link</option>
              <option v-for="zone in zones" :key="zone.zone" :value="zone.zone">
                {{ zone.zone }} ({{ zone.type }})
              </option>
            </select>
            <input v-if="selectedZoneType === 'vlan'" type="number" v-model="newVnetVlanTag" placeholder="VLAN Tag (e.g., 10)">
            <button @click="createSdnVnet">Create VNET</button>
          </div>
        </section>

        <div class="table-container">
          <h2>Existing VNETs</h2>
          <table>
            <thead>
              <tr>
                <th>VNET</th>
                <th>Zone</th>
                <th>Tag</th>
                <th>Actions</th> </tr>
            </thead>
            <tbody>
              <tr v-if="vnets.length === 0">
                <td colspan="4">No SDN VNETs found.</td>
              </tr>
              <tr v-for="vnet in vnets" :key="vnet.vnet">
                <td>{{ vnet.vnet }}</td>
                <td>{{ vnet.zone }}</td>
                <td>{{ vnet.tag || 'N/A' }}</td>
                <td>
                  <button class="delete-button" @click="deleteSdnVnet(vnet.vnet)">Delete</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.layout {
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  align-items: flex-start;
  gap: 2rem;
}

.column {
  flex: 1;
  min-width: 400px; /* Prevents it from shrinking too much */
}
header { text-align: center; margin-bottom: 2rem; }
.error-box { padding: 1rem; background-color: #ffebee; color: #c62828; border-radius: 5px; text-align: center; }
.action-section { background-color: var(--bg-light); padding: 2rem; border-radius: 8px; margin-bottom: 2rem; border: 1px solid var(--border-color); }
.action-section h2 { margin-top: 0; text-align: center; }
.create-form { display: flex; flex-direction: column; gap: 1rem; }
.create-form input, .create-form select { background-color: var(--bg-dark); color: var(--text-color); border: 1px solid var(--border-color); padding: 10px; border-radius: 5px; font-family: inherit; font-size: 14px; }
button { background-color: var(--accent-color); color: var(--bg-dark); font-weight: 700; border: none; padding: 10px 20px; font-size: 14px; border-radius: 5px; cursor: pointer; }
.divider { border: none; border-top: 1px solid var(--border-color); margin: 2rem 0; }
.table-container { background-color: var(--bg-light); padding: 2rem; border-radius: 8px; border: 1px solid var(--border-color); }
.table-container h2 { margin-top: 0; color: var(--accent-color); }
table { width: 100%; border-collapse: collapse; margin-top: 1.5rem; }
th, td { text-align: left; padding: 1rem; border-bottom: 1px solid var(--border-color); }
th { font-weight: 700; text-transform: uppercase; color: var(--text-muted); }
tbody tr:hover { background-color: rgba(255, 255, 255, 0.05); }
td[colspan="3"], td[colspan="4"] { text-align: center; color: var(--text-muted); padding: 2rem; }
.delete-button { background-color: var(--status-stopped); color: white; font-size: 12px; padding: 5px 10px; }
</style>
