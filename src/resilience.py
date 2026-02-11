"""
Resilience and redundancy module.
Provides automatic recovery, retries, backups, and fault tolerance.
"""

import os
import sys
import time
import shutil
import logging
import threading
import traceback
import functools
from pathlib import Path
from datetime import datetime, timedelta
from typing import Callable, Optional, Any, TypeVar
from dataclasses import dataclass, field

from src import get_app_dir

# Configure logging
LOG_DIR = get_app_dir() / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / f"pomponio_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("pomponio")


# ============================================================================
# Retry Decorator
# ============================================================================

T = TypeVar('T')


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Callable[[Exception, int], None] = None
):
    """
    Decorator that retries a function on failure.

    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries (seconds)
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Callback called on each retry with (exception, attempt_number)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}"
                        )
                        if on_retry:
                            on_retry(e, attempt)
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )

            raise last_exception

        return wrapper
    return decorator


# ============================================================================
# Database Backup Manager
# ============================================================================

class DatabaseBackupManager:
    """
    Automatic database backup with rotation and recovery.
    """

    def __init__(
        self,
        db_path: Path,
        backup_dir: Path = None,
        max_backups: int = 10,
        backup_interval_hours: int = 1
    ):
        self.db_path = Path(db_path)
        self.backup_dir = backup_dir or (self.db_path.parent / "backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.max_backups = max_backups
        self.backup_interval = timedelta(hours=backup_interval_hours)
        self._last_backup: Optional[datetime] = None
        self._lock = threading.Lock()

    def backup_now(self, reason: str = "manual") -> Optional[Path]:
        """Create immediate backup."""
        with self._lock:
            if not self.db_path.exists():
                logger.warning(f"Database not found at {self.db_path}")
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"pomponio_{timestamp}_{reason}.db"
            backup_path = self.backup_dir / backup_name

            try:
                shutil.copy2(self.db_path, backup_path)
                self._last_backup = datetime.now()
                logger.info(f"Database backed up to {backup_path}")
                self._rotate_backups()
                return backup_path
            except Exception as e:
                logger.error(f"Backup failed: {e}")
                return None

    def backup_if_needed(self) -> Optional[Path]:
        """Create backup if interval has passed."""
        if self._last_backup is None:
            return self.backup_now("auto")

        if datetime.now() - self._last_backup >= self.backup_interval:
            return self.backup_now("auto")

        return None

    def _rotate_backups(self):
        """Remove old backups beyond max_backups."""
        backups = sorted(
            self.backup_dir.glob("pomponio_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        for old_backup in backups[self.max_backups:]:
            try:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
            except Exception as e:
                logger.warning(f"Could not remove old backup {old_backup}: {e}")

    def list_backups(self) -> list[tuple[Path, datetime]]:
        """List available backups with timestamps."""
        backups = []
        for backup in self.backup_dir.glob("pomponio_*.db"):
            mtime = datetime.fromtimestamp(backup.stat().st_mtime)
            backups.append((backup, mtime))
        return sorted(backups, key=lambda x: x[1], reverse=True)

    def restore_latest(self) -> bool:
        """Restore from most recent backup."""
        backups = self.list_backups()
        if not backups:
            logger.error("No backups available for restore")
            return False

        latest_backup, _ = backups[0]
        return self.restore_from(latest_backup)

    def restore_from(self, backup_path: Path) -> bool:
        """Restore database from specific backup."""
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_path}")
            return False

        try:
            # Backup current before restore
            if self.db_path.exists():
                pre_restore = self.db_path.with_suffix(".db.pre_restore")
                shutil.copy2(self.db_path, pre_restore)
                logger.info(f"Current database backed up to {pre_restore}")

            shutil.copy2(backup_path, self.db_path)
            logger.info(f"Database restored from {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False


# ============================================================================
# Hardware Connection Manager
# ============================================================================

@dataclass
class ConnectionStatus:
    """Hardware connection status."""
    connected: bool
    last_check: datetime
    consecutive_failures: int = 0
    last_error: Optional[str] = None


class HardwareConnectionManager:
    """
    Manages hardware connections with automatic reconnection.
    """

    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 2.0
    HEALTH_CHECK_INTERVAL = 5.0

    def __init__(self):
        self._devices: dict[str, Any] = {}
        self._status: dict[str, ConnectionStatus] = {}
        self._callbacks: dict[str, list[Callable]] = {
            'disconnect': [],
            'reconnect': [],
            'failure': [],
        }
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def register_device(self, name: str, device: Any):
        """Register a device for monitoring."""
        with self._lock:
            self._devices[name] = device
            self._status[name] = ConnectionStatus(
                connected=self._check_device(device),
                last_check=datetime.now()
            )
            logger.info(f"Registered device: {name}")

    def _check_device(self, device: Any) -> bool:
        """Check if device is connected."""
        if hasattr(device, 'is_connected'):
            try:
                return device.is_connected()
            except:
                return False
        return True

    def _reconnect_device(self, name: str, device: Any) -> bool:
        """Attempt to reconnect device."""
        for attempt in range(1, self.MAX_RECONNECT_ATTEMPTS + 1):
            try:
                if hasattr(device, 'disconnect'):
                    try:
                        device.disconnect()
                    except:
                        pass

                if hasattr(device, 'connect'):
                    device.connect()

                if self._check_device(device):
                    logger.info(f"Reconnected {name} on attempt {attempt}")
                    return True

            except Exception as e:
                logger.warning(f"Reconnect {name} attempt {attempt} failed: {e}")

            time.sleep(self.RECONNECT_DELAY)

        return False

    def start_monitoring(self):
        """Start background monitoring thread."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info("Hardware monitoring started")

    def stop_monitoring(self):
        """Stop monitoring thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("Hardware monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            with self._lock:
                for name, device in self._devices.items():
                    was_connected = self._status[name].connected
                    is_connected = self._check_device(device)

                    self._status[name].last_check = datetime.now()
                    self._status[name].connected = is_connected

                    if was_connected and not is_connected:
                        # Device disconnected
                        self._status[name].consecutive_failures += 1
                        logger.warning(f"{name} disconnected")
                        self._notify('disconnect', name)

                        # Attempt reconnection
                        if self._reconnect_device(name, device):
                            self._status[name].connected = True
                            self._status[name].consecutive_failures = 0
                            self._notify('reconnect', name)
                        else:
                            self._notify('failure', name)

                    elif not was_connected and is_connected:
                        # Device reconnected externally
                        self._status[name].consecutive_failures = 0
                        logger.info(f"{name} reconnected")
                        self._notify('reconnect', name)

            time.sleep(self.HEALTH_CHECK_INTERVAL)

    def on_disconnect(self, callback: Callable[[str], None]):
        """Register disconnect callback."""
        self._callbacks['disconnect'].append(callback)

    def on_reconnect(self, callback: Callable[[str], None]):
        """Register reconnect callback."""
        self._callbacks['reconnect'].append(callback)

    def on_failure(self, callback: Callable[[str], None]):
        """Register permanent failure callback."""
        self._callbacks['failure'].append(callback)

    def _notify(self, event: str, device_name: str):
        """Notify registered callbacks."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(device_name)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def get_status(self, name: str) -> Optional[ConnectionStatus]:
        """Get device status."""
        return self._status.get(name)

    def is_connected(self, name: str) -> bool:
        """Check if device is currently connected."""
        status = self._status.get(name)
        return status.connected if status else False


# ============================================================================
# Operation Queue with Persistence
# ============================================================================

@dataclass
class PendingOperation:
    """An operation waiting to be completed."""
    id: str
    operation_type: str
    data: dict
    created_at: datetime = field(default_factory=datetime.now)
    attempts: int = 0
    last_error: Optional[str] = None


class OperationQueue:
    """
    Queue for operations that need to be persisted and retried.
    Survives crashes and restarts.
    """

    def __init__(self, queue_file: Path):
        self.queue_file = Path(queue_file)
        self._operations: dict[str, PendingOperation] = {}
        self._lock = threading.Lock()
        self._load_queue()

    def _load_queue(self):
        """Load pending operations from disk."""
        if not self.queue_file.exists():
            return

        try:
            import json
            with open(self.queue_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    op = PendingOperation(
                        id=item['id'],
                        operation_type=item['type'],
                        data=item['data'],
                        created_at=datetime.fromisoformat(item['created_at']),
                        attempts=item.get('attempts', 0),
                        last_error=item.get('last_error')
                    )
                    self._operations[op.id] = op
            logger.info(f"Loaded {len(self._operations)} pending operations")
        except Exception as e:
            logger.error(f"Failed to load operation queue: {e}")

    def _save_queue(self):
        """Save pending operations to disk."""
        try:
            import json
            data = []
            for op in self._operations.values():
                data.append({
                    'id': op.id,
                    'type': op.operation_type,
                    'data': op.data,
                    'created_at': op.created_at.isoformat(),
                    'attempts': op.attempts,
                    'last_error': op.last_error
                })
            with open(self.queue_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save operation queue: {e}")

    def add(self, operation_type: str, data: dict) -> str:
        """Add operation to queue."""
        import uuid
        op_id = str(uuid.uuid4())[:8]

        with self._lock:
            self._operations[op_id] = PendingOperation(
                id=op_id,
                operation_type=operation_type,
                data=data
            )
            self._save_queue()

        logger.info(f"Queued operation {op_id}: {operation_type}")
        return op_id

    def complete(self, op_id: str):
        """Mark operation as complete."""
        with self._lock:
            if op_id in self._operations:
                del self._operations[op_id]
                self._save_queue()
                logger.info(f"Completed operation {op_id}")

    def fail(self, op_id: str, error: str):
        """Record operation failure."""
        with self._lock:
            if op_id in self._operations:
                self._operations[op_id].attempts += 1
                self._operations[op_id].last_error = error
                self._save_queue()

    def get_pending(self) -> list[PendingOperation]:
        """Get all pending operations."""
        with self._lock:
            return list(self._operations.values())

    def clear(self):
        """Clear all pending operations."""
        with self._lock:
            self._operations.clear()
            self._save_queue()


# ============================================================================
# State Persistence for Crash Recovery
# ============================================================================

class StatePersistence:
    """
    Persists application state for crash recovery.
    """

    def __init__(self, state_file: Path):
        self.state_file = Path(state_file)
        self._state: dict = {}
        self._lock = threading.Lock()
        self._load_state()

    def _load_state(self):
        """Load state from disk."""
        if not self.state_file.exists():
            return

        try:
            import json
            with open(self.state_file, 'r') as f:
                self._state = json.load(f)
            logger.info("Loaded persisted state")
        except Exception as e:
            logger.warning(f"Could not load state: {e}")
            self._state = {}

    def _save_state(self):
        """Save state to disk."""
        try:
            import json
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self._state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save state: {e}")

    def set(self, key: str, value: Any):
        """Set state value."""
        with self._lock:
            self._state[key] = value
            self._save_state()

    def get(self, key: str, default: Any = None) -> Any:
        """Get state value."""
        with self._lock:
            return self._state.get(key, default)

    def remove(self, key: str):
        """Remove state value."""
        with self._lock:
            if key in self._state:
                del self._state[key]
                self._save_state()

    def clear(self):
        """Clear all state."""
        with self._lock:
            self._state.clear()
            self._save_state()

    def has_pending_work(self) -> bool:
        """Check if there's pending work from crash."""
        return bool(self._state.get('pending_package') or
                    self._state.get('pending_print') or
                    self._state.get('awaiting_scan'))


# ============================================================================
# Error Reporter
# ============================================================================

class ErrorReporter:
    """
    Collects and reports errors for debugging.
    """

    def __init__(self, log_dir: Path):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._error_count = 0

    def report_error(
        self,
        error: Exception,
        context: dict = None,
        fatal: bool = False
    ) -> str:
        """
        Report an error with context.
        Returns error ID for reference.
        """
        self._error_count += 1
        error_id = f"ERR{datetime.now().strftime('%Y%m%d%H%M%S')}{self._error_count:04d}"

        error_data = {
            'id': error_id,
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {},
            'fatal': fatal,
            'python_version': sys.version,
        }

        # Log to file
        error_file = self.log_dir / f"error_{error_id}.log"
        try:
            import json
            with open(error_file, 'w') as f:
                json.dump(error_data, f, indent=2, default=str)
        except:
            pass

        # Log to console
        if fatal:
            logger.critical(f"FATAL ERROR {error_id}: {error}")
        else:
            logger.error(f"ERROR {error_id}: {error}")

        return error_id

    def get_recent_errors(self, limit: int = 10) -> list[dict]:
        """Get recent error reports."""
        import json
        errors = []
        for error_file in sorted(self.log_dir.glob("error_*.log"), reverse=True)[:limit]:
            try:
                with open(error_file, 'r') as f:
                    errors.append(json.load(f))
            except:
                pass
        return errors


# ============================================================================
# Safe Operation Wrapper
# ============================================================================

def safe_operation(
    operation_name: str,
    fallback: Any = None,
    notify_user: bool = True
):
    """
    Decorator for safe operation execution with error handling.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Operation '{operation_name}' failed: {e}")
                logger.debug(traceback.format_exc())

                if notify_user and args and hasattr(args[0], 'status_bar'):
                    try:
                        args[0].status_bar.flash_error(f"Error: {operation_name}")
                    except:
                        pass

                return fallback

        return wrapper
    return decorator


# ============================================================================
# Input Sanitizer
# ============================================================================

class InputSanitizer:
    """
    Sanitizes and validates all user inputs.
    """

    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Sanitize string input."""
        if not value:
            return ""
        # Remove control characters, limit length
        clean = ''.join(c for c in value if c.isprintable() or c.isspace())
        return clean.strip()[:max_length]

    @staticmethod
    def sanitize_sku(value: str) -> Optional[str]:
        """Sanitize SKU input."""
        if not value:
            return None
        clean = ''.join(c for c in value if c.isdigit())
        if len(clean) > 5:
            return None
        return clean.zfill(5) if clean else None

    @staticmethod
    def sanitize_weight(value: Any) -> Optional[float]:
        """Sanitize weight input."""
        try:
            weight = float(value)
            if 0 < weight < 1000:
                return round(weight, 2)
            return None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def sanitize_barcode(value: str) -> Optional[str]:
        """Sanitize barcode input."""
        if not value:
            return None
        clean = ''.join(c for c in value if c.isdigit())
        if len(clean) == 12:  # UPC-A
            return clean
        return None

    @staticmethod
    def sanitize_customer_name(value: str) -> Optional[str]:
        """Sanitize customer name."""
        if not value:
            return None
        clean = InputSanitizer.sanitize_string(value, 100)
        if len(clean) < 2:
            return None
        return clean


# ============================================================================
# Global Instances
# ============================================================================

# Initialize global instances
_db_backup_manager: Optional[DatabaseBackupManager] = None
_hw_connection_manager: Optional[HardwareConnectionManager] = None
_operation_queue: Optional[OperationQueue] = None
_state_persistence: Optional[StatePersistence] = None
_error_reporter: Optional[ErrorReporter] = None


def init_resilience(data_dir: Path):
    """Initialize all resilience components."""
    global _db_backup_manager, _hw_connection_manager, _operation_queue
    global _state_persistence, _error_reporter

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    _db_backup_manager = DatabaseBackupManager(
        db_path=data_dir / "pomponio.db",
        backup_dir=data_dir / "backups"
    )

    _hw_connection_manager = HardwareConnectionManager()

    _operation_queue = OperationQueue(
        queue_file=data_dir / "pending_operations.json"
    )

    _state_persistence = StatePersistence(
        state_file=data_dir / "app_state.json"
    )

    _error_reporter = ErrorReporter(
        log_dir=data_dir / "logs"
    )

    logger.info("Resilience components initialized")


def get_backup_manager() -> Optional[DatabaseBackupManager]:
    return _db_backup_manager


def get_connection_manager() -> Optional[HardwareConnectionManager]:
    return _hw_connection_manager


def get_operation_queue() -> Optional[OperationQueue]:
    return _operation_queue


def get_state_persistence() -> Optional[StatePersistence]:
    return _state_persistence


def get_error_reporter() -> Optional[ErrorReporter]:
    return _error_reporter
