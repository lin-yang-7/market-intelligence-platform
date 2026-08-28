import type {
  AlertRow,
  ChartPoint,
  MarketMetric,
  MonitorRankingType,
  MonitorSnapshot,
  RankingMonitorHistoryEvent,
  MonitorChangeItem,
  MonitorStrategyEvent,
  PressureSupportInterpretation,
  RankingRow,
  SignalRow,
} from '../types/dashboard';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const apiBaseUrl = API_BASE_URL;

export async function getDashboardSnapshot() {
  return {
    metrics: mockMetrics,
    rankings: mockRankings,
    signals: mockSignals,
    alerts: mockAlerts,
    chart: mockChart,
    updatedAt: Date.now(),
  };
}

export async function getLongInflowPageData() {
  return {
    rankings: mockRankings,
    selected: mockRankings[0],
    signals: mockSignals.filter((signal) => signal.type === 'longInflow'),
    updatedAt: Date.now(),
  };
}

export async function getRankingPageData() {
  return {
    overall: mockRankings,
    longInflow: mockRankings,
    momentum: [...mockRankings].sort((left, right) => right.change24h - left.change24h),
    volume: [...mockRankings].sort((left, right) => right.volume24h - left.volume24h),
    chart: mockChart,
    updatedAt: Date.now(),
  };
}

interface ServiceResponse<T> {
  code: number;
  message: string;
  data: T;
}

export async function getRankingMonitorSnapshot(
  rankingType: MonitorRankingType,
): Promise<MonitorSnapshot> {
  if ((import.meta.env.VITE_RANKING_MONITOR_MODE ?? 'auto') !== 'mock') {
    try {
      const response = await fetch(
        `${API_BASE_URL}/v1/ranking/monitor/${rankingType}?exchange=binance&limit=50`,
        { method: 'POST' },
      );
      const payload = (await response.json()) as ServiceResponse<MonitorSnapshot>;
      if (!response.ok || payload.code !== 0) {
        throw new Error(payload.message || `Request failed with status ${response.status}`);
      }
      return payload.data;
    } catch (error) {
      if (!(error instanceof TypeError)) {
        throw error;
      }
    }
  }
  return mockMonitorSnapshots[rankingType];
}

export async function getRankingMonitorSnapshots(): Promise<MonitorSnapshot[]> {
  return await Promise.all(
    (['abnormalBullish', 'opportunityBullish', 'riskBearish'] as MonitorRankingType[]).map(
      getRankingMonitorSnapshot,
    ),
  );
}

export async function getRankingMonitorHistory(limit = 24): Promise<RankingMonitorHistoryEvent[]> {
  if ((import.meta.env.VITE_RANKING_MONITOR_MODE ?? 'auto') !== 'mock') {
    try {
      const params = new URLSearchParams({ limit: String(limit) });
      const response = await fetch(`${API_BASE_URL}/v1/history/ranking-monitor/events?${params}`);
      const payload = (await response.json()) as ServiceResponse<RankingMonitorHistoryEvent[]>;
      if (!response.ok || payload.code !== 0) {
        throw new Error(payload.message || `Request failed with status ${response.status}`);
      }
      return payload.data;
    } catch (error) {
      if (!(error instanceof TypeError)) {
        throw error;
      }
    }
  }
  return Object.values(mockMonitorSnapshots)
    .flatMap((snapshot) => [
      ...snapshot.changes.entered.map((item) => monitorHistoryEvent(snapshot, 'entered', item)),
      ...snapshot.changes.exited.map((item) => monitorHistoryEvent(snapshot, 'exited', item)),
      ...snapshot.changes.moved.map((item) => monitorHistoryEvent(snapshot, 'moved', item)),
      ...snapshot.changes.strategyEvents.map((item) =>
        monitorHistoryEvent(snapshot, item.event, {
          symbol: item.symbol ?? item.item?.symbol ?? item.event,
          exchange: item.item?.exchange ?? snapshot.exchange ?? 'binance',
          score: item.item?.score ?? 0,
        }, item),
      ),
    ])
    .sort((left, right) => right.timestamp - left.timestamp)
    .slice(0, limit);
}

export async function getPressureSupport(
  symbol: string,
  exchange = 'binance',
): Promise<PressureSupportInterpretation> {
  if ((import.meta.env.VITE_PRESSURE_SUPPORT_MODE ?? 'auto') !== 'mock') {
    try {
      const params = new URLSearchParams({ symbol, exchange });
      const response = await fetch(`${API_BASE_URL}/v1/feature/pressure-support?${params}`);
      const payload = (await response.json()) as ServiceResponse<PressureSupportInterpretation>;
      if (!response.ok || payload.code !== 0) {
        throw new Error(payload.message || `Request failed with status ${response.status}`);
      }
      return payload.data;
    } catch (error) {
      if (!(error instanceof TypeError)) {
        throw error;
      }
    }
  }
  const row = mockRankings.find((item) => item.symbol === symbol);
  const price = row?.price ?? 100;
  const bias = (row?.change24h ?? 0) >= 0 ? 'supportive' : 'pressure';
  const ratio = bias === 'supportive' ? 24 : 26;
  return {
    symbol,
    exchange,
    price,
    supportLevel: bias === 'supportive' ? price * 0.76 : price * 0.87,
    resistanceLevel: bias === 'supportive' ? price * 1.12 : price * 1.26,
    mainForceNetInflow: bias === 'supportive' ? 60_000_000 : -45_000_000,
    mainForceRatio: ratio,
    bias,
    guidance:
      bias === 'supportive'
        ? 'Main-force net inflow is positive; use support as defensive zone.'
        : 'Main-force outflow is active; resistance is the pressure zone.',
    timestamp: Date.now(),
  };
}

export async function getSignalPageData() {
  return {
    signals: mockSignals,
    selected: mockSignals[0],
    updatedAt: Date.now(),
  };
}

export async function getAlertCenterData() {
  return {
    alerts: mockAlerts,
    history: mockAlerts.filter((alert) => alert.status === 'triggered'),
    updatedAt: Date.now(),
  };
}

const mockMetrics: MarketMetric[] = [
  { label: 'Market Bias', value: 'Risk-On', change: '+6.4%', tone: 'positive' },
  { label: '24h Volume', value: '$128.4B', change: '+11.8%', tone: 'positive' },
  { label: 'Long Inflow', value: '$42.1B', change: '+18.2%', tone: 'positive' },
  { label: 'Volatility', value: 'Medium', change: '-3.1%', tone: 'neutral' },
];

const mockRankings: RankingRow[] = [
  {
    rank: 1,
    symbol: 'BTCUSDT',
    exchange: 'binance',
    price: 68880,
    inflow: 42_100_000_000,
    score: 96.4,
    confidence: 0.94,
    change24h: 4.8,
    volume24h: 300_000_000,
    reasons: ['high_inflow', 'volume_breakout', 'positive_momentum'],
    updatedAt: 1700000080000,
  },
  {
    rank: 2,
    symbol: 'ETHUSDT',
    exchange: 'binance',
    price: 3860,
    inflow: 21_700_000_000,
    score: 91.2,
    confidence: 0.9,
    change24h: 3.1,
    volume24h: 180_000_000,
    reasons: ['volume_breakout', 'positive_momentum'],
    updatedAt: 1700000074000,
  },
  {
    rank: 3,
    symbol: 'SOLUSDT',
    exchange: 'bybit',
    price: 182,
    inflow: 8_900_000_000,
    score: 87.6,
    confidence: 0.85,
    change24h: 6.3,
    volume24h: 94_000_000,
    reasons: ['positive_momentum'],
    updatedAt: 1700000069000,
  },
];

const mockSignals: SignalRow[] = [
  {
    signalId: 'sig_btc_long',
    symbol: 'BTCUSDT',
    type: 'longInflow',
    score: 96,
    confidence: 0.94,
    explanation: 'longInflow signal created: high_inflow, volume_breakout, positive_momentum',
    timestamp: 1700000060000,
  },
  {
    signalId: 'sig_eth_momentum',
    symbol: 'ETHUSDT',
    type: 'momentum',
    score: 89,
    confidence: 0.86,
    explanation: 'momentum signal created: volume_breakout, positive_momentum',
    timestamp: 1700000040000,
  },
];

const mockAlerts: AlertRow[] = [
  { alertId: 'alert_btc_long', symbol: 'BTCUSDT', type: 'longInflow', channel: 'sse', status: 'triggered' },
  { alertId: 'alert_eth_signal', symbol: 'ETHUSDT', type: 'signal', channel: 'websocket', status: 'active' },
  { alertId: 'alert_sol_volume', symbol: 'SOLUSDT', type: 'ranking', channel: 'sse', status: 'active' },
];

const mockChart: ChartPoint[] = [
  { label: '09:30', price: 67200, volume: 48 },
  { label: '10:00', price: 67640, volume: 62 },
  { label: '10:30', price: 68120, volume: 71 },
  { label: '11:00', price: 67980, volume: 58 },
  { label: '11:30', price: 68450, volume: 83 },
  { label: '12:00', price: 68880, volume: 91 },
];

const mockMonitorSnapshots: Record<MonitorRankingType, MonitorSnapshot> = {
  abnormalBullish: {
    rankingType: 'abnormalBullish',
    exchange: 'binance',
    updatedAt: Date.now(),
    active: [
      monitorItem(1, 'SOLUSDT', 88.4, 0.86, {
        price_momentum: 6.3,
        volume_activity: 94,
        long_inflow_score: 72,
      }),
      monitorItem(2, 'LINKUSDT', 81.2, 0.8, {
        price_momentum: 5.2,
        volume_activity: 78,
        long_inflow_score: 66,
      }),
    ],
    changes: {
      entered: [{ symbol: 'SOLUSDT', exchange: 'binance', toRank: 1, score: 88.4 }],
      exited: [],
      moved: [],
      strategyEvents: [
        {
          event: 'first_abnormal',
          severity: 'info',
          title: 'SOLUSDT first abnormal bullish entry',
          body: 'First abnormal bullish entry; track whether main-force inflow continues.',
          symbol: 'SOLUSDT',
          metadata: { rankingType: 'abnormalBullish' },
        },
      ],
    },
    summary: {
      activeCount: 2,
      enteredCount: 1,
      exitedCount: 0,
      scoreBand: { min: 55, max: null },
      guidance: 'First abnormal entries are high-attention candidates.',
      fomoSymbols: [],
    },
  },
  opportunityBullish: {
    rankingType: 'opportunityBullish',
    exchange: 'binance',
    updatedAt: Date.now(),
    active: [
      monitorItem(1, 'BTCUSDT', 72.5, 0.93, {
        price_momentum: 5,
        volume_activity: 100,
        long_inflow_score: 80,
      }),
      monitorItem(2, 'ETHUSDT', 68.7, 0.9, {
        price_momentum: 4.2,
        volume_activity: 86,
        long_inflow_score: 74,
      }),
    ],
    changes: {
      entered: [{ symbol: 'BTCUSDT', exchange: 'binance', toRank: 1, score: 72.5 }],
      exited: [],
      moved: [{ symbol: 'ETHUSDT', exchange: 'binance', fromRank: 3, toRank: 2, scoreChange: 4.1 }],
      strategyEvents: [
        {
          event: 'market_trend_up',
          severity: 'info',
          title: 'BTCUSDT entered opportunity bullish',
          body: 'BTC entered the opportunity monitor; market trend is treated as bullish.',
          symbol: 'BTCUSDT',
          metadata: { rankingType: 'opportunityBullish' },
        },
      ],
    },
    summary: {
      activeCount: 2,
      enteredCount: 1,
      exitedCount: 0,
      scoreBand: { min: 55, max: 80 },
      btcStatus: 'entered',
      ethStatus: 'active',
      marketBias: 'uptrend',
      guidance: 'BTC is in the opportunity monitor; treat the market as bullish trend.',
      selectionRule: 'Prefer opportunity candidates in the 55-80 score band.',
    },
  },
  riskBearish: {
    rankingType: 'riskBearish',
    exchange: 'binance',
    updatedAt: Date.now(),
    active: [
      monitorItem(1, 'DOGEUSDT', 76.2, 0.74, {
        price_momentum: -7.8,
        volume_activity: 88,
        long_inflow_score: 14,
      }),
    ],
    changes: {
      entered: [{ symbol: 'DOGEUSDT', exchange: 'binance', toRank: 1, score: 76.2 }],
      exited: [{ symbol: 'ADAUSDT', exchange: 'binance', fromRank: 5, previousScore: 57.1 }],
      moved: [],
      strategyEvents: [
        {
          event: 'tracking_ended',
          severity: 'info',
          title: 'ADAUSDT tracking ended',
          body: 'Symbol left the monitor; the tracked condition is no longer active.',
          symbol: 'ADAUSDT',
          metadata: { rankingType: 'riskBearish' },
        },
      ],
    },
    summary: {
      activeCount: 1,
      enteredCount: 1,
      exitedCount: 1,
      scoreBand: { min: 55, max: null },
      batchRisk: false,
      marketBias: 'localized_risk',
      guidance: 'Risk bearish monitor is active; review held positions.',
    },
  },
};

function monitorItem(
  rank: number,
  symbol: string,
  score: number,
  confidence: number,
  factors: Record<string, number>,
) {
  return {
    rank,
    symbol,
    exchange: 'binance',
    score,
    confidence,
    timestamp: Date.now(),
    factors,
    strategyState: score >= 80 ? 'fomo_watch' : 'steady_trend_candidate',
    signalColor: score >= 80 ? 'orange' : 'green',
    reasonTags: Object.keys(factors),
    guidance: 'Monitor candidate generated from mock factors.',
  };
}

function monitorHistoryEvent(
  snapshot: MonitorSnapshot,
  eventAction: string,
  item: MonitorChangeItem,
  strategy?: MonitorStrategyEvent,
): RankingMonitorHistoryEvent {
  return {
    exchange: item.exchange ?? snapshot.exchange ?? 'binance',
    symbol: item.symbol,
    rankingType: snapshot.rankingType,
    eventAction,
    fromRank: item.fromRank ?? 0,
    toRank: item.toRank ?? 0,
    score: item.score ?? item.item?.score ?? 0,
    previousScore: item.previousScore ?? 0,
    scoreChange: item.scoreChange ?? 0,
    marketBias: snapshot.summary.marketBias ?? '',
    summary: {
      ...snapshot.summary,
      event: strategy?.event,
      severity: strategy?.severity,
      title: strategy?.title,
      body: strategy?.body,
    },
    timestamp: snapshot.updatedAt,
  };
}
