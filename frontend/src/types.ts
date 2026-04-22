export type Severity = "none" | "yellow" | "red";

export interface DashboardSummary {
  alerts_red: number;
  alerts_yellow: number;
  active_enrolled_patients: number;
  billing_ready_patients: number;
  missing_readings_or_offline: number;
  estimated_monthly_revenue: number;
}

export interface QueuePatient {
  id: number;
  name: string;
  age: number;
  conditions: string[];
  med_count: number;
  last_refill_date: string;
  trigger_reasons: string[];
  priority_score: number;
  rpm_status: string;
}

export interface BillingSummary {
  month: string;
  total_enrolled_patients: number;
  patients_with_16_days: number;
  patients_with_20_minutes: number;
  qualifying_99454: number;
  qualifying_99457: number;
  qualifying_99458: number;
  estimated_gross_revenue: number;
  estimated_pharmacy_share: number;
  pharmacy_share_percent: number;
}
