from datetime import datetime
from io import BytesIO

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine, get_db
from .models import Alert, Device, InteractionLog, Patient, Physician, VitalReading
from .schemas import (
    AlertResolveRequest,
    BillingSummary,
    DashboardSummary,
    EnrollPatientRequest,
    IngestReadingRequest,
    InteractionLogRequest,
)
from .seed import seed_demo_data
from .services.alerts import evaluate_all_patients_alerts, evaluate_patient_alerts
from .services.billing import (
    RATES,
    compute_billing_rows,
    interaction_minutes_for_month,
    month_bounds,
    revenue_totals,
    transmission_days_for_month,
)
from .services.interactions import calculate_duration_minutes

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PharmRPM MVP API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def current_month() -> str:
    return datetime.utcnow().strftime("%Y-%m")


@app.on_event("startup")
def startup_seed():
    db = SessionLocal()
    try:
        if db.query(Patient).count() == 0:
            seed_demo_data(db)
        evaluate_all_patients_alerts(db)
    finally:
        db.close()


@app.get("/api/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)):
    month = current_month()
    billing_rows = compute_billing_rows(db, month)
    red_alerts = db.query(Alert).filter(Alert.status == "open", Alert.severity == "red").count()
    yellow_alerts = db.query(Alert).filter(Alert.status == "open", Alert.severity == "yellow").count()
    active_enrolled = db.query(Patient).filter(Patient.rpm_status == "enrolled").count()
    billing_ready = len([r for r in billing_rows if r["status"] == "billing ready"])
    missing = db.query(Patient).filter((Patient.device_offline.is_(True)) | (Patient.rpm_status == "enrolled")).all()
    missing_count = 0
    for patient in missing:
        latest = (
            db.query(VitalReading)
            .filter(VitalReading.patient_id == patient.id)
            .order_by(VitalReading.recorded_at.desc())
            .first()
        )
        if patient.device_offline or not latest or (datetime.utcnow() - latest.recorded_at).total_seconds() > 48 * 3600:
            missing_count += 1
    gross, _ = revenue_totals(billing_rows, 65)
    return DashboardSummary(
        alerts_red=red_alerts,
        alerts_yellow=yellow_alerts,
        active_enrolled_patients=active_enrolled,
        billing_ready_patients=billing_ready,
        missing_readings_or_offline=missing_count,
        estimated_monthly_revenue=gross,
    )


@app.get("/api/patients/queue")
def patient_queue(db: Session = Depends(get_db)):
    patients = (
        db.query(Patient)
        .order_by(desc(Patient.priority_score), desc(Patient.last_refill_date))
        .limit(20)
        .all()
    )
    return [
        {
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "conditions": p.conditions_csv.split(","),
            "med_count": p.med_count,
            "last_refill_date": p.last_refill_date,
            "trigger_reasons": p.trigger_reasons_csv.split(",") if p.trigger_reasons_csv else [],
            "priority_score": p.priority_score,
            "rpm_status": p.rpm_status,
        }
        for p in patients
    ]


@app.post("/api/patients/enroll")
def enroll_patient(payload: EnrollPatientRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.rpm_status = "enrolled"
    patient.enrolled_date = datetime.utcnow().date()
    if payload.physician_id:
        physician = db.query(Physician).filter(Physician.id == payload.physician_id).first()
        if not physician:
            raise HTTPException(status_code=404, detail="Physician not found")
        patient.physician_id = physician.id
    db.commit()
    return {"ok": True, "patient_id": patient.id}


@app.get("/api/patients")
def list_patients(db: Session = Depends(get_db)):
    patients = db.query(Patient).order_by(Patient.name).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "age": p.age,
            "conditions": p.conditions_csv.split(","),
            "rpm_status": p.rpm_status,
            "device_offline": p.device_offline,
            "priority_score": p.priority_score,
        }
        for p in patients
    ]


@app.get("/api/patients/{patient_id}")
def patient_detail(patient_id: int, db: Session = Depends(get_db)):
    month = current_month()
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    devices = db.query(Device).filter(Device.patient_id == patient_id).all()
    vitals = (
        db.query(VitalReading).filter(VitalReading.patient_id == patient_id).order_by(VitalReading.recorded_at.desc()).all()
    )
    recent_vitals = vitals[:20]
    alerts = db.query(Alert).filter(Alert.patient_id == patient_id).order_by(Alert.created_at.desc()).limit(15).all()
    interactions = (
        db.query(InteractionLog)
        .filter(InteractionLog.patient_id == patient_id)
        .order_by(InteractionLog.start_time.desc())
        .limit(20)
        .all()
    )
    tx_days = transmission_days_for_month(db, [patient_id], month).get(patient_id, 0)
    mins = interaction_minutes_for_month(db, [patient_id], month).get(patient_id, 0)

    seven_day = [v for v in vitals if (datetime.utcnow() - v.recorded_at).days <= 7]
    summary = {
        "avg_systolic": round(sum(v.systolic for v in seven_day if v.systolic) / max(1, len([v for v in seven_day if v.systolic])), 1),
        "avg_diastolic": round(sum(v.diastolic for v in seven_day if v.diastolic) / max(1, len([v for v in seven_day if v.diastolic])), 1),
        "avg_glucose": round(sum(v.glucose for v in seven_day if v.glucose) / max(1, len([v for v in seven_day if v.glucose])), 1),
        "avg_weight": round(sum(v.weight for v in seven_day if v.weight) / max(1, len([v for v in seven_day if v.weight])), 1),
        "avg_spo2": round(sum(v.spo2 for v in seven_day if v.spo2) / max(1, len([v for v in seven_day if v.spo2])), 1),
        "avg_hr": round(sum(v.heart_rate for v in seven_day if v.heart_rate) / max(1, len([v for v in seven_day if v.heart_rate])), 1),
    }

    return {
        "id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "phone": patient.phone,
        "address": patient.address,
        "conditions": patient.conditions_csv.split(","),
        "medications": [m.strip() for m in patient.medications_csv.split(",") if m.strip()],
        "devices": [{"id": d.id, "device_type": d.device_type, "serial_number": d.serial_number} for d in devices],
        "physician": patient.physician.name if patient.physician else "Unassigned",
        "rpm_status": patient.rpm_status,
        "transmission_days": tx_days,
        "interaction_minutes": mins,
        "billing_ready": tx_days >= 16 and mins >= 20,
        "cpt_qualifications": {
            "99453": patient.enrolled_date is not None,
            "99454": tx_days >= 16,
            "99457": mins >= 20,
            "99458": mins >= 40,
        },
        "seven_day_summary": summary,
        "recent_vitals": [
            {
                "id": v.id,
                "recorded_at": v.recorded_at,
                "systolic": v.systolic,
                "diastolic": v.diastolic,
                "glucose": v.glucose,
                "weight": v.weight,
                "spo2": v.spo2,
                "heart_rate": v.heart_rate,
                "transmission_counted": v.transmission_counted,
            }
            for v in recent_vitals
        ],
        "alerts": [
            {
                "id": a.id,
                "created_at": a.created_at,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "status": a.status,
                "resolution_note": a.resolution_note,
            }
            for a in alerts
        ],
        "interactions": [
            {
                "id": i.id,
                "interaction_type": i.interaction_type,
                "start_time": i.start_time,
                "end_time": i.end_time,
                "duration_minutes": i.duration_minutes,
                "topics_covered": i.topics_covered,
                "clinical_notes": i.clinical_notes,
                "consent_confirmed": i.consent_confirmed,
                "billing_period": i.billing_period,
            }
            for i in interactions
        ],
    }


@app.get("/api/patients/{patient_id}/vitals")
def patient_vitals(patient_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(VitalReading).filter(VitalReading.patient_id == patient_id).order_by(VitalReading.recorded_at.desc()).limit(50).all()
    )
    return rows


@app.get("/api/patients/{patient_id}/alerts")
def patient_alerts(patient_id: int, db: Session = Depends(get_db)):
    rows = db.query(Alert).filter(Alert.patient_id == patient_id).order_by(Alert.created_at.desc()).all()
    return rows


@app.get("/api/alerts")
def all_alerts(db: Session = Depends(get_db)):
    rows = db.query(Alert).order_by(Alert.created_at.desc()).limit(100).all()
    return [
        {
            "id": a.id,
            "patient_id": a.patient_id,
            "patient_name": a.patient.name if a.patient else "",
            "created_at": a.created_at,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "status": a.status,
            "resolution_note": a.resolution_note,
        }
        for a in rows
    ]


@app.post("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, payload: AlertResolveRequest, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = payload.status
    alert.resolution_note = payload.resolution_note
    alert.time_spent_minutes = payload.time_spent_minutes
    alert.resolved_at = datetime.utcnow()
    if payload.time_spent_minutes and payload.time_spent_minutes > 0:
        db.add(
            InteractionLog(
                patient_id=alert.patient_id,
                interaction_type="phone",
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow(),
                duration_minutes=payload.time_spent_minutes,
                topics_covered=f"Alert follow-up: {alert.alert_type}",
                clinical_notes=payload.resolution_note,
                consent_confirmed=True,
                billing_period=current_month(),
            )
        )
    db.commit()
    return {"ok": True}


@app.post("/api/interactions/log")
def log_interaction(payload: InteractionLogRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    try:
        duration = calculate_duration_minutes(payload.start_time, payload.end_time)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    interaction = InteractionLog(
        patient_id=payload.patient_id,
        interaction_type=payload.interaction_type,
        start_time=payload.start_time,
        end_time=payload.end_time,
        duration_minutes=duration,
        topics_covered=payload.topics_covered,
        clinical_notes=payload.clinical_notes,
        consent_confirmed=payload.consent_confirmed,
        billing_period=payload.billing_period,
    )
    db.add(interaction)
    db.commit()
    return {"ok": True, "duration_minutes": duration}


@app.get("/api/billing/summary", response_model=BillingSummary)
def billing_summary(
    month: str = Query(default_factory=current_month),
    pharmacy_share_percent: float = Query(default=65, ge=0, le=100),
    db: Session = Depends(get_db),
):
    rows = compute_billing_rows(db, month)
    gross, share = revenue_totals(rows, pharmacy_share_percent)
    return BillingSummary(
        month=month,
        total_enrolled_patients=len(rows),
        patients_with_16_days=len([r for r in rows if r["transmission_days"] >= 16]),
        patients_with_20_minutes=len([r for r in rows if r["interaction_minutes"] >= 20]),
        qualifying_99454=len([r for r in rows if "99454" in r["qualifying_codes"]]),
        qualifying_99457=len([r for r in rows if "99457" in r["qualifying_codes"]]),
        qualifying_99458=len([r for r in rows if "99458" in r["qualifying_codes"]]),
        estimated_gross_revenue=gross,
        estimated_pharmacy_share=share,
        pharmacy_share_percent=pharmacy_share_percent,
    )


@app.get("/api/billing/patients")
def billing_patients(month: str = Query(default_factory=current_month), db: Session = Depends(get_db)):
    return compute_billing_rows(db, month)


@app.get("/api/billing/summary/export")
def export_billing_summary(month: str = Query(default_factory=current_month), db: Session = Depends(get_db)):
    rows = compute_billing_rows(db, month)
    gross, share = revenue_totals(rows, 65)
    payload = {
        "month": month,
        "rates_2026": RATES,
        "summary": {
            "total_patients": len(rows),
            "gross_revenue": gross,
            "pharmacy_share_65_percent": share,
        },
        "patients": rows,
    }
    import json

    data = json.dumps(payload, indent=2).encode("utf-8")
    return StreamingResponse(
        BytesIO(data),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=pharmrpm-summary-{month}.json"},
    )


@app.post("/api/demo/seed")
def reseed_demo(db: Session = Depends(get_db)):
    seed_demo_data(db)
    evaluate_all_patients_alerts(db)
    return {"ok": True}


@app.post("/api/demo/ingest-mock-reading")
def ingest_mock_reading(payload: IngestReadingRequest, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    reading = VitalReading(
        patient_id=payload.patient_id,
        recorded_at=payload.recorded_at or datetime.utcnow(),
        systolic=payload.systolic,
        diastolic=payload.diastolic,
        glucose=payload.glucose,
        weight=payload.weight,
        spo2=payload.spo2,
        heart_rate=payload.heart_rate,
        source=payload.source,
        transmission_counted=True,
    )
    db.add(reading)
    db.commit()
    evaluate_patient_alerts(db, patient)
    db.commit()
    return {"ok": True, "reading_id": reading.id}


@app.get("/api/meta/rates")
def rates():
    return {"rates": RATES, "recurring_per_eligible_patient": 97.14}
