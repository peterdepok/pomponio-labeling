"""Reusable touch-optimized UI components for the labeling system.

All interactive elements meet the 80px minimum touch target requirement.
Designed for gloved hands on a capacitive touchscreen.
"""

import customtkinter as ctk
from typing import Callable, Optional

from src.ui import theme


class TouchButton(ctk.CTkButton):
    """Large touch-friendly button meeting 80px minimum height."""

    def __init__(
        self,
        master,
        text: str = "",
        command: Optional[Callable] = None,
        style: str = "primary",
        height: int = theme.TOUCH_TARGET_MIN,
        font: Optional[tuple] = None,
        **kwargs,
    ):
        style_map = {
            "primary": (theme.BTN_PRIMARY_BG, theme.BTN_PRIMARY_HOVER, theme.BTN_PRIMARY_TEXT),
            "success": (theme.BTN_SUCCESS_BG, theme.BTN_SUCCESS_HOVER, theme.BTN_SUCCESS_TEXT),
            "danger": (theme.BTN_DANGER_BG, theme.BTN_DANGER_HOVER, theme.BTN_DANGER_TEXT),
            "secondary": (theme.BTN_SECONDARY_BG, theme.BTN_SECONDARY_HOVER, theme.BTN_SECONDARY_TEXT),
        }
        bg, hover, text_color = style_map.get(style, style_map["primary"])

        super().__init__(
            master,
            text=text,
            command=command,
            height=height,
            font=font or theme.FONT_BODY_LARGE,
            fg_color=bg,
            hover_color=hover,
            text_color=text_color,
            corner_radius=theme.BUTTON_CORNER_RADIUS,
            **kwargs,
        )


class ProductButton(ctk.CTkButton):
    """Product selection button for the grid. Shows name and SKU."""

    def __init__(
        self,
        master,
        product_name: str,
        sku: str,
        category_color: dict,
        command: Optional[Callable] = None,
        **kwargs,
    ):
        self._product_name = product_name
        self._sku = sku

        # Truncate long names for display
        display_name = product_name if len(product_name) <= 28 else product_name[:26] + ".."

        super().__init__(
            master,
            text=f"{display_name}\n{sku}",
            command=command,
            height=theme.PRODUCT_BUTTON_HEIGHT,
            font=theme.FONT_BODY,
            fg_color=category_color.get("bg", theme.BTN_PRIMARY_BG),
            hover_color=category_color.get("hover", theme.BTN_PRIMARY_HOVER),
            text_color=theme.TEXT_PRIMARY,
            corner_radius=theme.BUTTON_CORNER_RADIUS,
            anchor="w",
            **kwargs,
        )


class WeightDisplay(ctk.CTkFrame):
    """Large weight readout display with stability indicator."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG_SECONDARY, **kwargs)

        self._weight_label = ctk.CTkLabel(
            self,
            text="0.000",
            font=theme.FONT_WEIGHT_DISPLAY,
            text_color=theme.TEXT_PRIMARY,
        )
        self._weight_label.pack(pady=(theme.PADDING_MEDIUM, 0))

        self._unit_label = ctk.CTkLabel(
            self,
            text="lb",
            font=theme.FONT_HEADING,
            text_color=theme.TEXT_SECONDARY,
        )
        self._unit_label.pack()

        self._status_label = ctk.CTkLabel(
            self,
            text="Place item on scale",
            font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY,
        )
        self._status_label.pack(pady=(0, theme.PADDING_MEDIUM))

    def set_weight(self, weight: float, stable: bool = False) -> None:
        """Update the displayed weight."""
        self._weight_label.configure(text=f"{weight:.3f}")
        if stable:
            self._status_label.configure(
                text="STABLE", text_color=theme.TEXT_SUCCESS
            )
        else:
            self._status_label.configure(
                text="Stabilizing...", text_color=theme.TEXT_WARNING
            )

    def set_locked(self, weight: float) -> None:
        """Show locked weight with visual confirmation."""
        self._weight_label.configure(
            text=f"{weight:.3f}", text_color=theme.TEXT_SUCCESS
        )
        self._status_label.configure(
            text="LOCKED", text_color=theme.TEXT_SUCCESS
        )

    def reset(self) -> None:
        """Reset to default state."""
        self._weight_label.configure(
            text="0.000", text_color=theme.TEXT_PRIMARY
        )
        self._status_label.configure(
            text="Place item on scale", text_color=theme.TEXT_SECONDARY
        )


class StatusIndicator(ctk.CTkFrame):
    """Visual status indicator showing workflow state."""

    STATES = [
        ("Select", "product_selected"),
        ("Weigh", "weight_captured"),
        ("Print", "label_printed"),
        ("Scan", "awaiting_scan"),
        ("Done", "verified"),
    ]

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG_SECONDARY, **kwargs)

        self._indicators: list[ctk.CTkLabel] = []

        for label_text, state_key in self.STATES:
            indicator = ctk.CTkLabel(
                self,
                text=label_text,
                font=theme.FONT_BODY,
                text_color=theme.TEXT_SECONDARY,
                fg_color=theme.BG_TERTIARY,
                corner_radius=4,
                width=100,
                height=40,
            )
            indicator.pack(side="left", padx=4, pady=8)
            self._indicators.append(indicator)

    def set_state(self, current_state: str) -> None:
        """Highlight the current workflow state."""
        state_keys = [s[1] for s in self.STATES]

        for i, (label_text, state_key) in enumerate(self.STATES):
            if state_key == current_state:
                color = theme.STATE_COLORS.get(state_key, theme.TEXT_ACCENT)
                self._indicators[i].configure(
                    text_color=color, fg_color=theme.BG_PRIMARY
                )
            elif state_keys.index(state_key) < state_keys.index(current_state) if current_state in state_keys else False:
                self._indicators[i].configure(
                    text_color=theme.TEXT_SUCCESS, fg_color=theme.BG_TERTIARY
                )
            else:
                self._indicators[i].configure(
                    text_color=theme.TEXT_SECONDARY, fg_color=theme.BG_TERTIARY
                )

    def reset(self) -> None:
        """Reset all indicators to default."""
        for indicator in self._indicators:
            indicator.configure(
                text_color=theme.TEXT_SECONDARY, fg_color=theme.BG_TERTIARY
            )


class InfoBar(ctk.CTkFrame):
    """Bottom status bar showing current animal, box, and package count."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.BG_TERTIARY, height=50, **kwargs)
        self.pack_propagate(False)

        self._animal_label = ctk.CTkLabel(
            self, text="No animal", font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY,
        )
        self._animal_label.pack(side="left", padx=theme.PADDING_MEDIUM)

        self._box_label = ctk.CTkLabel(
            self, text="No box", font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY,
        )
        self._box_label.pack(side="left", padx=theme.PADDING_MEDIUM)

        self._count_label = ctk.CTkLabel(
            self, text="0 packages", font=theme.FONT_BODY,
            text_color=theme.TEXT_SECONDARY,
        )
        self._count_label.pack(side="right", padx=theme.PADDING_MEDIUM)

    def update_info(
        self,
        animal_name: Optional[str] = None,
        box_number: Optional[int] = None,
        package_count: int = 0,
    ) -> None:
        self._animal_label.configure(
            text=animal_name or "No animal",
            text_color=theme.TEXT_PRIMARY if animal_name else theme.TEXT_SECONDARY,
        )
        self._box_label.configure(
            text=f"Box {box_number}" if box_number else "No box",
            text_color=theme.TEXT_PRIMARY if box_number else theme.TEXT_SECONDARY,
        )
        self._count_label.configure(
            text=f"{package_count} package{'s' if package_count != 1 else ''}",
            text_color=theme.TEXT_PRIMARY,
        )


class ConfirmDialog(ctk.CTkToplevel):
    """Modal confirmation dialog with large touch targets."""

    def __init__(
        self,
        master,
        title: str = "Confirm",
        message: str = "Are you sure?",
        confirm_text: str = "Yes",
        cancel_text: str = "No",
        on_confirm: Optional[Callable] = None,
        on_cancel: Optional[Callable] = None,
    ):
        super().__init__(master)
        self.title(title)
        self.geometry("500x300")
        self.configure(fg_color=theme.BG_PRIMARY)
        self.resizable(False, False)
        self.grab_set()

        self._on_confirm = on_confirm
        self._on_cancel = on_cancel

        msg_label = ctk.CTkLabel(
            self, text=message, font=theme.FONT_HEADING,
            text_color=theme.TEXT_PRIMARY, wraplength=440,
        )
        msg_label.pack(pady=(theme.PADDING_LARGE * 2, theme.PADDING_LARGE))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=theme.PADDING_LARGE, pady=theme.PADDING_MEDIUM)

        TouchButton(
            btn_frame, text=cancel_text, style="secondary",
            command=self._do_cancel, width=200,
        ).pack(side="left", padx=theme.PADDING_SMALL)

        TouchButton(
            btn_frame, text=confirm_text, style="success",
            command=self._do_confirm, width=200,
        ).pack(side="right", padx=theme.PADDING_SMALL)

    def _do_confirm(self) -> None:
        if self._on_confirm:
            self._on_confirm()
        self.destroy()

    def _do_cancel(self) -> None:
        if self._on_cancel:
            self._on_cancel()
        self.destroy()
