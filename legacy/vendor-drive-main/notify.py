"""
Ping delivery.

The guaranteed channel is the in-app Inbox tab -- every ping writes a
Notification row in the database (done in app.py) and that never depends on any
external service, account, bot, or setup. NO Telegram, no webhooks, nothing to
register anywhere.

This module only handles the OPTIONAL email copy, which fires solely if the
SMTP_* lines are filled in .env. If they aren't, every function here quietly
does nothing and returns False -- it can never break the app.
"""
import os

ACTION_LABELS = {
    "nda_request": "NDA Request",
    "purchase_request": "Purchase Request",
    "review_request": "Please Review",
    "quote_request": "Quote Request",
    "info_share": "Shared With You",
    "look_at_file": "Please Look At This File",
}


def send_email(to_email: str, subject: str, body_html: str) -> bool:
    """Optional. Only fires if SMTP_HOST/USER/PASS are all set in .env."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587") or 587)
    user = os.getenv("SMTP_USER", "")
    pwd = os.getenv("SMTP_PASS", "")
    sender = os.getenv("SMTP_FROM", user)
    if not all([host, user, pwd, to_email]):
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))
    try:
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, pwd)
            s.sendmail(sender, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"[MAIL] Failed (non-fatal, app keeps working): {e}")
        return False


def notify_member(member, action: str, from_user: str, message: str = "",
                  file_name: str = "") -> dict:
    """
    Attempts the optional email extra. The in-app inbox row is created in app.py
    and always happens regardless of this. Returns {"email": True/False}.
    """
    result = {"email": False}
    email = getattr(member, "email", "")
    if not email:
        return result
    label = ACTION_LABELS.get(action, action.replace("_", " ").title())
    subject = f"[Vendor Drive] {label}" + (f" - {file_name}" if file_name else "")
    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:20px">
      <h2 style="color:#1e293b;border-bottom:2px solid #3b82f6;padding-bottom:8px">{label}</h2>
      <p><strong>{from_user or 'A teammate'}</strong> pinged you on the Vendor Drive.</p>
      {f'<p style="background:#f1f5f9;border-radius:8px;padding:12px"><strong>File:</strong> {file_name}</p>' if file_name else ''}
      {f'<div style="background:#fffbeb;border-left:3px solid #f59e0b;padding:12px;margin:12px 0;border-radius:4px">{message}</div>' if message else ''}
      <p style="color:#64748b;font-size:12px;margin-top:20px">Open the drive and check your Inbox tab.</p>
    </div>
    """
    result["email"] = send_email(email, subject, html)
    return result
