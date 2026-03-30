import json
import os

import requests

try:
    import resend
    RESEND_SDK_AVAILABLE = True
except ImportError:
    resend = None
    RESEND_SDK_AVAILABLE = False


RESEND_API_URL = "https://api.resend.com/emails"


def _format_resend_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        message = payload.get("message") or payload.get("error")
        if isinstance(message, str) and message.strip():
            if "error code: 1010" in message.lower():
                return (
                    "Resend rejected the email (403/1010). Verify your sender domain in Resend "
                    "or send only to your verified owner email while the account is in test mode."
                )
            return message.strip()

    raw_text = response.text.strip()
    if raw_text:
        lowered = raw_text.lower()
        if "error code: 1010" in lowered:
            return (
                "Resend rejected the email (403/1010). Verify your sender domain in Resend "
                "or send only to your verified owner email while the account is in test mode."
            )
        return raw_text

    return f"HTTP {response.status_code}"


def _build_verification_email_html(verification_url: str) -> str:
    return f"""
    <html>
      <body style=\"font-family: Arial, sans-serif; line-height: 1.5; color: #0f172a;\">
        <h2>Verify your DocLynk account</h2>
        <p>Click the link below to verify your account:</p>
        <p><a href=\"{verification_url}\">Verify Email</a></p>
        <p>If you did not create this account, you can ignore this email.</p>
      </body>
    </html>
    """.strip()


def _build_otp_email_html(full_name: str, otp_code: str, expires_minutes: int) -> str:
    return f"""
        <html>
            <body style=\"font-family: Arial, sans-serif; line-height: 1.5; color: #0f172a;\">
                <h2>Verify your DocLynk registration</h2>
                <p>Hello {full_name},</p>
                <p>Your OTP code is:</p>
                <p style=\"font-size: 28px; font-weight: 700; letter-spacing: 4px;\">{otp_code}</p>
                <p>This OTP is valid for {expires_minutes} minutes.</p>
                <p>If you did not initiate this request, you can ignore this email.</p>
            </body>
        </html>
        """.strip()


def _build_password_reset_otp_email_html(full_name: str, otp_code: str, expires_minutes: int) -> str:
        return f"""
        <html>
            <body style=\"font-family: Arial, sans-serif; line-height: 1.5; color: #0f172a;\">
                <h2>Reset your DocLynk password</h2>
                <p>Hello {full_name},</p>
                <p>Your password reset OTP code is:</p>
                <p style=\"font-size: 28px; font-weight: 700; letter-spacing: 4px;\">{otp_code}</p>
                <p>This OTP is valid for {expires_minutes} minutes.</p>
                <p>If you did not request a password reset, ignore this email.</p>
            </body>
        </html>
        """.strip()


def send_verification_email(*, to_email: str, verification_url: str) -> tuple[bool, str]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("RESEND_FROM_EMAIL", "DocLynk <onboarding@resend.dev>").strip()

    if not api_key:
        return False, "RESEND_API_KEY is not configured"

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": "Verify your account",
        "html": _build_verification_email_html(verification_url),
    }

    if RESEND_SDK_AVAILABLE:
        try:
            resend.api_key = api_key
            response = resend.Emails.send(payload)
            if response and response.get("id"):
                return True, "Verification email sent"
            return False, f"Resend SDK error: {response}"
        except Exception as exc:
            message = str(exc)
            if "error code: 1010" in message.lower():
                message = (
                    "Resend rejected the email (403/1010). Verify your sender domain in Resend "
                    "or send only to your verified owner email while the account is in test mode."
                )
            return False, f"Resend SDK error: {message}"

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            data=json.dumps(payload),
            timeout=15,
        )
    except requests.RequestException as exc:
        return False, f"Resend connection error: {exc}"

    if response.ok:
        return True, "Verification email sent"

    return False, f"Resend HTTP error {response.status_code}: {_format_resend_error(response)}"


def send_registration_otp_email(*, to_email: str, full_name: str, otp_code: str, expires_minutes: int) -> tuple[bool, str]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("RESEND_FROM_EMAIL", "DocLynk <onboarding@resend.dev>").strip()

    if not api_key:
        return False, "RESEND_API_KEY is not configured"

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": "Verify your account OTP",
        "html": _build_otp_email_html(full_name=full_name, otp_code=otp_code, expires_minutes=expires_minutes),
    }

    if RESEND_SDK_AVAILABLE:
        try:
            resend.api_key = api_key
            response = resend.Emails.send(payload)
            if response and response.get("id"):
                return True, "OTP sent successfully"
            return False, f"Resend SDK error: {response}"
        except Exception as exc:
            message = str(exc)
            if "error code: 1010" in message.lower():
                message = (
                    "Resend rejected the email (403/1010). Verify your sender domain in Resend "
                    "or send only to your verified owner email while the account is in test mode."
                )
            return False, f"Resend SDK error: {message}"

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            data=json.dumps(payload),
            timeout=15,
        )
    except requests.RequestException as exc:
        return False, f"Resend connection error: {exc}"

    if response.ok:
        return True, "OTP sent successfully"

    return False, f"Resend HTTP error {response.status_code}: {_format_resend_error(response)}"


def send_password_reset_otp_email(*, to_email: str, full_name: str, otp_code: str, expires_minutes: int) -> tuple[bool, str]:
    api_key = os.getenv("RESEND_API_KEY", "").strip()
    from_email = os.getenv("RESEND_FROM_EMAIL", "DocLynk <onboarding@resend.dev>").strip()

    if not api_key:
        return False, "RESEND_API_KEY is not configured"

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": "Reset your password OTP",
        "html": _build_password_reset_otp_email_html(full_name=full_name, otp_code=otp_code, expires_minutes=expires_minutes),
    }

    if RESEND_SDK_AVAILABLE:
        try:
            resend.api_key = api_key
            response = resend.Emails.send(payload)
            if response and response.get("id"):
                return True, "Password reset OTP sent successfully"
            return False, f"Resend SDK error: {response}"
        except Exception as exc:
            message = str(exc)
            if "error code: 1010" in message.lower():
                message = (
                    "Resend rejected the email (403/1010). Verify your sender domain in Resend "
                    "or send only to your verified owner email while the account is in test mode."
                )
            return False, f"Resend SDK error: {message}"

    try:
        response = requests.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            data=json.dumps(payload),
            timeout=15,
        )
    except requests.RequestException as exc:
        return False, f"Resend connection error: {exc}"

    if response.ok:
        return True, "Password reset OTP sent successfully"

    return False, f"Resend HTTP error {response.status_code}: {_format_resend_error(response)}"
