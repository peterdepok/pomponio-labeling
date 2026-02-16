"""Flask API bridge for Pomponio Ranch Labeling System.

Serves the built React app as static files and exposes hardware + service endpoints:
    GET  /api/scale        - cached weight reading from Brecknell 6710U
    POST /api/print        - send ZPL to Zebra ZP 230D via win32print
    POST /api/email        - send CSV report via Resend API (queues on failure)
    POST /api/audit        - persist audit event to server-side log
    POST /api/export-csv   - save CSV to USB drive or local fallback
    GET  /api/health       - connection status for scale, printer, and email queue
    GET  /api/update/check - check GitHub for new commits
    POST /api/update/apply - git pull + npm build + restart

The scale is polled in a background daemon thread at 200ms intervals.
Queued emails are retried by a separate daemon thread every 5 minutes.
All reads from the HTTP layer hit an in-memory cache, never the serial port directly.
"""

import ctypes
import logging
import os
import sys
import threading
import time

# Add project root to path so `from src.scale import Scale` resolves.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, request, send_from_directory  # noqa: E402
from src.config import Config  # noqa: E402
from src.scale import Scale, ScaleError  # noqa: E402
from src.printer import Printer, PrinterError  # noqa: E402
from bridge.email_sender import send_email  # noqa: E402
from bridge.email_queue import enqueue, get_queue_length, start_retry_thread  # noqa: E402
from bridge.audit_store import append_event, start_audit_scheduler  # noqa: E402
from bridge.updater import check_for_update, apply_update, schedule_restart  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

config = Config(os.path.join(PROJECT_ROOT, "config.ini"))
config.load()

SCALE_POLL_INTERVAL = 0.2  # seconds (200ms, matches src/scale.py POLL_INTERVAL)
SCALE_RECONNECT_INTERVAL = 5.0  # seconds between reconnect attempts

# ---------------------------------------------------------------------------
# Scale background poller
# ---------------------------------------------------------------------------

scale_lock = threading.Lock()
latest_reading: dict = {
    "weight": 0.0,
    "stable": False,
    "unit": "lb",
    "error": None,
}

_scale_instance: Scale | None = None


def _get_scale() -> Scale:
    """Lazy-init the Scale singleton."""
    global _scale_instance
    if _scale_instance is None:
        _scale_instance = Scale(
            port=config.scale_port,
            baud_rate=config.scale_baud_rate,
        )
    return _scale_instance


def scale_poll_loop() -> None:
    """Background daemon: poll scale at SCALE_POLL_INTERVAL, cache reading."""
    scale = _get_scale()

    while True:
        # Attempt connection if not connected
        if not scale.connected:
            try:
                scale.connect()
                logger.info("Scale connected on %s", scale.port)
                with scale_lock:
                    latest_reading["error"] = None
            except ScaleError as e:
                with scale_lock:
                    latest_reading["weight"] = 0.0
                    latest_reading["stable"] = False
                    latest_reading["error"] = str(e)
                time.sleep(SCALE_RECONNECT_INTERVAL)
                continue

        # Poll a reading
        try:
            reading = scale.request_weight()
            with scale_lock:
                latest_reading["weight"] = round(reading.weight_lb, 3)
                latest_reading["stable"] = reading.stable
                latest_reading["unit"] = reading.unit
                latest_reading["error"] = None
        except ScaleError as e:
            logger.warning("Scale poll error: %s", e)
            with scale_lock:
                latest_reading["error"] = str(e)
            # If the serial connection broke, mark disconnected so we retry
            if scale._serial and not scale._serial.is_open:
                scale._serial = None

        time.sleep(SCALE_POLL_INTERVAL)


def start_scale_poller() -> threading.Thread:
    """Start the scale polling daemon thread."""
    t = threading.Thread(target=scale_poll_loop, daemon=True, name="scale-poller")
    t.start()
    logger.info("Scale poller started (interval=%.1fs)", SCALE_POLL_INTERVAL)
    return t


# ---------------------------------------------------------------------------
# Printer helper
# ---------------------------------------------------------------------------

_printer_instance: Printer | None = None


def _get_printer() -> Printer:
    """Lazy-init the Printer singleton."""
    global _printer_instance
    if _printer_instance is None:
        _printer_instance = Printer(printer_name=config.printer_name)
    return _printer_instance


def _check_printer_available(name: str) -> bool:
    """Check whether the named printer exists in the OS print queue."""
    try:
        if sys.platform == "win32":
            import win32print  # type: ignore[import-not-found]
            printers = [p[2] for p in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )]
            return name in printers
        else:
            # On non-Windows, assume available (dev mode with lp)
            return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Flask application
# ---------------------------------------------------------------------------

DIST_DIR = os.path.join(PROJECT_ROOT, "dist")

app = Flask(
    __name__,
    static_folder=DIST_DIR,
    static_url_path="",
)


@app.route("/api/scale", methods=["GET"])
def api_scale():
    """Return the latest cached scale reading."""
    with scale_lock:
        data = dict(latest_reading)

    # If there is an error, include it but still return weight/stable fields
    response = {
        "weight": data["weight"],
        "stable": data["stable"],
        "unit": data["unit"],
    }
    if data["error"]:
        response["error"] = data["error"]

    return jsonify(response)


@app.route("/api/scale/detect", methods=["GET"])
def api_scale_detect():
    """Scan available COM ports and test each for a Brecknell 6710U response.

    Returns a list of ports with their status (found, no_response, error).
    """
    try:
        import serial as pyserial
        from serial.tools.list_ports import comports
    except ImportError:
        return jsonify({"ok": False, "error": "pyserial not installed"}), 500

    results = []
    for port_info in sorted(comports(), key=lambda p: p.device):
        port_name = port_info.device
        entry = {"port": port_name, "description": port_info.description, "status": "unknown"}

        # Skip the port that the scale poller is already using
        scale = _get_scale()
        if scale.connected and scale.port == port_name:
            entry["status"] = "in_use"
            entry["note"] = "Currently connected"
            results.append(entry)
            continue

        try:
            test_serial = pyserial.Serial(
                port=port_name,
                baudrate=config.scale_baud_rate,
                bytesize=pyserial.EIGHTBITS,
                parity=pyserial.PARITY_NONE,
                stopbits=pyserial.STOPBITS_ONE,
                timeout=1.5,
            )
            test_serial.reset_input_buffer()
            test_serial.write(b"W\r")
            response = test_serial.read(50)
            test_serial.close()

            if response and (b"lb" in response or b"kg" in response or b"oz" in response):
                entry["status"] = "found"
                entry["note"] = "Brecknell scale detected"
            elif response:
                entry["status"] = "no_match"
                entry["note"] = "Device responded but not a recognized scale"
            else:
                entry["status"] = "no_response"
        except Exception as e:
            entry["status"] = "error"
            entry["note"] = str(e)

        results.append(entry)

    return jsonify({"ok": True, "ports": results})


@app.route("/api/print", methods=["POST"])
def api_print():
    """Receive ZPL and send to the Zebra printer."""
    body = request.get_json(silent=True) or {}
    zpl = body.get("zpl", "")

    if not zpl:
        return jsonify({"ok": False, "error": "No ZPL data provided"}), 400

    try:
        printer = _get_printer()
        printer.send_raw_zpl(zpl)
        logger.info("Label printed (%d bytes ZPL)", len(zpl))
        return jsonify({"ok": True})
    except PrinterError as e:
        logger.error("Print failed: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500
    except Exception as e:
        logger.error("Unexpected print error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/email", methods=["POST"])
def api_email():
    """Send a CSV report via Resend API. Queues on failure for background retry.

    Accepts optional `attachments` array for additional files alongside
    the primary csvContent/filename pair.
    """
    body = request.get_json(silent=True) or {}
    to = body.get("to", "")
    subject = body.get("subject", "")
    csv_content = body.get("csvContent", "")
    filename = body.get("filename", "report.csv")
    extra_attachments = body.get("attachments", [])

    if not to or not subject or not csv_content:
        return jsonify({"ok": False, "error": "Missing required fields (to, subject, csvContent)"}), 400

    result = send_email(config, to, subject, csv_content, filename,
                        attachments=extra_attachments)

    if result.get("ok"):
        return jsonify({"ok": True})

    # Send failed; queue for retry (include extra attachments in queued payload)
    enqueue({
        "to": to,
        "subject": subject,
        "csv_content": csv_content,
        "filename": filename,
        "attachments": extra_attachments,
    })
    logger.warning("Email to %s queued for retry: %s", to, result.get("error"))
    return jsonify({"ok": True, "queued": True, "error": result.get("error", "Send failed")})


@app.route("/api/email/test", methods=["POST"])
def api_email_test():
    """Send a test email and return the raw result (no queuing on failure)."""
    body = request.get_json(silent=True) or {}
    to = body.get("to", "")

    if not to:
        return jsonify({"ok": False, "error": "No recipient address provided"}), 400

    result = send_email(
        config, to,
        "Pomponio Ranch Test Email",
        "sku,product,weight\nTEST,Test Product,1.0",
        "test.csv",
    )
    return jsonify(result)


@app.route("/api/audit", methods=["POST"])
def api_audit():
    """Persist a single audit event to the server-side log file."""
    body = request.get_json(silent=True) or {}
    event_type = body.get("eventType", "")
    timestamp = body.get("timestamp", "")

    if not event_type or not timestamp:
        return jsonify({"ok": False, "error": "Missing eventType or timestamp"}), 400

    append_event(body)
    return jsonify({"ok": True})


@app.route("/api/export-csv", methods=["POST"])
def api_export_csv():
    """Save a CSV file to USB drive or local fallback directory."""
    body = request.get_json(silent=True) or {}
    csv_content = body.get("csvContent", "")
    filename = body.get("filename", "export.csv")

    if not csv_content:
        return jsonify({"ok": False, "error": "No CSV content provided"}), 400

    # Sanitize filename
    safe_name = "".join(c for c in filename if c.isalnum() or c in "._-")
    if not safe_name:
        safe_name = "export.csv"

    export_path = _find_export_path(safe_name)

    try:
        os.makedirs(os.path.dirname(export_path), exist_ok=True)
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(csv_content)
        logger.info("CSV exported to %s", export_path)
        return jsonify({"ok": True, "path": export_path})
    except OSError as e:
        logger.error("CSV export failed: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


def _find_export_path(filename: str) -> str:
    """Locate a USB drive or fall back to a local directory."""
    if sys.platform == "win32":
        try:
            # Check drives D: through G: for removable media
            DRIVE_REMOVABLE = 2
            for letter in "DEFG":
                drive = f"{letter}:\\"
                drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive)
                if drive_type == DRIVE_REMOVABLE and os.path.isdir(drive):
                    return os.path.join(drive, filename)
        except Exception:
            pass
        # No USB found; use local fallback
        fallback = os.path.join("C:\\", "pomponio-labeling", "exports")
        return os.path.join(fallback, filename)
    else:
        # Dev mode (macOS/Linux): use exports/ under project root
        fallback = os.path.join(PROJECT_ROOT, "exports")
        return os.path.join(fallback, filename)


@app.route("/api/health", methods=["GET"])
def api_health():
    """Return connection status for scale, printer, and email queue."""
    scale = _get_scale()
    printer_name = config.printer_name

    return jsonify({
        "scale": {
            "connected": scale.connected,
            "port": config.scale_port,
        },
        "printer": {
            "name": printer_name,
            "available": _check_printer_available(printer_name),
        },
        "email": {
            "queue_length": get_queue_length(),
            "configured": bool(config.resend_api_key),
        },
    })


@app.route("/api/update/check", methods=["GET"])
def api_update_check():
    """Check GitHub for available updates via git fetch."""
    result = check_for_update()
    return jsonify(result)


@app.route("/api/update/apply", methods=["POST"])
def api_update_apply():
    """Pull latest code, rebuild, and schedule a process restart."""
    result = apply_update()

    if result.get("ok"):
        schedule_restart(delay=2.0)
        return jsonify(result)

    return jsonify(result), 500


# SPA catch-all: serve index.html for any path not matched above
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    """Serve React SPA. Static assets resolve from dist/, everything else
    falls through to index.html for client-side routing."""
    # Try to serve the exact file first (JS, CSS, images, etc.)
    full_path = os.path.join(DIST_DIR, path)
    if path and os.path.isfile(full_path):
        return send_from_directory(DIST_DIR, path)
    # Fall back to index.html for SPA routing
    return send_from_directory(DIST_DIR, "index.html")


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

def create_app():
    """Initialize and return the Flask app with background threads running."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    start_scale_poller()
    start_retry_thread(config, interval=300)
    start_audit_scheduler(config)
    return app


# Allow `python bridge/server.py` for standalone testing
if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=8000, debug=False)
