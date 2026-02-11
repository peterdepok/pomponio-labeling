"""Product grid screen with category tabs.

Displays all active products organized by category (Steaks, Roasts, Ground,
Offal/Specialty, Bones, Sausage/Processed). Each button shows product name
and SKU code. Tapping a product triggers the labeling workflow.
"""

import logging
from typing import Callable, Optional

import customtkinter as ctk

from src.ui import theme
from src.ui.theme import classify_product, get_category_color, CATEGORY_COLORS
from src.ui.widgets import ProductButton

logger = logging.getLogger(__name__)

# Ordered category tabs
CATEGORY_ORDER = [
    "Steaks",
    "Roasts",
    "Ground",
    "Offal/Specialty",
    "Bones",
    "Sausage/Processed",
]


class ProductGrid(ctk.CTkFrame):
    """Product selection grid with category tab navigation."""

    def __init__(
        self,
        master,
        products: list[dict],
        on_select: Optional[Callable[[dict], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=theme.BG_PRIMARY, **kwargs)

        self._products = products
        self._on_select = on_select
        self._current_category = CATEGORY_ORDER[0]

        # Classify products into UI categories
        self._categorized: dict[str, list[dict]] = {cat: [] for cat in CATEGORY_ORDER}
        for product in products:
            cat = classify_product(product["sku"], product["name"])
            if cat in self._categorized:
                self._categorized[cat].append(product)

        self._build_ui()
        self._show_category(self._current_category)

    def _build_ui(self) -> None:
        """Build the tab bar and scrollable grid area."""
        # Category tab bar
        self._tab_frame = ctk.CTkFrame(
            self, fg_color=theme.BG_SECONDARY, height=theme.TAB_HEIGHT
        )
        self._tab_frame.pack(fill="x", padx=0, pady=0)
        self._tab_frame.pack_propagate(False)

        self._tab_buttons: dict[str, ctk.CTkButton] = {}
        for cat in CATEGORY_ORDER:
            colors = CATEGORY_COLORS.get(cat, CATEGORY_COLORS["Steaks"])
            count = len(self._categorized[cat])
            btn = ctk.CTkButton(
                self._tab_frame,
                text=f"{cat}\n({count})",
                font=theme.FONT_SMALL,
                fg_color=theme.BG_TERTIARY,
                hover_color=colors["hover"],
                text_color=theme.TEXT_SECONDARY,
                corner_radius=0,
                height=theme.TAB_HEIGHT,
                command=lambda c=cat: self._show_category(c),
            )
            btn.pack(side="left", fill="both", expand=True)
            self._tab_buttons[cat] = btn

        # Scrollable grid area
        self._scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=theme.BG_PRIMARY,
        )
        self._scroll_frame.pack(fill="both", expand=True, padx=theme.PADDING_SMALL, pady=theme.PADDING_SMALL)

        # Configure grid columns
        for col in range(theme.PRODUCT_GRID_COLUMNS):
            self._scroll_frame.columnconfigure(col, weight=1)

    def _show_category(self, category: str) -> None:
        """Display products for the selected category."""
        self._current_category = category

        # Update tab styling
        for cat, btn in self._tab_buttons.items():
            if cat == category:
                colors = CATEGORY_COLORS.get(cat, CATEGORY_COLORS["Steaks"])
                btn.configure(
                    fg_color=colors["bg"],
                    text_color=theme.TEXT_PRIMARY,
                )
            else:
                btn.configure(
                    fg_color=theme.BG_TERTIARY,
                    text_color=theme.TEXT_SECONDARY,
                )

        # Clear existing grid
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()

        # Populate grid
        products = self._categorized.get(category, [])
        colors = get_category_color(category)

        for i, product in enumerate(products):
            row = i // theme.PRODUCT_GRID_COLUMNS
            col = i % theme.PRODUCT_GRID_COLUMNS

            btn = ProductButton(
                self._scroll_frame,
                product_name=product["name"],
                sku=product["sku"],
                category_color=colors,
                command=lambda p=product: self._select_product(p),
            )
            btn.grid(
                row=row, column=col,
                padx=theme.GRID_GAP // 2,
                pady=theme.GRID_GAP // 2,
                sticky="nsew",
            )

    def _select_product(self, product: dict) -> None:
        """Handle product selection."""
        logger.info("Product selected: %s (%s)", product["name"], product["sku"])
        if self._on_select:
            self._on_select(product)

    def refresh(self, products: list[dict]) -> None:
        """Refresh the grid with updated product data."""
        self._products = products
        self._categorized = {cat: [] for cat in CATEGORY_ORDER}
        for product in products:
            cat = classify_product(product["sku"], product["name"])
            if cat in self._categorized:
                self._categorized[cat].append(product)

        # Update tab counts
        for cat, btn in self._tab_buttons.items():
            count = len(self._categorized[cat])
            btn.configure(text=f"{cat}\n({count})")

        self._show_category(self._current_category)
