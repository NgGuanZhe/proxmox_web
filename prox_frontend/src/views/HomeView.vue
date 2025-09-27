<script setup>
import { ref } from 'vue'
import VmCard from '../components/VmCard.vue'
import VmDetailModal from '../components/VmDetailModal.vue'

const vms = ref([])
const isLoading = ref(false)
const error = ref(null)
const selectedVm = ref(null)

async function fetchVMs() {
  isLoading.value = true
  error.value = null
  vms.value = []
  try {
    const response = await fetch('/api/vms')
    if (!response.ok) {
      throw new Error(`Server responded with status: ${response.status}`)
    }
    vms.value = await response.json()
  } catch (e) {
    error.value = e.message
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <header>
    <h1>VM Dashboard</h1>
    <p>A simple interface to view and manage virtual machines.</p>
    <button @click="fetchVMs" :disabled="isLoading">
      {{ isLoading ? 'Loading...' : 'Fetch VMs' }}
    </button>
  </header>

  <main>
    <div v-if="error" class="error-box">
      <p><strong>Error:</strong> {{ error }}</p>
    </div>

    <div class="vm-grid">
      <VmCard v-for="vm in vms" :key="vm.proxmox_id" :vm="vm" @click="selectedVm = vm" />
    </div>
  </main>

  <VmDetailModal v-if="selectedVm" :vm="selectedVm" @close="selectedVm = null" />
</template>

<style scoped>
header {
  text-align: center;
  margin-bottom: 3rem;
}
button {
  background-color: #007bff;
  color: white;
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.2s;
}
.error-box {
  padding: 1rem;
  background-color: #ffebee;
  color: #c62828;
  border-radius: 5px;
  text-align: center;
}
.vm-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}
</style>
