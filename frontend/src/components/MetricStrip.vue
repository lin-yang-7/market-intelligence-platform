<script setup lang="ts">
import type { MarketMetric } from '../types/dashboard';

defineProps<{
  metrics: MarketMetric[];
}>();
</script>

<template>
  <section class="metric-strip" aria-label="Market summary">
    <article v-for="metric in metrics" :key="metric.label" class="metric">
      <span class="metric__label">{{ metric.label }}</span>
      <strong class="metric__value">{{ metric.value }}</strong>
      <span :class="['metric__change', `tone-${metric.tone}`]">{{ metric.change }}</span>
    </article>
  </section>
</template>
