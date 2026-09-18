/**
 * Backend API client.
 * TODO: Replace NEXT_PUBLIC_API_URL with your actual backend URL in production.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DashboardMetrics {
  total_recovered: number;
  recovery_rate: number;
  active_cases: number;
  escalations: number;
  total_failed: number;
}

export interface RecoveryDataPoint {
  date: string;
  recovered: number;
  failed: number;
}

export interface Payment {
  id: number;
  customer_id: number;
  order_id: string;
  amount: number;
  status: "SUCCESS" | "FAILED" | "PENDING" | "RECOVERED";
  failure_reason: string | null;
  retry_count: number;
  created_at: string;
  updated_at: string;
}

export interface AIAction {
  id: number;
  customer_id: number;
  payment_id: number;
  action_type: "SEND_LINK" | "OFFER_DISCOUNT" | "RETRY" | "ESCALATE";
  reasoning: string | null;
  outcome: "RECOVERED" | "PENDING" | "FAILED";
  executed_at: string;
  metadata_json: string | null;
}

export interface Customer {
  id: number;
  name: string;
  email: string;
  mobile: string;
  ltv: number;
  churn_risk: number;
  created_at: string;
}

export interface PaginatedPayments {
  items: Payment[];
  total: number;
  page: number;
  size: number;
}

export interface PaginatedAIActions {
  items: AIAction[];
  total: number;
  page: number;
  size: number;
}

export interface CustomerDetail {
  customer: Customer;
  payments: Array<Payment & { created_at: string }>;
  ai_actions: Array<{
    id: number;
    action_type: string;
    reasoning: string | null;
    outcome: string;
    executed_at: string;
    metadata: string | null;
  }>;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(`API Error [${res.status}]: ${error}`);
  }

  return res.json();
}

// ── API Methods ───────────────────────────────────────────────────────────────

export const api = {
  // Dashboard
  getMetrics: () => apiFetch<DashboardMetrics>("/api/dashboard/metrics"),
  getRecoveryTrend: () => apiFetch<RecoveryDataPoint[]>("/api/dashboard/recovery-trend"),
  getFailedPayments: (page = 1, size = 20) =>
    apiFetch<PaginatedPayments>(`/api/dashboard/failed-payments?page=${page}&size=${size}`),
  getAIActions: (page = 1, size = 20) =>
    apiFetch<PaginatedAIActions>(`/api/dashboard/ai-actions?page=${page}&size=${size}`),
  getEscalations: (page = 1, size = 20) =>
    apiFetch<PaginatedAIActions>(`/api/dashboard/escalations?page=${page}&size=${size}`),

  // Customers
  getCustomers: () => apiFetch<Customer[]>("/api/customers/"),
  getCustomer: (id: number) => apiFetch<CustomerDetail>(`/api/customers/${id}`),

  // AI Agent
  triggerAI: (paymentId: number) =>
    apiFetch<AIAction>(`/api/ai/trigger/${paymentId}`, { method: "POST" }),
  resolveEscalation: (actionId: number) =>
    apiFetch<{ status: string }>(`/api/ai/escalations/${actionId}/resolve`, { method: "POST" }),
};

// ── Mock data (used when backend is offline for demo) ─────────────────────────

export const MOCK_METRICS: DashboardMetrics = {
  total_recovered: 247850.0,
  recovery_rate: 68.4,
  active_cases: 23,
  escalations: 4,
  total_failed: 89,
};

export const MOCK_TREND: RecoveryDataPoint[] = [
  { date: "Sep 11", recovered: 18200, failed: 42000 },
  { date: "Sep 12", recovered: 24500, failed: 38000 },
  { date: "Sep 13", recovered: 31200, failed: 45000 },
  { date: "Sep 14", recovered: 28900, failed: 39000 },
  { date: "Sep 15", recovered: 41000, failed: 51000 },
  { date: "Sep 16", recovered: 52300, failed: 48000 },
  { date: "Sep 17", recovered: 51750, failed: 37000 },
];

export const MOCK_PAYMENTS: Payment[] = [
  {
    id: 1, customer_id: 3, order_id: "ORD00000001SYNTH", amount: 4999,
    status: "FAILED", failure_reason: "Insufficient funds in account",
    retry_count: 1, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: 2, customer_id: 7, order_id: "ORD00000002SYNTH", amount: 1299,
    status: "FAILED", failure_reason: "Card declined by issuing bank",
    retry_count: 2, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: 3, customer_id: 12, order_id: "ORD00000003SYNTH", amount: 799,
    status: "FAILED", failure_reason: "OTP verification failed",
    retry_count: 0, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
  {
    id: 4, customer_id: 2, order_id: "ORD00000004SYNTH", amount: 9999,
    status: "FAILED", failure_reason: "Daily transaction limit exceeded",
    retry_count: 3, created_at: new Date().toISOString(), updated_at: new Date().toISOString(),
  },
];

export const MOCK_AI_ACTIONS: AIAction[] = [
  {
    id: 1, customer_id: 3, payment_id: 1, action_type: "SEND_LINK",
    reasoning: "High-value customer (LTV ₹28,500) with only 1 prior retry. Sending a personalized payment link with warm, empathetic tone. Recovery likelihood: High.",
    outcome: "PENDING", executed_at: new Date().toISOString(), metadata_json: null,
  },
  {
    id: 2, customer_id: 7, payment_id: 2, action_type: "OFFER_DISCOUNT",
    reasoning: "Premium customer showing payment friction after 2 attempts. Offering 10% discount to reduce barrier. Recovery likelihood: Medium-High.",
    outcome: "RECOVERED", executed_at: new Date(Date.now() - 3600000).toISOString(), metadata_json: null,
  },
  {
    id: 3, customer_id: 12, payment_id: 3, action_type: "RETRY",
    reasoning: "Standard customer (LTV ₹3,200). Auto-retry attempt 1. Failure reason: OTP verification failed. Recovery likelihood: Medium.",
    outcome: "PENDING", executed_at: new Date(Date.now() - 7200000).toISOString(), metadata_json: null,
  },
  {
    id: 4, customer_id: 2, payment_id: 4, action_type: "ESCALATE",
    reasoning: "Customer has exceeded 3 retry attempts. Automated recovery exhausted; escalating to human agent for direct intervention. Recovery likelihood: Low.",
    outcome: "PENDING", executed_at: new Date(Date.now() - 1800000).toISOString(), metadata_json: null,
  },
];
