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
