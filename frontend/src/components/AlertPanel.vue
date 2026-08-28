<script setup lang="ts">
import type { AlertRow } from '../types/dashboard';

defineProps<{
  alerts: AlertRow[];
}>();
</script>

<template>
  <section class="panel alert-panel" aria-label="Alert panel">
    <div class="panel__header">
      <h2>Alerts</h2>
      <span>{{ alerts.length }} rules</span>
    </div>
    <div v-for="alert in alerts" :key="alert.alertId" class="alert-row">
      <span :class="['status-dot', `status-${alert.status}`]"></span>
      <div>
        <strong>{{ alert.symbol }}</strong>
        <small>{{ alert.type }} / {{ alert.channel }}</small>
      </div>
      <span>{{ alert.status }}</span>
    </div>
  </section>
</template>
