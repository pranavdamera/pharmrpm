from datetime import date, datetime, timedelta
from random import Random

from sqlalchemy.orm import Session

from .models import Device, InteractionLog, Patient, Physician, VitalReading


def _month_string(d: datetime) -> str:
    return d.strftime("%Y-%m")


def seed_demo_data(db: Session):
    db.query(InteractionLog).delete()
    db.query(VitalReading).delete()
    db.query(Device).delete()
    db.query(Patient).delete()
    db.query(Physician).delete()
    db.commit()

    physicians = [
        Physician(name="Dr. Maya Chen", npi="1144256780"),
        Physician(name="Dr. Luis Bennett", npi="1432234511"),
    ]
    db.add_all(physicians)
    db.commit()

    now = datetime.utcnow()
    rng = Random(18)
    condition_sets = [
        ["HTN"],
        ["T2DM"],
        ["CHF"],
        ["COPD"],
        ["HTN", "T2DM"],
        ["HTN", "CHF"],
        ["T2DM", "COPD"],
        ["HTN", "COPD"],
    ]

    names = [
        "Mary Ramirez", "John Patel", "Teresa Kim", "George Williams", "Olivia Miller", "David Singh",
        "Nora Brooks", "Samuel Diaz", "Linda O'Neal", "Henry Collins", "Priya Shah", "Carlos Vega",
        "Evelyn Ross", "Thomas Green", "Ava Howard", "Marcus Lee",
    ]
    patients: list[Patient] = []
    for idx, name in enumerate(names):
        conditions = condition_sets[idx % len(condition_sets)]
        enrolled = idx < 11
        trigger_reasons = ["multiple chronic conditions", "recent refill gap"] if len(conditions) > 1 else ["chronic condition"]
        if idx % 3 == 0:
            trigger_reasons.append("recent ER follow-up")
        patient = Patient(
            name=name,
            age=58 + (idx % 24),
            gender="female" if idx % 2 == 0 else "male",
            phone=f"(555) 010-{1000 + idx}",
            address=f"{200 + idx} Market St, Springfield",
            conditions_csv=",".join(conditions),
            medications_csv="Lisinopril,Metformin,Atorvastatin" if "T2DM" in conditions else "Lisinopril,Atorvastatin",
            med_count=4 + (idx % 5),
            last_refill_date=date.today() - timedelta(days=(idx * 2) % 20),
            rpm_status="enrolled" if enrolled else "eligible",
            enrolled_date=date.today() - timedelta(days=60 - idx) if enrolled else None,
            priority_score=92 - idx * 3,
            trigger_reasons_csv=",".join(trigger_reasons),
            device_offline=True if idx in {3, 9, 14} else False,
            physician_id=physicians[idx % 2].id,
        )
        patients.append(patient)
    db.add_all(patients)
    db.commit()

    device_map = {
        "HTN": "BP cuff",
        "T2DM": "glucometer",
        "CHF": "weight scale",
        "COPD": "pulse oximeter",
    }
    for patient in patients:
        for cond in patient.conditions_csv.split(","):
            db.add(
                Device(
                    patient_id=patient.id,
                    device_type=device_map[cond],
                    serial_number=f"{cond}-{patient.id:03d}-{rng.randint(1000, 9999)}",
                    assigned_date=date.today() - timedelta(days=45),
                    active=True,
                )
            )
    db.commit()

    for patient in patients:
        if patient.rpm_status != "enrolled":
            continue
        for day_offset in range(24):
            if day_offset > 19 and patient.id % 4 == 0:
                continue
            reading_date = now - timedelta(days=day_offset, hours=rng.randint(0, 20))
            if patient.device_offline and day_offset < 4:
                continue
            systolic = 120 + rng.randint(-10, 30)
            diastolic = 76 + rng.randint(-7, 20)
            glucose = 110 + rng.randint(-25, 85) if "T2DM" in patient.conditions_csv else None
            weight = 175 + rng.randint(-3, 4) if "CHF" in patient.conditions_csv else None
            spo2 = 95 + rng.randint(-6, 2) if "COPD" in patient.conditions_csv else None
            if patient.id in {2, 6} and day_offset == 0 and glucose is not None:
                glucose = 268
            if patient.id in {4, 10} and day_offset == 0 and systolic:
                systolic = 186
            if patient.id in {3, 7} and day_offset < 2 and spo2 is not None:
                spo2 = 87
            if patient.id in {5, 8} and day_offset == 0 and weight is not None:
                weight += 6
            db.add(
                VitalReading(
                    patient_id=patient.id,
                    recorded_at=reading_date,
                    systolic=systolic if "HTN" in patient.conditions_csv else None,
                    diastolic=diastolic if "HTN" in patient.conditions_csv else None,
                    glucose=glucose,
                    weight=weight,
                    spo2=spo2,
                    heart_rate=70 + rng.randint(-12, 20),
                    transmission_counted=True,
                    source="device",
                )
            )
    db.commit()

    month = _month_string(now)
    for patient in patients:
        if patient.rpm_status != "enrolled":
            continue
        total_logs = 2 if patient.id % 3 else 3
        for i in range(total_logs):
            start = now - timedelta(days=12 - i * 3, hours=1)
            duration = 8 + (patient.id + i * 4) % 16
            db.add(
                InteractionLog(
                    patient_id=patient.id,
                    interaction_type=["phone", "video", "in_person", "secure_message"][i % 4],
                    start_time=start,
                    end_time=start + timedelta(minutes=duration),
                    duration_minutes=duration,
                    topics_covered="BP trend review, med adherence, symptom check",
                    clinical_notes="Patient engaged well. Reinforced medication and daily reading workflow.",
                    consent_confirmed=True,
                    billing_period=month,
                )
            )
    db.commit()
