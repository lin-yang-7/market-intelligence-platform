export interface HistorySeries {
  name: string;
  type: string;
  points: Record<string, number | string>[];
}

export interface TimelineEvent {
  timestamp: number;
  source: string;
  symbol: string;
  type: string;
  title: string;
  payload: Record<string, number | string | string[]>;
}

export interface HistorySnapshot {
  symbol: string;
  exchange?: string | null;
  interval: string;
  series: HistorySeries[];
  timeline: TimelineEvent[];
}
