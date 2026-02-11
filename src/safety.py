"""
Safety and validation module.
Provides bullet-proof checks and error recovery.
"""

import time
import threading
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum, auto


class WorkflowState(Enum):
    """Labeling workflow states - enforces correct sequence."""
    IDLE = auto()
    PRODUCT_SELECTED = auto()
    WEIGHT_CAPTURED = auto()
    LABEL_PRINTED = auto()
    AWAITING_SCAN = auto()
    VERIFIED = auto()


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    message: str
    can_retry: bool = False


class WorkflowGuard:
    """
    Enforces correct workflow sequence.
    Prevents skipping steps or invalid state transitions.
    """

    VALID_TRANSITIONS = {
        WorkflowState.IDLE: [WorkflowState.PRODUCT_SELECTED],
        WorkflowState.PRODUCT_SELECTED: [WorkflowState.WEIGHT_CAPTURED, WorkflowState.IDLE],
        WorkflowState.WEIGHT_CAPTURED: [WorkflowState.LABEL_PRINTED, WorkflowState.PRODUCT_SELECTED, WorkflowState.IDLE],
        WorkflowState.LABEL_PRINTED: [WorkflowState.AWAITING_SCAN],
        WorkflowState.AWAITING_SCAN: [WorkflowState.VERIFIED, WorkflowState.LABEL_PRINTED],  # Can reprint
        WorkflowState.VERIFIED: [WorkflowState.IDLE, WorkflowState.PRODUCT_SELECTED],  # Start next
    }

    def __init__(self):
        self.state = WorkflowState.IDLE
        self._lock = threading.Lock()
        self._state_callbacks: list[Callable[[WorkflowState], None]] = []

    def can_transition(self, to_state: WorkflowState) -> bool:
        """Check if transition is valid."""
        valid_targets = self.VALID_TRANSITIONS.get(self.state, [])
        return to_state in valid_targets

    def transition(self, to_state: WorkflowState) -> bool:
        """Attempt state transition. Returns True if successful."""
        with self._lock:
            if not self.can_transition(to_state):
                return False
            self.state = to_state
            for callback in self._state_callbacks:
                try:
                    callback(to_state)
                except:
                    pass
            return True

    def reset(self):
        """Reset to idle state."""
        with self._lock:
            self.state = WorkflowState.IDLE

    def on_state_change(self, callback: Callable[[WorkflowState], None]):
        """Register state change callback."""
        self._state_callbacks.append(callback)

    @property
    def can_select_product(self) -> bool:
        return self.state in [WorkflowState.IDLE, WorkflowState.VERIFIED, WorkflowState.PRODUCT_SELECTED]

    @property
    def can_print(self) -> bool:
        return self.state == WorkflowState.WEIGHT_CAPTURED

    @property
    def awaiting_scan(self) -> bool:
        return self.state == WorkflowState.AWAITING_SCAN


class WeightValidator:
    """
    Validates weight readings for reliability.
    """

    MIN_WEIGHT = 0.05  # Minimum valid weight (lbs)
    MAX_WEIGHT = 100.0  # Maximum valid weight (lbs)
    STABILITY_READINGS = 3  # Number of stable readings required
    STABILITY_TOLERANCE = 0.02  # Max variance for stability (lbs)

    def __init__(self):
        self._readings: list[float] = []
        self._stable_weight: Optional[float] = None

    def add_reading(self, weight: float) -> ValidationResult:
        """Add a weight reading and check validity."""
        # Range check
        if weight < 0:
            return ValidationResult(False, "Negative weight invalid", False)

        if weight > self.MAX_WEIGHT:
            return ValidationResult(False, f"Weight exceeds {self.MAX_WEIGHT} lb limit", False)

        # Track for stability
        self._readings.append(weight)
        if len(self._readings) > self.STABILITY_READINGS:
            self._readings.pop(0)

        return ValidationResult(True, "", False)

    def is_stable(self) -> bool:
        """Check if weight is stable (consistent readings)."""
        if len(self._readings) < self.STABILITY_READINGS:
            return False

        avg = sum(self._readings) / len(self._readings)
        variance = max(abs(r - avg) for r in self._readings)
        return variance <= self.STABILITY_TOLERANCE

    def get_stable_weight(self) -> Optional[float]:
        """Get stable weight if available."""
        if self.is_stable() and self._readings:
            weight = sum(self._readings) / len(self._readings)
            if weight >= self.MIN_WEIGHT:
                return round(weight, 2)
        return None

    def reset(self):
        """Reset readings."""
        self._readings.clear()
        self._stable_weight = None


class BarcodeValidator:
    """
    Validates barcode scans with timing and format checks.
    """

    MIN_SCAN_INTERVAL = 0.5  # Minimum seconds between scans (debounce)
    SCAN_TIMEOUT = 30.0  # Seconds to wait for scan after print

    def __init__(self):
        self._last_scan_time = 0.0
        self._expected_barcode: Optional[str] = None
        self._scan_deadline: Optional[float] = None

    def expect_barcode(self, barcode: str, timeout: float = None):
        """Set expected barcode for verification."""
        self._expected_barcode = barcode
        self._scan_deadline = time.time() + (timeout or self.SCAN_TIMEOUT)

    def validate_scan(self, scanned: str) -> ValidationResult:
        """Validate a barcode scan."""
        now = time.time()

        # Debounce rapid scans
        if now - self._last_scan_time < self.MIN_SCAN_INTERVAL:
            return ValidationResult(False, "Scan too fast, try again", True)

        self._last_scan_time = now

        # Check timeout
        if self._scan_deadline and now > self._scan_deadline:
            return ValidationResult(False, "Scan timeout - reprint label", True)

        # Check match
        if self._expected_barcode:
            if scanned == self._expected_barcode:
                return ValidationResult(True, "Barcode verified", False)
            else:
                return ValidationResult(False, "Wrong barcode scanned", True)

        return ValidationResult(True, "", False)

    def clear_expectation(self):
        """Clear expected barcode."""
        self._expected_barcode = None
        self._scan_deadline = None

    @property
    def is_expecting(self) -> bool:
        return self._expected_barcode is not None

    @property
    def time_remaining(self) -> Optional[float]:
        if self._scan_deadline:
            remaining = self._scan_deadline - time.time()
            return max(0, remaining)
        return None


class HardwareMonitor:
    """
    Monitors hardware connections and attempts recovery.
    """

    CHECK_INTERVAL = 5.0  # Seconds between checks
    RECONNECT_ATTEMPTS = 3
    RECONNECT_DELAY = 2.0

    def __init__(self, scale=None, printer=None):
        self.scale = scale
        self.printer = printer
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._on_disconnect: Optional[Callable[[str], None]] = None
        self._on_reconnect: Optional[Callable[[str], None]] = None

    def start(self):
        """Start monitoring."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)

    def on_disconnect(self, callback: Callable[[str], None]):
        """Set disconnect callback. Receives device name."""
        self._on_disconnect = callback

    def on_reconnect(self, callback: Callable[[str], None]):
        """Set reconnect callback. Receives device name."""
        self._on_reconnect = callback

    def _monitor_loop(self):
        """Background monitoring loop."""
        while self._running:
            # Check scale
            if self.scale and hasattr(self.scale, 'is_connected'):
                if not self.scale.is_connected():
                    self._notify_disconnect('scale')
                    self._attempt_reconnect('scale', self.scale)

            # Check printer
            if self.printer and hasattr(self.printer, 'is_connected'):
                if not self.printer.is_connected():
                    self._notify_disconnect('printer')
                    self._attempt_reconnect('printer', self.printer)

            time.sleep(self.CHECK_INTERVAL)

    def _notify_disconnect(self, device: str):
        if self._on_disconnect:
            try:
                self._on_disconnect(device)
            except:
                pass

    def _attempt_reconnect(self, device: str, hardware):
        """Attempt to reconnect hardware."""
        for attempt in range(self.RECONNECT_ATTEMPTS):
            try:
                if hasattr(hardware, 'connect'):
                    hardware.connect()
                    if hardware.is_connected():
                        if self._on_reconnect:
                            self._on_reconnect(device)
                        return True
            except:
                pass
            time.sleep(self.RECONNECT_DELAY)
        return False


class OperationLock:
    """
    Prevents concurrent operations that could cause issues.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._operation: Optional[str] = None

    def acquire(self, operation: str) -> bool:
        """Try to acquire lock for operation. Returns True if acquired."""
        with self._lock:
            if self._operation is None:
                self._operation = operation
                return True
            return False

    def release(self):
        """Release the lock."""
        with self._lock:
            self._operation = None

    @property
    def current_operation(self) -> Optional[str]:
        return self._operation

    def __enter__(self):
        if not self.acquire("context_manager"):
            raise RuntimeError(f"Cannot acquire lock: {self._operation} in progress")
        return self

    def __exit__(self, *args):
        self.release()


def validate_sku(sku: str) -> ValidationResult:
    """Validate SKU format."""
    if not sku:
        return ValidationResult(False, "SKU required", False)

    clean = sku.strip()
    if not clean.isdigit():
        return ValidationResult(False, "SKU must be numeric", False)

    if len(clean) > 5:
        return ValidationResult(False, "SKU too long (max 5 digits)", False)

    return ValidationResult(True, "", False)


def validate_weight(weight: float) -> ValidationResult:
    """Validate weight value."""
    if weight <= 0:
        return ValidationResult(False, "Weight must be positive", False)

    if weight < WeightValidator.MIN_WEIGHT:
        return ValidationResult(False, f"Weight too small (min {WeightValidator.MIN_WEIGHT} lb)", False)

    if weight > WeightValidator.MAX_WEIGHT:
        return ValidationResult(False, f"Weight too large (max {WeightValidator.MAX_WEIGHT} lb)", False)

    return ValidationResult(True, "", False)


def validate_customer_name(name: str) -> ValidationResult:
    """Validate customer name."""
    if not name or not name.strip():
        return ValidationResult(False, "Customer name required", False)

    clean = name.strip()
    if len(clean) < 2:
        return ValidationResult(False, "Name too short", False)

    if len(clean) > 100:
        return ValidationResult(False, "Name too long", False)

    return ValidationResult(True, "", False)
