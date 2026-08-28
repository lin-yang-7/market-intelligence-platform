import { apiBaseUrl } from './dashboard';
import type { HistorySnapshot } from '../types/history';

interface ServiceResponse<T> {
  code: number;
  message: string;
  data: T;
}

export async function getHistorySnapshot(symbol: string): Promise<HistorySnapshot> {
  const params = new URLSearchParams({
    symbol,
    interval: '1m',
    features: 'long_inflow_score,volume_spike_score,momentum_score',
    limit: '60',
  });
  try {
    const response = await fetch(`${apiBaseUrl}/v1/history/snapshot?${params.toString()}`);
    const payload = (await response.json()) as ServiceResponse<HistorySnapshot>;
    if (!response.ok || payload.code !== 0) {
      throw new Error(payload.message || 'History request failed');
    }
    return payload.data;
  } catch (error) {
    if (error instanceof TypeError) {
      return mockHistorySnapshot(symbol);
    }
    throw error;
  }
}

function mockHistorySnapshot(symbol: string): HistorySnapshot {
  const base = Date.now() - 5 * 60_000;
  const prices = [68100, 68240, 68080, 68420, 68610, 68840];
  const featureValues = [62, 71, 78, 84, 89, 93];
  const momentumValues = [48, 52, 49, 67, 76, 82];
  const volumeValues = [55, 61, 58, 73, 85, 91];
  return {
    symbol: symbol.toUpperCase(),
    exchange: 'binance',
    interval: '1m',
    series: [
      {
        name: 'price',
        type: 'kline',
        points: prices.map((close, index) => ({
          symbol: symbol.toUpperCase(),
          close,
          volume: 50 + index * 8,
          timestamp: base + index * 60_000,
        })),
      },
      {
        name: 'long_inflow_score',
        type: 'feature',
        points: featureValues.map((value, index) => ({
          symbol: symbol.toUpperCase(),
          value,
          timestamp: base + index * 60_000,
        })),
      },
      {
        name: 'momentum_score',
        type: 'feature',
        points: momentumValues.map((value, index) => ({
          symbol: symbol.toUpperCase(),
          value,
          timestamp: base + index * 60_000,
        })),
      },
      {
        name: 'volume_spike_score',
        type: 'feature',
        points: volumeValues.map((value, index) => ({
          symbol: symbol.toUpperCase(),
          value,
          timestamp: base + index * 60_000,
        })),
      },
      {
        name: 'signals',
        type: 'signal',
        points: [
          {
            signalId: 'sig_mock_momentum',
            symbol: symbol.toUpperCase(),
            type: 'momentum',
            score: 82,
            confidence: 0.8,
            timestamp: base + 4 * 60_000,
          },
          {
            signalId: 'sig_mock_history',
            symbol: symbol.toUpperCase(),
            type: 'longInflow',
            score: 91,
            confidence: 0.88,
            timestamp: base + 5 * 60_000,
          },
        ],
      },
    ],
    timeline: [
      {
        timestamp: base + 5 * 60_000,
        source: 'signal',
        symbol: symbol.toUpperCase(),
        type: 'longInflow',
        title: 'longInflow score 91',
        payload: { score: 91, confidence: 0.88 },
      },
      {
        timestamp: base + 4 * 60_000,
        source: 'feature',
        symbol: symbol.toUpperCase(),
        type: 'long_inflow_score',
        title: 'long_inflow_score reached 89',
        payload: { value: 89 },
      },
    ],
  };
}
