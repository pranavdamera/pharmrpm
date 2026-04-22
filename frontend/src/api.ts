import type { BillingSummary, DashboardSummary, QueuePatient } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://127.0.0.1:8004/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }
  return res.json();
}

export const api = {
  dashboard: () => request<DashboardSummary>("/dashboard/summary"),
  queue: () => request<QueuePatient[]>("/patients/queue"),
  patients: () => request<any[]>("/patients"),
  patientDetail: (id: number) => request<any>(`/patients/${id}`),
  allAlerts: () => request<any[]>("/alerts"),
  resolveAlert: (id: number, payload: any) =>
    request(`/alerts/${id}/resolve`, { method: "POST", body: JSON.stringify(payload) }),
  enrollPatient: (patient_id: number) =>
    request("/patients/enroll", { method: "POST", body: JSON.stringify({ patient_id }) }),
  logInteraction: (payload: any) =>
    request("/interactions/log", { method: "POST", body: JSON.stringify(payload) }),
  billingSummary: (month: string, pharmacySharePercent: number) =>
    request<BillingSummary>(`/billing/summary?month=${month}&pharmacy_share_percent=${pharmacySharePercent}`),
  billingPatients: (month: string) => request<any[]>(`/billing/patients?month=${month}`),
  seedDemo: () => request("/demo/seed", { method: "POST" }),
  ingestMock: (payload: any) =>
    request("/demo/ingest-mock-reading", { method: "POST", body: JSON.stringify(payload) }),
  summaryExportUrl: (month: string) => `${API_BASE}/billing/summary/export?month=${month}`
};
