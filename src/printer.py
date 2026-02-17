"""Zebra ZP230D label printer communication via ZPL II over USB.

Loads ZPL templates from data/templates/, substitutes variables, sends raw ZPL to printer.
"""

import logging
import os
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "data", "templates"
)


class PrinterError(Exception):
    """Raised on printer communication failure."""


class Printer:
    """Interface to the Zebra ZP230D label printer."""

    def __init__(self, printer_name: str, template_dir: str = DEFAULT_TEMPLATE_DIR):
        self.printer_name = printer_name
        self.template_dir = template_dir
        self._templates: dict[str, str] = {}

    def load_template(self, template_name: str) -> str:
        """Load a ZPL template file from the templates directory.

        Args:
            template_name: Filename (e.g., "package_label.zpl").

        Returns:
            Template string with placeholders.

        Raises:
            PrinterError: If template file not found.
        """
        if template_name in self._templates:
            return self._templates[template_name]

        path = os.path.join(self.template_dir, template_name)
        if not os.path.exists(path):
            raise PrinterError(f"Template not found: {path}")

        with open(path, "r") as f:
            template = f.read()

        self._templates[template_name] = template
        logger.debug("Loaded template: %s", template_name)
        return template

    def build_label(
        self,
        template_name: str,
        product_name: str,
        weight_lb: float,
        barcode_12: str,
    ) -> str:
        """Build ZPL label data by substituting variables into template.

        Args:
            template_name: ZPL template filename.
            product_name: Product display name.
            weight_lb: Weight in pounds.
            barcode_12: 12-digit UPC-A barcode string.

        Returns:
            Complete ZPL string ready to send to printer.
        """
        template = self.load_template(template_name)
        zpl = template.replace("{product_name}", product_name)
        zpl = zpl.replace("{weight_lb}", f"{weight_lb:.2f}")
        zpl = zpl.replace("{barcode_12}", barcode_12)
        return zpl

    def send_raw_zpl(self, zpl: str) -> None:
        """Send raw ZPL data to the printer.

        On Windows, writes directly to the printer share or device.
        Falls back to lpr/lp on other platforms.

        Args:
            zpl: Complete ZPL string.

        Raises:
            PrinterError: If printing fails.
        """
        logger.info("Sending ZPL to printer: %s (%d bytes)", self.printer_name, len(zpl))

        if sys.platform == "win32":
            self._send_windows(zpl)
        else:
            self._send_unix(zpl)

    def _send_windows(self, zpl: str) -> None:
        """Send ZPL on Windows via direct printer port write."""
        try:
            # Method 1: Write to shared printer via UNC path or direct port
            # The printer name should be the Windows printer share name
            import win32print  # type: ignore[import-not-found]

            handle = win32print.OpenPrinter(self.printer_name)
            try:
                win32print.StartDocPrinter(handle, 1, ("ZPL Label", None, "RAW"))
                win32print.StartPagePrinter(handle)
                win32print.WritePrinter(handle, zpl.encode("utf-8"))
                win32print.EndPagePrinter(handle)
                win32print.EndDocPrinter(handle)
                logger.info("Label sent successfully via win32print")
            finally:
                win32print.ClosePrinter(handle)
        except ImportError:
            # Fallback: use copy command to printer port
            logger.warning("win32print not available, attempting file-based print")
            self._send_file_fallback(zpl)
        except Exception as e:
            raise PrinterError(f"Windows print failed: {e}") from e

    def _send_file_fallback(self, zpl: str) -> None:
        """Fallback: write ZPL to a temp file and copy to printer."""
        import tempfile
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".zpl", delete=False
            ) as f:
                f.write(zpl)
                tmp_path = f.name
            result = subprocess.run(
                ["copy", "/b", tmp_path, self.printer_name],
                shell=True,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise PrinterError(f"File copy to printer failed: {result.stderr}")
        finally:
            if tmp_path is not None:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass

    def _send_unix(self, zpl: str) -> None:
        """Send ZPL on Unix/macOS via lp command (for development/testing)."""
        try:
            result = subprocess.run(
                ["lp", "-d", self.printer_name, "-o", "raw"],
                input=zpl,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise PrinterError(f"lp command failed: {result.stderr}")
            logger.info("Label sent successfully via lp")
        except FileNotFoundError:
            raise PrinterError("lp command not found; cannot print on this platform")

    def print_label(
        self,
        product_name: str,
        weight_lb: float,
        barcode_12: str,
        template_name: str = "package_label.zpl",
    ) -> str:
        """Build and print a package label. Returns the ZPL that was sent."""
        zpl = self.build_label(template_name, product_name, weight_lb, barcode_12)
        self.send_raw_zpl(zpl)
        return zpl

    def clear_template_cache(self) -> None:
        """Clear cached templates (e.g., after an update)."""
        self._templates.clear()
