<script setup>
import { ref, onMounted } from 'vue';
import { api } from '@/services/apiService';

const users = ref([]);
const currentUser = ref(null);
const isLoading = ref(true);
const error = ref(null);

onMounted(async () => {
  await fetchUsersAndCurrentUser();
});

async function fetchUsersAndCurrentUser() {
  isLoading.value = true;
  error.value = null;
  try {
    // Fetch both the user list and the current user's info at the same time
    const [usersData, currentUserData] = await Promise.all([
      api.get('/users/'),
      api.get('/users/me')
    ]);
    users.value = usersData;
    currentUser.value = currentUserData;
  } catch (e) {
    error.value = e.message;
  } finally {
    isLoading.value = false;
  }
}

// This is the new function to delete a user
async function deleteUser(userId) {
  if (!confirm('Are you sure you want to permanently delete this user? This cannot be undone.')) {
    return;
  }
  try {
    await api.delete(`/users/${userId}`);
    alert('User deleted successfully.');
    // Refresh the list after a successful deletion
    await fetchUsersAndCurrentUser();
  } catch(e) {
    error.value = e.message;
  }
}
</script>

<template>
  <header>
    <h1>User Management</h1>
    <p>View and manage registered users in the application.</p>
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
            <th>Admin</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.disabled ? 'Disabled' : 'Active' }}</td>
            <td>{{ user.is_admin ? 'Yes' : 'No' }}</td>
            <td>
              <button 
                v-if="currentUser && user.id !== currentUser.id" 
                class="delete-button" 
                @click="deleteUser(user.id)">
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
.table-container { background-color: var(--bg-light); padding: 2rem; border-radius: 8px; border: 1px solid var(--border-color); }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; padding: 1rem; border-bottom: 1px solid var(--border-color); }
th { color: var(--text-muted); text-transform: uppercase; font-size: 0.8rem; }
tbody tr:hover { background-color: rgba(255, 255, 255, 0.05); }
.delete-button {
  background-color: var(--status-stopped);
  color: white;
  font-weight: 700;
  border: none;
  padding: 5px 10px;
  font-size: 12px;
  border-radius: 5px;
  cursor: pointer;
}
</style>
