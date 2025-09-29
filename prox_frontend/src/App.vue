<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-layout">
    <nav class="sidebar">
      <div class="sidebar-header">
        <h2>Proxmox Control</h2>
      </div>
      <ul class="nav-links">
        <li>
          <RouterLink to="/">
            <span class="icon">🖥️</span>
            <span class="text">VM Dashboard</span>
          </RouterLink>
        </li>
        <li>
          <RouterLink to="/clone">
            <span class="icon">🐑</span>
            <span class="text">Clone Templates</span>
          </RouterLink>
        </li>
        <li>
          <RouterLink to="/snapshots">
            <span class="icon">📸</span>
            <span class="text">Snapshot Manager</span>
          </RouterLink>
        </li>
      </ul>
    </nav>

    <div class="main-content">
      <RouterView />
    </div>
  </div>
</template>

<style>
/* Global styles */
@import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;700&display=swap');
:root {
  --bg-dark: #212529;
  --bg-light: #282c34;
  --border-color: #495057;
  --text-color: #f8f9fa;
  --text-muted: #adb5bd;
  --accent-color: #00c9a7;
  --accent-hover: #00a286;
  --status-stopped: #e53935;
  --status-running: #43a047;
}
body { background-color: var(--bg-dark); color: var(--text-color); font-family: 'Roboto Mono', monospace; margin: 0; }
</style>

<style scoped>
/* Scoped styles */
.app-layout { display: flex; align-items: flex-start; gap: 2.5rem; padding: 1.5rem; }
.sidebar { width: 250px; background-color: var(--bg-light); border: 1px solid var(--border-color); border-radius: 8px; padding: 1.5rem 1rem; box-sizing: border-box; position: sticky; top: 1.5rem; }
.sidebar-header h2 { margin: 0 0 2.5rem 0; color: #fff; text-align: center; font-weight: 700; letter-spacing: 1px; }
.nav-links { list-style-type: none; padding: 0; margin: 0; }
.nav-links li a { display: flex; align-items: center; gap: 12px; color: var(--text-muted); text-decoration: none; padding: 0.8rem 1rem; border-radius: 6px; margin-bottom: 0.5rem; transition: background-color 0.2s, color 0.2s; border-left: 4px solid transparent; }
.nav-links li a:hover { background-color: #343a40; color: white; }
.nav-links li a.router-link-exact-active { background-color: rgba(0, 201, 167, 0.1); color: var(--accent-color); font-weight: 700; border-left-color: var(--accent-color); }
.main-content { flex-grow: 1; }
</style>
