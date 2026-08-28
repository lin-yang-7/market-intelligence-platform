import type { ApiKeyInfo, Subscription, UsageSummary, UserProfile } from './account';

export interface AdminSummaryMetric {
  label: string;
  value: number | string;
  tone: 'positive' | 'negative' | 'warning' | 'neutral' | string;
}

export interface AdminUserRow {
  profile: UserProfile;
  subscription?: Subscription | null;
  usage?: UsageSummary | null;
  apiKeyCount: number;
}

export interface AdminAuditEvent {
  actor: string;
  action: string;
  resource: string;
  result: string;
  timestamp: number;
  metadata: Record<string, string>;
}

export interface AdminSnapshot {
  metrics: AdminSummaryMetric[];
  users: AdminUserRow[];
  apiKeys: ApiKeyInfo[];
  subscriptions: Subscription[];
  usage: UsageSummary[];
  auditEvents: AdminAuditEvent[];
}

export interface AdminRoleDefinition {
  role: string;
  permissions: string[];
}

export interface OperationsAnalytics {
  totalEvents: number;
  activeUsers: number;
  eventCounts: Record<string, number>;
  recentEvents: Array<{
    userId: string;
    event: string;
    timestamp: number;
    metadata: Record<string, string>;
  }>;
}
