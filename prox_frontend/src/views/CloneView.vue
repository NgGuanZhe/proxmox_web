<script setup>
import { ref } from 'vue'
import { api } from '@/services/apiService'; // <-- Import the new service

const cloneStatus = ref(null)
const isCloning = ref(false)
const error = ref(null)
const deleteStatus = ref(null)
const isDeleting = ref(false)

async function cloneAllTemplates() {
  isCloning.value = true; error.value = null; cloneStatus.value = null; deleteStatus.value = null;
  try {
    cloneStatus.value = await api.post('/clone_templates', {});
  } catch (e) {
    error.value = e.message
  } finally {
    isCloning.value = false
  }
}

async function deleteAllClones() {
  if (!confirm("Are you sure you want to permanently delete ALL cloned VMs? This cannot be undone.")) {
    return;
  }

  isDeleting.value = true; error.value = null; cloneStatus.value = null; deleteStatus.value = null;
  try {
    deleteStatus.value = await api.post('/vms/delete_clones', {});
  } catch (e) {
    error.value = e.message
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <header>
    <h1>Template & Clone Management</h1>
    <p>Create or destroy cloned virtual machines based on your templates.</p>
  </header>

  <main>
    <section class="action-section">
      <h2>Clone Templates</h2>
      <p>Create a new set of linked clones from all available templates.</p>
      <button @click="cloneAllTemplates" :disabled="isCloning || isDeleting" class="clone-button">
        {{ isCloning ? 'Cloning in progress...' : 'Clone All Templates' }}
      </button>
      <div v-if="cloneStatus" class="status-box success">
        <p>{{ cloneStatus.message }}</p>
        <ul v-if="cloneStatus.cloned_vms && cloneStatus.cloned_vms.length">
          <li v-for="cloned in cloneStatus.cloned_vms" :key="cloned.new_id">
            Cloned '{{ cloned.template }}' to new VM '{{ cloned.new_name }}' (ID: {{ cloned.new_id }})
          </li>
        </ul>
      </div>
    </section>

    <hr class="divider" />
    <section class="action-section">
        <h2>Delete Clones</h2>
        <p>Permanently delete all VMs that were cloned from a template.</p>
        <button @click="deleteAllClones" :disabled="isCloning || isDeleting" class="delete-button">
            {{ isDeleting ? 'Deleting in progress...' : 'Delete All Cloned VMs' }}
        </button>
        <div v-if="deleteStatus" class="status-box success">
            <p>{{ deleteStatus.message }}</p>
            <ul v-if="deleteStatus.deleted_vms && deleteStatus.deleted_vms.length">
                <li v-for="vmName in deleteStatus.deleted_vms" :key="vmName">
                    Deleted '{{ vmName }}'
                </li>
            </ul>
        </div>
    </section>

    <div v-if="error" class="status-box error">
      <p><strong>Error:</strong> {{ error }}</p>
    </div>
  </main>
</template>

<style scoped>
header { text-align: center; margin-bottom: 2rem; }
.action-section {
  background-color: var(--bg-light);
  padding: 1.5rem 2rem;
  border-radius: 8px;
  text-align: center;
  border: 1px solid var(--border-color);
}
.action-section p { max-width: 600px; margin: 0 auto 1.5rem; color: var(--text-muted); }
button { font-weight: 700; border: none; padding: 12px 24px; font-size: 16px; border-radius: 5px; cursor: pointer; transition: background-color 0.2s; }
button:disabled { background-color: #555; color: #999; cursor: not-allowed; }
.clone-button { background-color: #ffc107; color: #1a1a1a; }
.delete-button { background-color: var(--status-stopped); color: white; }
.status-box { padding: 1rem; margin-top: 1.5rem; border-radius: 5px; text-align: left; }
.status-box.error { background-color: #ffebee; color: #c62828; }
.status-box.success { background-color: #e8f5e9; color: #2e7d32; }
.status-box ul { padding-left: 20px; margin: 0.5rem 0 0; }
.divider { border: none; border-top: 1px solid var(--border-color); margin: 2rem 0; }
</style>
