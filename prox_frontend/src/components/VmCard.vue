<script setup>
defineProps({
  vm: Object
})
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
      </div>
    </div>
    <div class="card-body">
      <p><strong>ID:</strong> {{ vm.proxmox_id }}</p>
      <p><strong>Node:</strong> {{ vm.node }}</p>
    </div>
  </div>
</template>

<style scoped>
.vm-card { background-color: var(--card-bg, #2a2a2a); border: 1px solid var(--border-color, #444); border-radius: 8px; padding: 1.5rem; transition: transform 0.2s, box-shadow 0.2s; cursor: pointer; }
.vm-card:hover { transform: translateY(-5px); box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2); }
.card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color, #444); padding-bottom: 1rem; margin-bottom: 1rem; }
.card-header h3 { margin: 0; color: #fff; font-size: 1.1rem; }
.card-body p { margin: 0.5rem 0; color: var(--text-muted, #adb5bd); }

/* --- NEW STYLES for the indicators --- */
.status-indicators {
  display: flex;
  align-items: center;
  gap: 8px;
}
.status { padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; color: white; }
.status.stopped { background-color: var(--status-stopped, #e53935); }
.status.running { background-color: var(--status-running, #43a047); }
.template-badge {
  background-color: #ffc107; /* gold */
  color: #1a1a1a;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}
</style>
