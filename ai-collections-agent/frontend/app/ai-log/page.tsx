"use client";

import { useEffect, useState, useCallback } from "react";
import { api, AIAction, MOCK_AI_ACTIONS } from "@/lib/api";
import { Bot, CheckCircle, Clock, XCircle, Send, Tag, RotateCcw, AlertTriangle } from "lucide-react";

const ACTION_META = {
  SEND_LINK: {
    icon: Send,
    label: "Send Payment Link",
    badge: "badge-send-link",
    color: "text-blue-400",
    iconBg: "bg-blue-500/10",
  },
  OFFER_DISCOUNT: {
    icon: Tag,
    label: "Offer 10% Discount",
    badge: "badge-offer-discount",
    color: "text-purple-400",
    iconBg: "bg-purple-500/10",
  },
  RETRY: {
    icon: RotateCcw,
    label: "Auto Retry",
    badge: "badge-retry",
    color: "text-amber-400",
    iconBg: "bg-amber-500/10",
  },
  ESCALATE: {
    icon: AlertTriangle,
    label: "Escalate to Human",
    badge: "badge-escalate",
    color: "text-rose-400",
    iconBg: "bg-rose-500/10",
  },
} as const;

const OUTCOME_META = {
  RECOVERED: { icon: CheckCircle, color: "text-emerald-400", label: "Recovered" },
  PENDING: { icon: Clock, color: "text-amber-400", label: "Pending" },
  FAILED: { icon: XCircle, color: "text-rose-400", label: "Failed" },
};

export default function AILogPage() {
  const [actions, setActions] = useState<AIAction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const fetchActions = useCallback(async () => {
    try {
      const data = await api.getAIActions(page, 20);
      setActions(data.items);
      setTotal(data.total);
    } catch {
      setActions(MOCK_AI_ACTIONS);
      setTotal(MOCK_AI_ACTIONS.length);
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchActions();
    const interval = setInterval(fetchActions, 5000);
    return () => clearInterval(interval);
  }, [fetchActions]);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Bot className="w-6 h-6 text-purple-400" />
          AI Decision Log
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          {total} total decisions — Gemini 1.5 Flash reasoning log
        </p>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-3 mb-8">
        {(Object.keys(ACTION_META) as Array<keyof typeof ACTION_META>).map((type) => {
          const count = actions.filter((a) => a.action_type === type).length;
          const meta = ACTION_META[type];
          const Icon = meta.icon;
          return (
            <div key={type} className={`glass-card p-4 flex items-center gap-3`}>
              <Icon className={`w-5 h-5 ${meta.color}`} />
              <div>
                <p className="text-lg font-bold text-white">{count}</p>
                <p className="text-xs text-gray-500">{meta.label}</p>
              </div>
            </div>
          );
        })}
      </div>

      {loading ? (
        <div className="glass-card p-12 text-center">
          <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto" />
        </div>
      ) : (
        <div className="space-y-3">
          {actions.map((action) => {
            const meta = ACTION_META[action.action_type];
            const outcome = OUTCOME_META[action.outcome];
            const Icon = meta.icon;
            const OutcomeIcon = outcome.icon;

            return (
              <div key={action.id} className="glass-card p-5 hover-lift border border-gray-800/60">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4 flex-1 min-w-0">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${meta.iconBg}`}>
                      <Icon className={`w-5 h-5 ${meta.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-2">
                        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${meta.badge}`}>
                          {meta.label}
                        </span>
                        <span className="text-xs text-gray-600">Customer #{action.customer_id}</span>
                        <span className="text-xs text-gray-600">Payment #{action.payment_id}</span>
                      </div>

                      {action.reasoning ? (
                        <p className="text-sm text-gray-400 leading-relaxed">
                          {action.reasoning}
                        </p>
                      ) : (
                        <p className="text-sm text-gray-600 italic">No reasoning captured</p>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-800/60`}>
                      <OutcomeIcon className={`w-3.5 h-3.5 ${outcome.color}`} />
                      <span className={`text-xs font-semibold ${outcome.color}`}>{outcome.label}</span>
                    </div>
                    <span className="text-xs text-gray-600">
                      {new Date(action.executed_at).toLocaleString("en-IN", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}

          {actions.length === 0 && (
            <div className="glass-card p-12 text-center text-gray-600">
              No AI decisions logged yet
            </div>
          )}
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between mt-6">
        <p className="text-sm text-gray-500">Showing page {page}</p>
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
            disabled={actions.length < 20}
            className="px-3 py-1.5 text-sm border border-gray-700 rounded-lg text-gray-400 hover:bg-gray-800 disabled:opacity-40 transition-colors"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
