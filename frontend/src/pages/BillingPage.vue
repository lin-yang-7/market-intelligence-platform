<script setup lang="ts">
import { onMounted, ref } from 'vue';

import { getBillingSnapshot } from '../api/billing';
import type { Invoice, PaymentEvent } from '../types/billing';

const invoices = ref<Invoice[]>([]);
const events = ref<PaymentEvent[]>([]);

function money(invoice: Invoice) {
  return `${invoice.currency} ${(invoice.amountCents / 100).toFixed(2)}`;
}

onMounted(async () => {
  const snapshot = await getBillingSnapshot();
  invoices.value = snapshot.invoices;
  events.value = snapshot.events;
});
</script>

<template>
  <main class="dashboard-shell">
    <section class="page-grid page-grid--detail">
      <div class="panel">
        <div class="panel__header">
          <h2>Billing</h2>
          <span>{{ invoices.length }} invoices</span>
        </div>
        <div class="wide-table">
          <div class="wide-table__row wide-table__row--billing wide-table__row--head">
            <span>Invoice</span>
            <span>Amount</span>
            <span>Status</span>
            <span>Issued</span>
            <span>Paid</span>
          </div>
          <div v-for="invoice in invoices" :key="invoice.invoiceNo" class="wide-table__row wide-table__row--billing">
            <strong>{{ invoice.invoiceNo }}</strong>
            <span>{{ money(invoice) }}</span>
            <span>{{ invoice.status }}</span>
            <span>{{ new Date(invoice.issuedAt).toLocaleDateString() }}</span>
            <span>{{ invoice.paidAt ? new Date(invoice.paidAt).toLocaleDateString() : '-' }}</span>
          </div>
        </div>
      </div>

      <aside class="panel detail-panel">
        <div class="panel__header">
          <h2>Payment Events</h2>
          <span>manual</span>
        </div>
        <section class="timeline">
          <article v-for="event in events" :key="event.eventId">
            <strong>{{ event.eventType }}</strong>
            <p>{{ event.provider }} / {{ event.status }} / {{ new Date(event.createdAt).toLocaleString() }}</p>
          </article>
        </section>
      </aside>
    </section>
  </main>
</template>
