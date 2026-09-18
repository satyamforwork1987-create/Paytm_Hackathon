"use client";

import { useEffect, useState } from "react";
import { api, Customer } from "@/lib/api";
import { Users, TrendingUp, ArrowRight } from "lucide-react";
import Link from "next/link";

const MOCK_CUSTOMERS: Customer[] = [
  { id: 1, name: "Priya Sharma", email: "priya.sharma@email.com", mobile: "9876543210", ltv: 48500, churn_risk: 0.12, created_at: new Date().toISOString() },
  { id: 2, name: "Rahul Verma", email: "rahul.verma@email.com", mobile: "9123456789", ltv: 32100, churn_risk: 0.34, created_at: new Date().toISOString() },
  { id: 3, name: "Anita Singh", email: "anita.singh@email.com", mobile: "9988776655", ltv: 15750, churn_risk: 0.67, created_at: new Date().toISOString() },
  { id: 4, name: "Vikram Patel", email: "vikram.patel@email.com", mobile: "9871234560", ltv: 8200, churn_risk: 0.45, created_at: new Date().toISOString() },
  { id: 5, name: "Meera Nair", email: "meera.nair@email.com", mobile: "9765432100", ltv: 3400, churn_risk: 0.82, created_at: new Date().toISOString() },
];

function RiskBadge({ risk }: { risk: number }) {
  if (risk > 0.7) return <span className="badge-failed text-xs px-2 py-0.5 rounded-full font-semibold">High Risk</span>;
  if (risk > 0.4) return <span className="badge-pending text-xs px-2 py-0.5 rounded-full font-semibold">Medium Risk</span>;
  return <span className="badge-recovered text-xs px-2 py-0.5 rounded-full font-semibold">Low Risk</span>;
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCustomers()
      .then(setCustomers)
      .catch(() => setCustomers(MOCK_CUSTOMERS))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Users className="w-6 h-6 text-blue-400" />
          Customers
        </h1>
        <p className="text-gray-500 text-sm mt-1">Click a customer to view their full profile and AI action history</p>
      </div>

      {loading ? (
        <div className="glass-card p-12 text-center">
          <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto" />
        </div>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-800/60">
                {["Name", "Email", "Mobile", "LTV", "Churn Risk", ""].map((h) => (
                  <th key={h} className="text-left px-6 py-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {customers.map((c) => (
                <tr key={c.id} className="border-b border-gray-800/40 table-row-hover">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-xs font-bold text-white">
                        {c.name.charAt(0)}
                      </div>
                      <span className="text-sm font-medium text-gray-200">{c.name}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{c.email}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{c.mobile}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-1.5">
                      <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-sm font-bold text-emerald-400">
                        ₹{c.ltv.toLocaleString("en-IN", { maximumFractionDigits: 0 })}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="space-y-1">
                      <RiskBadge risk={c.churn_risk} />
                      <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${c.churn_risk > 0.7 ? "bg-rose-500" : c.churn_risk > 0.4 ? "bg-amber-500" : "bg-emerald-500"}`}
                          style={{ width: `${c.churn_risk * 100}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <Link
                      href={`/customers/${c.id}`}
                      className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      View <ArrowRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
