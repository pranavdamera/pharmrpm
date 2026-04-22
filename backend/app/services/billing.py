from collections import defaultdict
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import InteractionLog, Patient, VitalReading

RATES = {
    "99453": 19.33,
    "99454": 48.42,
    "99457": 48.72,
    "99458": 38.22,
}


def month_bounds(month: str):
    start = datetime.strptime(month + "-01", "%Y-%m-%d")
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def transmission_days_for_month(db: Session, patient_ids: list[int], month: str) -> dict[int, int]:
    start, end = month_bounds(month)
    rows = (
        db.query(VitalReading.patient_id, func.date(VitalReading.recorded_at))
        .filter(VitalReading.patient_id.in_(patient_ids))
        .filter(VitalReading.recorded_at >= start, VitalReading.recorded_at < end)
        .filter(VitalReading.transmission_counted.is_(True))
        .all()
    )
    unique_days: dict[int, set[str]] = defaultdict(set)
    for patient_id, day_str in rows:
        unique_days[patient_id].add(str(day_str))
    return {pid: len(days) for pid, days in unique_days.items()}


def interaction_minutes_for_month(db: Session, patient_ids: list[int], month: str) -> dict[int, int]:
    rows = (
        db.query(InteractionLog.patient_id, func.sum(InteractionLog.duration_minutes))
        .filter(InteractionLog.patient_id.in_(patient_ids))
        .filter(InteractionLog.billing_period == month)
        .group_by(InteractionLog.patient_id)
        .all()
    )
    return {patient_id: int(total or 0) for patient_id, total in rows}


def qualifying_codes(transmission_days: int, interaction_minutes: int) -> list[str]:
    codes: list[str] = []
    if transmission_days >= 16:
        codes.append("99454")
    if interaction_minutes >= 20:
        codes.append("99457")
    if interaction_minutes >= 40:
        codes.append("99458")
    return codes


def billing_status(transmission_days: int, interaction_minutes: int) -> str:
    if transmission_days >= 16 and interaction_minutes >= 20:
        return "billing ready"
    if transmission_days >= 16 or interaction_minutes >= 20:
        return "partially ready"
    return "not ready"


def recurring_value_for_codes(codes: list[str]) -> float:
    return round(sum(RATES[code] for code in codes if code in {"99454", "99457", "99458"}), 2)


def compute_billing_rows(db: Session, month: str):
    enrolled_patients = db.query(Patient).filter(Patient.rpm_status == "enrolled").all()
    ids = [p.id for p in enrolled_patients]
    days_map = transmission_days_for_month(db, ids, month) if ids else {}
    mins_map = interaction_minutes_for_month(db, ids, month) if ids else {}

    rows = []
    for patient in enrolled_patients:
        t_days = days_map.get(patient.id, 0)
        i_mins = mins_map.get(patient.id, 0)
        codes = qualifying_codes(t_days, i_mins)
        rows.append(
            {
                "patient_id": patient.id,
                "patient_name": patient.name,
                "transmission_days": t_days,
                "interaction_minutes": i_mins,
                "qualifying_codes": codes,
                "status": billing_status(t_days, i_mins),
                "recurring_value": recurring_value_for_codes(codes),
            }
        )
    return rows


def revenue_totals(rows: list[dict], pharmacy_share_percent: float):
    gross = round(sum(row["recurring_value"] for row in rows), 2)
    pharmacy_share = round(gross * (pharmacy_share_percent / 100), 2)
    return gross, pharmacy_share
