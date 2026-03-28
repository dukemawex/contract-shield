import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://contract-shield.vercel.app")


def send_email(to: str, subject: str, html: str, text: str) -> None:
    """Send an email via Gmail SMTP SSL."""
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Contract Shield <{GMAIL_USER}>"
    msg["To"] = to
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as s:
        s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        s.sendmail(GMAIL_USER, to, msg.as_string())


def send_welcome_email(to: str) -> None:
    """Send welcome email to new user."""
    subject = "Your Contract Shield account is ready"
    text = (
        "Welcome to Contract Shield!\n\n"
        "Your account is ready. You have 3 free contract analyses included.\n\n"
        f"Get started at {FRONTEND_URL}\n\n"
        "— Contract Shield"
    )
    html = f"""
<div style="font-family:sans-serif;max-width:600px;margin:0 auto">
  <h2 style="color:#4f46e5">🛡️ Welcome to Contract Shield!</h2>
  <p>Your account is ready. You have <strong>3 free contract analyses</strong> included.</p>
  <p>
    <a href="{FRONTEND_URL}"
       style="background:#4f46e5;color:#fff;padding:12px 24px;border-radius:6px;
              text-decoration:none;display:inline-block;margin-top:8px">
      Start Analyzing
    </a>
  </p>
  <p style="color:#6b7280;font-size:14px;margin-top:24px">— Contract Shield</p>
</div>
"""
    send_email(to, subject, html, text)


def send_upgrade_email(to: str) -> None:
    """Send upgrade confirmation email."""
    subject = "You're now on Contract Shield Pro 🛡️"
    text = (
        "You're now on Contract Shield Pro!\n\n"
        "Unlimited analyses unlocked. Start uploading your contracts anytime.\n\n"
        f"Get started at {FRONTEND_URL}\n\n"
        "— Contract Shield"
    )
    html = f"""
<div style="font-family:sans-serif;max-width:600px;margin:0 auto">
  <h2 style="color:#4f46e5">🛡️ You're now on Contract Shield Pro!</h2>
  <p>Unlimited analyses unlocked. Start uploading your contracts anytime.</p>
  <p>
    <a href="{FRONTEND_URL}"
       style="background:#4f46e5;color:#fff;padding:12px 24px;border-radius:6px;
              text-decoration:none;display:inline-block;margin-top:8px">
      Upload a Contract
    </a>
  </p>
  <p style="color:#6b7280;font-size:14px;margin-top:24px">— Contract Shield</p>
</div>
"""
    send_email(to, subject, html, text)


def send_limit_email(to: str) -> None:
    """Send email when free limit is hit."""
    subject = "You've used all 3 free analyses"
    checkout_url = f"{FRONTEND_URL}/#upgrade"
    text = (
        "You've used all 3 free analyses on Contract Shield.\n\n"
        "Upgrade to Pro for $9/month and get unlimited analyses.\n\n"
        f"Upgrade now: {checkout_url}\n\n"
        "— Contract Shield"
    )
    html = f"""
<div style="font-family:sans-serif;max-width:600px;margin:0 auto">
  <h2 style="color:#4f46e5">🛡️ You've used all 3 free analyses</h2>
  <p>Upgrade to <strong>Contract Shield Pro</strong> for $9/month and get
     <strong>unlimited analyses</strong>.</p>
  <p>
    <a href="{checkout_url}"
       style="background:#4f46e5;color:#fff;padding:12px 24px;border-radius:6px;
              text-decoration:none;display:inline-block;margin-top:8px">
      Upgrade to Pro — $9/mo
    </a>
  </p>
  <p style="color:#6b7280;font-size:14px;margin-top:24px">— Contract Shield</p>
</div>
"""
    send_email(to, subject, html, text)
