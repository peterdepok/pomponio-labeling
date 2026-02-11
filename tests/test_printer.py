"""Tests for Zebra ZP230D printer module."""

import os
import pytest

from src.printer import Printer, PrinterError


@pytest.fixture
def template_dir():
    return os.path.join(os.path.dirname(__file__), "..", "data", "templates")


@pytest.fixture
def printer(template_dir):
    return Printer("TestPrinter", template_dir=template_dir)


class TestTemplateLoading:

    def test_load_package_template(self, printer):
        template = printer.load_template("package_label.zpl")
        assert "{product_name}" in template
        assert "{weight_lb}" in template
        assert "{barcode_12}" in template
        assert "^XA" in template
        assert "^XZ" in template

    def test_load_box_template(self, printer):
        template = printer.load_template("box_label.zpl")
        assert "{product_name}" in template

    def test_load_missing_template(self, printer):
        with pytest.raises(PrinterError, match="not found"):
            printer.load_template("nonexistent.zpl")

    def test_template_caching(self, printer):
        t1 = printer.load_template("package_label.zpl")
        t2 = printer.load_template("package_label.zpl")
        assert t1 is t2

    def test_clear_cache(self, printer):
        printer.load_template("package_label.zpl")
        assert len(printer._templates) > 0
        printer.clear_template_cache()
        assert len(printer._templates) == 0


class TestLabelBuilding:

    def test_build_label(self, printer):
        zpl = printer.build_label(
            "package_label.zpl",
            product_name="Bone-In Ribeye Steak 1.5in Thick",
            weight_lb=1.52,
            barcode_12="000100001525",
        )
        assert "Bone-In Ribeye Steak 1.5in Thick" in zpl
        assert "1.52" in zpl
        assert "000100001525" in zpl
        assert "{product_name}" not in zpl
        assert "{weight_lb}" not in zpl
        assert "{barcode_12}" not in zpl

    def test_build_label_formatting(self, printer):
        zpl = printer.build_label(
            "package_label.zpl",
            product_name="Ground Beef 70/30",
            weight_lb=1.0,
            barcode_12="001230010006",
        )
        assert "1.00" in zpl  # formatted to 2 decimal places

    def test_build_label_starts_ends_zpl(self, printer):
        zpl = printer.build_label(
            "package_label.zpl", "Test", 1.0, "000000001000"
        )
        assert zpl.strip().startswith("^XA")
        assert zpl.strip().endswith("^XZ")
