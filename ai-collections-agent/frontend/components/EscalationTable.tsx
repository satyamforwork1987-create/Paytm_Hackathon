"use client";

import React, { useState } from "react";
import { AIAction, api } from "@/lib/api";
import { AlertTriangle, CheckCircle, Clock, ChevronDown, ChevronUp, Loader2 } from "lucide-react";

interface EscalationTableProps {
  escalations: AIAction[];
  onResolved?: () => void;
}

export function EscalationTable({ escalations, onResolved }: EscalationTableProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const handleResolve = async (actionId: number) => {
    setResolvingId(actionId);
    try {
      await api.resolveEscalation(actionId);
      onResolved?.();
    } catch (err) {
      console.error("Failed to resolve escalation:", err);
    } finally {
      setResolvingId(null);
    }
  };

  if (escalations.length === 0) {
    return (
      <div className="glass-card p-12 text-center">
        <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3 opacity-60" />
        <p className="text-gray-400 font-medium">No escalations pending</p>
        <p className="text-gray-600 text-sm mt-1">The AI is handling all cases autonomously</p>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800/60">
              <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Case</th>
              <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Customer</th>
              <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Amount</th>
              <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Since</th>
              <th className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-4" />
            </tr>
          </thead>
          <tbody>
            {escalations.map((action) => (
              <React.Fragment key={action.id}>
                <tr
                  className="border-b border-gray-800/40 table-row-hover cursor-pointer"
                  onClick={() => setExpandedId(expandedId === action.id ? null : action.id)}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-rose-400" />
                      <span className="text-sm font-mono text-gray-400">ESC-{action.id.toString().padStart(4, "0")}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-300">Customer #{action.customer_id}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm font-medium text-white">—</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm text-gray-500">
                      {new Date(action.executed_at).toLocaleDateString("en-IN")}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-amber-400" />
                      <span className="badge-pending text-xs font-semibold px-2 py-0.5 rounded-full">
                        Open
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => { e.stopPropagation(); handleResolve(action.id); }}
                        disabled={resolvingId === action.id}
                        className="px-3 py-1.5 text-xs font-semibold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 rounded-lg hover:bg-emerald-500/25 transition-colors disabled:opacity-50 flex items-center gap-1.5"
                      >
                        {resolvingId === action.id ? (
                          <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                          <CheckCircle className="w-3 h-3" />
                        )}
                        Mark Resolved
                      </button>
                      {expandedId === action.id ? (
                        <ChevronUp className="w-4 h-4 text-gray-500" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      )}
                    </div>
                  </td>
                </tr>

                {expandedId === action.id && (
                  <tr key={`${action.id}-expanded`} className="border-b border-gray-800/40">
                    <td colSpan={6} className="px-6 py-4">
                      <div className="bg-rose-500/5 border border-rose-500/15 rounded-lg p-4">
                        <p className="text-xs font-semibold text-rose-400 uppercase tracking-wider mb-2">
                          AI Reasoning (why escalated)
                        </p>
                        <p className="text-sm text-gray-300 leading-relaxed">
                          {action.reasoning || "No reasoning available"}
                        </p>
                        <div className="mt-3 flex items-center gap-3 text-xs text-gray-600">
                          <span>Payment #{action.payment_id}</span>
                          <span>•</span>
                          <span>Action #{action.id}</span>
                          <span>•</span>
                          <span>{new Date(action.executed_at).toLocaleString("en-IN")}</span>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
