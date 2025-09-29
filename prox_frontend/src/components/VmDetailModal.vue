<script setup>
defineProps({
  vm: Object
})
</script>

<template>
  <div class="modal-overlay" @click="$emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h2>{{ vm.name }}</h2>
        <button class="close-button" @click="$emit('close')">&times;</button>
      </div>
      <div class="modal-body">
        <p><strong>ID:</strong> {{ vm.proxmox_id }}</p>
        <p><strong>Status:</strong> {{ vm.status }}</p>
        <p><strong>Node:</strong> {{ vm.node }}</p>
        <hr>
        <h4 v-if="vm.hardware_details">Hardware Details:</h4>
        <ul v-if="vm.hardware_details">
          <li><strong>CPU:</strong> {{ vm.hardware_details.cpu.sockets }} Socket(s), {{ vm.hardware_details.cpu.cores }} Core(s) ({{ vm.hardware_details.cpu.type }})</li>
          <li><strong>Memory:</strong> {{ vm.hardware_details.memory_mb }} MB</li>
          <li><strong>Boot Order:</strong> {{ vm.hardware_details.boot_order }}</li>
          <li>
            <strong>Disks:</strong>
            <ul>
              <li v-for="disk in vm.hardware_details.disks" :key="disk.device">
                {{ disk.device.toUpperCase() }}: {{ disk.size_gb }}GB on '{{ disk.storage }}' storage
              </li>
            </ul>
          </li>
          <li>
            <strong>Network Interfaces:</strong>
            <ul>
              <li v-for="nic in vm.hardware_details.network_interfaces" :key="nic.device">
                {{ nic.device.toUpperCase() }}: {{ nic.mac_address }} ({{ nic.model }}) on '{{ nic.bridge }}'
              </li>
            </ul>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0, 0, 0, 0.7); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.modal-content { background-color: var(--bg-light); color: var(--text-color); padding: 2rem; border-radius: 8px; border: 1px solid var(--border-color); width: 90%; max-width: 700px; max-height: 90vh; overflow-y: auto; }
.modal-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem; margin-bottom: 1rem; }
.modal-header h2 { margin: 0; color: #fff; }
.close-button { background: none; border: none; color: var(--text-color); font-size: 2.5rem; cursor: pointer; line-height: 1; }
.modal-body ul { list-style-type: none; padding-left: 1rem; }
.modal-body > ul > li { margin-bottom: 0.5rem; }
hr { border-color: var(--border-color); }
</style>
