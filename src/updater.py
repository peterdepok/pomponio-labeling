"""
Auto-updater for Pomponio Ranch Labeling System.
Checks GitHub releases for updates and applies them automatically.
"""

import os
import sys
import json
import shutil
import zipfile
import tempfile
import subprocess
import threading
from pathlib import Path
from typing import Optional, Callable, Tuple
from dataclasses import dataclass
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from src import get_app_dir

# Current version - increment this with each release
__version__ = "1.0.0"

# GitHub repository info
GITHUB_OWNER = "peterdepok"
GITHUB_REPO = "pomponio-labeling"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"


@dataclass
class ReleaseInfo:
    """Information about a GitHub release."""
    version: str
    tag_name: str
    name: str
    body: str  # Release notes
    download_url: str
    published_at: str
    size_bytes: int


def get_current_version() -> str:
    """Get the current application version."""
    return __version__


def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string into tuple for comparison."""
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v')
    parts = version_str.split('.')
    try:
        return (
            int(parts[0]) if len(parts) > 0 else 0,
            int(parts[1]) if len(parts) > 1 else 0,
            int(parts[2]) if len(parts) > 2 else 0
        )
    except ValueError:
        return (0, 0, 0)


def is_newer_version(remote: str, local: str) -> bool:
    """Check if remote version is newer than local."""
    remote_tuple = parse_version(remote)
    local_tuple = parse_version(local)
    return remote_tuple > local_tuple


def check_for_updates() -> Optional[ReleaseInfo]:
    """
    Check GitHub for a newer release.
    Returns ReleaseInfo if update available, None otherwise.
    """
    try:
        # Create request with user agent (GitHub requires this)
        request = Request(
            GITHUB_API_URL,
            headers={
                'User-Agent': 'Pomponio-Ranch-Labeling',
                'Accept': 'application/vnd.github.v3+json'
            }
        )

        with urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

        # Extract version from tag
        tag_name = data.get('tag_name', '')
        remote_version = tag_name.lstrip('v')

        # Check if newer
        if not is_newer_version(remote_version, __version__):
            return None

        # Find the zip asset for Windows
        download_url = None
        size_bytes = 0

        for asset in data.get('assets', []):
            name = asset.get('name', '').lower()
            if name.endswith('.zip') and 'windows' in name:
                download_url = asset.get('browser_download_url')
                size_bytes = asset.get('size', 0)
                break

        # If no Windows-specific asset, look for any zip
        if not download_url:
            for asset in data.get('assets', []):
                if asset.get('name', '').lower().endswith('.zip'):
                    download_url = asset.get('browser_download_url')
                    size_bytes = asset.get('size', 0)
                    break

        # Fallback to source zip if no release assets
        if not download_url:
            download_url = data.get('zipball_url')
            size_bytes = 0  # Unknown size for source archives

        if not download_url:
            return None

        return ReleaseInfo(
            version=remote_version,
            tag_name=tag_name,
            name=data.get('name', f'Version {remote_version}'),
            body=data.get('body', 'No release notes available.'),
            download_url=download_url,
            published_at=data.get('published_at', ''),
            size_bytes=size_bytes
        )

    except (URLError, HTTPError, json.JSONDecodeError, KeyError) as e:
        print(f"Update check failed: {e}")
        return None


def download_update(
    release: ReleaseInfo,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Optional[Path]:
    """
    Download the update zip file.
    Returns path to downloaded file, or None on failure.
    """
    try:
        request = Request(
            release.download_url,
            headers={'User-Agent': 'Pomponio-Ranch-Labeling'}
        )

        # Create temp file for download
        temp_dir = Path(tempfile.gettempdir()) / 'pomponio_update'
        temp_dir.mkdir(exist_ok=True)
        download_path = temp_dir / 'update.zip'

        with urlopen(request, timeout=60) as response:
            total_size = int(response.headers.get('Content-Length', 0))
            downloaded = 0
            chunk_size = 8192

            with open(download_path, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)

                    if progress_callback:
                        progress_callback(downloaded, total_size)

        return download_path

    except Exception as e:
        print(f"Download failed: {e}")
        return None


def apply_update(zip_path: Path, app_dir: Optional[Path] = None) -> bool:
    """
    Apply the downloaded update.
    This extracts the zip and replaces application files.
    Returns True on success.
    """
    try:
        # Determine application directory
        if app_dir is None:
            app_dir = get_app_dir()

        # Create backup of current installation
        backup_dir = app_dir.parent / 'pomponio_backup'
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

        # Backup critical files
        backup_dir.mkdir(exist_ok=True)
        for item in ['config.ini', 'data']:
            src = app_dir / item
            if src.exists():
                dst = backup_dir / item
                if src.is_dir():
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

        # Extract update to temp location
        extract_dir = Path(tempfile.gettempdir()) / 'pomponio_extract'
        if extract_dir.exists():
            shutil.rmtree(extract_dir)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)

        # Find the root of the extracted content
        # GitHub source zips have a nested folder
        extracted_items = list(extract_dir.iterdir())
        if len(extracted_items) == 1 and extracted_items[0].is_dir():
            source_dir = extracted_items[0]
        else:
            source_dir = extract_dir

        # Copy new files over existing (except config and data)
        for item in source_dir.iterdir():
            if item.name in ['config.ini', 'data', '.git', '__pycache__']:
                continue

            dst = app_dir / item.name

            if item.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)

        # Restore backed up config and data
        for item in ['config.ini', 'data']:
            backup_src = backup_dir / item
            if backup_src.exists():
                dst = app_dir / item
                if backup_src.is_dir():
                    if dst.exists():
                        # Merge data directories, preserving existing files
                        for subitem in backup_src.iterdir():
                            subdst = dst / subitem.name
                            if not subdst.exists():
                                if subitem.is_dir():
                                    shutil.copytree(subitem, subdst)
                                else:
                                    shutil.copy2(subitem, subdst)
                    else:
                        shutil.copytree(backup_src, dst)
                else:
                    shutil.copy2(backup_src, dst)

        # Cleanup
        shutil.rmtree(extract_dir, ignore_errors=True)

        return True

    except Exception as e:
        print(f"Update application failed: {e}")
        return False


def restart_application():
    """Restart the application after update."""
    if getattr(sys, 'frozen', False):
        # Running as exe - restart the exe
        exe_path = sys.executable
        subprocess.Popen([exe_path], cwd=Path(exe_path).parent)
    else:
        # Running as script - restart Python
        python = sys.executable
        script = sys.argv[0]
        subprocess.Popen([python, script] + sys.argv[1:])

    sys.exit(0)


class UpdateChecker:
    """
    Background update checker with UI callbacks.
    """

    def __init__(
        self,
        on_update_available: Optional[Callable[[ReleaseInfo], None]] = None,
        on_no_update: Optional[Callable[[], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        self.on_update_available = on_update_available
        self.on_no_update = on_no_update
        self.on_error = on_error
        self._thread: Optional[threading.Thread] = None

    def check_async(self):
        """Check for updates in background thread."""
        if self._thread and self._thread.is_alive():
            return  # Already checking

        self._thread = threading.Thread(target=self._check_worker, daemon=True)
        self._thread.start()

    def _check_worker(self):
        """Worker thread for update check."""
        try:
            release = check_for_updates()
            if release:
                if self.on_update_available:
                    self.on_update_available(release)
            else:
                if self.on_no_update:
                    self.on_no_update()
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))


class UpdateDownloader:
    """
    Background update downloader with progress callbacks.
    """

    def __init__(
        self,
        release: ReleaseInfo,
        on_progress: Optional[Callable[[int, int], None]] = None,
        on_complete: Optional[Callable[[Path], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        self.release = release
        self.on_progress = on_progress
        self.on_complete = on_complete
        self.on_error = on_error
        self._thread: Optional[threading.Thread] = None
        self._cancelled = False

    def download_async(self):
        """Download update in background thread."""
        if self._thread and self._thread.is_alive():
            return

        self._cancelled = False
        self._thread = threading.Thread(target=self._download_worker, daemon=True)
        self._thread.start()

    def cancel(self):
        """Cancel download."""
        self._cancelled = True

    def _download_worker(self):
        """Worker thread for download."""
        try:
            def progress(downloaded, total):
                if self._cancelled:
                    raise InterruptedError("Download cancelled")
                if self.on_progress:
                    self.on_progress(downloaded, total)

            zip_path = download_update(self.release, progress_callback=progress)

            if zip_path and not self._cancelled:
                if self.on_complete:
                    self.on_complete(zip_path)
            elif not self._cancelled:
                if self.on_error:
                    self.on_error("Download failed")

        except InterruptedError:
            pass  # Cancelled
        except Exception as e:
            if self.on_error:
                self.on_error(str(e))


def create_release_zip(version: str, output_dir: Optional[Path] = None) -> Path:
    """
    Create a release zip file for distribution.
    This is used when preparing a new release.
    """
    if output_dir is None:
        output_dir = Path.cwd()

    # Source directory
    src_dir = get_app_dir()

    # Output file
    zip_name = f"pomponio-labeling-windows-v{version}.zip"
    zip_path = output_dir / zip_name

    # Files to include
    include = [
        'run.py',
        'requirements.txt',
        'config.ini.example',
        'src',
        'data',
    ]

    # Files to exclude
    exclude = [
        '__pycache__',
        '.pyc',
        '.git',
        'dist',
        'build',
        '*.spec',
        'backups',
        'logs',
    ]

    def should_exclude(path: Path) -> bool:
        for pattern in exclude:
            if pattern in str(path):
                return True
        return False

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in include:
            item_path = src_dir / item
            if not item_path.exists():
                continue

            if item_path.is_file():
                if not should_exclude(item_path):
                    zf.write(item_path, item)
            else:
                for root, dirs, files in os.walk(item_path):
                    root_path = Path(root)
                    if should_exclude(root_path):
                        continue

                    for file in files:
                        file_path = root_path / file
                        if not should_exclude(file_path):
                            arc_name = file_path.relative_to(src_dir)
                            zf.write(file_path, arc_name)

    return zip_path


if __name__ == '__main__':
    # Test update check
    print(f"Current version: {__version__}")
    print("Checking for updates...")

    release = check_for_updates()
    if release:
        print(f"Update available: {release.version}")
        print(f"Release: {release.name}")
        print(f"Download: {release.download_url}")
        print(f"Notes: {release.body[:200]}...")
    else:
        print("No updates available.")
