<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/apiService'; // <-- Import the new service

const networks = ref({})
const isLoading = ref(true)
const error = ref(null)
const selectedNode = ref('')
const newBridgeName = ref('')

onMounted(async () => {
  await fetchNetworks()
})

async function fetchNetworks() {
  isLoading.value = true
  error.value = null
  try {
    networks.value = await api.get('/networks');
    if (Object.keys(networks.value).length > 0) {
      selectedNode.value = Object.keys(networks.value)[0];
    }
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}

async function createNetwork() {
  if (!selectedNode.value || !newBridgeName.value) {
    alert('Please select a node and provide a bridge name (e.g., vmbr1).')
    return
  }
  try {
    const payload = { node: selectedNode.value, iface: newBridgeName.value };
    await api.post('/networks', payload);
    
    alert(`Successfully created bridge: ${newBridgeName.value}`)
    newBridgeName.value = ''
    await fetchNetworks()
  } catch (e) {
    error.value = e.message
  }
}

async function deleteNetwork(node, iface) {
  if (!confirm(`Are you sure you want to delete the network bridge "${iface}" on node "${node}"?`)) {
    return;
  }
  try {
    await api.delete(`/networks/${node}/${iface}`);
    alert(`Successfully deleted bridge: ${iface}`);
    await fetchNetworks();
  } catch (e) {
    error.value = e.message;
  }
}
</script>

<template>
  <header>
    <h1>Network Manager</h1>
    <p>View and create virtual networks (Linux Bridges).</p>
  </header>
  <main>
    <section class="action-section">
      <h2>Create New Bridge</h2>
      <div class="create-form">
        <select v-model="selectedNode">
          <option disabled value="">Select Node</option>
          <option v-for="(net_info, nodeName) in networks" :key="nodeName" :value="nodeName">
            {{ nodeName }}
          </option>
        </select>
        <input type="text" v-model="newBridgeName" placeholder="New bridge name (e.g., vmbr1)">
        <button @click="createNetwork">Create</button>
      </div>
    </section>

    <hr class="divider" />
    
    <div v-if="isLoading">Loading networks...</div>
    <div v-if="error" class="error-box"><p><strong>Error:</strong> {{ error }}</p></div>

    <div v-for="(bridge_list, nodeName) in networks" :key="nodeName" class="node-section">
      <h2>Node: {{ nodeName }}</h2>
      <table>
        <thead>
          <tr>
            <th>Name (Iface)</th>
            <th>Type</th>
            <th>Active</th>
            <th>Comment</th>
            <th>Actions</th> </tr>
        </thead>
        <tbody>
          <tr v-for="bridge in bridge_list" :key="bridge.iface">
            <td>{{ bridge.iface }}</td>
            <td>{{ bridge.type }}</td>
            <td>{{ bridge.active ? 'Yes' : 'No' }}</td>
            <td>{{ bridge.comment }}</td>
            <td>
              <button class="delete-button" 
                      v-if="bridge.iface !== 'vmbr0'" 
                      @click="deleteNetwork(nodeName, bridge.iface)">
                Delete
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>

<style scoped>
header { text-align: center; margin-bottom: 2rem; }
.error-box { padding: 1rem; background-color: #ffebee; color: #c62828; border-radius: 5px; text-align: center; }
.action-section { background-color: var(--bg-light); padding: 1.5rem 2rem; border-radius: 8px; margin-bottom: 2rem; border: 1px solid var(--border-color); }
.action-section h2 { margin-top: 0; text-align: center; }
.create-form { display: flex; gap: 1rem; justify-content: center; }
.create-form input, .create-form select { background-color: var(--bg-dark); color: var(--text-color); border: 1px solid var(--border-color); padding: 10px; border-radius: 5px; }
button { background-color: var(--accent-color); color: var(--bg-dark); font-weight: 700; border: none; padding: 10px 20px; font-size: 14px; border-radius: 5px; cursor: pointer; }
.delete-button { background-color: var(--status-stopped); color: white; font-size: 12px; padding: 5px 10px; }
.divider { border: none; border-top: 1px solid var(--border-color); margin: 2rem 0; }
.node-section { margin-bottom: 2rem; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 12px; border-bottom: 1px solid var(--border-color); }
th { color: var(--accent-color); }
</style>
