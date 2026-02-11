"""Box management screen.

Displays open boxes, package counts per box, and allows closing boxes
with box label printing.
"""

import logging
from typing import Callable, Optional

import customtkinter as ctk

from src.database import Database
from src.ui import theme
from src.ui.widgets import TouchButton, ConfirmDialog

logger = logging.getLogger(__name__)


class BoxScreen(ctk.CTkFrame):
    """Box management interface."""

    def __init__(
        self,
        master,
        db: Database,
        current_animal_id: Optional[int] = None,
        on_close_box: Optional[Callable[[int, list[dict]], None]] = None,
        **kwargs,
    ):
        """
        Args:
            master: Parent widget.
            db: Database instance.
            current_animal_id: Active animal ID for box creation.
            on_close_box: Callback(box_id, summary) when a box is closed.
        """
        super().__init__(master, fg_color=theme.BG_PRIMARY, **kwargs)

        self._db = db
        self._animal_id = current_animal_id
        self._on_close_box = on_close_box

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        # Header
        header = ctk.CTkFrame(self, fg_color=theme.BG_SECONDARY)
        header.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_MEDIUM)

        ctk.CTkLabel(
            header, text="Box Management", font=theme.FONT_HEADING,
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_MEDIUM)

        self._new_box_btn = TouchButton(
            header, text="New Box", style="success",
            command=self._create_box, width=160,
        )
        self._new_box_btn.pack(side="right", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_SMALL)

        # Box list
        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color=theme.BG_PRIMARY,
        )
        self._list_frame.pack(fill="both", expand=True, padx=theme.PADDING_MEDIUM)

    def set_animal_id(self, animal_id: Optional[int]) -> None:
        """Update the current animal context."""
        self._animal_id = animal_id
        self.refresh()

    def refresh(self) -> None:
        """Reload box list from database."""
        for widget in self._list_frame.winfo_children():
            widget.destroy()

        if self._animal_id is None:
            ctk.CTkLabel(
                self._list_frame,
                text="Start an animal first to manage boxes.",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_SECONDARY,
            ).pack(pady=theme.PADDING_LARGE)
            return

        boxes = self._db.get_open_boxes(self._animal_id)
        if not boxes:
            ctk.CTkLabel(
                self._list_frame,
                text="No open boxes. Tap 'New Box' to start one.",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_SECONDARY,
            ).pack(pady=theme.PADDING_LARGE)
            return

        for box in boxes:
            self._add_box_card(box)

    def _add_box_card(self, box: dict) -> None:
        """Add a box card to the list."""
        card = ctk.CTkFrame(self._list_frame, fg_color=theme.BG_SECONDARY)
        card.pack(fill="x", pady=theme.PADDING_SMALL)

        # Box header
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=(theme.PADDING_SMALL, 0))

        ctk.CTkLabel(
            header_frame,
            text=f"Box {box['box_number']}",
            font=theme.FONT_HEADING,
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")

        # Package summary
        summary = self._db.get_box_summary(box["id"])
        total_packages = sum(s["quantity"] for s in summary)
        total_weight = sum(s["total_weight"] for s in summary)

        ctk.CTkLabel(
            header_frame,
            text=f"{total_packages} packages | {total_weight:.1f} lb",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY,
        ).pack(side="right")

        # SKU breakdown
        if summary:
            details_frame = ctk.CTkFrame(card, fg_color="transparent")
            details_frame.pack(fill="x", padx=theme.PADDING_LARGE, pady=theme.PADDING_SMALL)

            for item in summary:
                ctk.CTkLabel(
                    details_frame,
                    text=f"  {item['quantity']}x {item['product_name']} ({item['total_weight']:.1f} lb)",
                    font=theme.FONT_SMALL,
                    text_color=theme.TEXT_SECONDARY,
                    anchor="w",
                ).pack(fill="x")

        # Close box button
        TouchButton(
            card,
            text="Close Box",
            style="danger",
            command=lambda bid=box["id"]: self._confirm_close(bid),
            width=160,
        ).pack(pady=theme.PADDING_SMALL)

    def _create_box(self) -> None:
        """Create a new box for the current animal."""
        if self._animal_id is None:
            return
        box_id = self._db.create_box(self._animal_id)
        logger.info("Created box %d for animal %d", box_id, self._animal_id)
        self.refresh()

    def _confirm_close(self, box_id: int) -> None:
        """Show confirmation dialog before closing a box."""
        summary = self._db.get_box_summary(box_id)
        total = sum(s["quantity"] for s in summary)
        box = self._db.get_box(box_id)
        msg = f"Close Box {box['box_number']}?\n{total} packages inside."

        ConfirmDialog(
            self,
            title="Close Box",
            message=msg,
            confirm_text="Close and Print Labels",
            on_confirm=lambda: self._close_box(box_id),
        )

    def _close_box(self, box_id: int) -> None:
        """Close the box and trigger label printing."""
        summary = self._db.get_box_summary(box_id)
        self._db.close_box(box_id)
        logger.info("Closed box %d", box_id)

        if self._on_close_box:
            self._on_close_box(box_id, summary)

        self.refresh()
