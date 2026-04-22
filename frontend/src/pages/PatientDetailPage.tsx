import { FormEvent, useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { Badge, StatCard } from "../components/UI";

function severityFromReading(v: any, conditions: string[]): "none" | "yellow" | "red" {
  if (conditions.includes("HTN")) {
    if ((v.systolic ?? 0) > 180 || (v.diastolic ?? 0) > 120) return "red";
    if ((v.systolic ?? 0) > 140 || (v.diastolic ?? 0) > 90) return "yellow";
  }
  if (conditions.includes("T2DM") && v.glucose != null) {
    if (v.glucose > 250 || v.glucose < 70) return "red";
    if (v.glucose > 130) return "yellow";
  }
  if (conditions.includes("COPD") && v.spo2 != null) {
    if (v.spo2 < 88) return "red";
    if (v.spo2 < 93) return "yellow";
  }
  return "none";
}

export function PatientDetailPage() {
  const params = useParams();
  const patientId = Number(params.id);
  const [detail, setDetail] = useState<any | null>(null);
  const [note, setNote] = useState("");
  const [status, setStatus] = useState("monitored");
  const [timeSpent, setTimeSpent] = useState("0");
  const [selectedAlert, setSelectedAlert] = useState<number | null>(null);

  const load = () => api.patientDetail(patientId).then(setDetail);

  useEffect(() => {
    load();
  }, [patientId]);

  const month = useMemo(() => new Date().toISOString().slice(0, 7), []);
  if (!detail) return <p>Loading patient details...</p>;

  const resolveAlert = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedAlert) return;
    await api.resolveAlert(selectedAlert, {
      status,
      resolution_note: note,
      time_spent_minutes: Number(timeSpent)
    });
    setNote("");
    setSelectedAlert(null);
    await load();
  };

  const logInteraction = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    await api.logInteraction({
      patient_id: patientId,
      interaction_type: form.get("interaction_type"),
      start_time: form.get("start_time"),
      end_time: form.get("end_time"),
      topics_covered: form.get("topics_covered"),
      clinical_notes: form.get("clinical_notes"),
      consent_confirmed: form.get("consent_confirmed") === "on",
      billing_period: month
    });
    e.currentTarget.reset();
    await load();
  };

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-semibold">{detail.name}</h2>
          <p className="text-slate-600">{detail.age} y/o {detail.gender} • {detail.phone}</p>
        </div>
        <Badge text={detail.rpm_status} tone={detail.rpm_status === "enrolled" ? "green" : "slate"} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard title="Transmission Days" value={detail.transmission_days} />
        <StatCard title="Interaction Minutes" value={detail.interaction_minutes} />
        <StatCard title="Billing Readiness" value={detail.billing_ready ? "Ready" : "Not ready"} />
        <StatCard title="Supervising Physician" value={detail.physician} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-lg border bg-white p-4 space-y-2">
          <h3 className="font-semibold">Profile</h3>
          <p className="text-sm">Conditions: {detail.conditions.join(", ")}</p>
          <p className="text-sm">Medications: {detail.medications.join(", ")}</p>
          <p className="text-sm">Devices: {detail.devices.map((d: any) => d.device_type).join(", ")}</p>
          <p className="text-sm">Address: {detail.address}</p>
        </div>
        <div className="rounded-lg border bg-white p-4">
          <h3 className="font-semibold mb-2">7-Day Vital Summary</h3>
          <div className="text-sm grid grid-cols-2 gap-2">
            <p>Avg BP: {detail.seven_day_summary.avg_systolic}/{detail.seven_day_summary.avg_diastolic}</p>
            <p>Avg Glucose: {detail.seven_day_summary.avg_glucose}</p>
            <p>Avg Weight: {detail.seven_day_summary.avg_weight}</p>
            <p>Avg SpO2: {detail.seven_day_summary.avg_spo2}</p>
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4">
        <h3 className="font-semibold mb-2">Recent Vitals</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-slate-100">
              <tr><th className="p-2 text-left">Date</th><th className="p-2 text-left">BP</th><th className="p-2 text-left">Glucose</th><th className="p-2 text-left">Weight</th><th className="p-2 text-left">SpO2</th><th className="p-2 text-left">HR</th><th className="p-2 text-left">Severity</th><th className="p-2 text-left">Transmission Day</th></tr>
            </thead>
            <tbody>
              {detail.recent_vitals.slice(0, 12).map((v: any) => {
                const severity = severityFromReading(v, detail.conditions);
                return (
                  <tr key={v.id} className="border-t">
                    <td className="p-2">{new Date(v.recorded_at).toLocaleString()}</td>
                    <td className="p-2">{v.systolic ?? "-"} / {v.diastolic ?? "-"}</td>
                    <td className="p-2">{v.glucose ?? "-"}</td>
                    <td className="p-2">{v.weight ?? "-"}</td>
                    <td className="p-2">{v.spo2 ?? "-"}</td>
                    <td className="p-2">{v.heart_rate ?? "-"}</td>
                    <td className="p-2"><Badge text={severity} tone={severity === "red" ? "red" : severity === "yellow" ? "yellow" : "green"} /></td>
                    <td className="p-2">{v.transmission_counted ? "Yes" : "No"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-lg border bg-white p-4">
          <h3 className="font-semibold mb-2">Recent Alerts</h3>
          <div className="space-y-2">
            {detail.alerts.map((a: any) => (
              <div key={a.id} className="rounded border p-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm">{a.message}</span>
                  <Badge text={a.severity} tone={a.severity === "red" ? "red" : "yellow"} />
                </div>
                <div className="text-xs text-slate-500">{new Date(a.created_at).toLocaleString()} • {a.status}</div>
                {a.status === "open" ? (
                  <button className="mt-2 rounded bg-slate-900 text-white px-2 py-1 text-xs" onClick={() => setSelectedAlert(a.id)}>Resolve</button>
                ) : null}
              </div>
            ))}
          </div>
          {selectedAlert ? (
            <form className="mt-3 space-y-2" onSubmit={resolveAlert}>
              <select className="w-full border rounded p-2 text-sm" value={status} onChange={(e) => setStatus(e.target.value)}>
                <option value="monitored">monitored</option><option value="patient_contacted">patient_contacted</option>
                <option value="med_adherence_counseling">med_adherence_counseling</option><option value="escalated_to_physician">escalated_to_physician</option>
              </select>
              <textarea className="w-full border rounded p-2 text-sm" placeholder="Resolution note (required)" value={note} onChange={(e) => setNote(e.target.value)} required />
              <input className="w-full border rounded p-2 text-sm" value={timeSpent} onChange={(e) => setTimeSpent(e.target.value)} type="number" min={0} placeholder="Time spent (minutes, optional)" />
              <button className="rounded bg-teal-600 text-white px-3 py-1 text-sm">Submit alert resolution</button>
            </form>
          ) : null}
        </div>

        <div className="rounded-lg border bg-white p-4">
          <h3 className="font-semibold mb-2">Log Pharmacist Interaction</h3>
          <form className="space-y-2 text-sm" onSubmit={logInteraction}>
            <select className="w-full border rounded p-2" name="interaction_type" required>
              <option value="phone">phone</option><option value="video">video</option><option value="in_person">in_person</option><option value="secure_message">secure_message</option>
            </select>
            <input className="w-full border rounded p-2" name="start_time" type="datetime-local" required />
            <input className="w-full border rounded p-2" name="end_time" type="datetime-local" required />
            <input className="w-full border rounded p-2" name="topics_covered" placeholder="Topics covered" required />
            <textarea className="w-full border rounded p-2" name="clinical_notes" placeholder="Clinical notes" required />
            <label className="flex items-center gap-2"><input type="checkbox" name="consent_confirmed" defaultChecked /> Patient consent confirmed</label>
            <button className="rounded bg-teal-600 text-white px-3 py-1">Save interaction</button>
          </form>
          <h4 className="font-medium mt-4 mb-2">Interaction History</h4>
          <div className="space-y-2 max-h-64 overflow-auto">
            {detail.interactions.map((i: any) => (
              <div key={i.id} className="rounded border p-2 text-xs">
                <div>{i.interaction_type} • {i.duration_minutes} min • {new Date(i.start_time).toLocaleString()}</div>
                <div className="text-slate-600">{i.topics_covered}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-slate-600 mt-3">CPT 99457: {detail.interaction_minutes >= 20 ? "Qualified" : "Needs 20 minutes"} • CPT 99458: {detail.interaction_minutes >= 40 ? "Qualified" : "Needs 40 minutes"}</p>
        </div>
      </div>
    </div>
  );
}
