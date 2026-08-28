export interface Invoice {
  invoiceNo: string;
  amountCents: number;
  currency: string;
  status: string;
  issuedAt: number;
  paidAt?: number | null;
}

export interface PaymentEvent {
  eventId: string;
  provider: string;
  eventType: string;
  status: string;
  createdAt: number;
}
