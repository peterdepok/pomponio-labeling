"""Flask API bridge for Pomponio Ranch Labeling System.

Serves the built React app as static files and exposes two hardware endpoints:
    GET  /api/scale  - cached weight reading from Brecknell 6710U
    POST /api/print  - send ZPL to Zebra ZP 230D via win32print
    GET  /api/health - connection status for scale and printer

The scale is polled in a background daemon thread at 200ms intervals.
All reads from the HTTP layer hit an in-memory cache, never the serial port directly.
"""

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


@app.route("/api/health", methods=["GET"])
def api_health():
    """Return connection status for scale and printer."""
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
    })


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
    """Initialize and return the Flask app with the scale poller running."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    start_scale_poller()
    return app


# Allow `python bridge/server.py` for standalone testing
if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=8000, debug=False)
