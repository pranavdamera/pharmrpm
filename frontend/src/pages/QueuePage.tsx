import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Badge } from "../components/UI";
import type { QueuePatient } from "../types";

export function QueuePage() {
  const [rows, setRows] = useState<QueuePatient[]>([]);
  const [error, setError] = useState("");

  const load = () => api.queue().then(setRows).catch(() => setError("Failed to load queue"));

  useEffect(() => {
    load();
  }, []);

  const enroll = async (patientId: number) => {
    await api.enrollPatient(patientId);
    load();
  };

  if (error) return <p className="text-rose-600">{error}</p>;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Daily Patient Queue</h2>
      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-slate-100">
            <tr>
              <th className="text-left p-3">Patient</th><th className="text-left p-3">Conditions</th><th className="text-left p-3">Meds</th>
              <th className="text-left p-3">Last Refill</th><th className="text-left p-3">Triggers</th><th className="text-left p-3">Priority</th><th className="text-left p-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((p) => (
              <tr key={p.id} className="border-t">
                <td className="p-3">
                  <Link className="text-teal-700 hover:underline" to={`/patients/${p.id}`}>{p.name}</Link>
                  <div className="text-xs text-slate-500">Age {p.age}</div>
                </td>
                <td className="p-3">{p.conditions.join(", ")}</td>
                <td className="p-3">{p.med_count}</td>
                <td className="p-3">{p.last_refill_date}</td>
                <td className="p-3">{p.trigger_reasons.join(", ")}</td>
                <td className="p-3"><Badge text={String(p.priority_score)} tone={p.priority_score > 80 ? "red" : "yellow"} /></td>
                <td className="p-3">
                  {p.rpm_status === "enrolled" ? (
                    <Badge text="Enrolled" tone="green" />
                  ) : (
                    <button className="rounded bg-teal-600 text-white px-3 py-1" onClick={() => enroll(p.id)}>Enroll</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
