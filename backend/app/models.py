from datetime import datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Physician(Base):
    __tablename__ = "physicians"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    npi: Mapped[str] = mapped_column(String(30), unique=True)

    patients = relationship("Patient", back_populates="physician")


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(20))
    phone: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(String(255))
    conditions_csv: Mapped[str] = mapped_column(String(255))
    medications_csv: Mapped[str] = mapped_column(Text)
    med_count: Mapped[int] = mapped_column(Integer, default=0)
    last_refill_date: Mapped[datetime] = mapped_column(Date)
    rpm_status: Mapped[str] = mapped_column(String(30), default="eligible")
    enrolled_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    priority_score: Mapped[int] = mapped_column(Integer, default=0)
    trigger_reasons_csv: Mapped[str] = mapped_column(Text, default="")
    device_offline: Mapped[bool] = mapped_column(Boolean, default=False)
    physician_id: Mapped[int | None] = mapped_column(ForeignKey("physicians.id"), nullable=True)

    physician = relationship("Physician", back_populates="patients")
    devices = relationship("Device", back_populates="patient", cascade="all, delete-orphan")
    vitals = relationship("VitalReading", back_populates="patient", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="patient", cascade="all, delete-orphan")
    interactions = relationship("InteractionLog", back_populates="patient", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    device_type: Mapped[str] = mapped_column(String(50))
    serial_number: Mapped[str] = mapped_column(String(80))
    assigned_date: Mapped[datetime] = mapped_column(Date)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    patient = relationship("Patient", back_populates="devices")


class VitalReading(Base):
    __tablename__ = "vital_readings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    systolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diastolic: Mapped[int | None] = mapped_column(Integer, nullable=True)
    glucose: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    spo2: Mapped[float | None] = mapped_column(Float, nullable=True)
    heart_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    transmission_counted: Mapped[bool] = mapped_column(Boolean, default=True)
    source: Mapped[str] = mapped_column(String(40), default="device")

    patient = relationship("Patient", back_populates="vitals")


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    alert_type: Mapped[str] = mapped_column(String(80))
    severity: Mapped[str] = mapped_column(String(10))
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="open")
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    patient = relationship("Patient", back_populates="alerts")


class InteractionLog(Base):
    __tablename__ = "interaction_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), index=True)
    interaction_type: Mapped[str] = mapped_column(String(30))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    topics_covered: Mapped[str] = mapped_column(Text)
    clinical_notes: Mapped[str] = mapped_column(Text)
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=True)
    billing_period: Mapped[str] = mapped_column(String(7))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="interactions")
