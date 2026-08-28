<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';

import {
  getPressureSupport,
  getRankingMonitorHistory,
  getRankingMonitorSnapshots,
  getRankingPageData,
} from '../api/dashboard';
import MarketChart from '../components/MarketChart.vue';
import { useRealtime } from '../websocket/useRealtime';
import type {
  ChartPoint,
  MonitorChangeItem,
  MonitorEventAction,
  MonitorFeedItem,
  MonitorRankingType,
  MonitorSnapshot,
  MonitorStrategyEvent,
  PressureSupportInterpretation,
  RankingRow,
  RankingMonitorHistoryEvent,
} from '../types/dashboard';

type RankingType = 'overall' | 'longInflow' | 'momentum' | 'volume';
type SortKey = 'rank' | 'score' | 'change24h' | 'volume24h';

const activeType = ref<RankingType>('overall');
const sortKey = ref<SortKey>('rank');
const sortDirection = ref<'asc' | 'desc'>('asc');
const page = ref(1);
const pageSize = ref(5);
const selected = ref<RankingRow | null>(null);
const overall = ref<RankingRow[]>([]);
const longInflow = ref<RankingRow[]>([]);
const momentum = ref<RankingRow[]>([]);
const volume = ref<RankingRow[]>([]);
const chart = ref<ChartPoint[]>([]);
const pressureSupport = ref<PressureSupportInterpretation | null>(null);
const monitors = ref<Record<MonitorRankingType, MonitorSnapshot | null>>({
  abnormalBullish: null,
  opportunityBullish: null,
  riskBearish: null,
});
const monitorFeed = ref<MonitorFeedItem[]>([]);
const { connect, lastEvent, status } = useRealtime([
  'ranking.monitor.updated',
  'ranking.entered',
  'ranking.exited',
  'ranking.moved',
  'ranking.strategy',
]);

const rows = computed(() => {
  const source = {
    overall: overall.value,
    longInflow: longInflow.value,
    momentum: momentum.value,
    volume: volume.value,
  };
  return source[activeType.value];
});

const sortedRows = computed(() => {
  const direction = sortDirection.value === 'asc' ? 1 : -1;
  return [...rows.value].sort((left, right) => {
    return (left[sortKey.value] - right[sortKey.value]) * direction;
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(sortedRows.value.length / pageSize.value)));
const pagedRows = computed(() => {
  const start = (page.value - 1) * pageSize.value;
  return sortedRows.value.slice(start, start + pageSize.value);
});

function changeSort(nextKey: SortKey) {
  if (sortKey.value === nextKey) {
    sortDirection.value = sortDirection.value === 'asc' ? 'desc' : 'asc';
  } else {
    sortKey.value = nextKey;
    sortDirection.value = nextKey === 'rank' ? 'asc' : 'desc';
  }
  page.value = 1;
}

function changeType(type: RankingType) {
  activeType.value = type;
  page.value = 1;
  selected.value = null;
}

async function selectRow(row: RankingRow) {
  selected.value = row;
  pressureSupport.value = null;
  pressureSupport.value = await getPressureSupport(row.symbol, row.exchange);
}

const monitorTypes: MonitorRankingType[] = ['abnormalBullish', 'opportunityBullish', 'riskBearish'];
const monitorLabels: Record<MonitorRankingType, string> = {
  abnormalBullish: '异动看涨',
  opportunityBullish: '机会看涨',
  riskBearish: '风险看跌',
};

const monitorTone: Record<MonitorRankingType, string> = {
  abnormalBullish: 'tone-positive',
  opportunityBullish: 'tone-positive',
  riskBearish: 'tone-negative',
};

function pushFeed(
  rankingType: MonitorRankingType,
  action: MonitorEventAction,
  item: MonitorChangeItem,
  timestamp = Date.now(),
) {
  monitorFeed.value = [
    {
      ...item,
      id: `${rankingType}:${action}:${item.symbol}:${timestamp}:${monitorFeed.value.length}`,
      action,
      rankingType,
      timestamp,
    },
    ...monitorFeed.value,
  ].slice(0, 24);
}

function pushStrategyFeed(
  rankingType: MonitorRankingType,
  item: MonitorStrategyEvent,
  timestamp = Date.now(),
) {
  const feedItem: MonitorFeedItem = {
    symbol: item.symbol ?? item.item?.symbol ?? item.event,
    exchange: item.item?.exchange ?? 'binance',
    score: item.item?.score,
    item: item.item ?? undefined,
    id: `${rankingType}:strategy:${item.event}:${item.symbol ?? 'market'}:${timestamp}:${
      monitorFeed.value.length
    }`,
    action: 'strategy',
    rankingType,
    timestamp,
    event: item.event,
    severity: item.severity,
    title: item.title,
    body: item.body,
  };
  monitorFeed.value = [feedItem, ...monitorFeed.value].slice(0, 24);
}

function seedFeed(snapshot: MonitorSnapshot) {
  snapshot.changes.entered.forEach((item) => pushFeed(snapshot.rankingType, 'entered', item));
  snapshot.changes.exited.forEach((item) => pushFeed(snapshot.rankingType, 'exited', item));
  snapshot.changes.moved.forEach((item) => pushFeed(snapshot.rankingType, 'moved', item));
  snapshot.changes.strategyEvents?.forEach((item) => pushStrategyFeed(snapshot.rankingType, item));
}

function seedHistoryFeed(events: RankingMonitorHistoryEvent[]) {
  monitorFeed.value = events.map((event, index) => {
    const isBaseAction = ['entered', 'exited', 'moved'].includes(event.eventAction);
    return {
      symbol: event.symbol,
      exchange: event.exchange,
      fromRank: event.fromRank,
      toRank: event.toRank,
      score: event.score,
      previousScore: event.previousScore,
      scoreChange: event.scoreChange,
      id: `history:${event.rankingType}:${event.eventAction}:${event.symbol}:${event.timestamp}:${index}`,
      action: isBaseAction ? (event.eventAction as MonitorEventAction) : 'strategy',
      rankingType: event.rankingType,
      timestamp: event.timestamp,
      event: isBaseAction ? undefined : event.eventAction,
      severity: event.summary.severity,
      title: event.summary.title,
      body: event.summary.body,
    };
  }).slice(0, 24);
}

function changeText(item: MonitorFeedItem) {
  if (item.action === 'strategy') {
    return item.title ?? item.event ?? '策略事件';
  }
  if (item.action === 'entered') {
    return `上榜 #${item.toRank ?? '-'}`;
  }
  if (item.action === 'exited') {
    return `下榜 #${item.fromRank ?? '-'}`;
  }
  return `排名 ${item.fromRank ?? '-'} → ${item.toRank ?? '-'}`;
}

function statusText(statusValue?: string) {
  if (statusValue === 'entered') return '刚上榜';
  if (statusValue === 'exited') return '已下榜';
  if (statusValue === 'active') return '在榜';
  return '未在榜';
}

function scoreBand(snapshot: MonitorSnapshot) {
  const band = snapshot.summary.scoreBand;
  if (!band) return 'score filter';
  return band.max === null ? `${band.min}+` : `${band.min}-${band.max}`;
}

watch(lastEvent, (event) => {
  if (!event) {
    return;
  }
  if (event.event === 'ranking.monitor.updated') {
    const snapshot = event.data as unknown as MonitorSnapshot;
    monitors.value[snapshot.rankingType] = snapshot;
    return;
  }
  if (!['ranking.entered', 'ranking.exited', 'ranking.moved'].includes(event.event)) {
    if (event.event === 'ranking.strategy') {
      const data = (event.data ?? {}) as unknown as MonitorStrategyEvent & {
        rankingType: MonitorRankingType;
      };
      pushStrategyFeed(data.rankingType, data, event.timestamp ?? Date.now());
    }
    return;
  }
  const data = (event.data ?? {}) as unknown as MonitorChangeItem & {
    rankingType: MonitorRankingType;
  };
  const action = event.event.replace('ranking.', '') as MonitorEventAction;
  pushFeed(data.rankingType, action, data, event.timestamp ?? Date.now());
});

onMounted(async () => {
  const [data, monitorData, historyEvents] = await Promise.all([
    getRankingPageData(),
    getRankingMonitorSnapshots(),
    getRankingMonitorHistory(),
  ]);
  overall.value = data.overall;
  longInflow.value = data.longInflow;
  momentum.value = data.momentum;
  volume.value = data.volume;
  chart.value = data.chart;
  selected.value = data.overall[0];
  if (selected.value) {
    pressureSupport.value = await getPressureSupport(selected.value.symbol, selected.value.exchange);
  }
  seedHistoryFeed(historyEvents);
  monitorData.forEach((snapshot) => {
    monitors.value[snapshot.rankingType] = snapshot;
    if (historyEvents.length === 0) {
      seedFeed(snapshot);
    }
  });
  connect();
});
</script>

<template>
  <main class="dashboard-shell">
    <section class="page-grid page-grid--detail">
      <div class="panel">
        <div class="panel__header">
          <h2>Ranking</h2>
          <span>{{ rows.length }} rows</span>
        </div>
        <div class="tab-bar" role="tablist" aria-label="Ranking type">
          <button
            v-for="type in ['overall', 'longInflow', 'momentum', 'volume']"
            :key="type"
            :class="{ active: activeType === type }"
            type="button"
            @click="changeType(type as RankingType)"
          >
            {{ type }}
          </button>
        </div>
        <div class="filter-bar">
          <select v-model="sortKey" aria-label="Sort key" @change="page = 1">
            <option value="rank">Rank</option>
            <option value="score">Score</option>
            <option value="change24h">24h</option>
            <option value="volume24h">Volume</option>
          </select>
          <select v-model="sortDirection" aria-label="Sort direction" @change="page = 1">
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>
          <select v-model.number="pageSize" aria-label="Page size" @change="page = 1">
            <option :value="5">5 / page</option>
            <option :value="10">10 / page</option>
            <option :value="20">20 / page</option>
          </select>
        </div>
        <div class="wide-table">
          <div class="wide-table__row wide-table__row--head">
            <button type="button" @click="changeSort('rank')">Rank</button>
            <span>Symbol</span>
            <button type="button" @click="changeSort('score')">Score</button>
            <button type="button" @click="changeSort('change24h')">24h</button>
            <button type="button" @click="changeSort('volume24h')">Volume</button>
            <span>Updated</span>
          </div>
          <button
            v-for="row in pagedRows"
            :key="`${activeType}-${row.symbol}`"
            class="wide-table__row wide-table__row--button"
            type="button"
            @click="selectRow(row)"
          >
            <span class="rank">{{ row.rank }}</span>
            <strong>{{ row.symbol }}</strong>
            <span>{{ row.score.toFixed(1) }}</span>
            <span class="tone-positive">+{{ row.change24h.toFixed(1) }}%</span>
            <span>${{ (row.volume24h / 1_000_000).toFixed(0) }}M</span>
            <span>{{ new Date(row.updatedAt).toLocaleTimeString() }}</span>
          </button>
        </div>
        <div class="pagination-bar">
          <button type="button" :disabled="page <= 1" @click="page -= 1">Prev</button>
          <span>{{ page }} / {{ totalPages }}</span>
          <button type="button" :disabled="page >= totalPages" @click="page += 1">Next</button>
        </div>
      </div>

      <aside class="panel detail-panel" v-if="selected">
        <div class="panel__header">
          <h2>{{ selected.symbol }}</h2>
          <span>{{ selected.exchange }}</span>
        </div>
        <div class="score-card">
          <strong>{{ selected.score.toFixed(1) }}</strong>
          <span>Score</span>
        </div>
        <div class="factor-list">
          <div>
            <span>Confidence</span>
            <strong>{{ Math.round(selected.confidence * 100) }}%</strong>
          </div>
          <div>
            <span>24h Change</span>
            <strong>{{ selected.change24h.toFixed(1) }}%</strong>
          </div>
          <div>
            <span>Volume</span>
            <strong>${{ (selected.volume24h / 1_000_000).toFixed(0) }}M</strong>
          </div>
        </div>
        <section class="timeline" v-if="pressureSupport">
          <h3>Pressure / Support</h3>
          <article>
            <strong>{{ pressureSupport.bias }}</strong>
            <p>{{ pressureSupport.guidance }}</p>
          </article>
          <div class="factor-list">
            <div>
              <span>Support</span>
              <strong>{{ pressureSupport.supportLevel.toFixed(4) }}</strong>
            </div>
            <div>
              <span>Resistance</span>
              <strong>{{ pressureSupport.resistanceLevel.toFixed(4) }}</strong>
            </div>
            <div>
              <span>Main force net</span>
              <strong>${{ (pressureSupport.mainForceNetInflow / 1_000_000).toFixed(1) }}M</strong>
            </div>
            <div>
              <span>Ratio</span>
              <strong>{{ pressureSupport.mainForceRatio.toFixed(1) }}%</strong>
            </div>
          </div>
        </section>
        <section class="timeline">
          <h3>Reasons</h3>
          <article v-for="reason in selected.reasons" :key="reason">
            <strong>{{ reason }}</strong>
            <p>{{ selected.symbol }} / {{ activeType }}</p>
          </article>
        </section>
      </aside>

      <MarketChart :points="chart" />

      <section class="panel monitor-panel">
        <div class="panel__header">
          <h2>Monitor</h2>
          <span :class="['ws-status', `ws-status--${status}`]">{{ status }}</span>
        </div>
        <div class="monitor-grid">
          <article
            v-for="type in monitorTypes"
            :key="type"
            class="monitor-card"
          >
            <div class="monitor-card__head">
              <strong>{{ monitorLabels[type] }}</strong>
              <span :class="monitorTone[type]">{{ monitors[type]?.active.length ?? 0 }} active</span>
            </div>
            <div class="monitor-summary">
              <div>
                <span>Score</span>
                <strong>{{ monitors[type] ? scoreBand(monitors[type] as MonitorSnapshot) : '-' }}</strong>
              </div>
              <div>
                <span>Bias</span>
                <strong>{{ monitors[type]?.summary.marketBias ?? '-' }}</strong>
              </div>
              <div v-if="type === 'opportunityBullish'">
                <span>BTC / ETH</span>
                <strong>
                  {{ statusText(monitors[type]?.summary.btcStatus) }} /
                  {{ statusText(monitors[type]?.summary.ethStatus) }}
                </strong>
              </div>
              <div v-if="type === 'riskBearish'">
                <span>Batch risk</span>
                <strong>{{ monitors[type]?.summary.batchRisk ? 'ON' : 'OFF' }}</strong>
              </div>
            </div>
            <p>{{ monitors[type]?.summary.guidance ?? 'Waiting for monitor snapshot.' }}</p>
            <div class="monitor-list">
              <div v-for="item in monitors[type]?.active.slice(0, 5)" :key="`${type}-${item.symbol}`">
                <span class="rank">{{ item.rank }}</span>
                <strong>{{ item.symbol }}</strong>
                <span>{{ item.score.toFixed(1) }}</span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <aside class="panel monitor-feed">
        <div class="panel__header">
          <h2>Monitor Events</h2>
          <span>{{ monitorFeed.length }} events</span>
        </div>
        <article v-for="item in monitorFeed" :key="item.id" class="signal">
          <div>
            <strong>{{ item.symbol }}</strong>
            <span>
              {{ monitorLabels[item.rankingType] }} / {{ changeText(item) }}
            </span>
          </div>
          <p v-if="item.action === 'strategy'">{{ item.body }}</p>
          <footer>
            <span>{{ new Date(item.timestamp).toLocaleTimeString() }}</span>
            <span
              v-if="item.severity"
              :class="[
                'event-severity',
                `event-severity--${item.severity}`,
              ]"
            >
              {{ item.severity }}
            </span>
            <span v-if="item.score">score {{ item.score.toFixed(1) }}</span>
            <span v-if="item.scoreChange">Δ {{ item.scoreChange.toFixed(1) }}</span>
          </footer>
        </article>
      </aside>
    </section>
  </main>
</template>
