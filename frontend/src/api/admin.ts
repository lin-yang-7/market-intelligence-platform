import type { AdminRoleDefinition, AdminSnapshot, OperationsAnalytics } from '../types/admin';
import type { ApiKeyInfo, Subscription, UsageSummary, UserProfile } from '../types/account';
import { apiBaseUrl } from './dashboard';
import { getStoredSession } from './account';

const ADMIN_API_MODE = import.meta.env.VITE_ADMIN_API_MODE ?? 'auto';

interface ServiceResponse<T> {
  code: number;
  message: string;
  data: T;
}

export async function getAdminSnapshot(): Promise<AdminSnapshot> {
  const session = getStoredSession();
  if (ADMIN_API_MODE !== 'mock' && session?.accessToken && !session.accessToken.startsWith('demo.')) {
    try {
      return await request<AdminSnapshot>('/v1/admin/snapshot', session.accessToken);
    } catch (error) {
      if (!shouldUseFallback(error)) {
        throw error;
      }
    }
  }
  return mockAdminSnapshot();
}

export async function getAdminRoles(): Promise<AdminRoleDefinition[]> {
  const session = getStoredSession();
  if (ADMIN_API_MODE !== 'mock' && session?.accessToken && !session.accessToken.startsWith('demo.')) {
    try {
      return await request<AdminRoleDefinition[]>('/v1/admin/roles', session.accessToken);
    } catch (error) {
      if (!shouldUseFallback(error)) {
        throw error;
      }
    }
  }
  return mockRoles;
}

export async function getAdminOperations(): Promise<OperationsAnalytics> {
  const session = getStoredSession();
  if (ADMIN_API_MODE !== 'mock' && session?.accessToken && !session.accessToken.startsWith('demo.')) {
    return request<OperationsAnalytics>('/v1/admin/operations', session.accessToken);
  }
  return { totalEvents: 0, activeUsers: 0, eventCounts: {}, recentEvents: [] };
}

export async function updateAdminUser(
  userId: string,
  payload: { role?: string; status?: string; plan?: string },
): Promise<UserProfile> {
  const session = getStoredSession();
  if (ADMIN_API_MODE !== 'mock' && session?.accessToken && !session.accessToken.startsWith('demo.')) {
    return await request<UserProfile>(`/v1/admin/users/${encodeURIComponent(userId)}`, session.accessToken, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }
  return {
    ...(mockAdminSnapshot().users.find((row) => row.profile.userId === userId)?.profile ?? {
      userId,
      email: `${userId}@example.com`,
      role: 'user',
      plan: 'free',
      status: 'active',
    }),
    ...payload,
    updatedAt: Date.now(),
  };
}

async function request<T>(path: string, accessToken: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      ...init.headers,
    },
  });
  const payload = (await response.json()) as ServiceResponse<T>;
  if (!response.ok || payload.code !== 0) {
    throw new Error(payload.message || `Request failed with status ${response.status}`);
  }
  return payload.data;
}

const mockRoles: AdminRoleDefinition[] = [
  { role: 'admin', permissions: ['*'] },
  {
    role: 'user',
    permissions: [
      'market.read',
      'ranking.read',
      'signal.read',
      'alert.write',
      'notification.write',
      'billing.read',
    ],
  },
  { role: 'readonly', permissions: ['market.read', 'ranking.read', 'signal.read'] },
];

function shouldUseFallback(error: unknown) {
  return ADMIN_API_MODE === 'auto' && error instanceof TypeError;
}

function mockAdminSnapshot(): AdminSnapshot {
  const users: UserProfile[] = [
    {
      userId: 'usr_admin',
      email: 'admin@example.com',
      role: 'admin',
      plan: 'enterprise',
      status: 'active',
      createdAt: 1700000000000,
      updatedAt: 1700000000000,
    },
    {
      userId: 'usr_demo',
      email: 'demo@example.com',
      role: 'user',
      plan: 'pro',
      status: 'active',
      createdAt: 1700086400000,
      updatedAt: 1700086400000,
    },
    {
      userId: 'usr_free',
      email: 'research@example.com',
      role: 'user',
      plan: 'free',
      status: 'active',
      createdAt: 1700172800000,
      updatedAt: 1700172800000,
    },
  ];
  const subscriptions: Subscription[] = users.map((user) => ({
    subscriptionId: `sub_${user.userId}`,
    userId: user.userId,
    planId: user.plan,
    status: 'active',
    startedAt: user.createdAt ?? Date.now(),
  }));
  const usage: UsageSummary[] = [
    usageRow('usr_admin', 'enterprise', 1_000_000, 62800),
    usageRow('usr_demo', 'pro', 100_000, 18420),
    usageRow('usr_free', 'free', 1000, 620),
  ];
  const apiKeys: ApiKeyInfo[] = [
    {
      keyId: 'key_admin_ops',
      userId: 'usr_admin',
      name: 'Ops Console',
      apiKey: 'ms_live_xxxxxOps',
      scopes: ['*'],
      status: 'active',
      createdAt: 1700000000000,
    },
    {
      keyId: 'key_research',
      userId: 'usr_demo',
      name: 'Research',
      apiKey: 'ms_live_xxxxxResearch',
      scopes: ['market.read', 'ranking.read'],
      status: 'active',
      createdAt: 1700100000000,
    },
  ];
  return {
    metrics: [
      { label: 'users', value: users.length, tone: 'neutral' },
      { label: 'active_users', value: 3, tone: 'positive' },
      { label: 'paid_users', value: 2, tone: 'positive' },
      { label: 'api_requests', value: 81840, tone: 'neutral' },
      { label: 'api_keys', value: apiKeys.length, tone: 'neutral' },
      { label: 'disabled_keys', value: 0, tone: 'warning' },
    ],
    users: users.map((profile) => ({
      profile,
      subscription: subscriptions.find((row) => row.userId === profile.userId),
      usage: usage.find((row) => row.userId === profile.userId),
      apiKeyCount: apiKeys.filter((row) => row.userId === profile.userId).length,
    })),
    apiKeys,
    subscriptions,
    usage,
    auditEvents: [
      {
        actor: 'usr_admin',
        action: 'admin_snapshot',
        resource: 'admin',
        result: 'success',
        timestamp: Date.now() - 120000,
        metadata: {},
      },
      {
        actor: 'usr_demo',
        action: 'create_api_key',
        resource: 'key_research',
        result: 'success',
        timestamp: Date.now() - 3600000,
        metadata: {},
      },
    ],
  };
}

function usageRow(
  userId: string,
  planId: string,
  requestLimit: number,
  apiRequests: number,
): UsageSummary {
  return {
    userId,
    planId,
    periodStart: 1700000000000,
    periodEnd: 1700086400000,
    requestLimit,
    usage: {
      api_requests: apiRequests,
      websocket_connections: Math.round(apiRequests / 100),
      notifications: Math.round(apiRequests / 600),
    },
    remainingRequests: Math.max(0, requestLimit - apiRequests),
  };
}
