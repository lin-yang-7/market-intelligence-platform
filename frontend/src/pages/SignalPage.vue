<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { getSignalPageData } from '../api/dashboard';
import type { SignalRow } from '../types/dashboard';
import { useRealtime } from '../websocket/useRealtime';

const signals = ref<SignalRow[]>([]);
const selected = ref<SignalRow | null>(null);
const { connect, lastEvent, status } = useRealtime(['signal.created']);

onMounted(async () => {
  const data = await getSignalPageData();
  signals.value = data.signals;
  selected.value = data.selected;
  connect();
});
</script>

<template>
  <main class="dashboard-shell">
    <section class="page-grid page-grid--detail">
      <div class="panel">
        <div class="panel__header">
          <h2>Signal Center</h2>
          <span>WS {{ status }}</span>
        </div>
        <article
          v-for="signal in signals"
          :key="signal.signalId"
          class="signal signal--button"
          @click="selected = signal"
        >
          <div>
            <strong>{{ signal.symbol }}</strong>
            <span>{{ signal.type }}</span>
          </div>
          <p>{{ signal.explanation }}</p>
          <footer>
            <span>Score {{ signal.score }}</span>
            <span>Confidence {{ Math.round(signal.confidence * 100) }}%</span>
          </footer>
        </article>
      </div>

      <aside class="panel detail-panel" v-if="selected">
        <div class="panel__header">
          <h2>{{ selected.symbol }}</h2>
          <span>{{ selected.type }}</span>
        </div>
        <div class="score-card">
          <strong>{{ Math.round(selected.confidence * 100) }}%</strong>
          <span>Confidence</span>
        </div>
        <section class="timeline">
          <h3>Explanation</h3>
          <article>
            <strong>Summary</strong>
            <p>{{ selected.explanation }}</p>
          </article>
          <article>
            <strong>Realtime</strong>
            <p>{{ lastEvent?.event || 'waiting for signal.created' }}</p>
          </article>
          <article>
            <strong>Risk</strong>
            <p>Signal confidence is directional and should be evaluated with liquidity and volatility context.</p>
          </article>
        </section>
      </aside>
    </section>
  </main>
</template>
