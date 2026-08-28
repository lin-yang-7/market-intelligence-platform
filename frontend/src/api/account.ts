import type {
  AccountSnapshot,
  ApiKeyInfo,
  AuthPayload,
  AuthSession,
  Plan,
  Subscription,
  UsageSummary,
  UserProfile,
} from '../types/account';
import { apiBaseUrl } from './dashboard';

const SESSION_KEY = 'mip.auth.session';
const ACCOUNT_API_MODE = import.meta.env.VITE_ACCOUNT_API_MODE ?? 'auto';

interface ServiceResponse<T> {
  code: number;
  message: string;
  data: T;
}

export async function getAccountSnapshot(): Promise<AccountSnapshot> {
  const session = getStoredSession();
  if (ACCOUNT_API_MODE !== 'mock' && session?.accessToken) {
    try {
      const [profile, plans, apiKeys, usage, subscription] = await Promise.all([
        request<UserProfile>('/v1/user/profile', undefined, session.accessToken),
        request<Plan[]>('/v1/user/plans', undefined, session.accessToken),
        request<ApiKeyInfo[]>('/v1/user/api-keys', undefined, session.accessToken),
        request<UsageSummary>('/v1/user/usage', undefined, session.accessToken),
        request<Subscription>('/v1/user/subscription', undefined, session.accessToken),
      ]);
      const nextSession = { ...session, profile };
      saveSession(nextSession);
      return { profile, plans, apiKeys, usage, subscription };
    } catch (error) {
      if (!shouldUseFallback(error)) {
        throw error;
      }
    }
  }
  return mockAccountSnapshot(session?.profile ?? mockProfile);
}

export async function loginUser(payload: AuthPayload): Promise<AuthSession> {
  const normalizedEmail = payload.email.trim().toLowerCase();
  if (!normalizedEmail || !payload.password) {
    throw new Error('Email and password are required');
  }
  if (ACCOUNT_API_MODE !== 'mock') {
    try {
      const session = await request<AuthSession>('/v1/user/login', {
        method: 'POST',
        body: JSON.stringify({ email: normalizedEmail, password: payload.password }),
      });
      saveSession(session);
      return session;
    } catch (error) {
      if (!shouldUseFallback(error)) {
        throw error;
      }
    }
  }
  const session = makeSession(
    normalizedEmail,
    normalizedEmail === mockProfile.email ? mockProfile.plan : 'free',
  );
  saveSession(session);
  return session;
}

export async function registerUser(payload: AuthPayload): Promise<AuthSession> {
  const normalizedEmail = payload.email.trim().toLowerCase();
  if (!normalizedEmail || payload.password.length < 8) {
    throw new Error('Password must be at least 8 characters');
  }
  if (ACCOUNT_API_MODE !== 'mock') {
    try {
      await request<UserProfile>('/v1/user/register', {
        method: 'POST',
        body: JSON.stringify({
          email: normalizedEmail,
          password: payload.password,
          plan: payload.plan ?? 'free',
        }),
      });
      return await loginUser({ email: normalizedEmail, password: payload.password });
    } catch (error) {
      if (!shouldUseFallback(error)) {
        throw error;
      }
    }
  }
  const session = makeSession(normalizedEmail, payload.plan ?? 'free');
  saveSession(session);
  return session;
}

export async function createApiKey(name: string, scopes: string[]): Promise<ApiKeyInfo> {
  const session = requireSession();
  if (ACCOUNT_API_MODE !== 'mock' && !session.accessToken.startsWith('demo.')) {
    return await request<ApiKeyInfo>(
      '/v1/user/api-keys',
      {
        method: 'POST',
        body: JSON.stringify({ name, scopes }),
      },
      session.accessToken,
    );
  }
  const timestamp = Date.now();
  const apiKey: ApiKeyInfo = {
    keyId: `key_${Math.abs(hash(`${session.profile.email}:${name}:${timestamp}`))}`,
    name,
    apiKey: `ms_demo_${Math.abs(hash(`${name}:${timestamp}`))}`,
    secret: `sec_demo_${Math.abs(hash(`${timestamp}:${name}`))}`,
    scopes,
    status: 'active',
    createdAt: timestamp,
  };
  mockApiKeys.unshift(apiKey);
  return apiKey;
}

export async function disableApiKey(keyId: string): Promise<ApiKeyInfo> {
  const session = requireSession();
  if (ACCOUNT_API_MODE !== 'mock' && !session.accessToken.startsWith('demo.')) {
    return await request<ApiKeyInfo>(
      `/v1/user/api-keys/${encodeURIComponent(keyId)}`,
      { method: 'DELETE' },
      session.accessToken,
    );
  }
  const target = mockApiKeys.find((key) => key.keyId === keyId);
  if (!target) {
    throw new Error('API key not found');
  }
  target.status = 'disabled';
  target.updatedAt = Date.now();
  return target;
}

export function getStoredSession(): AuthSession | null {
  if (typeof window === 'undefined') {
    return null;
  }
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function logoutUser() {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.removeItem(SESSION_KEY);
}

function saveSession(session: AuthSession) {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  accessToken?: string,
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set('Content-Type', 'application/json');
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  const response = await fetch(`${apiBaseUrl}${path}`, {
    ...init,
    headers,
  });
  const payload = (await response.json()) as ServiceResponse<T>;
  if (!response.ok || payload.code !== 0) {
    throw new Error(payload.message || `Request failed with status ${response.status}`);
  }
  return payload.data;
}

function requireSession(): AuthSession {
  const session = getStoredSession();
  if (!session) {
    throw new Error('Login required');
  }
  return session;
}

function shouldUseFallback(error: unknown) {
  return ACCOUNT_API_MODE === 'auto' && error instanceof TypeError;
}

function mockAccountSnapshot(profile: UserProfile): AccountSnapshot {
  return {
    profile,
    plans: mockPlans,
    apiKeys: mockApiKeys,
    usage: {
      ...mockUsage,
      userId: profile.userId,
      planId: profile.plan,
      requestLimit:
        mockPlans.find((plan) => plan.planId === profile.plan)?.requestLimitPerDay ??
        mockUsage.requestLimit,
    },
    subscription: {
      subscriptionId: `sub_${profile.userId}`,
      userId: profile.userId,
      planId: profile.plan,
      status: 'active',
      startedAt: profile.createdAt ?? Date.now(),
    },
  };
}

function makeSession(email: string, plan: string): AuthSession {
  const now = Date.now();
  return {
    accessToken: `demo.${btoa(email)}.${now}`,
    tokenType: 'bearer',
    expiresIn: 86_400,
    profile: {
      userId: `usr_${Math.abs(hash(email))}`,
      email,
      role: 'user',
      plan,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
  };
}

function hash(value: string) {
  let result = 0;
  for (const char of value) {
    result = (result << 5) - result + char.charCodeAt(0);
    result |= 0;
  }
  return result;
}

const mockProfile: UserProfile = {
  userId: 'usr_demo',
  email: 'demo@example.com',
  role: 'user',
  plan: 'pro',
  status: 'active',
};

const mockPlans: Plan[] = [
  {
    planId: 'free',
    name: 'Free',
    priceMonthly: 0,
    requestLimitPerDay: 1000,
    features: ['Basic market data', 'Dashboard'],
  },
  {
    planId: 'pro',
    name: 'Pro',
    priceMonthly: 49,
    requestLimitPerDay: 100000,
    features: ['Full market data', 'Ranking', 'Signals', 'Realtime push'],
  },
  {
    planId: 'enterprise',
    name: 'Enterprise',
    priceMonthly: 499,
    requestLimitPerDay: 1000000,
    features: ['Full API', 'Custom quota', 'Dedicated support'],
  },
];

const mockApiKeys: ApiKeyInfo[] = [
  {
    keyId: 'key_research',
    name: 'Research',
    apiKey: 'ms_live_xxxxxxxxQ4Rt',
    scopes: ['market.read', 'ranking.read', 'signal.read'],
    status: 'active',
    createdAt: 1700000000000,
  },
  {
    keyId: 'key_dashboard',
    name: 'Dashboard',
    apiKey: 'ms_live_xxxxxxxxL9Ka',
    scopes: ['market.read'],
    status: 'disabled',
    createdAt: 1700000000000,
  },
];

const mockUsage: UsageSummary = {
  userId: 'usr_demo',
  planId: 'pro',
  requestLimit: 100000,
  usage: {
    api_requests: 18420,
    websocket_connections: 126,
    notifications: 48,
  },
  remainingRequests: 81580,
};
