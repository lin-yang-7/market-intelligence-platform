<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { createApiKey, disableApiKey, getAccountSnapshot } from '../api/account';
import type { ApiKeyInfo, Plan, UsageSummary, UserProfile } from '../types/account';

defineEmits<{
  signOut: [];
}>();

const profile = ref<UserProfile | null>(null);
const plans = ref<Plan[]>([]);
const apiKeys = ref<ApiKeyInfo[]>([]);
const usage = ref<UsageSummary | null>(null);
const errorMessage = ref('');
const createdSecret = ref('');

const activePlan = computed(() =>
  plans.value.find((plan) => plan.planId === profile.value?.plan),
);

const usagePercent = computed(() => {
  if (!usage.value) {
    return 0;
  }
  const used = usage.value.usage.api_requests ?? 0;
  return Math.min(100, Math.round((used / usage.value.requestLimit) * 100));
});

async function refresh() {
  errorMessage.value = '';
  const snapshot = await getAccountSnapshot();
  profile.value = snapshot.profile;
  plans.value = snapshot.plans;
  apiKeys.value = snapshot.apiKeys;
  usage.value = snapshot.usage;
}

async function handleCreateKey() {
  const name = window.prompt('API key name', 'Research');
  if (!name) {
    return;
  }
  errorMessage.value = '';
  createdSecret.value = '';
  try {
    const key = await createApiKey(name, ['market.read', 'ranking.read', 'signal.read']);
    createdSecret.value = key.secret ? `Secret: ${key.secret}` : '';
    await refresh();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Create API key failed';
  }
}

async function handleDisableKey(keyId: string) {
  errorMessage.value = '';
  createdSecret.value = '';
  try {
    await disableApiKey(keyId);
    await refresh();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Disable API key failed';
  }
}

onMounted(refresh);
</script>

<template>
  <main class="dashboard-shell">
    <section class="page-grid page-grid--detail">
      <div class="panel" v-if="profile && usage">
        <div class="panel__header">
          <h2>Account</h2>
          <button type="button" @click="$emit('signOut')">Sign out</button>
        </div>
        <div class="account-summary">
          <div>
            <small>Email</small>
            <strong>{{ profile.email }}</strong>
          </div>
          <div>
            <small>Plan</small>
            <strong>{{ activePlan?.name || profile.plan }}</strong>
          </div>
          <div>
            <small>Daily quota</small>
            <strong>{{ usage.requestLimit.toLocaleString() }}</strong>
          </div>
          <div>
            <small>Remaining</small>
            <strong>{{ usage.remainingRequests.toLocaleString() }}</strong>
          </div>
        </div>

        <section class="usage-meter">
          <div>
            <strong>API Requests</strong>
            <span>{{ usage.usage.api_requests.toLocaleString() }} used</span>
          </div>
          <progress :value="usagePercent" max="100"></progress>
        </section>

        <div class="panel__header panel__header--inner">
          <h2>API Keys</h2>
          <button type="button" @click="handleCreateKey">Create</button>
        </div>
        <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
        <p v-if="createdSecret" class="secret-note">{{ createdSecret }}</p>
        <div class="wide-table">
          <div class="wide-table__row wide-table__row--head">
            <span>Name</span>
            <span>API Key</span>
            <span>Status</span>
            <span>Scopes</span>
            <span>Created</span>
            <span>Action</span>
          </div>
          <div v-for="key in apiKeys" :key="key.keyId" class="wide-table__row">
            <strong>{{ key.name }}</strong>
            <span>{{ key.apiKey }}</span>
            <span>{{ key.status }}</span>
            <span>{{ key.scopes.join(', ') }}</span>
            <span>{{ new Date(key.createdAt).toLocaleDateString() }}</span>
            <button type="button" :disabled="key.status !== 'active'" @click="handleDisableKey(key.keyId)">
              Disable
            </button>
          </div>
        </div>
      </div>

      <aside class="panel detail-panel">
        <div class="panel__header">
          <h2>Plans</h2>
          <span>{{ plans.length }} tiers</span>
        </div>
        <article v-for="plan in plans" :key="plan.planId" class="plan-row">
          <div>
            <strong>{{ plan.name }}</strong>
            <small>${{ plan.priceMonthly }} / month</small>
          </div>
          <span>{{ plan.requestLimitPerDay.toLocaleString() }} req/day</span>
          <ul>
            <li v-for="feature in plan.features" :key="feature">{{ feature }}</li>
          </ul>
        </article>
      </aside>
    </section>
  </main>
</template>
