"""Email sender with triple transport: Brevo (primary), SMTP, and Resend API.

Transport priority:
    1. Brevo (if brevo_api_key is set in config.ini) -- 300 free emails/day
    2. SMTP  (if smtp username and password are set)  -- any SMTP provider
    3. Resend API (if resend_api_key is set)           -- legacy fallback

All transports use Python stdlib only (urllib.request, smtplib, email).
No external packages required.
"""

import base64
import json
import logging
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

logger = logging.getLogger(__name__)

BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
BREVO_TIMEOUT = 15        # seconds
RESEND_API_URL = "https://api.resend.com/emails"
RESEND_TIMEOUT = 10       # seconds
SMTP_TIMEOUT = 15         # seconds


# ---------- Brevo (formerly Sendinblue) ----------

def _send_brevo(config, recipients: list[str], subject: str,
                csv_content: str, filename: str,
                extra_attachments: list[dict] | None = None) -> dict:
    """Send email via the Brevo transactional email API.

    Free tier: 300 emails/day, no recipient restrictions.
    Sender email must be verified in the Brevo dashboard.
    Attachments are base64-encoded inline in the JSON payload.
    """
    api_key = config.brevo_api_key
    from_name = config.brevo_from_name
    from_email = config.brevo_from_email

    att_list = [
        {
            "name": filename,
            "content": base64.b64encode(csv_content.encode("utf-8")).decode("ascii"),
        }
    ]
    for extra in (extra_attachments or []):
        att_list.append({
            "name": extra["filename"],
            "content": base64.b64encode(extra["content"].encode("utf-8")).decode("ascii"),
        })

    payload = {
        "sender": {"name": from_name, "email": from_email},
        "to": [{"email": addr} for addr in recipients],
        "subject": subject,
        "textContent": "Report attached.",
        "attachment": att_list,
    }

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "PomponioLabeling/1.0",
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(BREVO_API_URL, data=data,
                                     headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=BREVO_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            logger.info("Email sent via Brevo to %s: %s (messageId=%s)",
                        ", ".join(recipients), subject,
                        body.get("messageId", "?"))
            return {"ok": True}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("message", error_body)
        except (json.JSONDecodeError, KeyError):
            error_msg = error_body
        logger.error("Brevo API error (%d): %s", e.code, error_msg)
        return {"ok": False, "error": f"Brevo API error ({e.code}): {error_msg}"}

    except urllib.error.URLError as e:
        logger.error("Network error (Brevo): %s", e.reason)
        return {"ok": False, "error": f"Network error: {e.reason}"}

    except OSError as e:
        logger.error("OS error (Brevo): %s", e)
        return {"ok": False, "error": f"Network error: {e}"}


# ---------- SMTP ----------

def _send_smtp(config, recipients: list[str], subject: str,
               csv_content: str, filename: str,
               extra_attachments: list[dict] | None = None) -> dict:
    """Send email via SMTP with STARTTLS.

    Works with Gmail app passwords and any provider that still supports
    basic SMTP AUTH. Microsoft consumer Outlook.com no longer supports
    basic auth (requires OAuth2), so use Brevo instead for Outlook accounts.
    """
    server_host = config.smtp_server
    server_port = config.smtp_port
    username = config.smtp_username
    password = config.smtp_password
    from_name = config.smtp_from_name

    from_addr = f"{from_name} <{username}>"

    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content("Report attached.")

    # Primary CSV attachment
    msg.add_attachment(
        csv_content.encode("utf-8"),
        maintype="text",
        subtype="csv",
        filename=filename,
    )

    # Extra attachments (audit log, etc.)
    for extra in (extra_attachments or []):
        msg.add_attachment(
            extra["content"].encode("utf-8"),
            maintype="text",
            subtype="csv",
            filename=extra["filename"],
        )

    try:
        with smtplib.SMTP(server_host, server_port, timeout=SMTP_TIMEOUT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(username, password)
            smtp.send_message(msg)

        logger.info("Email sent via SMTP to %s: %s", ", ".join(recipients), subject)
        return {"ok": True}

    except smtplib.SMTPAuthenticationError as e:
        logger.error("SMTP auth failed: %s", e)
        return {"ok": False, "error": f"SMTP login failed: {e.smtp_error.decode('utf-8', errors='replace') if isinstance(e.smtp_error, bytes) else e.smtp_error}"}

    except smtplib.SMTPException as e:
        logger.error("SMTP error: %s", e)
        return {"ok": False, "error": f"SMTP error: {e}"}

    except OSError as e:
        logger.error("Network error (SMTP): %s", e)
        return {"ok": False, "error": f"Network error: {e}"}


# ---------- Resend (legacy fallback) ----------

def _send_resend(config, recipients: list[str], subject: str,
                 csv_content: str, filename: str,
                 extra_attachments: list[dict] | None = None) -> dict:
    """Send email via the Resend HTTP API.

    Free tier only sends to the account holder's email. Kept as a
    legacy fallback; prefer Brevo for new deployments.
    """
    api_key = config.resend_api_key
    from_addr = config.resend_from

    att_list = [
        {
            "filename": filename,
            "content": base64.b64encode(csv_content.encode("utf-8")).decode("ascii"),
        }
    ]
    for extra in (extra_attachments or []):
        att_list.append({
            "filename": extra["filename"],
            "content": base64.b64encode(extra["content"].encode("utf-8")).decode("ascii"),
        })

    payload = {
        "from": from_addr,
        "to": recipients,
        "subject": subject,
        "text": "Report attached.",
        "attachments": att_list,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "PomponioLabeling/1.0",
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(RESEND_API_URL, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=RESEND_TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            logger.info("Email sent via Resend to %s: %s (id=%s)",
                        ", ".join(recipients), subject, body.get("id", "?"))
            return {"ok": True}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("message", error_body)
        except (json.JSONDecodeError, KeyError):
            error_msg = error_body
        logger.error("Resend API error (%d): %s", e.code, error_msg)
        return {"ok": False, "error": f"Resend API error ({e.code}): {error_msg}"}

    except urllib.error.URLError as e:
        logger.error("Network error (Resend): %s", e.reason)
        return {"ok": False, "error": f"Network error: {e.reason}"}

    except OSError as e:
        logger.error("OS error (Resend): %s", e)
        return {"ok": False, "error": f"Network error: {e}"}


# ---------- Public entry point ----------

def send_email(config, to: str, subject: str, csv_content: str, filename: str,
               *, attachments: list[dict] | None = None) -> dict:
    """Send an email with one or more CSV attachments.

    Transport priority:
        1. Brevo   (if brevo_api_key is set in config.ini)
        2. SMTP    (if smtp username and password are set)
        3. Resend  (if resend_api_key is set)
        4. Error   (no transport configured)

    Args:
        config: Config instance with brevo_*, smtp_*, and resend_* properties.
        to: Recipient email address(es), comma-separated for multiple.
        subject: Email subject line.
        csv_content: Raw CSV string for the primary attachment.
        filename: Primary attachment filename.
        attachments: Optional list of extra attachments, each a dict with
                     "content" (raw string) and "filename" keys.

    Returns:
        {"ok": True} on success, {"ok": False, "error": "<message>"} on failure.
    """
    # Normalize comma-separated recipients
    recipients = [addr.strip() for addr in to.split(",") if addr.strip()]
    if not recipients:
        return {"ok": False, "error": "No valid recipient addresses"}

    # 1. Brevo (free 300/day, no recipient restrictions)
    if config.brevo_configured:
        return _send_brevo(config, recipients, subject, csv_content, filename, attachments)

    # 2. SMTP (Gmail app passwords, etc.)
    if config.smtp_configured:
        return _send_smtp(config, recipients, subject, csv_content, filename, attachments)

    # 3. Resend API (legacy; free tier restricts recipients)
    if config.resend_api_key:
        return _send_resend(config, recipients, subject, csv_content, filename, attachments)

    return {"ok": False, "error": "No email transport configured. "
            "Set brevo_api_key, SMTP credentials, or resend_api_key in config.ini."}
