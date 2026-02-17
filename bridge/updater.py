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
    """Run a command in PROJECT_ROOT and return the result.

    On Windows, shell=True is required so cmd.exe can resolve .cmd
    wrappers like npm.cmd that subprocess cannot find directly.
    """
    return subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=(sys.platform == "win32"),
    )


def check_for_update() -> dict:
    """Fetch from origin and compare HEAD with origin/main.

    Returns:
        Dict with updateAvailable bool, currentCommit, latestCommit,
        and (if available) commitsBehind and summary.
    """
    try:
        # Detect current branch name (could be main or master)
        branch_result = _run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=5
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "main"

        # Fetch latest refs from origin
        fetch = _run(["git", "fetch", "origin"], timeout=30)
        if fetch.returncode != 0:
            return {"updateAvailable": False, "error": fetch.stderr.strip()}

        # Get local HEAD
        head = _run(["git", "rev-parse", "HEAD"], timeout=5)
        current_commit = head.stdout.strip()

        # Get remote HEAD for the tracked branch
        remote = _run(["git", "rev-parse", f"origin/{branch}"], timeout=5)
        if remote.returncode != 0:
            return {
                "updateAvailable": False,
                "error": f"No remote branch origin/{branch}",
                "currentCommit": current_commit[:8],
                "branch": branch,
            }
        latest_commit = remote.stdout.strip()

        if current_commit == latest_commit:
            return {
                "updateAvailable": False,
                "currentCommit": current_commit[:8],
                "latestCommit": latest_commit[:8],
            }

        # Count commits behind
        count = _run(
            ["git", "rev-list", "--count", f"HEAD..origin/{branch}"], timeout=5
        )
        commits_behind = int(count.stdout.strip()) if count.returncode == 0 else 0

        # Get one-line summaries of new commits
        log = _run(
            ["git", "log", "--oneline", f"HEAD..origin/{branch}"], timeout=5
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

    If the npm build fails after a successful git pull, the code is
    rolled back to the pre-pull commit with ``git reset --hard`` so
    the kiosk never serves a broken React build.

    Returns:
        Dict with ok bool. On success, restartRequired is True.
        On failure, error contains the stderr output.
    """
    try:
        # Detect current branch
        branch_result = _run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], timeout=5
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "main"

        # Record pre-pull SHA for rollback if build fails
        head_before = _run(["git", "rev-parse", "HEAD"], timeout=5)
        pre_pull_sha = head_before.stdout.strip() if head_before.returncode == 0 else ""

        # Stash any local changes (e.g. config.ini) so pull never conflicts
        stash = _run(["git", "stash", "--include-untracked"], timeout=10)
        did_stash = stash.returncode == 0 and "No local changes" not in stash.stdout

        # Pull latest
        pull = _run(["git", "pull", "origin", branch], timeout=60)
        if pull.returncode != 0:
            logger.error("git pull failed: %s", pull.stderr)
            # Restore stash even on failure
            if did_stash:
                _run(["git", "stash", "pop"], timeout=10)
            return {"ok": False, "error": f"git pull failed: {pull.stderr.strip()}"}

        # Restore stashed local changes
        if did_stash:
            pop = _run(["git", "stash", "pop"], timeout=10)
            if pop.returncode != 0:
                logger.warning("git stash pop had conflicts: %s", pop.stderr)

        logger.info("git pull succeeded: %s", pull.stdout.strip())

        # Rebuild React frontend
        build = _run(["npm", "run", "build"], timeout=120)
        if build.returncode != 0:
            logger.error("npm run build failed: %s", build.stderr)

            # Rollback: reset to pre-pull commit so the old dist/ stays valid
            if pre_pull_sha:
                logger.warning("Rolling back to %s after failed build", pre_pull_sha[:8])
                rollback = _run(
                    ["git", "reset", "--hard", pre_pull_sha], timeout=15
                )
                if rollback.returncode == 0:
                    logger.info("Rollback successful")
                    # Restore stash on top of rolled-back code
                    if did_stash:
                        _run(["git", "stash", "pop"], timeout=10)
                else:
                    logger.error("Rollback failed: %s", rollback.stderr)

            return {"ok": False, "error": f"Build failed: {build.stderr.strip()}"}

        logger.info("npm run build succeeded")
        return {"ok": True, "restartRequired": True}

    except subprocess.TimeoutExpired as e:
        cmd_name = "git pull" if "pull" in str(e.cmd) else "npm build"
        return {"ok": False, "error": f"{cmd_name} timed out"}
    except Exception as e:
        logger.error("Apply update failed: %s", e)
        return {"ok": False, "error": str(e)}


def _kill_browser() -> None:
    """Terminate the kiosk Chrome process if it is still running.

    Uses the module-level ``browser_process`` reference stored by
    run_production.main(). Imported lazily to avoid circular imports.
    Failures are logged but never raised; the restart must proceed
    regardless.
    """
    try:
        import run_production
        proc = run_production.browser_process
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except Exception:
                proc.kill()
            logger.info("Browser terminated before restart")
    except Exception as e:
        logger.warning("Browser cleanup during restart failed: %s", e)


def schedule_restart(delay: float = 2.0) -> None:
    """Schedule a process restart after a short delay.

    The delay allows the HTTP response to complete before the process
    exits. Chrome is killed first so the user does not see BRIDGE
    OFFLINE during the restart gap. On both platforms, the process
    simply terminates and relies on the external watchdog
    (start_kiosk.bat on Windows, systemd or similar on Unix) to
    relaunch it.

    On Unix without a watchdog, os.execv replaces the process in place
    as a fallback.
    """
    def _restart():
        time.sleep(delay)
        logger.info("Restarting application...")

        # Kill Chrome before exit so the user never sees BRIDGE OFFLINE
        _kill_browser()

        if sys.platform == "win32":
            # Exit cleanly; the watchdog loop in start_kiosk.bat will
            # detect the exit and relaunch run_production.py.
            # Do NOT spawn a child process here: that orphans it
            # outside the watchdog and breaks recovery on next reboot.
            logger.info("Exiting for watchdog relaunch (code 0)")
            os._exit(0)
        else:
            # Unix: replace current process in place
            entry_point = os.path.join(PROJECT_ROOT, "run_production.py")
            os.execv(sys.executable, [sys.executable, entry_point])

    t = threading.Thread(target=_restart, daemon=True, name="updater-restart")
    t.start()
    logger.info("Restart scheduled in %.1f seconds", delay)
