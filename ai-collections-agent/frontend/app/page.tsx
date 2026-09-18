"use client";

import { useEffect, useState, useCallback } from "react";
import {
  TrendingUp,
  CreditCard,
  Activity,
  AlertTriangle,
  RefreshCw,
  Bot,
  ArrowUpRight,
} from "lucide-react";
import { api, DashboardMetrics, RecoveryDataPoint, AIAction, MOCK_METRICS, MOCK_TREND, MOCK_AI_ACTIONS } from "@/lib/api";
import { RevenueChart } from "@/components/RevenueChart";
import { DecisionCard } from "@/components/DecisionCard";

const POLL_INTERVAL_MS = 5000;

function MetricCard({
  label,
  value,
  sub,
  icon: Icon,
  colorClass,
  cardClass,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  colorClass: string;
  cardClass: string;
}) {
  return (
    <div className={`glass-card p-6 border hover-lift ${cardClass}`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500 font-medium">{label}</p>
          <p className={`text-3xl font-bold mt-1 ${colorClass}`}>{value}</p>
          {sub && <p className="text-xs text-gray-600 mt-1">{sub}</p>}
        </div>
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${colorClass.replace("text-", "bg-").replace("400", "500/15")}`}>
          <Icon className={`w-5 h-5 ${colorClass}`} />
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [trend, setTrend] = useState<RecoveryDataPoint[]>([]);
  const [aiActions, setAiActions] = useState<AIAction[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [m, t, a] = await Promise.all([
        api.getMetrics(),
        api.getRecoveryTrend(),
        api.getAIActions(1, 6),
      ]);
      setMetrics(m);
      setTrend(t);
      setAiActions(a.items);
      setLastUpdated(new Date());
    } catch {
      // Backend offline — use mock data for demo
      setMetrics(MOCK_METRICS);
      setTrend(MOCK_TREND);
      setAiActions(MOCK_AI_ACTIONS);
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto" />
          <p className="text-gray-500 mt-4 text-sm">Loading AI Agent data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-white">Recovery Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">
            AI-powered payment recovery & churn prevention
          </p>
        </div>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <p className="text-xs text-gray-600">
              Updated {lastUpdated.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </p>
          )}
          <button
            onClick={fetchData}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-400 border border-gray-700 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard
          label="Total Recovered"
          value={`₹${((metrics?.total_recovered ?? 0) / 1000).toFixed(1)}K`}
          sub="Across all AI actions"
          icon={TrendingUp}
          colorClass="text-emerald-400"
          cardClass="metric-card-green"
        />
        <MetricCard
          label="Recovery Rate"
          value={`${metrics?.recovery_rate ?? 0}%`}
          sub={`${metrics?.total_failed ?? 0} total failed payments`}
          icon={Activity}
          colorClass="text-blue-400"
          cardClass="metric-card-blue"
        />
        <MetricCard
          label="Active Cases"
          value={String(metrics?.active_cases ?? 0)}
          sub="AI working autonomously"
          icon={Bot}
          colorClass="text-purple-400"
          cardClass="metric-card-purple"
        />
        <MetricCard
          label="Escalations"
          value={String(metrics?.escalations ?? 0)}
          sub="Awaiting human review"
          icon={AlertTriangle}
          colorClass="text-rose-400"
          cardClass="metric-card-rose"
        />
      </div>

      {/* Chart + Live Feed */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <RevenueChart data={trend} />
        </div>

        {/* Live AI Decisions Feed */}
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-white">Live AI Decisions</h3>
              <p className="text-xs text-gray-500 mt-0.5">Polling every 5s</p>
            </div>
            <span className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
              </span>
              <span className="text-xs text-blue-400">LIVE</span>
            </span>
          </div>
          <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1">
            {aiActions.length === 0 ? (
              <p className="text-gray-600 text-sm text-center py-8">No decisions yet</p>
            ) : (
              aiActions.map((action) => (
                <DecisionCard key={action.id} action={action} />
              ))
            )}
          </div>
          <a
            href="/ai-log"
            className="flex items-center justify-center gap-1.5 mt-4 text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            View full AI log <ArrowUpRight className="w-3 h-3" />
          </a>
        </div>
      </div>
    </div>
  );
}
