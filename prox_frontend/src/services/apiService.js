import router from '@/router';

const API_BASE_URL = '/api'; // All our API calls start with /api

// This is our central function for all API requests
async function request(endpoint, options = {}) {
  const token = localStorage.getItem('access_token');
  
  // Prepare headers
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // If a token exists, add the Authorization header
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle authentication errors globally
  if (response.status === 401) {
    localStorage.removeItem('access_token');
    router.push('/login'); // Redirect to login
    throw new Error('Session expired. Please log in again.');
  }
  
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || `HTTP error! status: ${response.status}`);
  }
  
  return data;
}

// Create a simple API object with methods for get, post, put, delete
export const api = {
  get: (endpoint) => request(endpoint),
  post: (endpoint, body) => request(endpoint, { method: 'POST', body: JSON.stringify(body) }),
  put: (endpoint, body) => request(endpoint, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (endpoint) => request(endpoint, { method: 'DELETE' }),
};
