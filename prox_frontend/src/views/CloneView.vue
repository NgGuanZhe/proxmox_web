<script setup>
import { ref } from 'vue'

const cloneStatus = ref(null)
const isCloning = ref(false)
const error = ref(null)

async function cloneAllTemplates() {
  isCloning.value = true
  error.value = null
  cloneStatus.value = null
  try {
    const response = await fetch('/api/clone_templates', { method: 'POST' })
    const result = await response.json()
    if (!response.ok) {
      throw new Error(result.detail || 'Cloning failed.')
    }
    cloneStatus.value = result
  } catch (e) {
    error.value = e.message
  } finally {
    isCloning.value = false
  }
}
</script>

<template>
  <header>
    <h1>Clone Templates</h1>
    <p>Automatically create a new set of linked clones from all available templates.</p>
  </header>

  <main>
    <section class="clone-section">
      <p>New VMs will be assigned the next available ID, starting after the highest existing ID in the 1000+ range.</p>
      <button @click="cloneAllTemplates" :disabled="isCloning">
        {{ isCloning ? 'Cloning in progress...' : 'Clone All Templates' }}
      </button>
      <div v-if="error" class="status-box error">
        <p><strong>Error:</strong> {{ error }}</p>
      </div>
      <div v-if="cloneStatus" class="status-box success">
        <p>{{ cloneStatus.message }}</p>
        <ul v-if="cloneStatus.cloned_vms && cloneStatus.cloned_vms.length">
          <li v-for="cloned in cloneStatus.cloned_vms" :key="cloned.new_id">
            Cloned '{{ cloned.template }}' to new VM '{{ cloned.new_name }}' (ID: {{ cloned.new_id }})
          </li>
        </ul>
      </div>
    </section>
  </main>
</template>

<style scoped>
header { text-align: center; margin-bottom: 2rem; }
.clone-section {
  background-color: var(--bg-light);
  padding: 1.5rem 2rem;
  border-radius: 8px;
  text-align: center;
  border: 1px solid var(--border-color);
}
.clone-section p {
  max-width: 600px;
  margin: 0 auto 1.5rem;
  color: var(--text-muted);
}
button {
  background-color: #ffc107;
  color: #1a1a1a;
  font-weight: 700;
  border: none;
  padding: 12px 24px;
  font-size: 16px;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.2s;
}
button:disabled { background-color: #555; color: #999; cursor: not-allowed; }
.status-box { padding: 1rem; margin-top: 1.5rem; border-radius: 5px; text-align: left; }
.status-box.error { background-color: #ffebee; color: #c62828; }
.status-box.success { background-color: #e8f5e9; color: #2e7d32; }
.status-box ul { padding-left: 20px; margin: 0.5rem 0 0; }
</style>
