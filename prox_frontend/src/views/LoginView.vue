<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const username = ref('');
const password = ref('');
const error = ref(null);
const router = useRouter();

async function handleLogin() {
  error.value = null;
  try {
    const response = await fetch('/api/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        username: username.value,
        password: password.value,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to log in.');
    }
    
    // Save the token and redirect to the dashboard
    localStorage.setItem('access_token', data.access_token);
    router.push('/'); // Redirect to the main dashboard page

  } catch (e) {
    error.value = e.message;
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-box">
      <h2>Proxmox Control Login</h2>
      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <label for="username">Username</label>
          <input type="text" id="username" v-model="username" required>
        </div>
        <div class="input-group">
          <label for="password">Password</label>
          <input type="password" id="password" v-model="password" required>
        </div>
        <button type="submit">Login</button>
        <div v-if="error" class="error-box">
          <p>{{ error }}</p>
        </div>
        <p class="switch-form">Don't have an account? <RouterLink to="/register">Register here</RouterLink></p>
      </form>
    </div>
  </div>
</template>

<style scoped>
.login-container { display: flex; align-items: center; justify-content: center; min-height: 100vh; background-color: var(--bg-dark); }
.login-box { background-color: var(--bg-light); padding: 2.5rem; border-radius: 8px; border: 1px solid var(--border-color); width: 100%; max-width: 400px; color: var(--text-color); }
h2 { text-align: center; margin-top: 0; color: var(--accent-color); font-family: 'Roboto Mono', monospace; }
.input-group { margin-bottom: 1.5rem; }
label { display: block; margin-bottom: 0.5rem; color: var(--text-muted); }
input { width: 100%; box-sizing: border-box; background-color: var(--bg-dark); color: var(--text-color); border: 1px solid var(--border-color); padding: 12px; border-radius: 5px; font-size: 16px; }
button { width: 100%; background-color: var(--accent-color); color: var(--bg-dark); font-weight: 700; border: none; padding: 12px; font-size: 16px; border-radius: 5px; cursor: pointer; }
.error-box { padding: 1rem; margin-top: 1rem; background-color: #ffebee; color: #c62828; border-radius: 5px; text-align: center; }
/* New style for the link */
.switch-form { text-align: center; margin-top: 1.5rem; font-size: 0.9rem; }
.switch-form a { color: var(--accent-color); text-decoration: none; }
</style>
