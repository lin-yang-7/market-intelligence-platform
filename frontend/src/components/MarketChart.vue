<script setup lang="ts">
import { computed } from 'vue';

import type { ChartPoint } from '../types/dashboard';

const props = defineProps<{
  points: ChartPoint[];
}>();

const maxPrice = computed(() => Math.max(...props.points.map((point) => point.price), 1));
const minPrice = computed(() => Math.min(...props.points.map((point) => point.price), 0));

function y(price: number) {
  const range = Math.max(1, maxPrice.value - minPrice.value);
  return 150 - ((price - minPrice.value) / range) * 120;
}

const linePoints = computed(() =>
  props.points.map((point, index) => `${index * 92 + 20},${y(point.price)}`).join(' '),
);
</script>

<template>
  <section class="panel chart-panel" aria-label="Market chart">
    <div class="panel__header">
      <h2>BTCUSDT Price / Volume</h2>
      <span>1m</span>
    </div>
    <svg viewBox="0 0 500 190" role="img" aria-label="BTCUSDT price chart">
      <polyline :points="linePoints" fill="none" stroke="#1f8a70" stroke-width="3" />
      <g v-for="(point, index) in points" :key="point.label">
        <rect
          :x="index * 92 + 11"
          :y="170 - point.volume"
          width="18"
          :height="point.volume"
          fill="#9ca3af"
          opacity="0.3"
        />
        <circle :cx="index * 92 + 20" :cy="y(point.price)" r="4" fill="#1f8a70" />
        <text :x="index * 92" y="186">{{ point.label }}</text>
      </g>
    </svg>
  </section>
</template>
