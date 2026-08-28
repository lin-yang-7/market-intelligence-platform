<script setup lang="ts">
import type { RankingRow } from '../types/dashboard';

defineProps<{
  rankings: RankingRow[];
}>();
</script>

<template>
  <section class="panel ranking-panel" aria-label="Long inflow ranking">
    <div class="panel__header">
      <h2>Long Inflow Ranking</h2>
      <span>Top {{ rankings.length }}</span>
    </div>
    <div class="data-table">
      <div class="data-table__row data-table__row--head">
        <span>#</span>
        <span>Symbol</span>
        <span>Score</span>
        <span>24h</span>
        <span>Volume</span>
      </div>
      <div v-for="row in rankings" :key="row.symbol" class="data-table__row">
        <span class="rank">{{ row.rank }}</span>
        <span>
          <strong>{{ row.symbol }}</strong>
          <small>{{ row.exchange }}</small>
        </span>
        <span>{{ row.score.toFixed(1) }}</span>
        <span class="tone-positive">+{{ row.change24h.toFixed(1) }}%</span>
        <span>${{ (row.volume24h / 1_000_000).toFixed(0) }}M</span>
      </div>
    </div>
  </section>
</template>
