import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Badge } from "../components/UI";

export function PatientsPage() {
  const [rows, setRows] = useState<any[]>([]);

  useEffect(() => {
    api.patients().then(setRows);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">All Patients</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {rows.map((p) => (
          <div key={p.id} className="rounded-lg border bg-white p-4">
            <div className="flex items-center justify-between">
              <Link className="font-semibold text-teal-700 hover:underline" to={`/patients/${p.id}`}>{p.name}</Link>
              <Badge text={p.rpm_status} tone={p.rpm_status === "enrolled" ? "green" : "slate"} />
            </div>
            <p className="text-sm text-slate-600 mt-1">Age {p.age} • {p.conditions.join(", ")}</p>
            <div className="mt-2 text-xs text-slate-500">Priority score: {p.priority_score}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
