from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import and_, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import require_role
from ..database import get_db
from ..models import Appointment, AppointmentStatus, User, UserRole
from ..schemas import AppointmentCreate, AppointmentOut, AppointmentStatusUpdate

router = APIRouter(prefix="/appointments", tags=["appointments"])


def _generate_time_slots() -> list[str]:
    slots = []
    for hour in range(9, 17):
        for minute in (0, 30):
            slots.append(datetime(2000, 1, 1, hour, minute).strftime("%H:%M"))
    return slots


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _to_time_slot(value: datetime) -> str:
    return value.strftime("%H:%M")


def _slot_start(value: str | None) -> str:
    return ((value or "").split("-")[0]).strip()


def _normalize_slot_label(value: str | None) -> str | None:
    token = _slot_start(value)
    if not token:
        return None
    for fmt in ["%I:%M %p", "%H:%M", "%H:%M:%S"]:
        try:
            return datetime.strptime(token, fmt).strftime("%H:%M")
        except ValueError:
            continue
    return None


def _parse_datetime(date_value, time_slot: str | None) -> datetime:
    token = _slot_start(time_slot)
    parsed_time = None
    for fmt in ["%I:%M %p", "%H:%M", "%H:%M:%S"]:
        try:
            parsed_time = datetime.strptime(token, fmt).time()
            break
        except ValueError:
            continue
    if parsed_time is None:
        parsed_time = datetime.min.time().replace(hour=9)
    # Return a naive local datetime so UI rendering does not apply unwanted UTC timezone shifts.
    return datetime.combine(date_value, parsed_time)


def _status_to_db(value: AppointmentStatus) -> str:
    if value == AppointmentStatus.APPROVED:
        return "Approved"
    if value == AppointmentStatus.REJECTED:
        return "Rejected"
    if value == AppointmentStatus.CANCELLED:
        return "Rejected"
    return "Pending"


def _status_from_db(value: str | None) -> AppointmentStatus:
    normalized = (value or "Pending").strip().lower()
    if normalized == "approved":
        return AppointmentStatus.APPROVED
    if normalized == "rejected":
        return AppointmentStatus.REJECTED
    return AppointmentStatus.PENDING


def _appointment_out(item: Appointment, doctor_name: str | None, patient_name: str | None) -> dict:
    scheduled_at = _parse_datetime(item.date, item.time_slot)
    return {
        "id": item.id,
        "patient_id": item.patient_id,
        "doctor_id": item.doctor_id,
        "patient_name": patient_name,
        "doctor_name": doctor_name,
        "scheduled_at": scheduled_at,
        "reason": item.reason,
        "status": _status_from_db(item.status),
        "created_at": scheduled_at,
        "updated_at": scheduled_at,
    }


def _booked_slots_for_doctor(db: Session, doctor_id: int, appointment_date) -> set[str]:
    rows = db.scalars(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.date == appointment_date,
                func.lower(func.coalesce(Appointment.status, "")) != "rejected",
            )
        )
    ).all()
    normalized = {_normalize_slot_label(row.time_slot) for row in rows}
    return {slot for slot in normalized if slot}


def _acquire_slot_lock(db: Session, doctor_id: int, appointment_date, time_slot: str) -> None:
    lock_key = f"book:{doctor_id}:{appointment_date}:{time_slot}"[:64]  # MySQL lock names max length is 64
    db.execute(text("SELECT GET_LOCK(:lock_key, 5)"), {"lock_key": lock_key})


@router.get("/available-slots")
@router.get("/availability")
async def get_available_slots(doctor_id: int, date: str, db: Session = Depends(get_db)):
    try:
        selected_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format, use YYYY-MM-DD")

    doctor = db.get(User, doctor_id)
    if not doctor or (doctor.role or "").lower() != UserRole.DOCTOR.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    all_slots = _generate_time_slots()
    booked_slots = _booked_slots_for_doctor(db, doctor_id, selected_date)
    available_slots = [slot for slot in all_slots if slot not in booked_slots]
    return {"available_slots": available_slots}


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def book_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    patient: User = Depends(require_role(UserRole.PATIENT)),
):
    doctor = db.get(User, payload.doctor_id)
    if not doctor or (doctor.role or "").lower() != UserRole.DOCTOR.value:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    appointment_date = payload.date
    appointment_time_slot = _normalize_slot_label(payload.time_slot)

    if not appointment_time_slot or appointment_time_slot not in _generate_time_slots():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid time slot")

    if appointment_date < datetime.now(timezone.utc).date():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Appointment date cannot be in the past")

    # Serialize all bookings for one doctor/date/slot to remove concurrent race windows.
    _acquire_slot_lock(db, payload.doctor_id, appointment_date, appointment_time_slot)

    # Old-project style conflict rule: doctor slot blocks when appointment is not rejected.
    doctor_conflict = db.scalar(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == payload.doctor_id,
                Appointment.date == appointment_date,
                func.lower(func.coalesce(Appointment.status, "")) != "rejected",
            )
        )
    )
    if doctor_conflict:
        doctor_rows = db.scalars(
            select(Appointment).where(
                and_(
                    Appointment.doctor_id == payload.doctor_id,
                    Appointment.date == appointment_date,
                    func.lower(func.coalesce(Appointment.status, "")) != "rejected",
                )
            )
        ).all()
        conflict_starts = {_normalize_slot_label(row.time_slot) for row in doctor_rows}
        if appointment_time_slot in conflict_starts:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot already booked")

    patient_rows = db.scalars(
        select(Appointment).where(
            and_(
                Appointment.patient_id == patient.id,
                Appointment.date == appointment_date,
                func.lower(func.coalesce(Appointment.status, "")) != "rejected",
            )
        )
    ).all()
    patient_conflict_starts = {_normalize_slot_label(row.time_slot) for row in patient_rows}
    if appointment_time_slot in patient_conflict_starts:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have an appointment at this time")

    # If old rejected row exists for this exact slot, recycle it instead of inserting a duplicate.
    reusable = db.scalars(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == payload.doctor_id,
                Appointment.date == appointment_date,
                func.lower(func.coalesce(Appointment.status, "")) == "rejected",
            )
        )
    ).all()
    reusable_slot = next((row for row in reusable if _normalize_slot_label(row.time_slot) == appointment_time_slot), None)

    if reusable_slot:
        reusable_slot.patient_id = patient.id
        reusable_slot.reason = payload.reason
        reusable_slot.time_slot = appointment_time_slot
        reusable_slot.status = "Pending"
        db.commit()
        db.refresh(reusable_slot)
        return _appointment_out(reusable_slot, doctor.full_name, patient.full_name)

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=payload.doctor_id,
        date=appointment_date,
        time_slot=appointment_time_slot,
        reason=payload.reason,
        status="Pending",
    )
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slot already booked")
    db.refresh(appointment)
    return _appointment_out(appointment, doctor.full_name, patient.full_name)


@router.get("", response_model=list[AppointmentOut])
def get_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.DOCTOR, UserRole.PATIENT)),
):
    if (current_user.role or "").lower() == UserRole.DOCTOR.value:
        appointments = db.scalars(select(Appointment).where(Appointment.doctor_id == current_user.id)).all()
    else:
        appointments = db.scalars(select(Appointment).where(Appointment.patient_id == current_user.id)).all()

    result = []
    for item in appointments:
        doctor = db.get(User, item.doctor_id)
        patient = db.get(User, item.patient_id)
        result.append(_appointment_out(item, doctor.full_name if doctor else None, patient.full_name if patient else None))

    result.sort(key=lambda row: row["scheduled_at"], reverse=True)
    return result


@router.put("/{appointment_id}/status", response_model=AppointmentOut)
def update_appointment_status(
    appointment_id: int,
    payload: AppointmentStatusUpdate,
    db: Session = Depends(get_db),
    doctor: User = Depends(require_role(UserRole.DOCTOR)),
):
    if payload.status not in [AppointmentStatus.APPROVED, AppointmentStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctors can only approve or reject appointments",
        )

    appointment = db.get(Appointment, appointment_id)
    if not appointment or appointment.doctor_id != doctor.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if _status_from_db(appointment.status) != AppointmentStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending appointments can be updated")

    appointment.status = _status_to_db(payload.status)
    db.commit()
    db.refresh(appointment)

    patient = db.get(User, appointment.patient_id)
    return _appointment_out(appointment, doctor.full_name, patient.full_name if patient else None)


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    patient: User = Depends(require_role(UserRole.PATIENT)),
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment or appointment.patient_id != patient.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if _status_from_db(appointment.status) == AppointmentStatus.REJECTED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rejected appointments cannot be cancelled")

    # Supabase check constraint allows Pending/Approved/Rejected only.
    appointment.status = "Rejected"
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
