<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { getAlertCenterData } from '../api/dashboard';
import {
  loadNotificationPreferences,
  saveNotificationPreferences,
  type NotificationPreference,
} from '../api/notification';
import type { AlertRow } from '../types/dashboard';

const alerts = ref<AlertRow[]>([]);
const history = ref<AlertRow[]>([]);
const channel = ref<'sse' | 'websocket'>('sse');
const preferences = ref<NotificationPreference[]>([]);
const activeAlerts = computed(() => alerts.value.filter((alert) => alert.status !== 'disabled'));

function togglePreference(channelName: 'sse' | 'websocket', enabled: boolean) {
  preferences.value = saveNotificationPreferences(
    preferences.value.map((item) =>
      item.channel === channelName ? { ...item, enabled } : item,
    ),
  );
}

onMounted(async () => {
  const data = await getAlertCenterData();
  alerts.value = data.alerts;
  history.value = data.history;
  preferences.value = loadNotificationPreferences();
});
</script>

<template>
  <main class="dashboard-shell">
    <section class="page-grid page-grid--detail">
      <div class="panel">
        <div class="panel__header">
          <h2>Alert Center</h2>
          <span>{{ activeAlerts.length }} active</span>
        </div>
        <div class="rule-builder">
          <select aria-label="Alert type">
            <option>longInflow</option>
            <option>signal</option>
            <option>price</option>
            <option>feature</option>
          </select>
          <input aria-label="Symbol" value="BTCUSDT" />
          <input aria-label="Threshold" type="number" value="90" />
          <select v-model="channel" aria-label="Notification channel">
            <option value="sse">sse</option>
            <option value="websocket">websocket</option>
          </select>
          <button type="button">Create</button>
        </div>
        <div v-for="alert in alerts" :key="alert.alertId" class="alert-row">
          <span :class="['status-dot', `status-${alert.status}`]"></span>
          <div>
            <strong>{{ alert.symbol }}</strong>
            <small>{{ alert.type }} / {{ alert.channel }}</small>
          </div>
          <span>{{ alert.status }}</span>
        </div>
      </div>

      <aside class="panel detail-panel">
        <div class="panel__header">
          <h2>Notification</h2>
          <span>{{ preferences.length }} channels</span>
        </div>
        <div v-for="item in preferences" :key="item.channel" class="setting-row">
          <strong>{{ item.channel }}</strong>
          <input
            type="checkbox"
            :checked="item.enabled"
            :aria-label="`${item.channel} enabled`"
            @change="togglePreference(item.channel, ($event.target as HTMLInputElement).checked)"
          />
        </div>
        <section class="timeline">
          <h3>History</h3>
          <article v-for="item in history" :key="`history-${item.alertId}`">
            <strong>{{ item.symbol }}</strong>
            <p>{{ item.type }} alert delivered through {{ item.channel }}</p>
          </article>
        </section>
      </aside>
    </section>
  </main>
</template>
