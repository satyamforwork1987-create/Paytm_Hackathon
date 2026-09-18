"use client";

import { useEffect, useState, useCallback } from "react";
import { api, AIAction, MOCK_AI_ACTIONS } from "@/lib/api";
import { EscalationTable } from "@/components/EscalationTable";
import { AlertTriangle, ShieldCheck } from "lucide-react";

export default function EscalationsPage() {
  const [escalations, setEscalations] = useState<AIAction[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchEscalations = useCallback(async () => {
    try {
      const data = await api.getEscalations(1, 50);
      setEscalations(data.items);
    } catch {
      // Mock: only show ESCALATE type actions from mock data
      setEscalations(MOCK_AI_ACTIONS.filter((a) => a.action_type === "ESCALATE"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEscalations();
  }, [fetchEscalations]);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-rose-400" />
          Human Escalation Queue
        </h1>
        <p className="text-gray-500 text-sm mt-1">
          Cases where the AI has exhausted automated recovery options
        </p>
      </div>

      {/* Context banner */}
      <div className="glass-card p-4 mb-6 border border-amber-500/20 bg-amber-500/5">
        <div className="flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-amber-300">AI Escalation Policy</p>
            <p className="text-sm text-gray-400 mt-1">
              The AI escalates a case after{" "}
              <span className="text-white font-medium">3 or more failed recovery attempts</span>.
              Human agents should reach out directly via phone or email to resolve these cases.
            </p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="glass-card p-12 text-center">
          <div className="w-8 h-8 border-2 border-rose-500/30 border-t-rose-500 rounded-full animate-spin mx-auto" />
        </div>
      ) : (
        <EscalationTable escalations={escalations} onResolved={fetchEscalations} />
      )}
    </div>
  );
}
