<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { apiBaseUrl, getDashboardSnapshot } from '../api/dashboard';
import AlertPanel from '../components/AlertPanel.vue';
import MarketChart from '../components/MarketChart.vue';
import MetricStrip from '../components/MetricStrip.vue';
import RankingPanel from '../components/RankingPanel.vue';
import SignalFeed from '../components/SignalFeed.vue';
import type { AlertRow, ChartPoint, MarketMetric, RankingRow, SignalRow } from '../types/dashboard';
import { useRealtime } from '../websocket/useRealtime';

const metrics = ref<MarketMetric[]>([]);
const rankings = ref<RankingRow[]>([]);
const signals = ref<SignalRow[]>([]);
const alerts = ref<AlertRow[]>([]);
const chart = ref<ChartPoint[]>([]);
const updatedAt = ref('');
const { channels, connect, lastEvent, status } = useRealtime();

onMounted(async () => {
  const snapshot = await getDashboardSnapshot();
  metrics.value = snapshot.metrics;
  rankings.value = snapshot.rankings;
  signals.value = snapshot.signals;
  alerts.value = snapshot.alerts;
  chart.value = snapshot.chart;
  updatedAt.value = new Date(snapshot.updatedAt).toLocaleTimeString();
  connect();
});
</script>

<template>
  <main class="dashboard-shell">
    <header class="topbar">
      <div>
        <h1>Market Intelligence Platform</h1>
        <p>API Gateway: {{ apiBaseUrl }}</p>
      </div>
      <div class="topbar__meta">
        <span>Updated {{ updatedAt || 'loading' }}</span>
        <span :class="['ws-status', `ws-status--${status}`]">
          WS {{ status }}
        </span>
      </div>
    </header>

    <section class="realtime-strip" aria-label="Realtime status">
      <span>{{ channels.length }} channels subscribed</span>
      <span>Last event: {{ lastEvent?.event || 'none' }}</span>
    </section>

    <MetricStrip :metrics="metrics" />

    <section class="dashboard-grid">
      <MarketChart :points="chart" />
      <RankingPanel :rankings="rankings" />
      <SignalFeed :signals="signals" />
      <AlertPanel :alerts="alerts" />
    </section>
  </main>
</template>
