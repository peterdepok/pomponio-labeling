"""Persistent audit log store with nightly email scheduler.

Events are appended to data/audit_log.json by the /api/audit endpoint.
A background daemon thread checks the clock every 60 seconds and, at 2am
local time, rotates the log (harvest + clear) and emails the contents as
a CSV attachment. If SMTP fails, the email is queued for retry via the
existing email_queue module.
"""

import csv
import io
import json
import logging
import os
import threading
import time
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AUDIT_PATH = os.path.join(_PROJECT_ROOT, "data", "audit_log.json")

_lock = threading.Lock()


# ---------------------------------------------------------------------------
# File operations (all under _lock)
# ---------------------------------------------------------------------------

def _read_events() -> list[dict]:
    """Load events from disk. Returns empty list if file missing or corrupt."""
    if not os.path.exists(_AUDIT_PATH):
        return []
    try:
        with open(_AUDIT_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read audit log: %s", e)
        return []


def _write_events(events: list[dict]) -> None:
    """Write events to disk, creating directory if needed."""
    os.makedirs(os.path.dirname(_AUDIT_PATH), exist_ok=True)
    with open(_AUDIT_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def append_event(event: dict) -> None:
    """Append a single audit event to the persistent log.

    Args:
        event: Dict with timestamp, eventType, and payload keys.
    """
    with _lock:
        events = _read_events()
        events.append(event)
        _write_events(events)


def read_events() -> list[dict]:
    """Return all events currently in the log."""
    with _lock:
        return _read_events()


def rotate_log() -> list[dict]:
    """Harvest all events and clear the log file.

    Returns:
        The list of events that were in the file before clearing.
    """
    with _lock:
        events = _read_events()
        _write_events([])
    return events


# ---------------------------------------------------------------------------
# CSV formatting
# ---------------------------------------------------------------------------

def _events_to_csv(events: list[dict]) -> str:
    """Format audit events as a three-column CSV string.

    Columns: timestamp, eventType, payload (JSON-stringified).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "eventType", "payload"])
    for e in events:
        writer.writerow([
            e.get("timestamp", ""),
            e.get("eventType", ""),
            json.dumps(e.get("payload", {})),
        ])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 2am scheduler
# ---------------------------------------------------------------------------

def _scheduler_loop(config) -> None:
    """Background loop: email the audit log at 2am local time."""
    from bridge.email_sender import send_email
    from bridge.email_queue import enqueue

    while True:
        time.sleep(60)

        now = datetime.now()
        if now.hour != 2 or now.minute >= 1:
            continue

        # We are in the 2:00am window
        events = read_events()
        if not events:
            # Nothing to send; sleep past this hour to avoid rechecking
            logger.debug("2am audit check: no events to send")
            time.sleep(3600)
            continue

        # Rotate: harvest events and clear file
        events = rotate_log()
        if not events:
            time.sleep(3600)
            continue

        # Format as CSV
        csv_content = _events_to_csv(events)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        filename = f"audit_log_{yesterday}.csv"

        # Determine recipient from config
        recipient = config.get("email", "audit_recipient", fallback="")

        if not recipient:
            logger.warning("No audit email recipient configured; skipping send")
            time.sleep(3600)
            continue

        subject = f"Pomponio Ranch Audit Log: {yesterday}"
        logger.info("Sending audit log email (%d events) to %s", len(events), recipient)

        result = send_email(config, recipient, subject, csv_content, filename)

        if result.get("ok"):
            logger.info("Audit log emailed successfully")
        else:
            # Queue for retry; events are already rotated out of the live file
            logger.warning("Audit log email failed, queuing: %s", result.get("error"))
            enqueue({
                "to": recipient,
                "subject": subject,
                "csv_content": csv_content,
                "filename": filename,
            })

        # Sleep past the rest of the 2am hour to prevent double-send
        time.sleep(3600)


def start_audit_scheduler(config) -> threading.Thread:
    """Launch the nightly audit log email daemon thread.

    Args:
        config: Config instance with smtp_* and email.audit_recipient properties.

    Returns:
        The started daemon Thread.
    """
    t = threading.Thread(
        target=_scheduler_loop,
        args=(config,),
        daemon=True,
        name="audit-scheduler",
    )
    t.start()
    logger.info("Audit scheduler started (sends at 2:00am local time)")
    return t
