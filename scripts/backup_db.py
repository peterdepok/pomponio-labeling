#!/usr/bin/env python3
"""
Backup the Pomponio database.

Usage:
    python scripts/backup_db.py                    # Backup to data/backups/
    python scripts/backup_db.py /path/to/backup   # Backup to specific location
    python scripts/backup_db.py --list            # List available backups
    python scripts/backup_db.py --restore FILE    # Restore from backup
"""

import argparse
import shutil
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import DB_PATH


BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"


def backup_database(dest_dir: Path = None) -> Path:
    """
    Create a timestamped backup of the database.
    Returns path to backup file.
    """
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        sys.exit(1)

    dest = dest_dir or BACKUP_DIR
    dest.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"pomponio_{timestamp}.db"
    backup_path = dest / backup_name

    shutil.copy2(DB_PATH, backup_path)
    print(f"Backup created: {backup_path}")
    print(f"Size: {backup_path.stat().st_size:,} bytes")

    return backup_path


def list_backups():
    """List available backup files."""
    if not BACKUP_DIR.exists():
        print("No backups found")
        return

    backups = sorted(BACKUP_DIR.glob("pomponio_*.db"), reverse=True)
    if not backups:
        print("No backups found")
        return

    print(f"\nAvailable backups ({BACKUP_DIR}):\n")
    print(f"{'Filename':<30} {'Size':>12} {'Date':>20}")
    print("-" * 65)

    for backup in backups:
        stat = backup.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        print(f"{backup.name:<30} {stat.st_size:>10,} B  {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\nTotal: {len(backups)} backup(s)")


def restore_database(backup_path: Path):
    """Restore database from backup."""
    if not backup_path.exists():
        # Try in backup directory
        backup_path = BACKUP_DIR / backup_path.name
        if not backup_path.exists():
            print(f"Error: Backup not found: {backup_path}")
            sys.exit(1)

    # Create backup of current before restoring
    if DB_PATH.exists():
        pre_restore = DB_PATH.with_suffix(".db.pre_restore")
        shutil.copy2(DB_PATH, pre_restore)
        print(f"Current database backed up to: {pre_restore}")

    shutil.copy2(backup_path, DB_PATH)
    print(f"Database restored from: {backup_path}")


def main():
    parser = argparse.ArgumentParser(description='Backup and restore Pomponio database')
    parser.add_argument('dest', nargs='?', help='Backup destination directory')
    parser.add_argument('--list', '-l', action='store_true', help='List available backups')
    parser.add_argument('--restore', '-r', metavar='FILE', help='Restore from backup file')
    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.restore:
        restore_database(Path(args.restore))
    else:
        dest = Path(args.dest) if args.dest else None
        backup_database(dest)


if __name__ == '__main__':
    main()
