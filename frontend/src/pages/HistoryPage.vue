<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { getHistorySnapshot } from '../api/history';
import HistoryChart from '../components/HistoryChart.vue';
import type { HistorySeries, HistorySnapshot } from '../types/history';

const symbol = ref('BTCUSDT');
const snapshot = ref<HistorySnapshot | null>(null);
const errorMessage = ref('');

const priceSeries = computed(() =>
  snapshot.value?.series.find((series) => series.name === 'price'),
);
const featureSeries = computed(
  () => snapshot.value?.series.filter((series) => series.type === 'feature') ?? [],
);
const signalSeries = computed(() =>
  snapshot.value?.series.find((series) => series.name === 'signals'),
);

function latestFeatureValue(series: HistorySeries) {
  const latest = series.points.at(-1);
  return latest ? Number(latest.value).toFixed(1) : '-';
}

async function loadHistory() {
  errorMessage.value = '';
  try {
    snapshot.value = await getHistorySnapshot(symbol.value);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'History request failed';
  }
}

onMounted(loadHistory);
</script>

<template>
  <main class="dashboard-shell">
    <section class="page-grid page-grid--detail">
      <div class="panel chart-panel">
        <div class="panel__header">
          <h2>Historical Analysis</h2>
          <span>{{ snapshot?.interval || '1m' }}</span>
        </div>
        <div class="filter-bar history-filter">
          <input v-model="symbol" aria-label="Symbol" />
          <button class="primary-action" type="button" @click="loadHistory">Load</button>
        </div>
        <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
        <HistoryChart :snapshot="snapshot" />
      </div>

      <aside class="panel detail-panel">
        <div class="panel__header">
          <h2>{{ snapshot?.symbol || symbol }}</h2>
          <span>{{ snapshot?.exchange || 'all' }}</span>
        </div>
        <div class="factor-list">
          <div v-for="series in featureSeries" :key="series.name">
            <span>{{ series.name }}</span>
            <strong>{{ latestFeatureValue(series) }}</strong>
          </div>
          <div>
            <span>Signals</span>
            <strong>{{ signalSeries?.points.length ?? 0 }}</strong>
          </div>
        </div>
        <section class="timeline">
          <h3>Timeline</h3>
          <article v-for="event in snapshot?.timeline ?? []" :key="`${event.source}-${event.timestamp}`">
            <strong>{{ event.title }}</strong>
            <p>{{ event.source }} / {{ event.type }} / {{ new Date(event.timestamp).toLocaleString() }}</p>
          </article>
        </section>
      </aside>
    </section>
  </main>
</template>
