"use client";

import { AIAction } from "@/lib/api";
import { Bot, ArrowRight, CheckCircle, Clock, XCircle, AlertTriangle } from "lucide-react";

interface DecisionCardProps {
  action: AIAction;
  customerName?: string;
  paymentAmount?: number;
}

const ACTION_COLORS = {
  SEND_LINK: { bg: "bg-blue-500/10", border: "border-blue-500/20", text: "text-blue-400", label: "Send Payment Link" },
  OFFER_DISCOUNT: { bg: "bg-purple-500/10", border: "border-purple-500/20", text: "text-purple-400", label: "Offer 10% Discount" },
  RETRY: { bg: "bg-amber-500/10", border: "border-amber-500/20", text: "text-amber-400", label: "Auto Retry" },
  ESCALATE: { bg: "bg-rose-500/10", border: "border-rose-500/20", text: "text-rose-400", label: "Escalate to Human" },
};

const OUTCOME_ICONS = {
  RECOVERED: <CheckCircle className="w-4 h-4 text-emerald-400" />,
  PENDING: <Clock className="w-4 h-4 text-amber-400" />,
  FAILED: <XCircle className="w-4 h-4 text-rose-400" />,
};

const OUTCOME_LABELS = {
  RECOVERED: "text-emerald-400",
  PENDING: "text-amber-400",
  FAILED: "text-rose-400",
};

export function DecisionCard({ action, customerName, paymentAmount }: DecisionCardProps) {
  const style = ACTION_COLORS[action.action_type];
  const timeAgo = formatTimeAgo(new Date(action.executed_at));

  return (
    <div className={`glass-card p-4 border ${style.border} hover-lift transition-all`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-lg ${style.bg} flex items-center justify-center flex-shrink-0`}>
            <Bot className={`w-4 h-4 ${style.text}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${style.bg} ${style.text} border ${style.border}`}>
                {style.label}
              </span>
            </div>
            {customerName && (
              <p className="text-sm font-medium text-gray-300 mt-1">{customerName}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {OUTCOME_ICONS[action.outcome]}
          <span className={`text-xs font-semibold ${OUTCOME_LABELS[action.outcome]}`}>
            {action.outcome}
          </span>
        </div>
      </div>

      {action.reasoning && (
        <p className="text-sm text-gray-400 mt-3 leading-relaxed line-clamp-3">
          {action.reasoning}
        </p>
      )}

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-800/60">
        {paymentAmount !== undefined && (
          <span className="text-xs text-gray-500">
            ₹{paymentAmount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
          </span>
        )}
        <span className="text-xs text-gray-600 ml-auto">{timeAgo}</span>
      </div>
    </div>
  );
}

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}
