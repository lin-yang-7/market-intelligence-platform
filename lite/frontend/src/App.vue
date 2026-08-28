<script setup lang="ts">
// Standalone Lite frontend: it only consumes the two display read models.
import { computed, onMounted, onUnmounted, ref } from 'vue';

interface ApiResponse<T> { code: number; message: string; data: T }
interface RankingItem {
  rank: number;
  symbol: string;
  exchange: string;
  score: number;
  confidence: number;
  timestamp: number;
  factors: Record<string, number>;
  modelVersion?: string | null;
  opportunityScore?: number | null;
  riskScore?: number | null;
  riskWarning?: string | null;
}
interface Ticker { symbol: string; price: number; change24h?: number | null; volume24h?: number | null }
interface Row extends RankingItem { price?: number; change24h?: number; volume24h?: number }

const apiBase = import.meta.env.VITE_API_BASE_URL ?? '/api';
const rows = ref<Row[]>([]);
const loading = ref(false);
const error = ref('');
const updatedAt = ref('等待后端数据');
let refreshTimer: ReturnType<typeof setInterval> | undefined;

const bullish = computed(() => rows.value.filter((row) => row.score >= 60).length);
const marketBias = computed(() => {
  const score = rows.value.reduce((total, row) => total + row.score, 0) / Math.max(rows.value.length, 1);
  return score >= 60 ? '偏多' : score <= 40 ? '偏空' : '震荡';
});

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${apiBase}${path}`);
  const payload = await response.json() as ApiResponse<T>;
  if (!response.ok || payload.code !== 0) throw new Error(payload.message || `请求失败 (${response.status})`);
  return payload.data;
}

async function refresh() {
  if (loading.value) return;
  loading.value = true;
  error.value = '';
  try {
    const ranking = await request<RankingItem[]>('/v1/ranking/overall?exchange=binance&limit=50');
    const withTickers = await Promise.all(ranking.map(async (item) => {
      try {
        const ticker = await request<Ticker>(`/v1/market/ticker?exchange=${encodeURIComponent(item.exchange)}&symbol=${encodeURIComponent(item.symbol)}`);
        return { ...item, price: ticker.price, change24h: ticker.change24h ?? 0, volume24h: ticker.volume24h ?? 0 };
      } catch { return item; }
    }));
    rows.value = withTickers;
    updatedAt.value = new Date().toLocaleString('zh-CN');
  } catch (caught) {
    error.value = caught instanceof Error ? caught.message : '读取后端数据失败';
  } finally { loading.value = false; }
}

function direction(row: Row) { return row.score >= 60 ? '看涨' : row.score <= 40 ? '看跌' : '中性'; }
function formatPrice(value?: number) { return value === undefined ? '-' : `$${value.toLocaleString('en-US', { maximumFractionDigits: 6 })}`; }
function formatVolume(value?: number) { return value === undefined ? '-' : value >= 1e9 ? `$${(value / 1e9).toFixed(2)}B` : `$${(value / 1e6).toFixed(1)}M`; }
function explanation(row: Row) {
  const entries = Object.entries(row.factors).sort((left, right) => Math.abs(right[1]) - Math.abs(left[1])).slice(0, 3);
  return entries.map(([name, value]) => `${name}: ${value.toFixed(1)}`).join(' · ') || '等待特征计算';
}

onMounted(() => { refresh(); refreshTimer = setInterval(refresh, 15_000); });
onUnmounted(() => { if (refreshTimer) clearInterval(refreshTimer); });
</script>

<template>
  <main class="lite-shell">
    <header class="lite-header">
      <div>
        <p class="lite-eyebrow">MARKET INTELLIGENCE · LITE</p>
        <h1>市场预测与排行</h1>
        <p>后端持续采集、计算并保存行情与特征；页面只展示平台 API 的实时结果。</p>
      </div>
      <button type="button" :disabled="loading" @click="refresh">{{ loading ? '更新中…' : '刷新' }}</button>
    </header>
    <p v-if="error" class="lite-error">{{ error }}。首次启动后请等待采集和特征计算完成。</p>
    <section class="lite-metrics">
      <article><span>市场判断</span><strong>{{ marketBias }}</strong></article>
      <article><span>看涨候选</span><strong>{{ bullish }} / {{ rows.length }}</strong></article>
      <article><span>排行覆盖</span><strong>Top {{ rows.length }}</strong></article>
      <article><span>更新时间</span><strong>{{ updatedAt }}</strong></article>
    </section>
    <section class="lite-panel">
      <div class="lite-panel__header"><div><h2>综合预测排行</h2><p>评分来自已保存的特征；它是规则/模型评分，不是收益或价格保证。</p></div></div>
      <div class="lite-table" role="table">
        <div class="lite-table__row lite-table__head" role="row"><span>#</span><span>交易对</span><span>价格</span><span>24h</span><span>预测评分</span><span>置信度</span><span>主要依据</span></div>
        <div v-for="row in rows" :key="row.symbol" class="lite-table__row" role="row">
          <span>{{ row.rank }}</span><strong>{{ row.symbol }}</strong><span>{{ formatPrice(row.price) }}</span>
          <span :class="(row.change24h ?? 0) >= 0 ? 'lite-up' : 'lite-down'">{{ row.change24h === undefined ? '-' : `${row.change24h >= 0 ? '+' : ''}${row.change24h.toFixed(2)}%` }}</span>
          <span :class="['lite-direction', `lite-direction--${direction(row)}`]">{{ direction(row) }} {{ row.score.toFixed(1) }}</span>
          <span>{{ Math.round(row.confidence * 100) }}%</span><small>{{ explanation(row) }} · {{ formatVolume(row.volume24h) }}</small>
        </div>
      </div>
    </section>
  </main>
</template>
