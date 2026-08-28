export interface UserProfile {
  userId: string;
  email: string;
  role: string;
  plan: string;
  status: string;
  createdAt?: number;
  updatedAt?: number;
}

export interface AuthSession {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
  profile: UserProfile;
}

export interface AuthPayload {
  email: string;
  password: string;
  plan?: string;
}

export interface Plan {
  planId: string;
  name: string;
  priceMonthly: number;
  requestLimitPerDay: number;
  features: string[];
}

export interface ApiKeyInfo {
  keyId: string;
  userId?: string;
  name: string;
  apiKey: string;
  secret?: string;
  scopes: string[];
  status: string;
  createdAt: number;
  updatedAt?: number;
}

export interface Subscription {
  subscriptionId: string;
  userId: string;
  planId: string;
  status: string;
  startedAt: number;
  renewsAt?: number | null;
}

export interface UsageSummary {
  userId: string;
  planId: string;
  periodStart?: number;
  periodEnd?: number;
  requestLimit: number;
  usage: Record<string, number>;
  remainingRequests: number;
}

export interface AccountSnapshot {
  profile: UserProfile;
  plans: Plan[];
  apiKeys: ApiKeyInfo[];
  usage: UsageSummary;
  subscription?: Subscription;
}
