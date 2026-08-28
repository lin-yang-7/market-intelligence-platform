export interface NotificationPreference {
  channel: 'sse' | 'websocket';
  enabled: boolean;
}

const PREF_KEY = 'mip.notification.preferences';

export function loadNotificationPreferences(): NotificationPreference[] {
  const raw = window.localStorage.getItem(PREF_KEY);
  if (!raw) {
    return defaultPreferences;
  }
  try {
    return JSON.parse(raw) as NotificationPreference[];
  } catch {
    window.localStorage.removeItem(PREF_KEY);
    return defaultPreferences;
  }
}

export function saveNotificationPreferences(
  preferences: NotificationPreference[],
): NotificationPreference[] {
  window.localStorage.setItem(PREF_KEY, JSON.stringify(preferences));
  return preferences;
}

const defaultPreferences: NotificationPreference[] = [
  { channel: 'sse', enabled: true },
  { channel: 'websocket', enabled: true },
];
