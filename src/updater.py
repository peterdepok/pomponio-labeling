"""Auto-updater via GitHub Releases API.

On application launch:
    1. Check latest release version from GitHub
    2. Compare with current version
    3. If newer, download and self-update
    4. Preserve config.ini and data/ across updates
"""

import json
import logging
import os
import shutil
import sys
import tempfile
import zipfile
from typing import Optional

import requests

from src.config import Config

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com/repos/{owner}/{repo}/releases/latest"
DEFAULT_OWNER = "peterdepok"
DEFAULT_REPO = "caldera-decision-engine"
REQUEST_TIMEOUT = 15


class UpdaterError(Exception):
    """Raised on update failure."""


class Updater:
    """GitHub release auto-updater."""

    def __init__(
        self,
        config: Config,
        owner: str = DEFAULT_OWNER,
        repo: str = DEFAULT_REPO,
    ):
        self._config = config
        self._owner = owner
        self._repo = repo
        self._current_version = config.version

    def check_for_update(self) -> Optional[dict]:
        """Check GitHub for a newer release.

        Returns:
            Dict with version, download_url, notes if update available, else None.
        """
        url = GITHUB_API.format(owner=self._owner, repo=self._repo)
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code != 200:
                logger.warning("GitHub API returned %d", response.status_code)
                return None

            release = response.json()
            latest_version = release.get("tag_name", "").lstrip("v")

            if not latest_version:
                return None

            if self._is_newer(latest_version, self._current_version):
                # Find the zip asset
                download_url = None
                for asset in release.get("assets", []):
                    if asset["name"].endswith(".zip"):
                        download_url = asset["browser_download_url"]
                        break

                if download_url is None:
                    # Fall back to source zip
                    download_url = release.get("zipball_url")

                return {
                    "version": latest_version,
                    "download_url": download_url,
                    "notes": release.get("body", ""),
                    "name": release.get("name", ""),
                }

            logger.info("Current version %s is up to date", self._current_version)
            return None

        except requests.RequestException as e:
            logger.warning("Update check failed: %s", e)
            return None

    def download_and_apply(self, download_url: str, new_version: str) -> bool:
        """Download update zip and apply it.

        Preserves config.ini and data/ directory across updates.

        Args:
            download_url: URL to download the update archive.
            new_version: Version string for the update.

        Returns:
            True if update was applied and restart is needed.
        """
        try:
            logger.info("Downloading update %s from %s", new_version, download_url)

            # Download to temp file
            response = requests.get(download_url, stream=True, timeout=60)
            response.raise_for_status()

            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name

            logger.info("Downloaded update to %s", tmp_path)

            # Backup config and data
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_backup = None
            data_backup = None

            config_path = os.path.join(app_dir, "config.ini")
            data_path = os.path.join(app_dir, "data")

            if os.path.exists(config_path):
                config_backup = tempfile.mktemp(suffix=".ini")
                shutil.copy2(config_path, config_backup)

            if os.path.exists(data_path):
                data_backup = tempfile.mkdtemp()
                shutil.copytree(data_path, os.path.join(data_backup, "data"))

            # Extract update
            with zipfile.ZipFile(tmp_path, "r") as zf:
                zf.extractall(app_dir)

            # Restore config and data
            if config_backup and os.path.exists(config_backup):
                shutil.copy2(config_backup, config_path)
                os.unlink(config_backup)

            if data_backup:
                backup_data = os.path.join(data_backup, "data")
                if os.path.exists(backup_data):
                    # Merge: keep existing data files, add new ones
                    for item in os.listdir(backup_data):
                        src = os.path.join(backup_data, item)
                        dst = os.path.join(data_path, item)
                        if os.path.isfile(src) and not item.endswith(".zpl"):
                            # Preserve database and CSV, but allow template updates
                            shutil.copy2(src, dst)
                shutil.rmtree(data_backup)

            # Update version in config
            self._config.set("app", "version", new_version)
            self._config.save()

            # Clean up
            os.unlink(tmp_path)

            logger.info("Update applied: %s -> %s", self._current_version, new_version)
            return True

        except Exception as e:
            logger.error("Update failed: %s", e)
            return False

    @staticmethod
    def _is_newer(latest: str, current: str) -> bool:
        """Compare version strings (semver-like)."""
        try:
            latest_parts = [int(x) for x in latest.split(".")]
            current_parts = [int(x) for x in current.split(".")]
            # Pad to same length
            while len(latest_parts) < len(current_parts):
                latest_parts.append(0)
            while len(current_parts) < len(latest_parts):
                current_parts.append(0)
            return latest_parts > current_parts
        except (ValueError, AttributeError):
            return False
