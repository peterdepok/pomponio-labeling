"""Pomponio Ranch Labeling System - Production Entry Point.

Starts the Flask bridge serving the React UI at localhost:8000
and opens Chrome (or Edge) in kiosk mode on the Beelink Mini PC.

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

# Isolated Chrome profile so kiosk runs as its own process (not delegated
# to an existing Chrome/Edge instance). Stored inside the project directory.
KIOSK_PROFILE_DIR = os.path.join(PROJECT_ROOT, ".kiosk-profile")

# Module-level reference to the browser subprocess so the /api/shutdown
# endpoint can terminate Chrome before killing the Python process.
# Set in main(), read by bridge.server.api_shutdown().
browser_process: subprocess.Popen | None = None

# ---------------------------------------------------------------------------
# Browser detection (Chrome preferred, Edge fallback)
# ---------------------------------------------------------------------------

BROWSER_CANDIDATES = [
    # Google Chrome (preferred for kiosk stability)
    os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                 "Google", "Chrome", "Application", "chrome.exe"),
    os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
                 "Google", "Chrome", "Application", "chrome.exe"),
    os.path.join(os.environ.get("LOCALAPPDATA", ""),
                 "Google", "Chrome", "Application", "chrome.exe"),
    # Microsoft Edge (fallback)
    os.path.join(os.environ.get("PROGRAMFILES(X86)", "C:\\Program Files (x86)"),
                 "Microsoft", "Edge", "Application", "msedge.exe"),
    os.path.join(os.environ.get("PROGRAMFILES", "C:\\Program Files"),
                 "Microsoft", "Edge", "Application", "msedge.exe"),
]


def find_browser() -> str | None:
    """Return the path to Chrome or Edge, or None if neither found."""
    for path in BROWSER_CANDIDATES:
        if path and os.path.isfile(path):
            return path
    return None


# ---------------------------------------------------------------------------
# Flask startup
# ---------------------------------------------------------------------------

def start_flask() -> threading.Thread:
    """Start the Flask bridge in a daemon thread.

    The thread is stored so the main loop can check ``t.is_alive()``
    and exit (code 1) if Flask crashes, letting the watchdog relaunch.

    Uses werkzeug make_server() which sets SO_REUSEADDR by default,
    allowing the port to rebind immediately after os._exit(42) even
    while the previous socket is in TIME_WAIT on Windows.

    Falls back to app.run() if make_server is unavailable.
    """
    from bridge.server import create_app

    application = create_app()

    def run():
        try:
            from werkzeug.serving import make_server
            # make_server sets SO_REUSEADDR by default, which is the key fix:
            # after os._exit(42) the socket enters TIME_WAIT and blocks bind()
            # for up to 30s on Windows. SO_REUSEADDR bypasses this.
            server = make_server("0.0.0.0", PORT, application, threaded=True)
            server.serve_forever()
        except Exception as e:
            # Fallback: use app.run() if make_server fails for any reason.
            # Less resilient to TIME_WAIT but still functional.
            print(f"make_server failed ({e}), falling back to app.run()")
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
# Chrome profile lock cleanup
# ---------------------------------------------------------------------------

def _clean_chrome_profile(profile_dir: str) -> None:
    """Clean stale Chrome lock files and session data from a previous force-kill.

    When Chrome is terminated via taskkill /F, it cannot clean up its
    profile lock files. On next launch with the same --user-data-dir,
    Chrome may:
      - Show a "restore session" infobar (breaks kiosk mode)
      - Delegate to a non-existent "primary" instance and exit immediately
      - Refuse to open the URL, showing a blank page
      - Restore a cached ERR_CONNECTION_REFUSED page

    We remove the lock files and session restore data before launching
    so Chrome always starts as the primary instance with a clean state.
    """
    import shutil

    if not os.path.isdir(profile_dir):
        return

    # Lock files that prevent Chrome from becoming the primary instance
    lock_files = [
        "SingletonLock",      # Linux/macOS
        "SingletonSocket",    # Linux
        "SingletonCookie",    # Linux
        "lockfile",           # Windows
    ]
    for name in lock_files:
        lock_path = os.path.join(profile_dir, name)
        try:
            if os.path.exists(lock_path):
                os.remove(lock_path)
                print(f"Removed stale Chrome lock: {lock_path}")
        except OSError:
            pass  # locked by a running Chrome; leave it

    # Session restore data that causes Chrome to show previous page
    # (often the ERR_CONNECTION_REFUSED error) instead of the new URL.
    # Located in Default/Sessions/ within the user-data-dir.
    sessions_dir = os.path.join(profile_dir, "Default", "Sessions")
    try:
        if os.path.isdir(sessions_dir):
            shutil.rmtree(sessions_dir, ignore_errors=True)
            print(f"Cleared Chrome session data: {sessions_dir}")
    except OSError:
        pass


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
    flask_thread = start_flask()

    if not wait_for_flask():
        print("ERROR: Flask did not start within 15 seconds.")
        sys.exit(1)

    print(f"Flask bridge ready at {URL}")

    # 3. Launch browser in kiosk mode
    browser = find_browser()
    browser_proc = None

    global browser_process

    # Clean stale Chrome profile left by taskkill /F:
    # lock files (prevent becoming primary instance) and session data
    # (causes Chrome to restore the previous ERR_CONNECTION_REFUSED page).
    _clean_chrome_profile(KIOSK_PROFILE_DIR)

    if browser:
        # Cache-bust URL prevents Chrome from restoring a cached
        # ERR_CONNECTION_REFUSED page from a previous session.
        cache_bust = f"?_t={int(time.time())}"
        launch_url = f"{URL}{cache_bust}"
        print(f"Launching kiosk browser: {browser}")
        print(f"  URL: {launch_url}")
        browser_proc = subprocess.Popen([
            browser,
            f"--user-data-dir={KIOSK_PROFILE_DIR}",
            "--kiosk",
            "--disable-restore-session-state",
            "--disable-session-crashed-bubble",
            "--disable-infobars",
            "--no-first-run",
            "--disable-translate",
            "--disable-features=TranslateUI",
            "--autoplay-policy=no-user-gesture-required",
            launch_url,
        ])

        # Store reference for /api/shutdown to use
        browser_process = browser_proc

        def cleanup():
            if browser_proc and browser_proc.poll() is None:
                browser_proc.terminate()

        atexit.register(cleanup)
    else:
        print("No browser found. Open the following URL manually:")
        print(f"  {URL}")

    # 4. Keep alive with Flask health monitoring. If the Flask daemon
    #    thread dies (uncaught exception, segfault in C extension, etc.)
    #    exit with code 1 so the watchdog relaunches immediately.
    print("Press Ctrl+C to stop the server.")
    try:
        while True:
            time.sleep(0.5)  # check every 500ms (was 2s, too slow for kiosk)
            if not flask_thread.is_alive():
                print("FATAL: Flask thread died unexpectedly. Exiting for watchdog restart.")
                sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
