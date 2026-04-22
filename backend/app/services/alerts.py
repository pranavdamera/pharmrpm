from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ..models import Alert, Patient, VitalReading


def _create_alert(db: Session, patient_id: int, alert_type: str, severity: str, message: str):
    alert = Alert(
        patient_id=patient_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        status="open",
    )
    db.add(alert)


def evaluate_patient_alerts(db: Session, patient: Patient):
    readings = (
        db.query(VitalReading)
        .filter(VitalReading.patient_id == patient.id)
        .order_by(VitalReading.recorded_at.desc())
        .limit(6)
        .all()
    )
    if not readings:
        # Enrolled patients with no incoming data should still be visible in workflow.
        _create_alert(db, patient.id, "missing_readings", "red", "No readings available for this patient")
        return

    latest = readings[0]
    now = datetime.utcnow()
    last_age = now - latest.recorded_at

    if last_age > timedelta(hours=72):
        _create_alert(db, patient.id, "missing_readings", "red", "No reading received in over 72 hours")
    elif last_age > timedelta(hours=48):
        _create_alert(db, patient.id, "missing_readings", "yellow", "No reading received in over 48 hours")

    conditions = set(patient.conditions_csv.split(","))
    recent = readings[:3]

    if "HTN" in conditions:
        if latest.systolic and latest.systolic > 180:
            _create_alert(db, patient.id, "hypertension", "red", f"Systolic {latest.systolic} exceeds 180")
        elif latest.systolic and latest.systolic > 140:
            _create_alert(db, patient.id, "hypertension", "yellow", f"Systolic {latest.systolic} exceeds 140")
        if latest.diastolic and latest.diastolic > 120:
            _create_alert(db, patient.id, "hypertension", "red", f"Diastolic {latest.diastolic} exceeds 120")
        diastolic_recent = [r.diastolic for r in recent if r.diastolic is not None]
        if len(diastolic_recent) >= 2 and all(d > 90 for d in diastolic_recent):
            _create_alert(db, patient.id, "hypertension", "yellow", "Sustained diastolic readings above 90")

    if "T2DM" in conditions and latest.glucose:
        if latest.glucose > 250 or latest.glucose < 70:
            _create_alert(db, patient.id, "glucose", "red", f"Critical glucose reading: {latest.glucose}")
        elif latest.glucose > 130:
            _create_alert(db, patient.id, "glucose", "yellow", f"Fasting glucose above goal: {latest.glucose}")

    if "CHF" in conditions:
        chf_readings = [r for r in readings if r.weight is not None]
        if len(chf_readings) >= 2:
            latest_w = chf_readings[0]
            one_day = next(
                (r for r in chf_readings[1:] if (latest_w.recorded_at - r.recorded_at) <= timedelta(hours=24)),
                None,
            )
            two_day = next(
                (r for r in chf_readings[1:] if (latest_w.recorded_at - r.recorded_at) <= timedelta(hours=48)),
                None,
            )
            if two_day and latest_w.weight - two_day.weight > 5:
                _create_alert(db, patient.id, "chf_weight", "red", "Weight gain > 5 lb in 48 hours")
            elif one_day and latest_w.weight - one_day.weight > 2:
                _create_alert(db, patient.id, "chf_weight", "yellow", "Weight gain > 2 lb in 24 hours")

    if "COPD" in conditions:
        spo2_vals = [r.spo2 for r in recent if r.spo2 is not None]
        if latest.spo2 is not None and latest.spo2 < 88:
            _create_alert(db, patient.id, "oxygen", "red", f"SpO2 {latest.spo2}% below 88")
        elif len(spo2_vals) >= 2 and all(v < 93 for v in spo2_vals):
            _create_alert(db, patient.id, "oxygen", "yellow", "Sustained SpO2 below 93")


def evaluate_all_patients_alerts(db: Session):
    db.query(Alert).filter(Alert.status == "open").delete()
    patients = db.query(Patient).all()
    for patient in patients:
        evaluate_patient_alerts(db, patient)
    db.commit()
