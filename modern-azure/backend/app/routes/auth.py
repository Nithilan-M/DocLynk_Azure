import os
import secrets
from hashlib import sha256
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import create_access_token, hash_password, verify_password
from ..database import get_db
from ..email import send_password_reset_otp_email, send_registration_otp_email
from ..models import PasswordResetOTP, PendingRegistration, User, UserRole
from ..schemas import (
    ForgotPasswordRequest,
    MessageResponse,
    RegisterResponse,
    ResendVerificationRequest,
    ResetPasswordWithOtpRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    VerifyEmailResponse,
    VerifyOtpRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
OTP_MAX_ATTEMPTS = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))
OTP_SECRET_KEY = os.getenv("OTP_SECRET_KEY") or os.getenv("JWT_SECRET_KEY")


def _new_otp_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _otp_hash(*, registration_id: int, email: str, otp: str) -> str:
    payload = f"{OTP_SECRET_KEY}:{registration_id}:{email.lower()}:{otp}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _password_reset_otp_hash(*, email: str, otp: str) -> str:
    payload = f"{OTP_SECRET_KEY}:reset:{email.lower()}:{otp}"
    return sha256(payload.encode("utf-8")).hexdigest()


def _map_user_integrity_error(exc: IntegrityError) -> HTTPException:
    error_text = str(getattr(exc, "orig", exc)).lower()
    if "unique_name_per_role" in error_text:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this name already exists for the selected role. Please use a different name.",
        )
    if "users_email_key" in error_text or "email" in error_text:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unable to create account due to existing data constraints.",
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    email = payload.email.lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    pending = db.scalar(select(PendingRegistration).where(PendingRegistration.email == email))
    otp_code = _new_otp_code()
    otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)

    if pending:
        pending.full_name = payload.full_name
        pending.password_hash = hash_password(payload.password)
        pending.role = payload.role.value
        pending.specialization = payload.specialization if payload.role == UserRole.DOCTOR else None
        pending.otp_expires_at = otp_expires_at
        pending.otp_attempts = 0
        db.add(pending)
        db.flush()
        pending.otp_hash = _otp_hash(registration_id=pending.id, email=email, otp=otp_code)
    else:
        pending = PendingRegistration(
            full_name=payload.full_name,
            email=email,
            password_hash=hash_password(payload.password),
            role=payload.role.value,
            specialization=payload.specialization if payload.role == UserRole.DOCTOR else None,
            otp_hash="",
            otp_expires_at=otp_expires_at,
            otp_attempts=0,
        )
        db.add(pending)
        db.flush()
        pending.otp_hash = _otp_hash(registration_id=pending.id, email=email, otp=otp_code)

    db.commit()

    email_ok, email_message = send_registration_otp_email(
        to_email=email,
        full_name=payload.full_name,
        otp_code=otp_code,
        expires_minutes=OTP_EXPIRE_MINUTES,
    )
    if not email_ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP email: {email_message}",
        )

    return {
        "message": "OTP sent to your email.",
        "email": email,
    }


@router.post("/verify-otp", response_model=VerifyEmailResponse)
def verify_otp(payload: VerifyOtpRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    pending = db.scalar(select(PendingRegistration).where(PendingRegistration.email == email))
    if not pending:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration request not found")

    now = datetime.now(timezone.utc)
    expiry = pending.otp_expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired. Please request a new one.")

    if pending.otp_attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many failed attempts. Please request a new OTP.")

    expected_hash = _otp_hash(registration_id=pending.id, email=email, otp=payload.otp)
    if not secrets.compare_digest(expected_hash, pending.otp_hash):
        pending.otp_attempts += 1
        db.add(pending)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        db.delete(pending)
        db.commit()
        if not bool(getattr(existing, "is_verified", False)):
            existing.is_verified = True
            db.add(existing)
            db.commit()
        return {"message": "Email verified successfully.", "verified": True}

    user = User(
        full_name=pending.full_name,
        email=email,
        password_hash=pending.password_hash,
        role=pending.role,
        is_verified=True,
        verification_token=None,
        token_expiry=None,
    )
    db.add(user)
    try:
        db.delete(pending)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _map_user_integrity_error(exc)

    return {"message": "Email verified and account created successfully.", "verified": True}


@router.post("/resend-verification", response_model=RegisterResponse)
def resend_verification(payload: ResendVerificationRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    pending = db.scalar(select(PendingRegistration).where(PendingRegistration.email == email))
    if not pending:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registration request not found")

    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified. Please login.")

    otp_code = _new_otp_code()
    pending.otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)
    pending.otp_attempts = 0
    pending.otp_hash = _otp_hash(registration_id=pending.id, email=email, otp=otp_code)
    db.add(pending)
    db.commit()

    email_ok, email_message = send_registration_otp_email(
        to_email=email,
        full_name=pending.full_name,
        otp_code=otp_code,
        expires_minutes=OTP_EXPIRE_MINUTES,
    )
    if not email_ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend OTP email: {email_message}",
        )

    return {
        "message": "A new OTP has been sent to your email.",
        "email": email,
    }


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(subject=str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    user = db.scalar(select(User).where(User.email == email))

    # Prevent email enumeration by returning same response even if account does not exist.
    generic_message = "If an account exists with this email, a password reset OTP has been sent."
    if not user:
        return {"message": generic_message}

    otp_code = _new_otp_code()
    otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)
    reset_row = db.scalar(select(PasswordResetOTP).where(PasswordResetOTP.email == email))

    if reset_row:
        reset_row.otp_expires_at = otp_expires_at
        reset_row.otp_attempts = 0
        reset_row.otp_hash = _password_reset_otp_hash(email=email, otp=otp_code)
        db.add(reset_row)
    else:
        reset_row = PasswordResetOTP(
            email=email,
            otp_hash=_password_reset_otp_hash(email=email, otp=otp_code),
            otp_expires_at=otp_expires_at,
            otp_attempts=0,
        )
        db.add(reset_row)

    db.commit()

    email_ok, email_message = send_password_reset_otp_email(
        to_email=email,
        full_name=user.full_name,
        otp_code=otp_code,
        expires_minutes=OTP_EXPIRE_MINUTES,
    )
    if not email_ok:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send password reset OTP: {email_message}",
        )

    return {"message": generic_message}


@router.post("/reset-password-otp", response_model=MessageResponse)
def reset_password_otp(payload: ResetPasswordWithOtpRequest, db: Session = Depends(get_db)):
    email = payload.email.lower()
    reset_row = db.scalar(select(PasswordResetOTP).where(PasswordResetOTP.email == email))
    if not reset_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reset request not found")

    now = datetime.now(timezone.utc)
    expiry = reset_row.otp_expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP has expired. Please request a new one.")

    if reset_row.otp_attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many failed attempts. Please request a new OTP.")

    expected_hash = _password_reset_otp_hash(email=email, otp=payload.otp)
    if not secrets.compare_digest(expected_hash, reset_row.otp_hash):
        reset_row.otp_attempts += 1
        db.add(reset_row)
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    user = db.scalar(select(User).where(User.email == email))
    if not user:
        db.delete(reset_row)
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = hash_password(payload.new_password)
    db.add(user)
    db.delete(reset_row)
    db.commit()

    return {"message": "Password reset successfully. Please login with your new password."}
