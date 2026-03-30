from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from ..auth import require_admin
from ..database import get_db
from ..models import Appointment, User

router = APIRouter(prefix="/admin", tags=["admin"])


def _status_to_key(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    if normalized == "approved":
        return "approved"
    if normalized == "rejected":
        return "rejected"
    if normalized == "completed":
        return "completed"
    return "pending"


def _status_to_db(value: str) -> str:
    key = value.strip().lower()
    if key == "approved":
        return "Approved"
    if key == "rejected":
        return "Rejected"
    if key == "completed":
        return "Completed"
    return "Pending"


def _appointment_datetime(date_value, time_slot: str | None) -> str:
    token = (time_slot or "").split("-")[0].strip()
    parsed_time = None
    for fmt in ["%H:%M", "%H:%M:%S", "%I:%M %p"]:
        try:
            parsed_time = datetime.strptime(token, fmt).time()
            break
        except ValueError:
            continue
    if parsed_time is None:
        parsed_time = datetime.min.time().replace(hour=9)
    return datetime.combine(date_value, parsed_time).isoformat()


def _generate_time_slots() -> list[str]:
    slots = []
    for hour in range(9, 17):
        for minute in (0, 30):
            slots.append(datetime(2000, 1, 1, hour, minute).strftime("%H:%M"))
    return slots


def _booked_slots_for_date(db: Session, doctor_id: int, target_date: date) -> set[str]:
    rows = db.scalars(
        select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.date == target_date,
                func.lower(func.coalesce(Appointment.status, "")) != "rejected",
            )
        )
    ).all()
    return {(row.time_slot or "").split("-")[0].strip() for row in rows if (row.time_slot or "").strip()}


def _next_seed_date() -> date:
    return datetime.now().date() + timedelta(days=1)


@router.get("/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    total_doctors = db.scalar(select(func.count()).select_from(User).where(func.lower(User.role) == "doctor")) or 0
    total_patients = db.scalar(select(func.count()).select_from(User).where(func.lower(User.role) == "patient")) or 0
    total_admins = db.scalar(select(func.count()).select_from(User).where(User.is_admin.is_(True))) or 0

    total_appointments = db.scalar(select(func.count()).select_from(Appointment)) or 0

    rows = db.scalars(select(Appointment)).all()
    pending_appointments = sum(1 for row in rows if _status_to_key(row.status) == "pending")
    approved_appointments = sum(1 for row in rows if _status_to_key(row.status) == "approved")
    rejected_appointments = sum(1 for row in rows if _status_to_key(row.status) == "rejected")

    recent_users_rows = db.scalars(select(User).order_by(User.id.desc()).limit(5)).all()
    recent_users = [
        {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "role": (user.role or "").lower(),
            "is_admin": bool(getattr(user, "is_admin", False)),
        }
        for user in recent_users_rows
    ]

    recent_appointment_rows = db.scalars(select(Appointment).order_by(Appointment.id.desc()).limit(5)).all()
    recent_appointments = []
    for item in recent_appointment_rows:
        patient = db.get(User, item.patient_id)
        doctor = db.get(User, item.doctor_id)
        recent_appointments.append(
            {
                "id": item.id,
                "date": str(item.date),
                "time_slot": item.time_slot,
                "status": _status_to_key(item.status),
                "reason": item.reason,
                "patient_name": patient.full_name if patient else f"Patient #{item.patient_id}",
                "doctor_name": doctor.full_name if doctor else f"Doctor #{item.doctor_id}",
                "scheduled_at": _appointment_datetime(item.date, item.time_slot),
            }
        )

    return {
        "stats": {
            "total_users": total_users,
            "total_doctors": total_doctors,
            "total_patients": total_patients,
            "total_admins": total_admins,
            "total_appointments": total_appointments,
            "pending_appointments": pending_appointments,
            "approved_appointments": approved_appointments,
            "rejected_appointments": rejected_appointments,
        },
        "recent_users": recent_users,
        "recent_appointments": recent_appointments,
    }


@router.get("/users")
def get_admin_users(
    search: str = Query(default=""),
    role: str = Query(default=""),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = select(User)

    search_term = search.strip()
    if search_term:
        like_value = f"%{search_term}%"
        query = query.where(or_(User.full_name.ilike(like_value), User.email.ilike(like_value)))

    role_value = role.strip().lower()
    if role_value in {"doctor", "patient"}:
        query = query.where(func.lower(User.role) == role_value)

    query = query.order_by(User.id.desc())
    users = db.scalars(query).all()

    return {
        "users": [
            {
                "id": user.id,
                "name": user.full_name,
                "email": user.email,
                "role": (user.role or "").lower(),
                "is_admin": bool(getattr(user, "is_admin", False)),
                "auth_provider": "email",
                "email_verified": True,
            }
            for user in users
        ]
    }


@router.put("/users/{user_id}")
def update_admin_user(
    user_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    role = (payload.get("role") or "").strip().lower()

    if not name or not email or role not in {"doctor", "patient"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user payload")

    duplicate = db.scalar(select(User).where(and_(User.email == email, User.id != user_id)))
    if duplicate:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use")

    user.full_name = name
    user.email = email
    user.role = role
    db.commit()

    return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
def delete_admin_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own account")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    appointments = db.scalars(
        select(Appointment).where(or_(Appointment.patient_id == user_id, Appointment.doctor_id == user_id))
    ).all()
    for appointment in appointments:
        db.delete(appointment)

    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@router.post("/users/{user_id}/toggle-admin")
def toggle_admin_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot change your own admin status")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_admin = not bool(user.is_admin)
    db.commit()
    return {"message": f"Admin status {'granted' if user.is_admin else 'revoked'} successfully"}


@router.get("/appointments")
def get_admin_appointments(
    status_filter: str = Query(default="", alias="status"),
    doctor_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    query = select(Appointment)

    if status_filter.strip():
        normalized_status = _status_to_db(status_filter)
        query = query.where(Appointment.status == normalized_status)

    if doctor_id is not None:
        query = query.where(Appointment.doctor_id == doctor_id)

    query = query.order_by(Appointment.date.desc(), Appointment.time_slot.desc())
    appointments = db.scalars(query).all()

    doctors = db.scalars(select(User).where(func.lower(User.role) == "doctor").order_by(User.full_name.asc())).all()

    items = []
    for item in appointments:
        patient = db.get(User, item.patient_id)
        doctor = db.get(User, item.doctor_id)
        items.append(
            {
                "id": item.id,
                "date": str(item.date),
                "time_slot": item.time_slot,
                "reason": item.reason,
                "status": _status_to_key(item.status),
                "patient_id": item.patient_id,
                "doctor_id": item.doctor_id,
                "patient_name": patient.full_name if patient else f"Patient #{item.patient_id}",
                "patient_email": patient.email if patient else None,
                "doctor_name": doctor.full_name if doctor else f"Doctor #{item.doctor_id}",
                "doctor_email": doctor.email if doctor else None,
                "scheduled_at": _appointment_datetime(item.date, item.time_slot),
            }
        )

    return {
        "appointments": items,
        "doctors": [{"id": doctor.id, "name": doctor.full_name} for doctor in doctors],
    }


@router.put("/appointments/{appointment_id}/status")
def update_admin_appointment_status(
    appointment_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    status_value = (payload.get("status") or "").strip().lower()
    if status_value not in {"pending", "approved", "rejected", "completed"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")

    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    appointment.status = _status_to_db(status_value)
    db.commit()
    return {"message": "Appointment status updated"}


@router.delete("/appointments/{appointment_id}")
def delete_admin_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    appointment = db.get(Appointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    db.delete(appointment)
    db.commit()
    return {"message": "Appointment deleted successfully"}


@router.post("/appointments/seed-missing")
def seed_missing_doctor_appointments(
    payload: dict,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    target_date_raw = (payload.get("date") or "").strip()
    if target_date_raw:
        try:
            target_date = datetime.strptime(target_date_raw, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format, use YYYY-MM-DD")
    else:
        target_date = _next_seed_date()

    doctors = db.scalars(select(User).where(func.lower(func.coalesce(User.role, "")) == "doctor").order_by(User.id.asc())).all()
    patients = db.scalars(select(User).where(func.lower(func.coalesce(User.role, "")) == "patient").order_by(User.id.asc())).all()

    if not doctors:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No doctors found")
    if not patients:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No patients found")

    all_slots = _generate_time_slots()
    created = 0
    skipped = 0
    assignments = []
    patient_index = 0

    for doctor in doctors:
        existing_for_doctor = db.scalar(select(func.count()).select_from(Appointment).where(Appointment.doctor_id == doctor.id)) or 0
        if existing_for_doctor > 0:
            skipped += 1
            continue

        booked_slots = _booked_slots_for_date(db, doctor.id, target_date)
        free_slots = [slot for slot in all_slots if slot not in booked_slots]
        if not free_slots:
            skipped += 1
            continue

        chosen_patient = patients[patient_index % len(patients)]
        patient_index += 1

        appointment = Appointment(
            patient_id=chosen_patient.id,
            doctor_id=doctor.id,
            date=target_date,
            time_slot=free_slots[0],
            reason="Auto-seeded by admin for doctor onboarding",
            status="Pending",
        )
        db.add(appointment)
        created += 1
        assignments.append(
            {
                "doctor_id": doctor.id,
                "doctor_name": doctor.full_name,
                "patient_id": chosen_patient.id,
                "patient_name": chosen_patient.full_name,
                "date": str(target_date),
                "time_slot": free_slots[0],
            }
        )

    db.commit()
    return {
        "message": "Seed completed",
        "target_date": str(target_date),
        "created": created,
        "skipped": skipped,
        "assignments": assignments,
    }
