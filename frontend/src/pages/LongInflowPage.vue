<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { getLongInflowPageData } from '../api/dashboard';
import type { RankingRow, SignalRow } from '../types/dashboard';

const rankings = ref<RankingRow[]>([]);
const selected = ref<RankingRow | null>(null);
const signals = ref<SignalRow[]>([]);

onMounted(async () => {
  const data = await getLongInflowPageData();
  rankings.value = data.rankings;
  selected.value = data.selected;
  signals.value = data.signals;
});
</script>

<template>
  <main class="dashboard-shell">
    <section class="page-grid page-grid--detail">
      <div class="panel">
        <div class="panel__header">
          <h2>Long Inflow</h2>
          <span>{{ rankings.length }} symbols</span>
        </div>
        <div class="filter-bar" aria-label="Long inflow filters">
          <select aria-label="Timeframe">
            <option>1h</option>
            <option>4h</option>
            <option>24h</option>
          </select>
          <select aria-label="Exchange">
            <option>All exchanges</option>
            <option>Binance</option>
            <option>Bybit</option>
          </select>
          <input aria-label="Minimum score" type="number" min="0" max="100" value="80" />
          <input aria-label="Minimum confidence" type="number" min="0" max="100" value="80" />
        </div>
        <div class="wide-table">
          <div class="wide-table__row wide-table__row--head">
            <span>Rank</span>
            <span>Symbol</span>
            <span>Price</span>
            <span>Inflow</span>
            <span>Score</span>
            <span>Confidence</span>
          </div>
          <button
            v-for="row in rankings"
            :key="row.symbol"
            class="wide-table__row wide-table__row--button"
            type="button"
            @click="selected = row"
          >
            <span class="rank">{{ row.rank }}</span>
            <strong>{{ row.symbol }}</strong>
            <span>${{ row.price.toLocaleString() }}</span>
            <span>${{ (row.inflow / 1_000_000_000).toFixed(1) }}B</span>
            <span>{{ row.score.toFixed(1) }}</span>
            <span>{{ Math.round(row.confidence * 100) }}%</span>
          </button>
        </div>
      </div>

      <aside class="panel detail-panel" v-if="selected">
        <div class="panel__header">
          <h2>{{ selected.symbol }}</h2>
          <span>{{ selected.exchange }}</span>
        </div>
        <div class="score-card">
          <strong>{{ selected.score.toFixed(1) }}</strong>
          <span>Long inflow score</span>
        </div>
        <div class="factor-list">
          <div v-for="reason in selected.reasons" :key="reason">
            <span>{{ reason }}</span>
            <strong>active</strong>
          </div>
        </div>
        <section class="timeline">
          <h3>Signal Timeline</h3>
          <article v-for="signal in signals" :key="signal.signalId">
            <strong>{{ signal.type }}</strong>
            <p>{{ signal.explanation }}</p>
          </article>
        </section>
      </aside>
    </section>
  </main>
</template>
