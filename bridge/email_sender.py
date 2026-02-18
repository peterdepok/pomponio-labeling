"""Email sender with dual transport: SMTP (primary) and Resend API (optional).

Tries SMTP first when credentials are present in config.ini. Falls back to
the Resend HTTP API if a resend_api_key is configured. At least one method
must be configured or send_email returns an error.

SMTP uses Python's built-in smtplib and email modules (no pip dependencies).
Resend uses urllib.request (also stdlib). No external packages required.
"""

import base64
import json
import logging
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_TIMEOUT = 10   # seconds
SMTP_TIMEOUT = 15     # seconds


def _send_smtp(config, recipients: list[str], subject: str,
               csv_content: str, filename: str,
               extra_attachments: list[dict] | None = None) -> dict:
    """Send email via SMTP with STARTTLS (Outlook, Gmail, etc.).

    Uses the app password from config.ini, not the main account password.
    Microsoft Outlook requires app passwords for SMTP since late 2025.
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


def _send_resend(config, recipients: list[str], subject: str,
                 csv_content: str, filename: str,
                 extra_attachments: list[dict] | None = None) -> dict:
    """Send email via the Resend HTTP API (requires paid plan for custom domains)."""
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


def send_email(config, to: str, subject: str, csv_content: str, filename: str,
               *, attachments: list[dict] | None = None) -> dict:
    """Send an email with one or more CSV attachments.

    Transport priority:
        1. SMTP (if smtp username and password are set in config.ini)
        2. Resend API (if resend_api_key is set in config.ini)
        3. Error (no transport configured)

    Args:
        config: Config instance with smtp_* and resend_* properties.
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

    # Try SMTP first (free, no external service dependency)
    if config.smtp_configured:
        return _send_smtp(config, recipients, subject, csv_content, filename, attachments)

    # Fall back to Resend API
    if config.resend_api_key:
        return _send_resend(config, recipients, subject, csv_content, filename, attachments)

    return {"ok": False, "error": "No email transport configured. "
            "Set SMTP username/password or Resend API key in config.ini."}
