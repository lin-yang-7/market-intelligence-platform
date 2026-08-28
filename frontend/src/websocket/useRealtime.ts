import { onBeforeUnmount, ref } from 'vue';

import type { RealtimeEvent, RealtimeStatus } from '../types/realtime';

const DEFAULT_CHANNELS = [
  'market.ticker',
  'ranking.updated',
  'signal.created',
  'alert.triggered',
  'notification.sent',
];

export function useRealtime(subscriptionChannels = DEFAULT_CHANNELS) {
  const status = ref<RealtimeStatus>('idle');
  const channels = ref<string[]>([]);
  const lastEvent = ref<RealtimeEvent | null>(null);
  let socket: WebSocket | null = null;
  let heartbeat: number | undefined;

  function connect() {
    if (socket || typeof WebSocket === 'undefined') {
      return;
    }
    status.value = 'connecting';
    const wsUrl = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8008/v1/ws';
    socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      status.value = 'connected';
      socket?.send(JSON.stringify({ action: 'subscribe', channels: subscriptionChannels }));
      heartbeat = window.setInterval(() => socket?.send('ping'), 30_000);
    };

    socket.onmessage = (message) => {
      if (message.data === 'pong') {
        return;
      }
      const event = JSON.parse(message.data) as RealtimeEvent;
      lastEvent.value = event;
      if (event.event === 'subscribed' && event.channels) {
        channels.value = event.channels;
      }
    };

    socket.onerror = () => {
      status.value = 'error';
    };

    socket.onclose = () => {
      status.value = 'disconnected';
      socket = null;
      if (heartbeat) {
        window.clearInterval(heartbeat);
      }
    };
  }

  onBeforeUnmount(() => {
    if (heartbeat) {
      window.clearInterval(heartbeat);
    }
    socket?.close();
  });

  return {
    channels,
    connect,
    lastEvent,
    status,
  };
}
