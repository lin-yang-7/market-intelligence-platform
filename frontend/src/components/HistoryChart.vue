<script setup lang="ts">
import { computed } from 'vue';

import type { HistorySnapshot } from '../types/history';

const props = defineProps<{
  snapshot: HistorySnapshot | null;
}>();

const priceSeries = computed(() =>
  props.snapshot?.series.find((series) => series.name === 'price'),
);
const featureSeries = computed(
  () => props.snapshot?.series.filter((series) => series.type === 'feature') ?? [],
);
const signalSeries = computed(() =>
  props.snapshot?.series.find((series) => series.name === 'signals'),
);
const pricePoints = computed(() =>
  (priceSeries.value?.points ?? []).map((point) => ({
    timestamp: Number(point.timestamp),
    close: Number(point.close),
    volume: Number(point.volume ?? 0),
  })),
);
const signalPoints = computed(() =>
  (signalSeries.value?.points ?? []).map((point) => ({
    timestamp: Number(point.timestamp),
    score: Number(point.score ?? 0),
    type: String(point.type ?? 'signal'),
  })),
);
const maxPrice = computed(() => Math.max(...pricePoints.value.map((point) => point.close), 1));
const minPrice = computed(() => Math.min(...pricePoints.value.map((point) => point.close), 0));
const maxVolume = computed(() => Math.max(...pricePoints.value.map((point) => point.volume), 1));
const priceLine = computed(() =>
  pricePoints.value.map((point, index) => `${x(index)},${priceY(point.close)}`).join(' '),
);

function x(index: number) {
  const count = Math.max(1, pricePoints.value.length - 1);
  return 28 + (index / count) * 432;
}

function priceY(price: number) {
  const range = Math.max(1, maxPrice.value - minPrice.value);
  return 142 - ((price - minPrice.value) / range) * 106;
}

function volumeHeight(volume: number) {
  return Math.max(4, (volume / maxVolume.value) * 48);
}

function featureLine(featureName: string) {
  const series = featureSeries.value.find((item) => item.name === featureName);
  return (series?.points ?? [])
    .map((point, index) => `${x(index)},${156 - (Number(point.value) / 100) * 104}`)
    .join(' ');
}

function signalX(timestamp: number) {
  const index = pricePoints.value.findIndex((point) => point.timestamp >= timestamp);
  return x(index >= 0 ? index : pricePoints.value.length - 1);
}
</script>

<template>
  <svg class="history-chart" viewBox="0 0 500 220" role="img" aria-label="history chart">
    <g opacity="0.45">
      <line v-for="tick in [40, 80, 120, 160]" :key="tick" x1="24" x2="466" :y1="tick" :y2="tick" />
    </g>
    <polyline :points="priceLine" fill="none" stroke="#1f8a70" stroke-width="3" />
    <polyline
      v-if="featureLine('long_inflow_score')"
      :points="featureLine('long_inflow_score')"
      fill="none"
      stroke="#2563eb"
      stroke-width="2"
    />
    <polyline
      v-if="featureLine('momentum_score')"
      :points="featureLine('momentum_score')"
      fill="none"
      stroke="#ca8a04"
      stroke-width="2"
    />
    <g v-for="(point, index) in pricePoints" :key="point.timestamp">
      <rect
        :x="x(index) - 5"
        :y="196 - volumeHeight(point.volume)"
        width="10"
        :height="volumeHeight(point.volume)"
        fill="#7c8a86"
        opacity="0.32"
      />
      <circle :cx="x(index)" :cy="priceY(point.close)" r="3.5" fill="#1f8a70" />
    </g>
    <g v-for="signal in signalPoints" :key="`${signal.timestamp}-${signal.type}`">
      <path
        :d="`M ${signalX(signal.timestamp)} 24 l 7 13 h -14 z`"
        fill="#b42318"
      />
    </g>
    <g class="chart-legend">
      <text x="28" y="214">Price</text>
      <text x="84" y="214">Long inflow</text>
      <text x="176" y="214">Momentum</text>
      <text x="260" y="214">Volume</text>
      <text x="328" y="214">Signals</text>
    </g>
  </svg>
</template>
