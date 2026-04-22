from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    alerts_red: int
    alerts_yellow: int
    active_enrolled_patients: int
    billing_ready_patients: int
    missing_readings_or_offline: int
    estimated_monthly_revenue: float


class QueuePatient(BaseModel):
    id: int
    name: str
    age: int
    conditions: list[str]
    med_count: int
    last_refill_date: date
    trigger_reasons: list[str]
    priority_score: int
    rpm_status: str


class EnrollPatientRequest(BaseModel):
    patient_id: int
    physician_id: int | None = None


class AlertResolveRequest(BaseModel):
    status: Literal[
        "monitored",
        "patient_contacted",
        "med_adherence_counseling",
        "escalated_to_physician",
    ]
    resolution_note: str = Field(min_length=4)
    time_spent_minutes: int | None = Field(default=None, ge=0, le=120)


class InteractionLogRequest(BaseModel):
    patient_id: int
    interaction_type: Literal["phone", "video", "in_person", "secure_message"]
    start_time: datetime
    end_time: datetime
    topics_covered: str
    clinical_notes: str
    consent_confirmed: bool
    billing_period: str


class IngestReadingRequest(BaseModel):
    patient_id: int
    recorded_at: datetime | None = None
    systolic: int | None = None
    diastolic: int | None = None
    glucose: float | None = None
    weight: float | None = None
    spo2: float | None = None
    heart_rate: float | None = None
    source: str = "device"


class BillingPatientRow(BaseModel):
    patient_id: int
    patient_name: str
    transmission_days: int
    interaction_minutes: int
    qualifying_codes: list[str]
    status: str
    recurring_value: float


class BillingSummary(BaseModel):
    month: str
    total_enrolled_patients: int
    patients_with_16_days: int
    patients_with_20_minutes: int
    qualifying_99454: int
    qualifying_99457: int
    qualifying_99458: int
    estimated_gross_revenue: float
    estimated_pharmacy_share: float
    pharmacy_share_percent: float
