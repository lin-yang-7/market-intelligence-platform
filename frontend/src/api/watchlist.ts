import type { SavedFilter, WatchSymbol } from '../types/watchlist';

const WATCHLIST_KEY = 'mip.watchlist';
const FILTERS_KEY = 'mip.saved.filters';

export function loadWatchlist(): WatchSymbol[] {
  return readJson<WatchSymbol[]>(WATCHLIST_KEY, defaultWatchlist);
}

export function saveWatchSymbol(symbol: string, exchange = 'binance', note = ''): WatchSymbol[] {
  const rows = loadWatchlist();
  const normalized = symbol.trim().toUpperCase();
  if (!normalized) {
    return rows;
  }
  const next = [
    {
      symbol: normalized,
      exchange: exchange.trim().toLowerCase() || 'binance',
      note,
      createdAt: Date.now(),
    },
    ...rows.filter((row) => row.symbol !== normalized),
  ];
  writeJson(WATCHLIST_KEY, next);
  return next;
}

export function removeWatchSymbol(symbol: string): WatchSymbol[] {
  const next = loadWatchlist().filter((row) => row.symbol !== symbol);
  writeJson(WATCHLIST_KEY, next);
  return next;
}

export function loadSavedFilters(): SavedFilter[] {
  return readJson<SavedFilter[]>(FILTERS_KEY, defaultFilters);
}

export function saveFilter(name: string, scope: string, conditions: string): SavedFilter[] {
  const rows = loadSavedFilters();
  const normalizedName = name.trim();
  if (!normalizedName) {
    return rows;
  }
  const next = [
    {
      filterId: `filter_${Date.now()}`,
      name: normalizedName,
      scope,
      conditions,
      createdAt: Date.now(),
    },
    ...rows,
  ];
  writeJson(FILTERS_KEY, next);
  return next;
}

export function removeFilter(filterId: string): SavedFilter[] {
  const next = loadSavedFilters().filter((row) => row.filterId !== filterId);
  writeJson(FILTERS_KEY, next);
  return next;
}

function readJson<T>(key: string, fallback: T): T {
  const raw = window.localStorage.getItem(key);
  if (!raw) {
    return fallback;
  }
  try {
    return JSON.parse(raw) as T;
  } catch {
    window.localStorage.removeItem(key);
    return fallback;
  }
}

function writeJson<T>(key: string, value: T) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

const defaultWatchlist: WatchSymbol[] = [
  { symbol: 'BTCUSDT', exchange: 'binance', note: 'Core market benchmark', createdAt: 1700000000000 },
  { symbol: 'ETHUSDT', exchange: 'binance', note: 'High liquidity alt', createdAt: 1700000000000 },
];

const defaultFilters: SavedFilter[] = [
  {
    filterId: 'filter_long_inflow',
    name: 'Long inflow >= 80',
    scope: 'ranking',
    conditions: 'long_inflow_score >= 80, volume_activity >= 70',
    createdAt: 1700000000000,
  },
];
