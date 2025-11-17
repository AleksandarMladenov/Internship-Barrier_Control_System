import smtplib, ssl
from datetime import datetime
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


def send_payment_link_email(to: str, checkout_url: str) -> bool:
    if not settings.EMAIL_ENABLED:
        return False

    msg = EmailMessage()
    msg["Subject"] = "Complete your subscription payment – Petroff Parking"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to
    msg.set_content(
        f"Hello,\n\n"
        f"Please complete your subscription payment here:\n{checkout_url}\n\n"
        f"After payment, your access will be reactivated automatically.\n"
    )

    ctx = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        s.starttls(context=ctx)
        if settings.SMTP_USERNAME:
            s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        s.send_message(msg)

    return True


def _fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M")


def _fmt_money(cents: int | None, currency: str = "EUR") -> str:
    if cents is None:
        return "—"

    amount = cents / 100.0
    return f"{amount:.2f} {currency}"


def send_receipt_email(
        to: str,
        *,
        session_id: int,
        plate_full: str,
        started_at: datetime | None,
        ended_at: datetime | None,
        amount_cents: int | None,
        currency: str = "EUR",
) -> bool:
    """
    Send a simple parking receipt email for a finished session.
    Reuses the same SMTP config as the other email helpers.
    """
    if not settings.EMAIL_ENABLED:
        return False

    entry_str = _fmt_dt(started_at)
    exit_str = _fmt_dt(ended_at)
    paid_str = _fmt_money(amount_cents, currency)

    msg = EmailMessage()
    msg["Subject"] = f"Parking receipt #{session_id} – Petroff Parking"
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to

    msg.set_content(
        "Thank you for parking with us.\n\n"
        f"Receipt #{session_id}\n"
        f"Plate: {plate_full}\n"
        f"Entry: {entry_str}\n"
        f"Exit: {exit_str}\n"
        f"Paid: {paid_str}\n\n"
        "Parking space Address • Vratsa, 3000\n"
    )

    ctx = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
        s.starttls(context=ctx)
        if settings.SMTP_USERNAME:
            s.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        s.send_message(msg)

    return True
