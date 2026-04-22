import { useEffect, useState } from "react";
import { api } from "../api";
import { Badge } from "../components/UI";

export function AlertsPage() {
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    api.allAlerts().then(setAlerts);
  }, []);

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Alerts</h2>
      <div className="rounded-lg border bg-white divide-y">
        {alerts.map((a) => (
          <div key={a.id} className="p-3 flex justify-between items-center">
            <div>
              <p className="text-sm font-medium">{a.patient_name}: {a.message}</p>
              <p className="text-xs text-slate-500">{new Date(a.created_at).toLocaleString()} • {a.status}</p>
            </div>
            <Badge text={a.severity} tone={a.severity === "red" ? "red" : "yellow"} />
          </div>
        ))}
      </div>
    </div>
  );
}
