<script setup>
import { ref } from 'vue'

defineProps({
  vm: Object
})

const isMenuOpen = ref(false)
</script>

<template>
  <div class="vm-card">
    <div class="card-header">
      <h3>{{ vm.name }}</h3>
      <div class="status-indicators">
        <span v-if="vm.hardware_details && vm.hardware_details.template === 1" class="template-badge">
          TEMPLATE
        </span>
        <span class="status" :class="vm.status">
          {{ vm.status }}
        </span>

        <div class="actions-menu" v-if="!vm.hardware_details.template">
          <button @click.stop="isMenuOpen = !isMenuOpen" class="menu-toggle">⋮</button>
          <div v-if="isMenuOpen" class="dropdown-menu" @mouseleave="isMenuOpen = false">
            <a href="#" @click.stop.prevent="$emit('rename', vm)">Rename VM</a>
            <a href="#" @click.stop.prevent="$emit('delete', vm)" class="delete-option">Delete VM</a>
            </div>
        </div>
      </div>
    </div>
    <div class="card-body" @click="$emit('view', vm)">
      <p><strong>ID:</strong> {{ vm.proxmox_id }}</p>
      <p><strong>Node:</strong> {{ vm.node }}</p>
    </div>
  </div>
</template>

<style scoped>
.vm-card {
  background-color: var(--card-bg, #2a2a2a);
  border: 1px solid var(--border-color, #444);
  border-radius: 8px;
  padding: 1.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative; /* Needed for the dropdown menu positioning */
}
.vm-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color, #444);
  padding-bottom: 1rem;
  margin-bottom: 1rem;
}
.card-header h3 {
  margin: 0;
  color: #fff;
  font-size: 1.1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.card-body {
  cursor: pointer;
}
.card-body p {
  margin: 0.5rem 0;
  color: var(--text-muted, #adb5bd);
}
.status-indicators {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.status {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
  color: white;
  text-transform: uppercase;
}
.status.stopped {
  background-color: var(--status-stopped, #e53935);
}
.status.running {
  background-color: var(--status-running, #43a047);
}
.template-badge {
  background-color: #ffc107; /* gold */
  color: #1a1a1a;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}

/* --- NEW STYLES for the dropdown menu --- */
.actions-menu {
  position: relative;
}
.menu-toggle {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0 0.5rem;
  line-height: 1;
  border-radius: 4px;
}
.menu-toggle:hover {
  background-color: rgba(255,255,255,0.1);
}
.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background-color: #343a40;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 0.5rem 0;
  z-index: 10;
  min-width: 120px;
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.dropdown-menu a {
  display: block;
  padding: 0.5rem 1rem;
  color: var(--text-color);
  text-decoration: none;
}
.dropdown-menu a:hover {
  background-color: var(--accent-color);
  color: var(--bg-dark);
}
.delete-option:hover {
  background-color: var(--status-stopped) !important;
  color: white !important;
}
</style>
