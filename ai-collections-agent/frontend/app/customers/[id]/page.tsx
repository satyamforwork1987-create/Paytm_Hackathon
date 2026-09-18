"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, CustomerDetail } from "@/lib/api";
import {
  User,
  TrendingUp,
  CreditCard,
  Bot,
  ArrowLeft,
  CheckCircle,
  Clock,
  XCircle,
  AlertTriangle,
  Send,
  Tag,
  RotateCcw,
} from "lucide-react";
import Link from "next/link";

const ACTION_ICONS: Record<string, React.ElementType> = {
  SEND_LINK: Send,
  OFFER_DISCOUNT: Tag,
  RETRY: RotateCcw,
  ESCALATE: AlertTriangle,
};

const ACTION_COLORS: Record<string, string> = {
  SEND_LINK: "text-blue-400",
  OFFER_DISCOUNT: "text-purple-400",
  RETRY: "text-amber-400",
  ESCALATE: "text-rose-400",
};

const OUTCOME_ICONS: Record<string, React.ElementType> = {
  RECOVERED: CheckCircle,
  PENDING: Clock,
  FAILED: XCircle,
};

const OUTCOME_COLORS: Record<string, string> = {
  RECOVERED: "text-emerald-400",
  PENDING: "text-amber-400",
  FAILED: "text-rose-400",
};

const MOCK_DETAIL: CustomerDetail = {
  customer: {
    id: 1,
    name: "Priya Sharma",
    email: "priya.sharma@email.com",
    mobile: "9876543210",
    ltv: 48500,
    churn_risk: 0.12,
    created_at: new Date(Date.now() - 86400000 * 180).toISOString(),
  },
  payments: [
    { id: 1, customer_id: 1, order_id: "ORD00000001SYNTH", amount: 4999, status: "FAILED", failure_reason: "Insufficient funds", retry_count: 1, created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    { id: 2, customer_id: 1, order_id: "ORD00000002SYNTH", amount: 1999, status: "RECOVERED", failure_reason: null, retry_count: 0, created_at: new Date(Date.now() - 86400000).toISOString(), updated_at: new Date().toISOString() },
  ],
  ai_actions: [
    { id: 1, action_type: "SEND_LINK", reasoning: "High-value customer with low churn risk. Sending personalized payment link.", outcome: "PENDING", executed_at: new Date().toISOString(), metadata: null },
    { id: 2, action_type: "OFFER_DISCOUNT", reasoning: "Previous retry failed. Offering 10% discount to incentivize payment.", outcome: "RECOVERED", executed_at: new Date(Date.now() - 86400000).toISOString(), metadata: null },
  ],
};

export default function CustomerDetailPage() {
  const params = useParams();
  const [detail, setDetail] = useState<CustomerDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const id = Number(params.id);
    api.getCustomer(id)
      .then(setDetail)
      .catch(() => setDetail(MOCK_DETAIL))
      .finally(() => setLoading(false));
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="p-8 text-center text-gray-500">
        Customer not found.{" "}
        <Link href="/customers" className="text-blue-400 hover:underline">Back to customers</Link>
      </div>
    );
  }

  const { customer, payments, ai_actions } = detail;

  return (
    <div className="p-8">
      <Link
        href="/customers"
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-300 mb-6 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Customers
      </Link>

      {/* Profile Card */}
      <div className="glass-card p-6 mb-6 flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white">
            {customer.name.charAt(0)}
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">{customer.name}</h1>
            <p className="text-gray-500 text-sm">{customer.email}</p>
            <p className="text-gray-600 text-sm">{customer.mobile}</p>
            <p className="text-gray-700 text-xs mt-1">Member since {new Date(customer.created_at).toLocaleDateString("en-IN", { year: "numeric", month: "long" })}</p>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">Lifetime Value</p>
            <p className="text-2xl font-bold text-emerald-400">
              ₹{customer.ltv.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
            </p>
          </div>
          <div className="text-center">
            <p className="text-xs text-gray-500 mb-1">Churn Risk</p>
            <p className={`text-2xl font-bold ${customer.churn_risk > 0.7 ? "text-rose-400" : customer.churn_risk > 0.4 ? "text-amber-400" : "text-emerald-400"}`}>
              {(customer.churn_risk * 100).toFixed(0)}%
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Payment History */}
        <div className="glass-card p-6">
          <h2 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
            <CreditCard className="w-4 h-4 text-blue-400" />
            Payment History
          </h2>
          <div className="space-y-3">
            {payments.length === 0 ? (
              <p className="text-gray-600 text-sm">No payments found</p>
            ) : payments.map((p) => (
              <div key={p.id} className="flex items-center justify-between py-2 border-b border-gray-800/40 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-300">₹{p.amount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}</p>
                  <p className="text-xs text-gray-600 font-mono">{p.order_id.slice(0, 20)}...</p>
                  {p.failure_reason && <p className="text-xs text-rose-400 mt-0.5">{p.failure_reason}</p>}
                </div>
                <div className="text-right">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                    p.status === "RECOVERED" ? "badge-recovered" :
                    p.status === "FAILED" ? "badge-failed" : "badge-pending"
                  }`}>
                    {p.status}
                  </span>
                  <p className="text-xs text-gray-600 mt-1">{new Date(p.created_at).toLocaleDateString("en-IN")}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* AI Action History */}
        <div className="glass-card p-6">
          <h2 className="text-base font-semibold text-white flex items-center gap-2 mb-4">
            <Bot className="w-4 h-4 text-purple-400" />
            AI Action History
          </h2>
          <div className="space-y-3">
            {ai_actions.length === 0 ? (
              <p className="text-gray-600 text-sm">No AI actions yet</p>
            ) : ai_actions.map((action) => {
              const Icon = ACTION_ICONS[action.action_type] || Bot;
              const OutcomeIcon = OUTCOME_ICONS[action.outcome] || Clock;
              return (
                <div key={action.id} className="border border-gray-800/60 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Icon className={`w-4 h-4 ${ACTION_COLORS[action.action_type] || "text-gray-400"}`} />
                      <span className="text-sm font-semibold text-gray-300">{action.action_type.replace("_", " ")}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <OutcomeIcon className={`w-3.5 h-3.5 ${OUTCOME_COLORS[action.outcome] || "text-gray-400"}`} />
                      <span className={`text-xs font-semibold ${OUTCOME_COLORS[action.outcome] || "text-gray-400"}`}>{action.outcome}</span>
                    </div>
                  </div>
                  {action.reasoning && (
                    <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">{action.reasoning}</p>
                  )}
                  <p className="text-xs text-gray-700 mt-2">
                    {new Date(action.executed_at).toLocaleString("en-IN")}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
