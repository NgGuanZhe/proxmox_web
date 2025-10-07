<script setup>
import { ref, onMounted } from 'vue';
import { api } from '@/services/apiService';

const users = ref([]);
const isLoading = ref(true);
const error = ref(null);

onMounted(async () => {
  await fetchUsers();
});

async function fetchUsers() {
  isLoading.value = true;
  error.value = null;
  try {
    users.value = await api.get('/users/');
  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <header>
    <h1>User Management</h1>
    <p>View all registered users in the application.</p>
  </header>
  <main>
    <div v-if="isLoading">Loading users...</div>
    <div v-if="error" class="error-box"><p><strong>Error:</strong> {{ error }}</p></div>
    
    <div class="table-container" v-if="!isLoading && !error">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.disabled ? 'Disabled' : 'Active' }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>

<style scoped>
/* (You can reuse the same table styles from your other pages) */
header { text-align: center; margin-bottom: 2rem; }
.error-box { padding: 1rem; background-color: #ffebee; color: #c62828; border-radius: 5px; text-align: center; }
.table-container { background-color: var(--bg-light); padding: 2rem; border-radius: 8px; border: 1px solid var(--border-color); }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 1rem; border-bottom: 1px solid var(--border-color); }
th { color: var(--text-muted); }
tbody tr:hover { background-color: rgba(255, 255, 255, 0.05); }
</style>
