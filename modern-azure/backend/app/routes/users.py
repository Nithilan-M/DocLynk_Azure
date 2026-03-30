from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import require_role
from ..database import get_db
from ..models import User, UserRole
from ..schemas import DoctorOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/doctors", response_model=list[DoctorOut])
def list_doctors(
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.DOCTOR, UserRole.PATIENT)),
):
    doctors = db.scalars(
        select(User)
        .where(func.lower(func.coalesce(User.role, "")) == UserRole.DOCTOR.value)
        .order_by(User.full_name.asc())
    ).all()
    return [{"id": doctor.id, "full_name": doctor.full_name, "specialization": None} for doctor in doctors]
