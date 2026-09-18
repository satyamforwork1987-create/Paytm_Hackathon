"use client";

import { useEffect, useState, useCallback } from "react";
import { api, Payment, MOCK_PAYMENTS } from "@/lib/api";
import { CreditCard, AlertCircle, Bot, ChevronDown, ChevronUp, Loader2, Zap } from "lucide-react";

const STATUS_STYLES: Record<string, string> = {
  FAILED: "badge-failed",
  PENDING: "badge-pending",
  SUCCESS: "badge-recovered",
  RECOVERED: "badge-recovered",
};

function FailureReasonDrawer({ payment, onClose }: { payment: Payment; onClose: () => void }) {
  const [triggering, setTriggering] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const handleTriggerAI = async () => {
    setTriggering(true);
    try {
      const action = await api.triggerAI(payment.id);
      setResult(`AI decided: ${action.action_type} — ${action.reasoning?.slice(0, 120)}...`);
    } catch {
      setResult("Failed to trigger AI — backend may be offline.");
    } finally {
      setTriggering(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="glass-card w-full max-w-lg p-6 border border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <CreditCard className="w-4 h-4 text-rose-400" />
            Payment Detail
          </h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-sm">✕ Close</button>
        </div>

        <div className="space-y-3 mb-5">
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Order ID</span>
            <span className="font-mono text-gray-300">{payment.order_id}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Amount</span>
            <span className="font-bold text-white">₹{payment.amount.toLocaleString("en-IN")}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Failure Reason</span>
            <span className="text-rose-400 font-medium max-w-[200px] text-right">{payment.failure_reason || "Unknown"}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Retries</span>
            <span className="text-amber-400 font-semibold">{payment.retry_count}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-500">Created</span>
            <span className="text-gray-400">{new Date(payment.created_at).toLocaleString("en-IN")}</span>
          </div>
        </div>

        {result && (
          <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-3 mb-4 text-sm text-blue-300">
            {result}
          </div>
        )}

        <button
          onClick={handleTriggerAI}
          disabled={triggering}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 bg-blue-500/15 hover:bg-blue-500/25 text-blue-400 border border-blue-500/30 rounded-xl text-sm font-semibold transition-colors disabled:opacity-50"
        >
          {triggering ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bot className="w-4 h-4" />}
          {triggering ? "Triggering AI..." : "Trigger AI Decision Now"}
        </button>
      </div>
    </div>
  );
}

export default function FailedPaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [selectedPayment, setSelectedPayment] = useState<Payment | null>(null);

  const fetchPayments = useCallback(async () => {
    try {
      const data = await api.getFailedPayments(page, 20);
      setPayments(data.items);
      setTotal(data.total);
    } catch {
      setPayments(MOCK_PAYMENTS);
      setTotal(MOCK_PAYMENTS.length);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => { fetchPayments(); }, [fetchPayments]);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <CreditCard className="w-6 h-6 text-rose-400" />
          Failed Payments
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          {total} failed payments — click a row to inspect & trigger AI
        </p>
      </div>

      {loading ? (
        <div className="glass-card p-12 text-center">
          <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto" />
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800/60">
                  {["Customer", "Order ID", "Amount", "Failure Reason", "Retries", "Status", "AI"].map((h) => (
                    <th key={h} className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {payments.map((payment) => (
                  <tr
                    key={payment.id}
                    className="border-b border-gray-800/40 table-row-hover cursor-pointer"
                    onClick={() => setSelectedPayment(payment)}
                  >
                    <td className="px-6 py-4 text-sm text-gray-300">#{payment.customer_id}</td>
                    <td className="px-6 py-4 text-sm font-mono text-gray-500">{payment.order_id.slice(0, 16)}...</td>
                    <td className="px-6 py-4 text-sm font-bold text-white">
                      ₹{payment.amount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                    </td>
                    <td className="px-6 py-4 text-sm text-rose-300 max-w-[200px] truncate">
                      {payment.failure_reason || "—"}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-sm font-bold ${payment.retry_count >= 3 ? "text-rose-400" : "text-amber-400"}`}>
                        {payment.retry_count}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${STATUS_STYLES[payment.status] || "badge-pending"}`}>
                        {payment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={(e) => { e.stopPropagation(); setSelectedPayment(payment); }}
                        className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                      >
                        <Zap className="w-3 h-3" /> Trigger
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-gray-800/60">
            <p className="text-sm text-gray-500">Page {page}</p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 text-sm border border-gray-700 rounded-lg text-gray-400 hover:bg-gray-800 disabled:opacity-40 transition-colors"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={payments.length < 20}
                className="px-3 py-1.5 text-sm border border-gray-700 rounded-lg text-gray-400 hover:bg-gray-800 disabled:opacity-40 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {selectedPayment && (
        <FailureReasonDrawer payment={selectedPayment} onClose={() => setSelectedPayment(null)} />
      )}
    </div>
  );
}
