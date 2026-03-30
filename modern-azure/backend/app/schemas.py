from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from .models import AppointmentStatus, UserRole


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    specialization: str | None = Field(default=None, max_length=120)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    specialization: str | None = None
    is_admin: bool = False
    is_verified: bool = False

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


class DoctorOut(BaseModel):
    id: int
    full_name: str
    specialization: str | None = None

    model_config = {"from_attributes": True}


class AppointmentCreate(BaseModel):
    doctor_id: int = Field(gt=0)
    date: date
    time_slot: str = Field(pattern=r"^([01][0-9]|2[0-3]):(00|30)$")
    reason: str | None = Field(default=None, max_length=1000)


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    patient_name: str | None = None
    doctor_name: str | None = None
    scheduled_at: datetime
    reason: str | None
    status: AppointmentStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AppointmentStatusUpdate(BaseModel):
    status: AppointmentStatus


class MessageResponse(BaseModel):
    message: str


class RegisterResponse(BaseModel):
    message: str
    email: EmailStr


class VerifyEmailResponse(BaseModel):
    message: str
    verified: bool


class VerifyOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(pattern=r"^\d{6}$")


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordWithOtpRequest(BaseModel):
    email: EmailStr
    otp: str = Field(pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)
