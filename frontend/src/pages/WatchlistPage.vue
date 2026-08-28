<script setup lang="ts">
import { onMounted, ref } from 'vue';

import {
  loadSavedFilters,
  loadWatchlist,
  removeFilter,
  removeWatchSymbol,
  saveFilter,
  saveWatchSymbol,
} from '../api/watchlist';
import type { SavedFilter, WatchSymbol } from '../types/watchlist';

const symbols = ref<WatchSymbol[]>([]);
const filters = ref<SavedFilter[]>([]);
const newSymbol = ref('SOLUSDT');
const newNote = ref('');
const filterName = ref('High momentum');
const filterScope = ref('ranking');
const filterConditions = ref('price_momentum >= 3, volume_activity >= 70');

function refresh() {
  symbols.value = loadWatchlist();
  filters.value = loadSavedFilters();
}

function addSymbol() {
  symbols.value = saveWatchSymbol(newSymbol.value, 'binance', newNote.value);
  newSymbol.value = '';
  newNote.value = '';
}

function deleteSymbol(symbol: string) {
  symbols.value = removeWatchSymbol(symbol);
}

function addFilter() {
  filters.value = saveFilter(filterName.value, filterScope.value, filterConditions.value);
  filterName.value = '';
}

function deleteFilter(filterId: string) {
  filters.value = removeFilter(filterId);
}

onMounted(refresh);
</script>

<template>
  <main class="dashboard-shell">
    <section class="page-grid page-grid--detail">
      <div class="panel">
        <div class="panel__header">
          <h2>Watchlist</h2>
          <span>{{ symbols.length }} symbols</span>
        </div>
        <div class="filter-bar watchlist-form">
          <input v-model="newSymbol" aria-label="Symbol" />
          <input v-model="newNote" aria-label="Note" placeholder="Note" />
          <button class="primary-action" type="button" @click="addSymbol">Add</button>
        </div>
        <div class="wide-table">
          <div class="wide-table__row wide-table__row--head wide-table__row--watch">
            <span>Symbol</span>
            <span>Exchange</span>
            <span>Note</span>
            <span>Created</span>
            <span>Action</span>
          </div>
          <div v-for="item in symbols" :key="item.symbol" class="wide-table__row wide-table__row--watch">
            <strong>{{ item.symbol }}</strong>
            <span>{{ item.exchange }}</span>
            <span>{{ item.note || '-' }}</span>
            <span>{{ new Date(item.createdAt).toLocaleDateString() }}</span>
            <button type="button" @click="deleteSymbol(item.symbol)">Remove</button>
          </div>
        </div>
      </div>

      <aside class="panel detail-panel">
        <div class="panel__header">
          <h2>Saved Filters</h2>
          <span>{{ filters.length }}</span>
        </div>
        <div class="auth-form saved-filter-form">
          <label>
            <small>Name</small>
            <input v-model="filterName" />
          </label>
          <label>
            <small>Scope</small>
            <select v-model="filterScope">
              <option value="ranking">ranking</option>
              <option value="signal">signal</option>
              <option value="feature">feature</option>
            </select>
          </label>
          <label>
            <small>Conditions</small>
            <input v-model="filterConditions" />
          </label>
          <button class="primary-action" type="button" @click="addFilter">Save</button>
        </div>
        <section class="timeline">
          <article v-for="filter in filters" :key="filter.filterId">
            <strong>{{ filter.name }}</strong>
            <p>{{ filter.scope }} / {{ filter.conditions }}</p>
            <button type="button" @click="deleteFilter(filter.filterId)">Delete</button>
          </article>
        </section>
      </aside>
    </section>
  </main>
</template>
