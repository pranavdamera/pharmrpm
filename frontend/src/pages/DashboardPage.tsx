import { useEffect, useState } from "react";
import { api } from "../api";
import { StatCard } from "../components/UI";
import type { DashboardSummary } from "../types";

export function DashboardPage() {
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.dashboard().then(setData).catch(() => setError("Failed to load dashboard."));
  }, []);

  if (error) return <p className="text-rose-600">{error}</p>;
  if (!data) return <p>Loading dashboard...</p>;

  return (
    <div className="space-y-5">
      <h2 className="text-2xl font-semibold">Dashboard Home</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="Red Alerts Today" value={data.alerts_red} />
        <StatCard title="Yellow Alerts Today" value={data.alerts_yellow} />
        <StatCard title="Active Enrolled Patients" value={data.active_enrolled_patients} />
        <StatCard title="Billing Ready This Month" value={data.billing_ready_patients} />
        <StatCard title="Missing Readings / Offline" value={data.missing_readings_or_offline} />
        <StatCard title="Estimated Gross Revenue" value={`$${data.estimated_monthly_revenue.toFixed(2)}`} />
      </div>
      <div className="rounded-lg border bg-white p-4">
        <p className="text-sm text-slate-700">
          Recurring eligible patient value (99454 + 99457): <span className="font-semibold">$97.14</span>
        </p>
      </div>
    </div>
  );
}
