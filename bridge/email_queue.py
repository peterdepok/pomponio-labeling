"""Persistent email queue with background retry thread.

When email send fails (no internet, API down), the email is saved to a JSON
file on disk. A daemon thread retries queued emails every `interval` seconds.
Thread-safe via threading.Lock.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Resolve data directory relative to project root (parent of bridge/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_QUEUE_PATH = os.path.join(_PROJECT_ROOT, "data", "email_queue.json")

_lock = threading.Lock()


def _read_queue() -> list[dict]:
    """Load the queue from disk. Returns empty list if file missing or corrupt."""
    if not os.path.exists(_QUEUE_PATH):
        return []
    try:
        with open(_QUEUE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to read email queue: %s", e)
        return []


def _write_queue(queue: list[dict]) -> None:
    """Write the queue to disk, creating the data directory if needed."""
    os.makedirs(os.path.dirname(_QUEUE_PATH), exist_ok=True)
    with open(_QUEUE_PATH, "w", encoding="utf-8") as f:
        json.dump(queue, f, indent=2)


def enqueue(entry: dict) -> None:
    """Add an email to the retry queue.

    Args:
        entry: Dict with keys: to, subject, csv_content, filename.
               A queued_at timestamp is added automatically.
    """
    entry["queued_at"] = datetime.now(timezone.utc).isoformat()
    with _lock:
        queue = _read_queue()
        queue.append(entry)
        _write_queue(queue)
    logger.info("Email queued for %s: %s (queue size: %d)",
                entry.get("to"), entry.get("subject"), len(queue))


def get_queue_length() -> int:
    """Return the number of pending emails in the queue."""
    with _lock:
        return len(_read_queue())


def _retry_loop(config, interval: float) -> None:
    """Background loop: retry queued emails every `interval` seconds."""
    # Import here to avoid circular import at module level
    from bridge.email_sender import send_email

    while True:
        time.sleep(interval)

        with _lock:
            queue = _read_queue()

        if not queue:
            continue

        logger.info("Retrying %d queued email(s)...", len(queue))
        succeeded = []

        for i, entry in enumerate(queue):
            result = send_email(
                config,
                to=entry["to"],
                subject=entry["subject"],
                csv_content=entry["csv_content"],
                filename=entry["filename"],
            )
            if result.get("ok"):
                logger.info("Queued email sent: %s -> %s", entry["subject"], entry["to"])
                succeeded.append(i)
            else:
                logger.warning("Queued email retry failed: %s", result.get("error"))

        # Remove succeeded entries (iterate in reverse to preserve indices)
        if succeeded:
            with _lock:
                queue = _read_queue()
                for idx in sorted(succeeded, reverse=True):
                    if idx < len(queue):
                        queue.pop(idx)
                _write_queue(queue)
            logger.info("Cleared %d email(s) from queue, %d remaining",
                        len(succeeded), len(queue))


def start_retry_thread(config, interval: float = 300) -> threading.Thread:
    """Launch the email retry daemon thread.

    Args:
        config: Config instance with resend_api_key property.
        interval: Seconds between retry attempts (default 300 = 5 minutes).

    Returns:
        The started daemon Thread.
    """
    t = threading.Thread(
        target=_retry_loop,
        args=(config, interval),
        daemon=True,
        name="email-retry",
    )
    t.start()
    logger.info("Email retry thread started (interval=%ds)", interval)
    return t
