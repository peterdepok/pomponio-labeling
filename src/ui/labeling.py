"""Primary labeling workflow screen.

Implements the state machine UI:
    IDLE -> PRODUCT_SELECTED -> WEIGHT_CAPTURED -> LABEL_PRINTED -> AWAITING_SCAN -> VERIFIED

Shows current product, live weight, action buttons, and scan verification.
"""

import logging
from typing import Callable, Optional

import customtkinter as ctk

from src.barcode import generate_barcode
from src.safety import Workflow, WorkflowState, WorkflowError
from src.scanner import Scanner, ScanResult
from src.ui import theme
from src.ui.widgets import (
    TouchButton,
    WeightDisplay,
    StatusIndicator,
    InfoBar,
)

logger = logging.getLogger(__name__)


class LabelingScreen(ctk.CTkFrame):
    """Primary workflow screen for package labeling."""

    def __init__(
        self,
        master,
        workflow: Workflow,
        scanner: Scanner,
        on_print_request: Optional[Callable[[str, str, float, str], None]] = None,
        on_package_complete: Optional[Callable[[dict], None]] = None,
        **kwargs,
    ):
        """
        Args:
            master: Parent widget.
            workflow: Shared workflow state machine.
            scanner: Shared scanner instance.
            on_print_request: Callback(product_name, sku, weight, barcode) to trigger print.
            on_package_complete: Callback(package_data) when a package is verified.
        """
        super().__init__(master, fg_color=theme.BG_PRIMARY, **kwargs)

        self._workflow = workflow
        self._scanner = scanner
        self._on_print_request = on_print_request
        self._on_package_complete = on_package_complete

        self._build_ui()
        self._update_for_state()

        # Scanner callback
        self._scanner.set_callback(self._on_scan)

        # Hidden entry for keyboard wedge capture
        self._scan_entry = ctk.CTkEntry(self, width=0, height=0, fg_color="transparent", border_width=0)
        self._scan_entry.place(x=-100, y=-100)
        self._scan_entry.bind("<Return>", self._on_scan_entry)
        self._scan_entry.bind("<KP_Enter>", self._on_scan_entry)

    def _build_ui(self) -> None:
        """Build the labeling screen layout."""
        # Workflow status indicator
        self._status_bar = StatusIndicator(self)
        self._status_bar.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=(theme.PADDING_MEDIUM, 0))

        # Product info section
        self._product_frame = ctk.CTkFrame(self, fg_color=theme.BG_SECONDARY)
        self._product_frame.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_MEDIUM)

        self._product_name_label = ctk.CTkLabel(
            self._product_frame,
            text="Select a product",
            font=theme.FONT_HEADING,
            text_color=theme.TEXT_PRIMARY,
        )
        self._product_name_label.pack(pady=(theme.PADDING_MEDIUM, 0))

        self._sku_label = ctk.CTkLabel(
            self._product_frame,
            text="",
            font=theme.FONT_MONO,
            text_color=theme.TEXT_SECONDARY,
        )
        self._sku_label.pack(pady=(0, theme.PADDING_MEDIUM))

        # Weight display
        self._weight_display = WeightDisplay(self)
        self._weight_display.pack(
            fill="x", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_SMALL
        )

        # Barcode display (shows after printing)
        self._barcode_label = ctk.CTkLabel(
            self,
            text="",
            font=theme.FONT_MONO,
            text_color=theme.TEXT_ACCENT,
        )
        self._barcode_label.pack(pady=theme.PADDING_SMALL)

        # Scan result display
        self._scan_result_label = ctk.CTkLabel(
            self,
            text="",
            font=theme.FONT_HEADING,
            text_color=theme.TEXT_PRIMARY,
        )
        self._scan_result_label.pack(pady=theme.PADDING_SMALL)

        # Action buttons
        self._btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._btn_frame.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_MEDIUM)

        self._print_btn = TouchButton(
            self._btn_frame,
            text="Print Label",
            style="success",
            height=theme.TOUCH_TARGET_LARGE,
            font=theme.FONT_HEADING,
            command=self._do_print,
        )
        self._print_btn.pack(fill="x", pady=theme.PADDING_SMALL)

        self._reweigh_btn = TouchButton(
            self._btn_frame,
            text="Re-weigh",
            style="primary",
            command=self._do_reweigh,
        )
        self._reweigh_btn.pack(fill="x", pady=theme.PADDING_SMALL)

        self._cancel_btn = TouchButton(
            self._btn_frame,
            text="Cancel",
            style="danger",
            command=self._do_cancel,
        )
        self._cancel_btn.pack(fill="x", pady=theme.PADDING_SMALL)

    def set_product(self, product: dict) -> None:
        """Called when a product is selected from the grid."""
        try:
            self._workflow.select_product(
                product["id"], product["name"], product["sku"]
            )
        except WorkflowError as e:
            logger.warning("Cannot select product: %s", e)
            return

        self._product_name_label.configure(text=product["name"])
        self._sku_label.configure(text=f"SKU: {product['sku']}")
        self._weight_display.reset()
        self._barcode_label.configure(text="")
        self._scan_result_label.configure(text="")
        self._update_for_state()

    def update_weight(self, weight: float, stable: bool) -> None:
        """Called on each scale reading to update the display."""
        if self._workflow.state == WorkflowState.PRODUCT_SELECTED:
            self._weight_display.set_weight(weight, stable)

    def lock_weight(self, weight: float) -> None:
        """Called when the scale locks a stable weight."""
        if self._workflow.state != WorkflowState.PRODUCT_SELECTED:
            return

        try:
            self._workflow.capture_weight(weight)
        except WorkflowError as e:
            logger.warning("Cannot capture weight: %s", e)
            return

        self._weight_display.set_locked(weight)
        self._update_for_state()

    def _do_print(self) -> None:
        """Handle Print Label button."""
        ctx = self._workflow.context
        if ctx.sku is None or ctx.weight_lb is None:
            return

        try:
            barcode = generate_barcode(ctx.sku, ctx.weight_lb)
        except Exception as e:
            logger.error("Barcode generation failed: %s", e)
            self._scan_result_label.configure(
                text=f"Barcode error: {e}", text_color=theme.TEXT_WARNING
            )
            return

        try:
            self._workflow.print_label(barcode)
        except WorkflowError as e:
            logger.warning("Cannot print: %s", e)
            return

        self._barcode_label.configure(text=f"Barcode: {barcode}")

        # Trigger actual printing
        if self._on_print_request:
            self._on_print_request(ctx.product_name, ctx.sku, ctx.weight_lb, barcode)

        # Move to awaiting scan
        try:
            self._workflow.await_scan()
        except WorkflowError:
            pass

        self._scanner.set_expected(barcode)
        self._scan_result_label.configure(
            text="Scan the label now", text_color=theme.TEXT_ACCENT
        )
        self._update_for_state()

        # Focus the hidden scan entry
        self._scan_entry.focus_set()

    def _do_reweigh(self) -> None:
        """Handle Re-weigh button."""
        try:
            self._workflow.reweigh()
        except WorkflowError as e:
            logger.warning("Cannot re-weigh: %s", e)
            return

        self._weight_display.reset()
        self._barcode_label.configure(text="")
        self._scan_result_label.configure(text="")
        self._update_for_state()

    def _do_cancel(self) -> None:
        """Handle Cancel button."""
        self._workflow.cancel()
        self._scanner.clear_expected()
        self._product_name_label.configure(text="Select a product")
        self._sku_label.configure(text="")
        self._weight_display.reset()
        self._barcode_label.configure(text="")
        self._scan_result_label.configure(text="")
        self._update_for_state()

    def _on_scan_entry(self, event=None) -> None:
        """Handle Enter key in the hidden scan entry (keyboard wedge)."""
        raw = self._scan_entry.get()
        self._scan_entry.delete(0, "end")
        if raw:
            self._scanner.process_raw_input(raw)

    def _on_scan(self, result: ScanResult) -> None:
        """Handle scan result from scanner."""
        if self._workflow.state != WorkflowState.AWAITING_SCAN:
            return

        if result.matched:
            self._scan_result_label.configure(
                text="VERIFIED", text_color=theme.TEXT_SUCCESS
            )
            try:
                self._workflow.verify(0)  # package_id set by caller
            except WorkflowError:
                pass

            if self._on_package_complete:
                ctx = self._workflow.context
                self._on_package_complete({
                    "product_id": ctx.product_id,
                    "product_name": ctx.product_name,
                    "sku": ctx.sku,
                    "weight_lb": ctx.weight_lb,
                    "barcode": ctx.barcode,
                })

            # Auto-return to idle after brief delay
            self.after(1500, self._finish_cycle)
        else:
            self._scan_result_label.configure(
                text=f"MISMATCH\nScanned: {result.scanned}\nExpected: {result.expected}",
                text_color=theme.TEXT_WARNING,
            )
            logger.warning(
                "Scan mismatch: scanned=%s expected=%s",
                result.scanned, result.expected,
            )

    def _finish_cycle(self) -> None:
        """Complete the workflow cycle and return to idle."""
        try:
            self._workflow.complete()
        except WorkflowError:
            self._workflow.cancel()

        self._scanner.clear_expected()
        self._product_name_label.configure(text="Select a product")
        self._sku_label.configure(text="")
        self._weight_display.reset()
        self._barcode_label.configure(text="")
        self._scan_result_label.configure(text="")
        self._update_for_state()

    def _update_for_state(self) -> None:
        """Update button visibility and status indicator based on workflow state."""
        state = self._workflow.state
        self._status_bar.set_state(state.value)

        # Button visibility
        show_print = state == WorkflowState.WEIGHT_CAPTURED
        show_reweigh = state == WorkflowState.WEIGHT_CAPTURED
        show_cancel = state != WorkflowState.IDLE

        self._print_btn.pack_forget()
        self._reweigh_btn.pack_forget()
        self._cancel_btn.pack_forget()

        if show_print:
            self._print_btn.pack(fill="x", pady=theme.PADDING_SMALL)
        if show_reweigh:
            self._reweigh_btn.pack(fill="x", pady=theme.PADDING_SMALL)
        if show_cancel:
            self._cancel_btn.pack(fill="x", pady=theme.PADDING_SMALL)
