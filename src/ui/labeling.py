"""
Package labeling screen.
Core workflow: Select product -> Capture weight -> Print label -> Scan verify
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional, Callable

from ..database import (
    Product, Package, Box,
    get_active_products, get_products_by_category, get_product_by_id,
    create_package, verify_package, get_package_by_barcode,
    get_current_box, create_box, assign_package_to_box, update_box_totals,
    get_packages_in_box, log_scan
)
from ..barcode import generate_package_barcode, parse_package_barcode, validate_package_barcode
from ..printer import LabelGenerator, ZebraPrinter, MockPrinter
from ..scale import Scale, MockScale, WeightReading
from ..scanner import ScanEvent, play_success_beep, play_error_beep
from .widgets import (
    COLORS, FONT_LARGE, FONT_MEDIUM, FONT_SMALL,
    TouchButton, ProductButton, WeightDisplay, StatusBar,
    PackageList, BoxSummary, show_verification
)


class LabelingScreen(tk.Frame):
    """
    Main package labeling screen.

    Layout:
    +------------------+------------------+
    | Product Grid     | Weight Display   |
    |                  |                  |
    |                  | [PRINT] button   |
    +------------------+------------------+
    | Box Summary      | Package List     |
    +------------------+------------------+
    | Status Bar                          |
    +-------------------------------------+
    """

    def __init__(
        self,
        parent,
        scale: Optional[Scale] = None,
        printer: Optional[ZebraPrinter] = None,
        on_scan: Optional[Callable[[ScanEvent], None]] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS['bg'])

        # Hardware
        self.scale = scale or MockScale()
        self.printer = printer or MockPrinter()
        self.label_gen = LabelGenerator()

        # State
        self.selected_product: Optional[Product] = None
        self.current_weight: float = 0.0
        self.weight_stable: bool = False
        self.current_box: Optional[Box] = None
        self.pending_package_id: Optional[int] = None
        self.pending_barcode: Optional[str] = None

        # Build UI
        self._build_ui()

        # Load data
        self._load_products()
        self._load_current_box()

        # Start scale reading
        if self.scale:
            self.scale.on_weight(self._on_weight_update)
            self.scale.on_stable(self._on_weight_stable)
            try:
                self.scale.connect()
                self.scale.start_continuous()
            except Exception as e:
                self.status_bar.set_status(f"Scale error: {e}", 'error')

    def _build_ui(self):
        """Build the labeling screen UI."""
        # Main container with two columns
        main = tk.Frame(self, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Left column - Product grid
        left_col = tk.Frame(main, bg=COLORS['bg'])
        left_col.pack(side='left', fill='both', expand=True)

        # Category tabs
        self.tab_frame = tk.Frame(left_col, bg=COLORS['bg'])
        self.tab_frame.pack(fill='x', pady=(0, 10))

        # Product grid (scrollable)
        grid_container = tk.Frame(left_col, bg=COLORS['card_bg'], relief='solid', bd=1)
        grid_container.pack(fill='both', expand=True)

        self.grid_canvas = tk.Canvas(grid_container, bg=COLORS['card_bg'], highlightthickness=0)
        self.grid_scrollbar = ttk.Scrollbar(grid_container, orient='vertical', command=self.grid_canvas.yview)

        self.product_grid = tk.Frame(self.grid_canvas, bg=COLORS['card_bg'])
        self.product_grid.bind('<Configure>', lambda e: self.grid_canvas.configure(scrollregion=self.grid_canvas.bbox('all')))

        self.grid_canvas.create_window((0, 0), window=self.product_grid, anchor='nw')
        self.grid_canvas.configure(yscrollcommand=self.grid_scrollbar.set)

        self.grid_canvas.pack(side='left', fill='both', expand=True)
        self.grid_scrollbar.pack(side='right', fill='y')

        # Right column
        right_col = tk.Frame(main, bg=COLORS['bg'], width=350)
        right_col.pack(side='right', fill='y', padx=(20, 0))
        right_col.pack_propagate(False)

        # Selected product display
        self.selected_frame = tk.Frame(right_col, bg=COLORS['card_bg'], relief='solid', bd=1)
        self.selected_frame.pack(fill='x', pady=(0, 10))

        tk.Label(
            self.selected_frame,
            text="SELECTED",
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=COLORS['disabled']
        ).pack(pady=(10, 5))

        self.selected_name_var = tk.StringVar(value="None")
        tk.Label(
            self.selected_frame,
            textvariable=self.selected_name_var,
            font=FONT_MEDIUM,
            bg=COLORS['card_bg'],
            fg=COLORS['fg'],
            wraplength=300
        ).pack(pady=(0, 10))

        # Weight display
        self.weight_display = WeightDisplay(right_col)
        self.weight_display.pack(fill='x', pady=(0, 10))

        # Print button
        self.print_btn = TouchButton(
            right_col,
            text="PRINT LABEL",
            command=self._on_print,
            style='success'
        )
        self.print_btn.pack(fill='x', pady=(0, 10), ipady=10)
        self.print_btn.config(state='disabled')

        # Box summary
        self.box_summary = BoxSummary(right_col)
        self.box_summary.pack(fill='x', pady=(0, 10))

        # Package list
        self.package_list = PackageList(right_col)
        self.package_list.pack(fill='both', expand=True, pady=(0, 10))

        # Close box button
        self.close_box_btn = TouchButton(
            right_col,
            text="CLOSE BOX",
            command=self._on_close_box,
            style='warning'
        )
        self.close_box_btn.pack(fill='x', ipady=5)

        # Status bar at bottom
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side='bottom', fill='x')

        # Product buttons dict for selection state
        self.product_buttons: dict[int, ProductButton] = {}
        self.category_buttons: dict[str, tk.Button] = {}
        self.current_category: Optional[str] = None

    def _load_products(self):
        """Load products and build grid."""
        self.products_by_category = get_products_by_category()

        # Create category tabs
        for widget in self.tab_frame.winfo_children():
            widget.destroy()

        for category in self.products_by_category.keys():
            btn = tk.Button(
                self.tab_frame,
                text=category,
                font=FONT_SMALL,
                bg=COLORS['bg'],
                fg=COLORS['fg'],
                relief='flat',
                cursor='hand2',
                padx=15,
                pady=8,
                command=lambda c=category: self._select_category(c)
            )
            btn.pack(side='left', padx=2)
            self.category_buttons[category] = btn

        # Select first category
        if self.products_by_category:
            first_category = list(self.products_by_category.keys())[0]
            self._select_category(first_category)

    def _select_category(self, category: str):
        """Select a category and display its products."""
        self.current_category = category

        # Update tab styling
        for cat, btn in self.category_buttons.items():
            if cat == category:
                btn.config(bg=COLORS['primary'], fg='white')
            else:
                btn.config(bg=COLORS['bg'], fg=COLORS['fg'])

        # Clear product grid
        for widget in self.product_grid.winfo_children():
            widget.destroy()
        self.product_buttons.clear()

        # Add products in grid layout (3 columns)
        products = self.products_by_category.get(category, [])
        for i, product in enumerate(products):
            row, col = divmod(i, 3)

            btn = ProductButton(
                self.product_grid,
                product_name=product.name,
                price_per_lb=product.price_per_lb,
                on_select=lambda p=product: self._select_product(p)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            self.product_buttons[product.id] = btn

        # Configure grid weights
        for col in range(3):
            self.product_grid.columnconfigure(col, weight=1)

    def _select_product(self, product: Product):
        """Select a product for labeling."""
        # Deselect previous
        if self.selected_product:
            btn = self.product_buttons.get(self.selected_product.id)
            if btn:
                btn.set_selected(False)

        # Select new
        self.selected_product = product
        self.selected_name_var.set(product.name)

        btn = self.product_buttons.get(product.id)
        if btn:
            btn.set_selected(True)

        self._update_print_button_state()
        self.status_bar.set_status(f"Selected: {product.name}")

    def _on_weight_update(self, reading: WeightReading):
        """Handle weight reading from scale."""
        self.current_weight = reading.weight_lbs
        self.weight_stable = reading.stable
        self.weight_display.set_weight(reading.weight_lbs, reading.stable)
        self._update_print_button_state()

    def _on_weight_stable(self, reading: WeightReading):
        """Handle stable weight reading."""
        self.status_bar.set_status(f"Weight stable: {reading.weight_lbs:.2f} lb")

    def _update_print_button_state(self):
        """Enable/disable print button based on state."""
        can_print = (
            self.selected_product is not None and
            self.current_weight > 0.05 and
            self.weight_stable
        )
        self.print_btn.config(state='normal' if can_print else 'disabled')

    def _on_print(self):
        """Handle print button press."""
        if not self.selected_product or self.current_weight <= 0:
            return

        product = self.selected_product
        weight = self.current_weight

        # Generate barcode
        barcode = generate_package_barcode(product.sku, weight)

        # Create package record
        package_id = create_package(product.id, weight, barcode)
        self.pending_package_id = package_id
        self.pending_barcode = barcode

        # Generate and print label
        date_str = datetime.now().strftime("%m/%d/%y")
        zpl = self.label_gen.package_label(
            product_name=product.name,
            sku=product.sku,
            weight_lbs=weight,
            price_per_lb=product.price_per_lb,
            barcode=barcode,
            date_packed=date_str
        )

        try:
            self.printer.send_zpl(zpl)
            self.status_bar.set_status(f"Printed label. Scan to verify: {barcode}", 'warning')
        except Exception as e:
            self.status_bar.flash_error(f"Print error: {e}")
            return

    def handle_scan(self, event: ScanEvent):
        """Handle barcode scan for verification."""
        barcode = event.barcode.strip()

        # Check if this is the pending package verification
        if self.pending_barcode and barcode == self.pending_barcode:
            self._verify_pending_package(barcode)
            return

        # Try to look up existing package
        package = get_package_by_barcode(barcode)
        if package:
            if package.verified:
                self.status_bar.set_status(f"Package already verified: {package.product_name}", 'info')
            else:
                self.status_bar.flash_error("Unknown scan context")
        else:
            # Validate barcode format
            parsed = parse_package_barcode(barcode)
            if parsed:
                self.status_bar.flash_error(f"Package not found: SKU {parsed.sku}")
            else:
                self.status_bar.flash_error("Invalid barcode format")
            play_error_beep()

        log_scan('package', 0, barcode, False)

    def _verify_pending_package(self, barcode: str):
        """Verify the pending package after scan."""
        if not self.pending_package_id:
            return

        # Validate
        valid, msg = validate_package_barcode(barcode)
        if not valid:
            show_verification(self, False, msg)
            play_error_beep()
            log_scan('package', self.pending_package_id, barcode, False)
            return

        # Mark verified
        verify_package(self.pending_package_id)

        # Ensure we have a box
        if not self.current_box:
            box_id = create_box()
            self.current_box = get_current_box()

        # Assign to box
        assign_package_to_box(self.pending_package_id, self.current_box.id)
        update_box_totals(self.current_box.id)

        # Log success
        log_scan('package', self.pending_package_id, barcode, True)

        # Show success
        show_verification(self, True, "Package Verified")
        play_success_beep()
        self.status_bar.flash_success("Package added to box")

        # Update UI
        self._load_current_box()

        # Clear pending state
        self.pending_package_id = None
        self.pending_barcode = None

    def _load_current_box(self):
        """Load and display current box."""
        self.current_box = get_current_box()

        if self.current_box:
            packages = get_packages_in_box(self.current_box.id)

            self.box_summary.set_box(
                self.current_box.box_number,
                len(packages),
                sum(p.weight_lbs for p in packages)
            )

            self.package_list.clear()
            for pkg in packages:
                self.package_list.add_package(
                    pkg.product_name or "Unknown",
                    pkg.weight_lbs,
                    pkg.verified
                )

            self.close_box_btn.config(state='normal' if packages else 'disabled')
        else:
            self.box_summary.set_box(None)
            self.package_list.clear()
            self.close_box_btn.config(state='disabled')

    def _on_close_box(self):
        """Handle close box button."""
        if not self.current_box:
            return

        # This will be handled by the boxes screen
        # For now, just signal that we want to close
        self.status_bar.set_status("Navigate to Boxes tab to close box", 'warning')

    def cleanup(self):
        """Clean up resources."""
        if self.scale:
            self.scale.stop_continuous()
            self.scale.disconnect()
