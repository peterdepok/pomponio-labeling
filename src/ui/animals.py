"""Animal tracking and manifest generation screen.

Manages animal lifecycle: start animal, view packages, close animal
with manifest spreadsheet generation.
"""

import logging
from datetime import datetime
from typing import Callable, Optional

import customtkinter as ctk

from src.database import Database
from src.ui import theme
from src.ui.widgets import TouchButton, ConfirmDialog

logger = logging.getLogger(__name__)


class AnimalScreen(ctk.CTkFrame):
    """Animal tracking and manifest interface."""

    def __init__(
        self,
        master,
        db: Database,
        on_animal_changed: Optional[Callable[[Optional[int]], None]] = None,
        on_generate_manifest: Optional[Callable[[int], Optional[str]], None] = None,
        **kwargs,
    ):
        """
        Args:
            master: Parent widget.
            db: Database instance.
            on_animal_changed: Callback(animal_id) when active animal changes.
            on_generate_manifest: Callback(animal_id) to generate manifest, returns path.
        """
        super().__init__(master, fg_color=theme.BG_PRIMARY, **kwargs)

        self._db = db
        self._on_animal_changed = on_animal_changed
        self._on_generate_manifest = on_generate_manifest

        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        # Header with new animal button
        header = ctk.CTkFrame(self, fg_color=theme.BG_SECONDARY)
        header.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_MEDIUM)

        ctk.CTkLabel(
            header, text="Animal Tracking", font=theme.FONT_HEADING,
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_MEDIUM)

        self._new_btn = TouchButton(
            header, text="Start Animal", style="success",
            command=self._start_animal_dialog, width=180,
        )
        self._new_btn.pack(side="right", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_SMALL)

        # Animal list
        self._list_frame = ctk.CTkScrollableFrame(
            self, fg_color=theme.BG_PRIMARY,
        )
        self._list_frame.pack(fill="both", expand=True, padx=theme.PADDING_MEDIUM)

    def refresh(self) -> None:
        """Reload animal list from database."""
        for widget in self._list_frame.winfo_children():
            widget.destroy()

        animals = self._db.get_open_animals()
        if not animals:
            ctk.CTkLabel(
                self._list_frame,
                text="No active animals. Tap 'Start Animal' to begin.",
                font=theme.FONT_BODY,
                text_color=theme.TEXT_SECONDARY,
            ).pack(pady=theme.PADDING_LARGE)
            return

        for animal in animals:
            self._add_animal_card(animal)

    def _add_animal_card(self, animal: dict) -> None:
        """Add an animal card to the list."""
        card = ctk.CTkFrame(self._list_frame, fg_color=theme.BG_SECONDARY)
        card.pack(fill="x", pady=theme.PADDING_SMALL)

        # Animal header
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=(theme.PADDING_SMALL, 0))

        ctk.CTkLabel(
            header_frame,
            text=animal["name"],
            font=theme.FONT_HEADING,
            text_color=theme.TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame,
            text=f"Started: {animal['started_at']}",
            font=theme.FONT_SMALL,
            text_color=theme.TEXT_SECONDARY,
        ).pack(side="right")

        # Package summary
        packages = self._db.get_packages_for_animal(animal["id"])
        manifest_data = self._db.get_animal_manifest_data(animal["id"])
        total_weight = sum(p["weight_lb"] for p in packages)

        stats_frame = ctk.CTkFrame(card, fg_color="transparent")
        stats_frame.pack(fill="x", padx=theme.PADDING_LARGE, pady=theme.PADDING_SMALL)

        ctk.CTkLabel(
            stats_frame,
            text=f"{len(packages)} packages | {len(manifest_data)} SKUs | {total_weight:.1f} lb total",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY,
        ).pack(anchor="w")

        # SKU breakdown (condensed)
        if manifest_data:
            details_frame = ctk.CTkFrame(card, fg_color="transparent")
            details_frame.pack(fill="x", padx=theme.PADDING_LARGE, pady=(0, theme.PADDING_SMALL))

            for item in manifest_data[:8]:  # show first 8 SKUs
                ctk.CTkLabel(
                    details_frame,
                    text=f"  {item['quantity']}x {item['product_name']} ({item['total_weight']:.1f} lb)",
                    font=theme.FONT_SMALL,
                    text_color=theme.TEXT_SECONDARY,
                    anchor="w",
                ).pack(fill="x")

            if len(manifest_data) > 8:
                ctk.CTkLabel(
                    details_frame,
                    text=f"  ... and {len(manifest_data) - 8} more SKUs",
                    font=theme.FONT_SMALL,
                    text_color=theme.TEXT_SECONDARY,
                ).pack(fill="x")

        # Action buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=theme.PADDING_MEDIUM, pady=theme.PADDING_SMALL)

        TouchButton(
            btn_frame,
            text="Use This Animal",
            style="primary",
            command=lambda aid=animal["id"]: self._select_animal(aid),
            width=180,
        ).pack(side="left", padx=theme.PADDING_SMALL)

        TouchButton(
            btn_frame,
            text="Close and Generate Manifest",
            style="danger",
            command=lambda aid=animal["id"], name=animal["name"]: self._confirm_close(aid, name),
            width=280,
        ).pack(side="right", padx=theme.PADDING_SMALL)

    def _start_animal_dialog(self) -> None:
        """Open dialog to name and start a new animal."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Start New Animal")
        dialog.geometry("500x300")
        dialog.configure(fg_color=theme.BG_PRIMARY)
        dialog.resizable(False, False)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Animal Name", font=theme.FONT_HEADING,
            text_color=theme.TEXT_PRIMARY,
        ).pack(pady=(theme.PADDING_LARGE, theme.PADDING_SMALL))

        # Default name suggestion
        today = datetime.now().strftime("%m/%d/%Y")
        open_animals = self._db.get_open_animals()
        next_num = len(open_animals) + 1
        default_name = f"Beef #{next_num} - {today}"

        name_entry = ctk.CTkEntry(
            dialog, width=400, height=60, font=theme.FONT_BODY_LARGE,
            fg_color=theme.BG_INPUT, text_color=theme.TEXT_PRIMARY,
        )
        name_entry.pack(pady=theme.PADDING_MEDIUM)
        name_entry.insert(0, default_name)
        name_entry.select_range(0, "end")
        name_entry.focus_set()

        species_var = ctk.StringVar(value="Beef")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=theme.PADDING_LARGE, pady=theme.PADDING_MEDIUM)

        TouchButton(
            btn_frame, text="Cancel", style="secondary",
            command=dialog.destroy, width=180,
        ).pack(side="left")

        def do_create():
            name = name_entry.get().strip()
            if not name:
                return
            aid = self._db.create_animal(name, species_var.get())
            logger.info("Started animal: %s (id=%d)", name, aid)
            dialog.destroy()
            self._select_animal(aid)
            self.refresh()

        TouchButton(
            btn_frame, text="Start", style="success",
            command=do_create, width=180,
        ).pack(side="right")

    def _select_animal(self, animal_id: int) -> None:
        """Set the active animal for labeling."""
        if self._on_animal_changed:
            self._on_animal_changed(animal_id)
        logger.info("Active animal set to %d", animal_id)

    def _confirm_close(self, animal_id: int, name: str) -> None:
        """Confirm before closing an animal."""
        packages = self._db.get_packages_for_animal(animal_id)
        msg = f"Close '{name}'?\n{len(packages)} packages will be finalized."

        ConfirmDialog(
            self,
            title="Close Animal",
            message=msg,
            confirm_text="Close and Generate Manifest",
            on_confirm=lambda: self._close_animal(animal_id),
        )

    def _close_animal(self, animal_id: int) -> None:
        """Close the animal and generate manifest."""
        manifest_path = None
        if self._on_generate_manifest:
            manifest_path = self._on_generate_manifest(animal_id)

        self._db.close_animal(animal_id, manifest_path=manifest_path)
        logger.info("Closed animal %d, manifest: %s", animal_id, manifest_path)

        if self._on_animal_changed:
            self._on_animal_changed(None)

        self.refresh()
