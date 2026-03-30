import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class UserRole(str, enum.Enum):
    DOCTOR = "doctor"
    PATIENT = "patient"


class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column("name", String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str | None] = mapped_column("password", Text(), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean(), default=False, nullable=False)
    verification_token: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    doctor_appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", foreign_keys="Appointment.doctor_id", back_populates="doctor"
    )
    patient_appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", foreign_keys="Appointment.patient_id", back_populates="patient"
    )


class PendingRegistration(Base):
    __tablename__ = "pending_registrations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text(), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(120), nullable=True)
    otp_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    otp_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    otp_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class PasswordResetOTP(Base):
    __tablename__ = "password_reset_otps"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    otp_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    otp_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    otp_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("doctor_id", "date", "time_slot", name="appointments_doctor_id_date_time_slot_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[Date] = mapped_column(Date(), nullable=False)
    time_slot: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="Pending", nullable=False)

    doctor: Mapped[User] = relationship("User", foreign_keys=[doctor_id], back_populates="doctor_appointments")
    patient: Mapped[User] = relationship("User", foreign_keys=[patient_id], back_populates="patient_appointments")
