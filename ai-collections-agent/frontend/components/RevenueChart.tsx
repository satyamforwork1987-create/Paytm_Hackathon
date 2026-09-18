"use client";

import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import { RecoveryDataPoint } from "@/lib/api";

interface RevenueChartProps {
  data: RecoveryDataPoint[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card p-3 text-sm">
        <p className="text-gray-300 font-semibold mb-2">{label}</p>
        {payload.map((p: any) => (
          <div key={p.dataKey} className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
            <span className="text-gray-400">{p.name}:</span>
            <span className="font-bold" style={{ color: p.color }}>
              ₹{p.value.toLocaleString("en-IN")}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function RevenueChart({ data }: RevenueChartProps) {
  return (
    <div className="glass-card p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Recovery Trend</h3>
          <p className="text-sm text-gray-500 mt-0.5">Last 7 days — Recovered vs Failed Revenue</p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1.5 rounded-full bg-emerald-500 block" />
            <span className="text-gray-400">Recovered</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-1.5 rounded-full bg-rose-500 block" />
            <span className="text-gray-400">Failed</span>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
          <defs>
            <linearGradient id="colorRecovered" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
          <XAxis
            dataKey="date"
            tick={{ fill: "#6b7280", fontSize: 12 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#6b7280", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            type="monotone"
            dataKey="recovered"
            name="Recovered"
            stroke="#10b981"
            strokeWidth={2.5}
            fill="url(#colorRecovered)"
            dot={{ fill: "#10b981", strokeWidth: 0, r: 4 }}
            activeDot={{ r: 6, fill: "#10b981", stroke: "#fff", strokeWidth: 2 }}
          />
          <Area
            type="monotone"
            dataKey="failed"
            name="Failed"
            stroke="#f43f5e"
            strokeWidth={2}
            fill="url(#colorFailed)"
            dot={{ fill: "#f43f5e", strokeWidth: 0, r: 3 }}
            activeDot={{ r: 5, fill: "#f43f5e", stroke: "#fff", strokeWidth: 2 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
