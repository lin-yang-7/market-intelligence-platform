<script setup lang="ts">
import type { SignalRow } from '../types/dashboard';

defineProps<{
  signals: SignalRow[];
}>();
</script>

<template>
  <section class="panel signal-feed" aria-label="Signal feed">
    <div class="panel__header">
      <h2>Signal Feed</h2>
      <span>Live</span>
    </div>
    <article v-for="signal in signals" :key="signal.signalId" class="signal">
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
  </section>
</template>
