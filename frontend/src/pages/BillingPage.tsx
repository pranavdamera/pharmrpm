import { useEffect, useState } from "react";
import { api } from "../api";
import { Badge, StatCard } from "../components/UI";
import type { BillingSummary } from "../types";

export function BillingPage() {
  const month = new Date().toISOString().slice(0, 7);
  const [share, setShare] = useState(65);
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [rows, setRows] = useState<any[]>([]);

  const load = () => {
    api.billingSummary(month, share).then(setSummary);
    api.billingPatients(month).then(setRows);
  };

  useEffect(() => {
    load();
  }, [share]);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Billing + Monthly Summary</h2>
      <div className="rounded-lg border bg-white p-4 flex items-center gap-3">
        <label className="text-sm">Pharmacy share %</label>
        <input type="number" className="border rounded p-2 text-sm w-24" min={0} max={100} value={share} onChange={(e) => setShare(Number(e.target.value))} />
        <a className="rounded bg-slate-900 text-white px-3 py-2 text-sm" href={api.summaryExportUrl(month)}>Generate Summary</a>
      </div>
      {summary ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard title="Enrolled Patients" value={summary.total_enrolled_patients} />
          <StatCard title=">=16 Transmission Days" value={summary.patients_with_16_days} />
          <StatCard title=">=20 Interaction Minutes" value={summary.patients_with_20_minutes} />
          <StatCard title="Qualifying 99454" value={summary.qualifying_99454} />
          <StatCard title="Qualifying 99457" value={summary.qualifying_99457} />
          <StatCard title="Qualifying 99458" value={summary.qualifying_99458} />
          <StatCard title="Estimated Gross Revenue" value={`$${summary.estimated_gross_revenue.toFixed(2)}`} />
          <StatCard title="Estimated Pharmacy Share" value={`$${summary.estimated_pharmacy_share.toFixed(2)}`} />
        </div>
      ) : <p>Loading billing summary...</p>}

      <div className="rounded-lg border bg-white overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-100">
            <tr><th className="p-2 text-left">Patient</th><th className="p-2 text-left">Transmission Days</th><th className="p-2 text-left">Interaction Minutes</th><th className="p-2 text-left">Codes</th><th className="p-2 text-left">Status</th><th className="p-2 text-left">Recurring Value</th></tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr className="border-t" key={row.patient_id}>
                <td className="p-2">{row.patient_name}</td>
                <td className="p-2">{row.transmission_days}</td>
                <td className="p-2">{row.interaction_minutes}</td>
                <td className="p-2">{row.qualifying_codes.join(", ") || "-"}</td>
                <td className="p-2">
                  <Badge text={row.status} tone={row.status === "billing ready" ? "green" : row.status === "partially ready" ? "yellow" : "slate"} />
                </td>
                <td className="p-2">${row.recurring_value.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
