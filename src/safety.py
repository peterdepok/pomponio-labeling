"""Workflow state machine for the labeling process.

States:
    IDLE -> PRODUCT_SELECTED -> WEIGHT_CAPTURED -> LABEL_PRINTED -> AWAITING_SCAN -> VERIFIED

Enforces step sequence. Prevents skipping steps. Provides reset/cancel at any state.
"""

import logging
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class WorkflowState(Enum):
    IDLE = "idle"
    PRODUCT_SELECTED = "product_selected"
    WEIGHT_CAPTURED = "weight_captured"
    LABEL_PRINTED = "label_printed"
    AWAITING_SCAN = "awaiting_scan"
    VERIFIED = "verified"


# Valid transitions: current state -> set of allowed next states
TRANSITIONS: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.IDLE: {WorkflowState.PRODUCT_SELECTED},
    WorkflowState.PRODUCT_SELECTED: {WorkflowState.WEIGHT_CAPTURED},
    WorkflowState.WEIGHT_CAPTURED: {WorkflowState.LABEL_PRINTED},
    WorkflowState.LABEL_PRINTED: {WorkflowState.AWAITING_SCAN},
    WorkflowState.AWAITING_SCAN: {WorkflowState.VERIFIED},
    WorkflowState.VERIFIED: {WorkflowState.IDLE},
}


class WorkflowError(Exception):
    """Raised when an invalid state transition is attempted."""


class WorkflowContext:
    """Data accumulated through the workflow."""

    def __init__(self):
        self.product_id: Optional[int] = None
        self.product_name: Optional[str] = None
        self.sku: Optional[str] = None
        self.weight_lb: Optional[float] = None
        self.barcode: Optional[str] = None
        self.animal_id: Optional[int] = None
        self.box_id: Optional[int] = None
        self.package_id: Optional[int] = None

    def clear(self) -> None:
        """Reset all context data."""
        self.product_id = None
        self.product_name = None
        self.sku = None
        self.weight_lb = None
        self.barcode = None
        self.package_id = None
        # animal_id and box_id persist across packages


class Workflow:
    """State machine enforcing the labeling workflow sequence."""

    def __init__(self):
        self._state = WorkflowState.IDLE
        self.context = WorkflowContext()
        self._on_state_change: Optional[Callable[[WorkflowState, WorkflowState], None]] = None

    @property
    def state(self) -> WorkflowState:
        return self._state

    def set_callback(self, callback: Callable[[WorkflowState, WorkflowState], None]) -> None:
        """Set callback for state changes. Called with (old_state, new_state)."""
        self._on_state_change = callback

    def transition(self, new_state: WorkflowState) -> None:
        """Attempt a state transition.

        Args:
            new_state: Target state.

        Raises:
            WorkflowError: If transition is not valid from current state.
        """
        allowed = TRANSITIONS.get(self._state, set())
        if new_state not in allowed:
            raise WorkflowError(
                f"Cannot transition from {self._state.value} to {new_state.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )
        old_state = self._state
        self._state = new_state
        logger.info("Workflow: %s -> %s", old_state.value, new_state.value)
        if self._on_state_change:
            self._on_state_change(old_state, new_state)

    def select_product(self, product_id: int, name: str, sku: str) -> None:
        """Transition to PRODUCT_SELECTED."""
        self.transition(WorkflowState.PRODUCT_SELECTED)
        self.context.product_id = product_id
        self.context.product_name = name
        self.context.sku = sku

    def capture_weight(self, weight_lb: float) -> None:
        """Transition to WEIGHT_CAPTURED."""
        if weight_lb <= 0:
            raise WorkflowError("Weight must be positive")
        self.transition(WorkflowState.WEIGHT_CAPTURED)
        self.context.weight_lb = weight_lb

    def print_label(self, barcode: str) -> None:
        """Transition to LABEL_PRINTED."""
        self.transition(WorkflowState.LABEL_PRINTED)
        self.context.barcode = barcode

    def await_scan(self) -> None:
        """Transition to AWAITING_SCAN."""
        self.transition(WorkflowState.AWAITING_SCAN)

    def verify(self, package_id: int) -> None:
        """Transition to VERIFIED."""
        self.transition(WorkflowState.VERIFIED)
        self.context.package_id = package_id

    def complete(self) -> None:
        """Return to IDLE after verification, clearing per-package context."""
        self.transition(WorkflowState.IDLE)
        self.context.clear()

    def cancel(self) -> None:
        """Cancel current operation and return to IDLE from any state."""
        old = self._state
        self._state = WorkflowState.IDLE
        self.context.clear()
        logger.info("Workflow cancelled from %s", old.value)
        if self._on_state_change:
            self._on_state_change(old, WorkflowState.IDLE)

    def reweigh(self) -> None:
        """Go back to PRODUCT_SELECTED to re-weigh. Only valid from WEIGHT_CAPTURED."""
        if self._state != WorkflowState.WEIGHT_CAPTURED:
            raise WorkflowError(
                f"Re-weigh only valid from weight_captured, currently: {self._state.value}"
            )
        old = self._state
        self._state = WorkflowState.PRODUCT_SELECTED
        self.context.weight_lb = None
        logger.info("Re-weigh: returning to product_selected")
        if self._on_state_change:
            self._on_state_change(old, WorkflowState.PRODUCT_SELECTED)
