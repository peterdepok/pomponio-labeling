"""Email sender using the Resend HTTP API.

Sends a CSV attachment via a single POST to https://api.resend.com/emails.
No external dependencies: uses urllib.request + json from the standard library.
Replaces the previous SMTP-based sender that was blocked by Microsoft.
"""

import base64
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_TIMEOUT = 30  # seconds


def send_email(config, to: str, subject: str, csv_content: str, filename: str) -> dict:
    """Send an email with a CSV attachment via the Resend API.

    Args:
        config: Config instance with resend_api_key and resend_from properties.
        to: Recipient email address(es), comma-separated for multiple.
        subject: Email subject line.
        csv_content: Raw CSV string to attach.
        filename: Attachment filename (e.g. "manifest_Cow1_123456.csv").

    Returns:
        {"ok": True} on success, {"ok": False, "error": "<message>"} on failure.
    """
    api_key = config.resend_api_key
    from_addr = config.resend_from

    if not api_key:
        return {"ok": False, "error": "Resend API key not configured in config.ini"}

    # Normalize comma-separated recipients (strip whitespace, drop blanks)
    recipients = [addr.strip() for addr in to.split(",") if addr.strip()]
    if not recipients:
        return {"ok": False, "error": "No valid recipient addresses"}

    # Build the Resend API payload
    payload = {
        "from": from_addr,
        "to": recipients,
        "subject": subject,
        "text": "Report attached.",
        "attachments": [
            {
                "filename": filename,
                "content": base64.b64encode(csv_content.encode("utf-8")).decode("ascii"),
            }
        ],
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
        logger.error("Network error sending email: %s", e.reason)
        return {"ok": False, "error": f"Network error: {e.reason}"}

    except OSError as e:
        logger.error("OS error sending email: %s", e)
        return {"ok": False, "error": f"Network error: {e}"}
