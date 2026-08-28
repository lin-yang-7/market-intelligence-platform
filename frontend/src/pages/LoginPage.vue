<script setup lang="ts">
import { ref } from 'vue';

import { loginUser, registerUser } from '../api/account';
import type { AuthSession } from '../types/account';

const emit = defineEmits<{
  authenticated: [session: AuthSession];
}>();

const mode = ref<'login' | 'register'>('login');
const email = ref('demo@example.com');
const password = ref('password123');
const plan = ref('free');
const errorMessage = ref('');
const isSubmitting = ref(false);

async function submit() {
  errorMessage.value = '';
  isSubmitting.value = true;
  try {
    const session =
      mode.value === 'login'
        ? await loginUser({ email: email.value, password: password.value })
        : await registerUser({ email: email.value, password: password.value, plan: plan.value });
    emit('authenticated', session);
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Authentication failed';
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <main class="auth-shell">
    <section class="auth-panel">
      <div class="panel__header">
        <h2>Market Intelligence</h2>
        <span>{{ mode === 'login' ? 'Login' : 'Register' }}</span>
      </div>

      <div class="tab-bar auth-tabs">
        <button type="button" :class="{ active: mode === 'login' }" @click="mode = 'login'">
          Login
        </button>
        <button type="button" :class="{ active: mode === 'register' }" @click="mode = 'register'">
          Register
        </button>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <label>
          <small>Email</small>
          <input v-model="email" autocomplete="email" type="email" required />
        </label>
        <label>
          <small>Password</small>
          <input
            v-model="password"
            autocomplete="current-password"
            minlength="8"
            type="password"
            required
          />
        </label>
        <label v-if="mode === 'register'">
          <small>Plan</small>
          <select v-model="plan">
            <option value="free">Free</option>
            <option value="pro">Pro</option>
            <option value="enterprise">Enterprise</option>
          </select>
        </label>

        <p v-if="errorMessage" class="form-error">{{ errorMessage }}</p>
        <button class="primary-action" type="submit" :disabled="isSubmitting">
          {{ isSubmitting ? 'Submitting' : mode === 'login' ? 'Login' : 'Create account' }}
        </button>
      </form>
    </section>
  </main>
</template>
