<script setup lang="ts">
import { computed, ref } from 'vue';

import AccountPage from './pages/AccountPage.vue';
import AdminPage from './pages/AdminPage.vue';
import AlertCenterPage from './pages/AlertCenterPage.vue';
import BillingPage from './pages/BillingPage.vue';
import DashboardPage from './pages/DashboardPage.vue';
import HistoryPage from './pages/HistoryPage.vue';
import LoginPage from './pages/LoginPage.vue';
import LongInflowPage from './pages/LongInflowPage.vue';
import RankingPage from './pages/RankingPage.vue';
import SignalPage from './pages/SignalPage.vue';
import WatchlistPage from './pages/WatchlistPage.vue';
import { getStoredSession, logoutUser } from './api/account';
import type { AuthSession } from './types/account';
import type { PageKey } from './types/navigation';

const activePage = ref<PageKey>('dashboard');
const session = ref<AuthSession | null>(getStoredSession());
const navItems: { key: PageKey; label: string }[] = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'long-inflow', label: 'Long Inflow' },
  { key: 'ranking', label: 'Ranking' },
  { key: 'signals', label: 'Signals' },
  { key: 'alerts', label: 'Alerts' },
  { key: 'history', label: 'History' },
  { key: 'watchlist', label: 'Watchlist' },
  { key: 'billing', label: 'Billing' },
  { key: 'admin', label: 'Admin' },
  { key: 'account', label: 'Account' },
];

const visibleNavItems = computed(() =>
  navItems.filter((item) => item.key !== 'admin' || session.value?.profile.role === 'admin'),
);

const activeComponent = computed(() => {
  const pages = {
    dashboard: DashboardPage,
    'long-inflow': LongInflowPage,
    ranking: RankingPage,
    signals: SignalPage,
    alerts: AlertCenterPage,
    history: HistoryPage,
    watchlist: WatchlistPage,
    billing: BillingPage,
    admin: AdminPage,
    account: AccountPage,
  };
  return pages[activePage.value];
});

function handleAuthenticated(nextSession: AuthSession) {
  session.value = nextSession;
  activePage.value = 'dashboard';
}

function handleSignOut() {
  logoutUser();
  session.value = null;
  activePage.value = 'dashboard';
}
</script>

<template>
  <LoginPage v-if="!session" @authenticated="handleAuthenticated" />
  <nav v-else class="app-nav" aria-label="Primary navigation">
    <strong>Market Intelligence</strong>
    <div>
      <button
        v-for="item in visibleNavItems"
        :key="item.key"
        :class="{ active: activePage === item.key }"
        type="button"
        @click="activePage = item.key"
      >
        {{ item.label }}
      </button>
    </div>
    <div class="nav-account">
      <span>{{ session.profile.email }}</span>
      <button type="button" @click="handleSignOut">Sign out</button>
    </div>
  </nav>
  <component :is="activeComponent" v-if="session" @sign-out="handleSignOut" />
</template>
