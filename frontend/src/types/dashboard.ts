export interface MarketMetric {
  label: string;
  value: string;
  change: string;
  tone: 'positive' | 'negative' | 'neutral';
}

export interface RankingRow {
  rank: number;
  symbol: string;
  exchange: string;
  price: number;
  inflow: number;
  score: number;
  confidence: number;
  change24h: number;
  volume24h: number;
  reasons: string[];
  updatedAt: number;
}

export type MonitorRankingType = 'abnormalBullish' | 'opportunityBullish' | 'riskBearish';
export type MonitorEventAction = 'entered' | 'exited' | 'moved' | 'strategy';

export interface MonitorRankingItem {
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
  strategyState?: string | null;
  signalColor?: string | null;
  reasonTags?: string[];
  guidance?: string | null;
}

export interface MonitorChangeItem {
  symbol: string;
  exchange: string;
  fromRank?: number;
  toRank?: number;
  score?: number;
  previousScore?: number;
  scoreChange?: number;
  item?: MonitorRankingItem;
}

export interface MonitorChanges {
  entered: MonitorChangeItem[];
  exited: MonitorChangeItem[];
  moved: MonitorChangeItem[];
  strategyEvents: MonitorStrategyEvent[];
}

export interface MonitorStrategyEvent {
  event: string;
  severity: 'info' | 'warning' | 'critical' | string;
  title: string;
  body: string;
  symbol?: string | null;
  item?: MonitorRankingItem | null;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface RankingMonitorHistoryEvent {
  exchange: string;
  symbol: string;
  rankingType: MonitorRankingType;
  eventAction: string;
  fromRank: number;
  toRank: number;
  score: number;
  previousScore: number;
  scoreChange: number;
  marketBias: string;
  summary: {
    event?: string;
    severity?: string;
    title?: string;
    body?: string;
    [key: string]: unknown;
  };
  timestamp: number;
}

export interface MonitorSummary {
  activeCount?: number;
  enteredCount?: number;
  exitedCount?: number;
  scoreBand?: {
    min: number;
    max: number | null;
  };
  btcStatus?: string;
  ethStatus?: string;
  marketBias?: string;
  guidance?: string;
  selectionRule?: string;
  riskNote?: string | null;
  batchRisk?: boolean;
  fomoSymbols?: string[];
}

export interface MonitorSnapshot {
  rankingType: MonitorRankingType;
  exchange: string | null;
  updatedAt: number;
  active: MonitorRankingItem[];
  changes: MonitorChanges;
  summary: MonitorSummary;
}

export interface MonitorFeedItem extends MonitorChangeItem {
  id: string;
  action: MonitorEventAction;
  rankingType: MonitorRankingType;
  timestamp: number;
  event?: string;
  severity?: string;
  title?: string;
  body?: string;
}

export interface PressureSupportInterpretation {
  symbol: string;
  exchange: string;
  price: number;
  supportLevel: number;
  resistanceLevel: number;
  mainForceNetInflow: number;
  mainForceRatio: number;
  bias: 'supportive' | 'pressure' | 'neutral' | string;
  guidance: string;
  timestamp: number;
}

export interface SignalRow {
  signalId: string;
  symbol: string;
  type: string;
  score: number;
  confidence: number;
  explanation: string;
  timestamp: number;
}

export interface AlertRow {
  alertId: string;
  symbol: string;
  type: string;
  channel: string;
  status: 'active' | 'triggered' | 'disabled';
}

export interface ChartPoint {
  label: string;
  price: number;
  volume: number;
}
