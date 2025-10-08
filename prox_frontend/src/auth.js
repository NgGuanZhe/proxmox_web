import { reactive } from 'vue';
import { api } from '@/services/apiService';

// This is a reactive object that will be shared across your app
export const userState = reactive({
  user: null,
  isAdmin: false,
  isAuthenticated: !!localStorage.getItem('access_token'),

  async fetchUser() {
    if (!this.isAuthenticated) return;
    try {
      this.user = await api.get('/users/me');
      this.isAdmin = this.user.is_admin;
    } catch (e) {
      this.logout();
    }
  },

  logout() {
    localStorage.removeItem('access_token');
    this.user = null;
    this.isAdmin = false;
    this.isAuthenticated = false;
    // Redirect to login page
    window.location.pathname = '/login';
  }
});
