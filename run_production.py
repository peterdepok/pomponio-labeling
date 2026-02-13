"""Pomponio Ranch Labeling System - Production Entry Point.

Starts the Flask bridge serving the React UI at localhost:8000
and opens Chrome in kiosk mode on the Beelink Mini PC.

Usage:
    python run_production.py
"""

import atexit
import os
import subprocess
import sys
import threading
import time

# Project root is the directory containing this script
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

PORT = 8000
URL = f"http://localhost:{PORT}"

# ---------------------------------------------------------------------------
# Chrome detection (Windows 11)
# ---------------------------------------------------------------------------

CHROME_CANDIDATES = [
    os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                 "Google", "Chrome", "Application", "chrome.exe"),
    os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
                 "Google", "Chrome", "Application", "chrome.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""),
                 "Google", "Chrome", "Application", "chrome.exe"),
]


def find_chrome() -> str | None:
    """Return the path to chrome.exe, or None if not found."""
    for path in CHROME_CANDIDATES:
        if path and os.path.isfile(path):
            return path
    return None


# ---------------------------------------------------------------------------
# Flask startup
# ---------------------------------------------------------------------------

def start_flask() -> threading.Thread:
    """Start the Flask bridge in a daemon thread."""
    from bridge.server import create_app

    application = create_app()

    def run():
        application.run(
            host="0.0.0.0",
            port=PORT,
            debug=False,
            use_reloader=False,
        )

    t = threading.Thread(target=run, daemon=True, name="flask-server")
    t.start()
    return t


def wait_for_flask(timeout_s: float = 15.0) -> bool:
    """Poll /api/health until Flask responds or timeout expires."""
    import urllib.request
    import urllib.error

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(f"{URL}/api/health", timeout=1)
            return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # 1. Verify the React build exists
    dist_index = os.path.join(PROJECT_ROOT, "dist", "index.html")
    if not os.path.isfile(dist_index):
        print("ERROR: dist/index.html not found.")
        print("Run 'npm run build' to generate the React build first.")
        sys.exit(1)

    # 2. Start Flask
    print(f"Starting Flask bridge on port {PORT}...")
    start_flask()

    if not wait_for_flask():
        print("ERROR: Flask did not start within 15 seconds.")
        sys.exit(1)

    print(f"Flask bridge ready at {URL}")

    # 3. Launch Chrome in kiosk mode
    chrome = find_chrome()
    chrome_proc = None

    if chrome:
        print(f"Launching Chrome kiosk: {chrome}")
        chrome_proc = subprocess.Popen([
            chrome,
            "--kiosk",
            "--disable-restore-session-state",
            "--disable-infobars",
            "--no-first-run",
            "--disable-translate",
            URL,
        ])

        def cleanup():
            if chrome_proc and chrome_proc.poll() is None:
                chrome_proc.terminate()

        atexit.register(cleanup)
    else:
        print("Chrome not found. Open the following URL manually:")
        print(f"  {URL}")

    # 4. Wait until Chrome exits or user presses Ctrl+C
    try:
        if chrome_proc:
            chrome_proc.wait()
            print("Chrome closed. Shutting down.")
        else:
            print("Press Ctrl+C to stop the server.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        if chrome_proc and chrome_proc.poll() is None:
            chrome_proc.terminate()


if __name__ == "__main__":
    main()
