import smtplib, ssl
from email.message import EmailMessage
from ..core.settings import settings

def send_invite_email(to: str, invite_url: str) -> bool:
    if not settings.EMAIL_ENABLED:
        return False
    msg = EmailMessage()
    msg["Subject"] = "You're invited to Petroff Parking Admin"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg.set_content(
        f"You're invited to Petroff Parking.\n\n"
        f"Set your password and join:\n{invite_url}\n"
    )
    ctx = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        s.starttls(context=ctx)
        if settings.SMTP_USERNAME:
            s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        s.send_message(msg)
    return True

def send_verification_email(to: str, verify_url: str) -> bool:
    if not settings.EMAIL_ENABLED:
        return False

    msg = EmailMessage()
    msg["Subject"] = "Verify Your Vehicle Ownership – Petroff Parking"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg.set_content(
        f"Hello,\n\n"
        f"Please verify that you own this vehicle by clicking the link below:\n"
        f"{verify_url}\n\n"
        f"If you did not request this, you can ignore this email.\n"
    )

    ctx = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        s.starttls(context=ctx)
        if settings.SMTP_USERNAME:
            s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        s.send_message(msg)

    return True

