<script setup>
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { api } from '@/services/apiService';

const username = ref('');
const password = ref('');
const error = ref(null);
const success = ref(null);
const router = useRouter();

const passwordRequirements = computed(() => {
  const p = password.value;
  return {
    length: p.length >= 8,
    lowercase: /[a-z]/.test(p),
    uppercase: /[A-Z]/.test(p),
    number: /\d/.test(p),
    symbol: /[\W_]/.test(p),
  };
});
const isPasswordValid = computed(() => {
  return Object.values(passwordRequirements.value).every(Boolean);
});

async function handleRegister() {
  error.value = null;
  success.value = null;
  try {
    await api.post('/users/', {
      username: username.value,
      password: password.value,
    });
    success.value = "Registration successful! You can now log in.";
    setTimeout(() => {
      router.push('/login');
    }, 2000);
  } catch (e) {
    error.value = e.message;
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-box">
      <h2>Register New User</h2>
      <form @submit.prevent="handleRegister">
        <div class="input-group">
          <label for="username">Username</label>
          <input type="text" id="username" v-model="username" required>
        </div>
        <div class="input-group">
          <label for="password">Password</label>
          <input type="password" id="password" v-model="password" required>
        </div>
        <button type="submit">Register</button>
        <div v-if="error" class="error-box"><p>{{ error }}</p></div>
        <div v-if="success" class="success-box"><p>{{ success }}</p></div>
        <p class="switch-form">Already have an account? <RouterLink to="/login">Login</RouterLink></p>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* (You can reuse the same styles as LoginView.vue) */
.success-box { padding: 1rem; margin-top: 1rem; background-color: #e8f5e9; color: #2e7d32; border-radius: 5px; text-align: center; }
.requirements {
  list-style: none;
  padding: 0;
  margin: -0.5rem 0 1.5rem 0;
  font-size: 0.8rem;
  color: var(--text-muted);
}
.requirements li {
  transition: color 0.3s;
}
.requirements li::before {
  content: '❌ ';
  margin-right: 0.5em;
}
.requirements li.met {
  color: var(--status-running);
  text-decoration: line-through;
}
.requirements li.met::before {
  content: '✅ ';
}
</style>
