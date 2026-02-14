"""Git-based self-updater for the Pomponio Ranch Labeling System.

Provides two operations exposed via Flask endpoints:

    check_for_update()  - git fetch + compare HEAD vs origin/main
    apply_update()      - git pull + npm run build
    schedule_restart()  - delayed os.execv (Unix) or subprocess.Popen (Windows)

All git/npm commands run from PROJECT_ROOT with subprocess.run.
"""

import logging
import os
import subprocess
import sys
import threading
import time

logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run(cmd: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a command in PROJECT_ROOT and return the result."""
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def check_for_update() -> dict:
    """Fetch from origin and compare HEAD with origin/main.

    Returns:
        Dict with updateAvailable bool, currentCommit, latestCommit,
        and (if available) commitsBehind and summary.
    """
    try:
        # Fetch latest refs from origin
        fetch = _run(["git", "fetch", "origin"], timeout=30)
        if fetch.returncode != 0:
            return {"updateAvailable": False, "error": fetch.stderr.strip()}

        # Get local HEAD
        head = _run(["git", "rev-parse", "HEAD"], timeout=5)
        current_commit = head.stdout.strip()

        # Get remote HEAD
        remote = _run(["git", "rev-parse", "origin/main"], timeout=5)
        latest_commit = remote.stdout.strip()

        if current_commit == latest_commit:
            return {
                "updateAvailable": False,
                "currentCommit": current_commit[:8],
                "latestCommit": latest_commit[:8],
            }

        # Count commits behind
        count = _run(
            ["git", "rev-list", "--count", "HEAD..origin/main"], timeout=5
        )
        commits_behind = int(count.stdout.strip()) if count.returncode == 0 else 0

        # Get one-line summaries of new commits
        log = _run(
            ["git", "log", "--oneline", "HEAD..origin/main"], timeout=5
        )
        summary = log.stdout.strip() if log.returncode == 0 else ""

        return {
            "updateAvailable": True,
            "currentCommit": current_commit[:8],
            "latestCommit": latest_commit[:8],
            "commitsBehind": commits_behind,
            "summary": summary,
        }

    except subprocess.TimeoutExpired:
        return {"updateAvailable": False, "error": "Git fetch timed out"}
    except Exception as e:
        logger.error("Update check failed: %s", e)
        return {"updateAvailable": False, "error": str(e)}


def apply_update() -> dict:
    """Pull latest code and rebuild the React frontend.

    Returns:
        Dict with ok bool. On success, restartRequired is True.
        On failure, error contains the stderr output.
    """
    try:
        # Pull latest
        pull = _run(["git", "pull", "origin", "main"], timeout=60)
        if pull.returncode != 0:
            logger.error("git pull failed: %s", pull.stderr)
            return {"ok": False, "error": f"git pull failed: {pull.stderr.strip()}"}

        logger.info("git pull succeeded: %s", pull.stdout.strip())

        # Rebuild React frontend
        build = _run(["npm", "run", "build"], timeout=120)
        if build.returncode != 0:
            logger.error("npm run build failed: %s", build.stderr)
            return {"ok": False, "error": f"Build failed: {build.stderr.strip()}"}

        logger.info("npm run build succeeded")
        return {"ok": True, "restartRequired": True}

    except subprocess.TimeoutExpired as e:
        cmd_name = "git pull" if "pull" in str(e.cmd) else "npm build"
        return {"ok": False, "error": f"{cmd_name} timed out"}
    except Exception as e:
        logger.error("Apply update failed: %s", e)
        return {"ok": False, "error": str(e)}


def schedule_restart(delay: float = 2.0) -> None:
    """Schedule a process restart after a short delay.

    The delay allows the HTTP response to complete before the process
    replaces itself. On Unix, uses os.execv to atomically replace the
    process. On Windows, spawns a new process then exits.
    """
    def _restart():
        time.sleep(delay)
        logger.info("Restarting application...")

        entry_point = os.path.join(PROJECT_ROOT, "run_production.py")

        if sys.platform == "win32":
            # Windows: spawn new process, then exit current
            subprocess.Popen(
                [sys.executable, entry_point],
                cwd=PROJECT_ROOT,
            )
            os._exit(0)
        else:
            # Unix: replace current process in place
            os.execv(sys.executable, [sys.executable, entry_point])

    t = threading.Thread(target=_restart, daemon=True, name="updater-restart")
    t.start()
    logger.info("Restart scheduled in %.1f seconds", delay)
