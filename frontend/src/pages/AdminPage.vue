<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { getAdminOperations, getAdminRoles, getAdminSnapshot, updateAdminUser } from '../api/admin';
import { getStoredSession } from '../api/account';
import type { AdminRoleDefinition, AdminSnapshot, OperationsAnalytics } from '../types/admin';

const snapshot = ref<AdminSnapshot | null>(null);
const roles = ref<AdminRoleDefinition[]>([]);
const operations = ref<OperationsAnalytics | null>(null);
const loading = ref(true);
const error = ref('');
const actionMessage = ref('');
const activeSection = ref('users');

const session = getStoredSession();
const canAccessAdmin = computed(() => session?.profile.role === 'admin');
const users = computed(() => snapshot.value?.users ?? []);
const apiKeys = computed(() => snapshot.value?.apiKeys ?? []);
const auditEvents = computed(() => snapshot.value?.auditEvents ?? []);
const highUsageUsers = computed(() =>
  users.value
    .map((row) => ({
      ...row,
      usageRate: row.usage ? Math.round((1 - row.usage.remainingRequests / row.usage.requestLimit) * 100) : 0,
    }))
    .sort((left, right) => right.usageRate - left.usageRate)
    .slice(0, 5),
);

onMounted(async () => {
  if (!canAccessAdmin.value) {
    loading.value = false;
    return;
  }
  try {
    const [adminSnapshot, roleDefinitions, operationData] = await Promise.all([
      getAdminSnapshot(),
      getAdminRoles(),
      getAdminOperations(),
    ]);
    snapshot.value = adminSnapshot;
    roles.value = roleDefinitions;
    operations.value = operationData;
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to load admin snapshot';
  } finally {
    loading.value = false;
  }
});

function formatTime(value?: number) {
  if (!value) {
    return '-';
  }
  return new Date(value).toLocaleString();
}

async function patchUser(userId: string, payload: { role?: string; status?: string; plan?: string }) {
  try {
    actionMessage.value = '';
    const updated = await updateAdminUser(userId, payload);
    if (snapshot.value) {
      snapshot.value.users = snapshot.value.users.map((row) =>
        row.profile.userId === userId ? { ...row, profile: updated } : row,
      );
    }
    actionMessage.value = `${updated.email} updated`;
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to update user';
  }
}

function metricLabel(label: string) {
  return label.replaceAll('_', ' ');
}
</script>

<template>
  <main class="dashboard-shell admin-shell">
    <header class="topbar">
      <div>
        <h1>Admin Console</h1>
        <p>Operational control surface adapted from the Vben admin layout pattern.</p>
      </div>
      <div class="topbar__meta">
        <span>role / {{ session?.profile.role ?? 'unknown' }}</span>
        <span>{{ session?.profile.email }}</span>
      </div>
    </header>

    <section v-if="!canAccessAdmin" class="panel admin-denied">
      <div>
        <h2>Admin access required</h2>
        <p>Only users with the admin role can open this console.</p>
      </div>
    </section>

    <section v-else-if="loading" class="panel">
      <div class="panel__header">
        <h2>Loading</h2>
        <span>admin snapshot</span>
      </div>
    </section>

    <section v-else-if="error" class="panel">
      <div class="panel__header">
        <h2>Admin API error</h2>
        <span>{{ error }}</span>
      </div>
    </section>

    <template v-else-if="snapshot">
      <section class="admin-layout">
        <aside class="admin-sider">
          <strong>Market Ops</strong>
          <button :class="{ active: activeSection === 'users' }" type="button" @click="activeSection = 'users'">
            Users
          </button>
          <button :class="{ active: activeSection === 'apiKeys' }" type="button" @click="activeSection = 'apiKeys'">
            API Keys
          </button>
          <button :class="{ active: activeSection === 'audit' }" type="button" @click="activeSection = 'audit'">
            Audit
          </button>
          <button :class="{ active: activeSection === 'ops' }" type="button" @click="activeSection = 'ops'">
            Operations
          </button>
        </aside>

        <div class="admin-content">
          <section class="metric-strip admin-metrics">
            <article v-for="metric in snapshot.metrics" :key="metric.label" class="metric">
              <span class="metric__label">{{ metricLabel(metric.label) }}</span>
              <strong class="metric__value">{{ metric.value.toLocaleString() }}</strong>
              <span :class="`metric__change tone-${metric.tone}`">admin</span>
            </article>
          </section>

          <section v-if="activeSection === 'users'" class="panel">
            <div class="panel__header">
              <h2>User Management</h2>
              <span>{{ users.length }} users</span>
            </div>
            <p v-if="actionMessage" class="secret-note">{{ actionMessage }}</p>
            <div class="wide-table">
              <div class="wide-table__row wide-table__row--admin wide-table__row--head">
                <span>User</span>
                <span>Role</span>
                <span>Plan</span>
                <span>Usage</span>
                <span>Keys</span>
                <span>Status</span>
                <span>Actions</span>
              </div>
              <div v-for="row in users" :key="row.profile.userId" class="wide-table__row wide-table__row--admin">
                <strong>{{ row.profile.email }}</strong>
                <span>{{ row.profile.role }}</span>
                <span>{{ row.subscription?.planId ?? row.profile.plan }}</span>
                <span>{{ row.usage?.usage.api_requests?.toLocaleString() ?? 0 }}</span>
                <span>{{ row.apiKeyCount }}</span>
                <span>{{ row.profile.status }}</span>
                <span class="admin-actions">
                  <button type="button" @click="patchUser(row.profile.userId, { role: row.profile.role === 'admin' ? 'user' : 'admin' })">
                    {{ row.profile.role === 'admin' ? 'User' : 'Admin' }}
                  </button>
                  <button type="button" @click="patchUser(row.profile.userId, { status: row.profile.status === 'active' ? 'disabled' : 'active' })">
                    {{ row.profile.status === 'active' ? 'Disable' : 'Activate' }}
                  </button>
                </span>
              </div>
            </div>
          </section>

          <section v-else-if="activeSection === 'apiKeys'" class="panel">
            <div class="panel__header">
              <h2>API Key Oversight</h2>
              <span>{{ apiKeys.length }} keys</span>
            </div>
            <div class="wide-table">
              <div class="wide-table__row wide-table__row--admin wide-table__row--head">
                <span>Name</span>
                <span>User</span>
                <span>Status</span>
                <span>Scopes</span>
                <span>Created</span>
                <span>Key</span>
              </div>
              <div v-for="key in apiKeys" :key="key.keyId" class="wide-table__row wide-table__row--admin">
                <strong>{{ key.name }}</strong>
                <span>{{ key.userId }}</span>
                <span>{{ key.status }}</span>
                <span>{{ key.scopes.join(', ') }}</span>
                <span>{{ formatTime(key.createdAt) }}</span>
                <span>{{ key.apiKey }}</span>
              </div>
            </div>
          </section>

          <section v-else-if="activeSection === 'audit'" class="panel">
            <div class="panel__header">
              <h2>Audit Log</h2>
              <span>{{ auditEvents.length }} events</span>
            </div>
            <article v-for="event in auditEvents" :key="`${event.actor}-${event.action}-${event.timestamp}`" class="signal">
              <div>
                <strong>{{ event.action }}</strong>
                <span class="event-severity event-severity--info">{{ event.result }}</span>
              </div>
              <p>{{ event.actor }} / {{ event.resource }}</p>
              <footer>{{ formatTime(event.timestamp) }}</footer>
            </article>
          </section>

          <section v-else class="page-grid page-grid--detail">
            <div class="panel">
              <div class="panel__header">
                <h2>High Usage Users</h2>
                <span>quota pressure</span>
              </div>
              <div v-for="row in highUsageUsers" :key="row.profile.userId" class="setting-row">
                <span>{{ row.profile.email }}</span>
                <strong>{{ row.usageRate }}%</strong>
              </div>
            </div>
            <div class="panel detail-panel">
              <div class="panel__header">
                <h2>Admin Permissions</h2>
                <span>RBAC</span>
              </div>
              <div class="role-matrix">
                <article v-for="role in roles" :key="role.role">
                  <strong>{{ role.role }}</strong>
                  <p>{{ role.permissions.join(', ') }}</p>
                </article>
              </div>
            </div>
            <div class="panel detail-panel">
              <div class="panel__header">
                <h2>Product Operations</h2>
                <span>{{ operations?.activeUsers ?? 0 }} active users</span>
              </div>
              <p>Total tracked events: {{ operations?.totalEvents ?? 0 }}</p>
              <div v-for="(count, event) in operations?.eventCounts ?? {}" :key="event" class="setting-row">
                <span>{{ event }}</span>
                <strong>{{ count }}</strong>
              </div>
            </div>
          </section>
        </div>
      </section>
    </template>
  </main>
</template>
