"""SMTP email sender using Python stdlib.

Sends a CSV attachment via STARTTLS to the configured SMTP server (Outlook).
No external dependencies: smtplib + email.mime are part of the standard library.
"""

import logging
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

logger = logging.getLogger(__name__)

SMTP_TIMEOUT = 30  # seconds


def send_email(config, to: str, subject: str, csv_content: str, filename: str) -> dict:
    """Send an email with a CSV attachment via STARTTLS.

    Args:
        config: Config instance with smtp_* properties.
        to: Recipient email address(es), comma-separated for multiple.
        subject: Email subject line.
        csv_content: Raw CSV string to attach.
        filename: Attachment filename (e.g. "manifest_Cow1_123456.csv").

    Returns:
        {"ok": True} on success, {"ok": False, "error": "<message>"} on failure.
    """
    server_addr = config.smtp_server
    port = config.smtp_port
    username = config.smtp_username
    password = config.smtp_password
    from_name = config.smtp_from_name

    if not password:
        return {"ok": False, "error": "SMTP password not configured in config.ini"}

    # Normalize comma-separated recipients (strip whitespace, drop blanks)
    recipients = [addr.strip() for addr in to.split(",") if addr.strip()]
    if not recipients:
        return {"ok": False, "error": "No valid recipient addresses"}

    # Build the MIME message
    msg = MIMEMultipart()
    msg["From"] = formataddr((from_name, username))
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    # Plain text body
    msg.attach(MIMEText("Report attached.", "plain"))

    # CSV attachment
    part = MIMEBase("application", "octet-stream")
    part.set_payload(csv_content.encode("utf-8"))
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
    msg.attach(part)

    try:
        with smtplib.SMTP(server_addr, port, timeout=SMTP_TIMEOUT) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        logger.info("Email sent to %s: %s", ", ".join(recipients), subject)
        return {"ok": True}
    except smtplib.SMTPAuthenticationError as e:
        logger.error("SMTP auth failed: %s", e)
        return {"ok": False, "error": f"SMTP authentication failed: {e}"}
    except smtplib.SMTPException as e:
        logger.error("SMTP error: %s", e)
        return {"ok": False, "error": f"SMTP error: {e}"}
    except OSError as e:
        # Network unreachable, DNS failure, connection refused, timeout
        logger.error("Network error sending email: %s", e)
        return {"ok": False, "error": f"Network error: {e}"}
