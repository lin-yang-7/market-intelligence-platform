export type RealtimeStatus = 'idle' | 'connecting' | 'connected' | 'disconnected' | 'error';

export interface RealtimeEvent {
  event: string;
  timestamp?: number;
  data?: Record<string, unknown>;
  channels?: string[];
  code?: number;
  message?: string;
}

