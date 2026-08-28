export interface WatchSymbol {
  symbol: string;
  exchange: string;
  note: string;
  createdAt: number;
}

export interface SavedFilter {
  filterId: string;
  name: string;
  scope: string;
  conditions: string;
  createdAt: number;
}
