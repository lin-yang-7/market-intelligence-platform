import type { Invoice, PaymentEvent } from '../types/billing';

export async function getBillingSnapshot() {
  return {
    invoices: mockInvoices,
    events: mockEvents,
  };
}

const mockInvoices: Invoice[] = [
  {
    invoiceNo: 'INV-2026-0001',
    amountCents: 4900,
    currency: 'USD',
    status: 'paid',
    issuedAt: 1785542400000,
    paidAt: 1785542500000,
  },
  {
    invoiceNo: 'INV-2026-0002',
    amountCents: 4900,
    currency: 'USD',
    status: 'open',
    issuedAt: 1788220800000,
  },
];

const mockEvents: PaymentEvent[] = [
  {
    eventId: 'evt_paid_001',
    provider: 'manual',
    eventType: 'invoice.paid',
    status: 'processed',
    createdAt: 1785542500000,
  },
  {
    eventId: 'evt_open_002',
    provider: 'manual',
    eventType: 'invoice.created',
    status: 'recorded',
    createdAt: 1788220800000,
  },
];
