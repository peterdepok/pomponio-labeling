"""Main application with tab navigation between screens.

Entry point for the Pomponio Ranch Labeling System.
Coordinates database, hardware, and UI modules.
"""

import logging
import os
import sys
from typing import Optional

import customtkinter as ctk

from src.config import Config
from src.database import Database
from src.safety import Workflow, WorkflowState
from src.scanner import Scanner
from src.scale import Scale, ScaleReading, ScaleError
from src.printer import Printer, PrinterError
from src.barcode import generate_barcode
from src.ui import theme
from src.ui.widgets import TouchButton, InfoBar
from src.ui.products import ProductGrid
from src.ui.labeling import LabelingScreen
from src.ui.boxes import BoxScreen
from src.ui.animals import AnimalScreen

logger = logging.getLogger(__name__)


class App(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Configuration
        self._config = Config()
        self._config.load()

        # Setup logging
        self._setup_logging()

        # Window setup
        self.title("Pomponio Ranch Labeling System")
        self.geometry("1280x1024")
        self.configure(fg_color=theme.BG_PRIMARY)
        ctk.set_appearance_mode("dark")

        # Core objects
        self._db = Database(self._config.db_path)
        self._db.connect()
        self._load_products()

        self._workflow = Workflow()
        self._scanner = Scanner()
        self._scale: Optional[Scale] = None
        self._printer: Optional[Printer] = None

        # State
        self._current_animal_id: Optional[int] = None
        self._current_box_id: Optional[int] = None

        # Build UI
        self._build_ui()

        # Try connecting hardware (non-fatal if absent)
        self._try_connect_hardware()

        # Workflow callback
        self._workflow.set_callback(self._on_workflow_state_change)

    def _setup_logging(self) -> None:
        """Configure file and console logging."""
        log_level = getattr(logging, self._config.log_level, logging.INFO)
        log_file = self._config.log_file

        handlers = [logging.StreamHandler()]
        try:
            handlers.append(logging.FileHandler(log_file))
        except OSError:
            pass

        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            handlers=handlers,
        )
        logger.info("Application starting, version %s", self._config.version)

    def _load_products(self) -> None:
        """Load product database from CSV if empty."""
        existing = self._db.get_all_active_products()
        if not existing:
            csv_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data", "pomponio_skus.csv",
            )
            if os.path.exists(csv_path):
                try:
                    count = self._db.import_products_from_csv(csv_path)
                    logger.info("Imported %d products from CSV", count)
                except Exception as e:
                    logger.error("CSV import failed: %s", e)

    def _build_ui(self) -> None:
        """Build the main application layout with tab navigation."""
        # Tab navigation bar at top
        self._nav_frame = ctk.CTkFrame(self, fg_color=theme.BG_TERTIARY, height=70)
        self._nav_frame.pack(fill="x")
        self._nav_frame.pack_propagate(False)

        self._tab_buttons: dict[str, ctk.CTkButton] = {}
        tabs = [
            ("Label", self._show_labeling),
            ("Products", self._show_products),
            ("Boxes", self._show_boxes),
            ("Animals", self._show_animals),
        ]

        for tab_name, command in tabs:
            btn = ctk.CTkButton(
                self._nav_frame,
                text=tab_name,
                font=theme.FONT_BODY_LARGE,
                fg_color=theme.BG_TERTIARY,
                hover_color=theme.BTN_PRIMARY_HOVER,
                text_color=theme.TEXT_SECONDARY,
                corner_radius=0,
                height=70,
                command=command,
            )
            btn.pack(side="left", fill="both", expand=True)
            self._tab_buttons[tab_name] = btn

        # Content area
        self._content_frame = ctk.CTkFrame(self, fg_color=theme.BG_PRIMARY)
        self._content_frame.pack(fill="both", expand=True)

        # Info bar at bottom
        self._info_bar = InfoBar(self)
        self._info_bar.pack(fill="x", side="bottom")

        # Build screens (lazy, only the visible one is packed)
        products = self._db.get_all_active_products()

        self._product_grid = ProductGrid(
            self._content_frame,
            products=products,
            on_select=self._on_product_selected,
        )

        self._labeling_screen = LabelingScreen(
            self._content_frame,
            workflow=self._workflow,
            scanner=self._scanner,
            on_print_request=self._on_print_request,
            on_package_complete=self._on_package_complete,
        )

        self._box_screen = BoxScreen(
            self._content_frame,
            db=self._db,
            current_animal_id=self._current_animal_id,
            on_close_box=self._on_close_box,
        )

        self._animal_screen = AnimalScreen(
            self._content_frame,
            db=self._db,
            on_animal_changed=self._on_animal_changed,
            on_generate_manifest=self._on_generate_manifest,
        )

        self._screens = {
            "Label": self._labeling_screen,
            "Products": self._product_grid,
            "Boxes": self._box_screen,
            "Animals": self._animal_screen,
        }
        self._current_screen: Optional[str] = None

        # Show labeling screen by default
        self._show_labeling()

    def _show_screen(self, name: str) -> None:
        """Switch to the named screen."""
        if self._current_screen == name:
            return

        # Hide current
        for screen in self._screens.values():
            screen.pack_forget()

        # Show target
        self._screens[name].pack(fill="both", expand=True)
        self._current_screen = name

        # Update nav styling
        for tab_name, btn in self._tab_buttons.items():
            if tab_name == name:
                btn.configure(
                    fg_color=theme.BTN_PRIMARY_BG,
                    text_color=theme.TEXT_PRIMARY,
                )
            else:
                btn.configure(
                    fg_color=theme.BG_TERTIARY,
                    text_color=theme.TEXT_SECONDARY,
                )

    def _show_labeling(self) -> None:
        self._show_screen("Label")

    def _show_products(self) -> None:
        self._show_screen("Products")

    def _show_boxes(self) -> None:
        self._box_screen.refresh()
        self._show_screen("Boxes")

    def _show_animals(self) -> None:
        self._animal_screen.refresh()
        self._show_screen("Animals")

    # --- Hardware ---

    def _try_connect_hardware(self) -> None:
        """Attempt to connect scale and printer. Non-fatal on failure."""
        # Scale
        try:
            self._scale = Scale(
                self._config.scale_port,
                self._config.scale_baud_rate,
            )
            self._scale.connect()
            self._scale.start_polling(
                on_weight=self._on_scale_weight,
                on_lock=self._on_scale_lock,
            )
            logger.info("Scale connected on %s", self._config.scale_port)
        except ScaleError as e:
            logger.warning("Scale not connected: %s", e)
            self._scale = None

        # Printer
        try:
            self._printer = Printer(
                self._config.printer_name,
                template_dir=self._config.template_dir,
            )
            # Test template loading
            self._printer.load_template("package_label.zpl")
            logger.info("Printer configured: %s", self._config.printer_name)
        except PrinterError as e:
            logger.warning("Printer not configured: %s", e)
            self._printer = None

    # --- Callbacks ---

    def _on_product_selected(self, product: dict) -> None:
        """Handle product selection from the grid."""
        self._show_labeling()
        self._labeling_screen.set_product(product)

    def _on_scale_weight(self, reading: ScaleReading) -> None:
        """Handle live weight reading from scale (called from background thread)."""
        self.after(0, lambda: self._labeling_screen.update_weight(
            reading.weight_lb, reading.stable
        ))

    def _on_scale_lock(self, weight: float) -> None:
        """Handle locked weight from scale (called from background thread)."""
        self.after(0, lambda: self._labeling_screen.lock_weight(weight))

    def _on_print_request(self, product_name: str, sku: str, weight: float, barcode: str) -> None:
        """Handle print request from labeling screen."""
        if self._printer is None:
            logger.warning("Print requested but no printer configured")
            return

        try:
            self._printer.print_label(product_name, weight, barcode)
            logger.info("Label printed: %s %.2f lb %s", product_name, weight, barcode)
        except PrinterError as e:
            logger.error("Print failed: %s", e)

    def _on_package_complete(self, package_data: dict) -> None:
        """Handle verified package from labeling screen."""
        if self._current_animal_id is None or self._current_box_id is None:
            logger.warning("Package complete but no animal/box set")
            return

        product = self._db.get_product_by_sku(package_data["sku"])
        if product is None:
            logger.error("Product not found for SKU %s", package_data["sku"])
            return

        pkg_id = self._db.create_package(
            product_id=product["id"],
            animal_id=self._current_animal_id,
            box_id=self._current_box_id,
            weight_lb=package_data["weight_lb"],
            barcode=package_data["barcode"],
        )
        self._db.mark_package_verified(pkg_id, True)
        self._db.log_scan(package_data["barcode"], package_data["barcode"], True)

        # Update info bar
        packages = self._db.get_packages_for_box(self._current_box_id)
        box = self._db.get_box(self._current_box_id)
        animal = self._db.get_animal(self._current_animal_id)
        self._info_bar.update_info(
            animal_name=animal["name"] if animal else None,
            box_number=box["box_number"] if box else None,
            package_count=len(packages),
        )

        logger.info("Package recorded: id=%d barcode=%s", pkg_id, package_data["barcode"])

    def _on_close_box(self, box_id: int, summary: list[dict]) -> None:
        """Handle box closure. Print box labels."""
        if self._printer:
            for item in summary:
                try:
                    # Box labels use a different template
                    zpl = self._printer.load_template("box_label.zpl")
                    zpl = zpl.replace("{product_name}", item["product_name"])
                    zpl = zpl.replace("{quantity}", str(item["quantity"]))
                    zpl = zpl.replace("{total_weight}", f"{item['total_weight']:.1f}")
                    zpl = zpl.replace("{barcode_12}", "000000000000")  # placeholder for box labels
                    self._printer.send_raw_zpl(zpl)
                except PrinterError as e:
                    logger.error("Box label print failed: %s", e)

        # Open a new box automatically
        if self._current_animal_id:
            self._current_box_id = self._db.create_box(self._current_animal_id)
            logger.info("Auto-opened new box %d", self._current_box_id)

    def _on_animal_changed(self, animal_id: Optional[int]) -> None:
        """Handle active animal change."""
        self._current_animal_id = animal_id
        self._box_screen.set_animal_id(animal_id)

        if animal_id is not None:
            # Auto-create first box if none exist
            boxes = self._db.get_open_boxes(animal_id)
            if not boxes:
                self._current_box_id = self._db.create_box(animal_id)
                logger.info("Auto-created box for animal %d", animal_id)
            else:
                self._current_box_id = boxes[0]["id"]

            animal = self._db.get_animal(animal_id)
            box = self._db.get_box(self._current_box_id) if self._current_box_id else None
            self._info_bar.update_info(
                animal_name=animal["name"] if animal else None,
                box_number=box["box_number"] if box else None,
                package_count=0,
            )
        else:
            self._current_box_id = None
            self._info_bar.update_info()

    def _on_generate_manifest(self, animal_id: int) -> Optional[str]:
        """Generate manifest spreadsheet for an animal."""
        try:
            from src.manifest import generate_manifest
            return generate_manifest(self._db, animal_id)
        except ImportError:
            logger.warning("Manifest module not available yet")
            return None
        except Exception as e:
            logger.error("Manifest generation failed: %s", e)
            return None

    def _on_workflow_state_change(self, old: WorkflowState, new: WorkflowState) -> None:
        """Handle workflow state transitions."""
        logger.debug("Workflow: %s -> %s", old.value, new.value)

        # Reset scale lock when returning to product_selected
        if new == WorkflowState.PRODUCT_SELECTED and self._scale:
            self._scale.reset_lock()

    def destroy(self) -> None:
        """Clean shutdown."""
        if self._scale:
            self._scale.disconnect()
        self._db.close()
        super().destroy()


def main():
    """Application entry point."""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
