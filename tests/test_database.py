"""Tests for SQLite database module."""

import os
import tempfile
import pytest

from src.database import Database


@pytest.fixture
def db():
    """Provide a fresh in-memory database for each test."""
    d = Database(":memory:")
    d.connect()
    yield d
    d.close()


@pytest.fixture
def csv_path():
    """Path to the real pomponio_skus.csv."""
    return os.path.join(os.path.dirname(__file__), "..", "data", "pomponio_skus.csv")


# ---------------------------------------------------------------------------
# Schema and connection
# ---------------------------------------------------------------------------

class TestConnection:

    def test_connect_creates_tables(self, db):
        tables = db.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {r["name"] for r in tables}
        assert "products" in names
        assert "animals" in names
        assert "boxes" in names
        assert "packages" in names
        assert "scan_log" in names

    def test_connect_file_database(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        try:
            d = Database(path)
            d.connect()
            assert os.path.exists(path)
            d.close()
        finally:
            os.unlink(path)

    def test_ensure_connected_raises(self):
        d = Database(":memory:")
        with pytest.raises(RuntimeError):
            d.get_all_active_products()


# ---------------------------------------------------------------------------
# Product import
# ---------------------------------------------------------------------------

class TestProductImport:

    def test_import_from_csv(self, db, csv_path):
        count = db.import_products_from_csv(csv_path)
        assert count > 0

    def test_import_count(self, db, csv_path):
        """CSV has 108 data rows (71 beef active + 37 pork inactive)."""
        count = db.import_products_from_csv(csv_path)
        assert count == 108

    def test_import_idempotent(self, db, csv_path):
        first = db.import_products_from_csv(csv_path)
        second = db.import_products_from_csv(csv_path)
        assert first > 0
        assert second == 0  # all already exist

    def test_import_missing_file(self, db):
        with pytest.raises(FileNotFoundError):
            db.import_products_from_csv("/nonexistent/file.csv")

    def test_import_duplicate_sku_in_csv(self, db, tmp_path):
        csv_file = tmp_path / "dupes.csv"
        csv_file.write_text(
            "sku,name,category,unit,active\n"
            "00100,Ribeye,Beef,lb,true\n"
            "00100,Ribeye Dup,Beef,lb,true\n"
        )
        with pytest.raises(ValueError, match="Duplicate SKU"):
            db.import_products_from_csv(str(csv_file))


# ---------------------------------------------------------------------------
# Product queries
# ---------------------------------------------------------------------------

class TestProductQueries:

    @pytest.fixture(autouse=True)
    def _load_products(self, db, csv_path):
        db.import_products_from_csv(csv_path)

    def test_get_product_by_sku(self, db):
        product = db.get_product_by_sku("00100")
        assert product is not None
        assert product["name"] == "Ribeye Steak Bone-In 1.5in Thick"
        assert product["category"] == "Beef"
        assert product["unit"] == "lb"

    def test_get_product_not_found(self, db):
        assert db.get_product_by_sku("99999") is None

    def test_get_products_by_category(self, db):
        beef = db.get_products_by_category("Beef")
        assert len(beef) > 0
        assert all(p["category"] == "Beef" for p in beef)

    def test_get_products_inactive_excluded(self, db):
        pork_active = db.get_products_by_category("Pork", active_only=True)
        pork_all = db.get_products_by_category("Pork", active_only=False)
        assert len(pork_active) == 0
        assert len(pork_all) > 0

    def test_get_all_active_products(self, db):
        active = db.get_all_active_products()
        assert len(active) == 71
        assert all(p["active"] for p in active)

    def test_get_categories(self, db):
        cats = db.get_categories()
        assert "Beef" in cats
        # Pork has no active products, so should not appear
        assert "Pork" not in cats


# ---------------------------------------------------------------------------
# Animals
# ---------------------------------------------------------------------------

class TestAnimals:

    def test_create_animal(self, db):
        aid = db.create_animal("Beef #1 - 2/15/2026")
        assert aid is not None
        assert aid > 0

    def test_get_animal(self, db):
        aid = db.create_animal("Beef #1")
        animal = db.get_animal(aid)
        assert animal["name"] == "Beef #1"
        assert animal["species"] == "Beef"
        assert animal["closed_at"] is None

    def test_close_animal(self, db):
        aid = db.create_animal("Beef #1")
        db.close_animal(aid, manifest_path="/tmp/manifest.xlsx")
        animal = db.get_animal(aid)
        assert animal["closed_at"] is not None
        assert animal["manifest_path"] == "/tmp/manifest.xlsx"

    def test_get_open_animals(self, db):
        a1 = db.create_animal("Beef #1")
        a2 = db.create_animal("Beef #2")
        db.close_animal(a1)
        open_animals = db.get_open_animals()
        assert len(open_animals) == 1
        assert open_animals[0]["id"] == a2


# ---------------------------------------------------------------------------
# Boxes
# ---------------------------------------------------------------------------

class TestBoxes:

    def test_create_box(self, db):
        aid = db.create_animal("Beef #1")
        bid = db.create_box(aid)
        assert bid is not None

    def test_box_number_auto_increments(self, db):
        aid = db.create_animal("Beef #1")
        b1 = db.create_box(aid)
        b2 = db.create_box(aid)
        box1 = db.get_box(b1)
        box2 = db.get_box(b2)
        assert box1["box_number"] == 1
        assert box2["box_number"] == 2

    def test_close_box(self, db):
        aid = db.create_animal("Beef #1")
        bid = db.create_box(aid)
        db.close_box(bid)
        box = db.get_box(bid)
        assert box["closed_at"] is not None

    def test_get_open_boxes(self, db):
        aid = db.create_animal("Beef #1")
        b1 = db.create_box(aid)
        b2 = db.create_box(aid)
        db.close_box(b1)
        open_boxes = db.get_open_boxes(aid)
        assert len(open_boxes) == 1
        assert open_boxes[0]["id"] == b2


# ---------------------------------------------------------------------------
# Packages
# ---------------------------------------------------------------------------

class TestPackages:

    @pytest.fixture(autouse=True)
    def _setup(self, db, csv_path):
        db.import_products_from_csv(csv_path)
        self.aid = db.create_animal("Beef #1")
        self.bid = db.create_box(self.aid)
        self.product = db.get_product_by_sku("00100")

    def test_create_package(self, db):
        pid = db.create_package(
            self.product["id"], self.aid, self.bid, 1.52, "000100001525"
        )
        assert pid > 0

    def test_mark_verified(self, db):
        pid = db.create_package(
            self.product["id"], self.aid, self.bid, 1.52, "000100001525"
        )
        db.mark_package_verified(pid, True)
        pkgs = db.get_packages_for_box(self.bid)
        assert pkgs[0]["scan_matched"] == 1

    def test_get_packages_for_box(self, db):
        db.create_package(self.product["id"], self.aid, self.bid, 1.52, "000100001525")
        db.create_package(self.product["id"], self.aid, self.bid, 2.0, "000100002008")
        pkgs = db.get_packages_for_box(self.bid)
        assert len(pkgs) == 2
        assert pkgs[0]["product_name"] == "Ribeye Steak Bone-In 1.5in Thick"

    def test_get_packages_for_animal(self, db):
        db.create_package(self.product["id"], self.aid, self.bid, 1.52, "000100001525")
        pkgs = db.get_packages_for_animal(self.aid)
        assert len(pkgs) == 1

    def test_box_summary(self, db):
        p2 = db.get_product_by_sku("00101")
        db.create_package(self.product["id"], self.aid, self.bid, 1.52, "000100001525")
        db.create_package(self.product["id"], self.aid, self.bid, 2.0, "000100002008")
        db.create_package(p2["id"], self.aid, self.bid, 1.0, "000101001006")
        summary = db.get_box_summary(self.bid)
        assert len(summary) == 2  # two distinct SKUs
        ribeye = next(s for s in summary if s["sku"] == "00100")
        assert ribeye["quantity"] == 2
        assert abs(ribeye["total_weight"] - 3.52) < 0.001


# ---------------------------------------------------------------------------
# Manifest data
# ---------------------------------------------------------------------------

class TestManifest:

    @pytest.fixture(autouse=True)
    def _setup(self, db, csv_path):
        db.import_products_from_csv(csv_path)
        self.aid = db.create_animal("Beef #1")
        self.bid = db.create_box(self.aid)
        p1 = db.get_product_by_sku("00100")
        p2 = db.get_product_by_sku("00123")
        db.create_package(p1["id"], self.aid, self.bid, 1.52, "barcode1")
        db.create_package(p1["id"], self.aid, self.bid, 2.0, "barcode2")
        db.create_package(p2["id"], self.aid, self.bid, 1.0, "barcode3")

    def test_manifest_data(self, db):
        data = db.get_animal_manifest_data(self.aid)
        assert len(data) == 2  # two SKUs

    def test_manifest_weights(self, db):
        data = db.get_animal_manifest_data(self.aid)
        ribeye = next(d for d in data if d["sku"] == "00100")
        assert ribeye["quantity"] == 2
        assert ribeye["weights"] == [1.52, 2.0]
        assert abs(ribeye["total_weight"] - 3.52) < 0.001

    def test_manifest_sorted_by_sku(self, db):
        data = db.get_animal_manifest_data(self.aid)
        skus = [d["sku"] for d in data]
        assert skus == sorted(skus)


# ---------------------------------------------------------------------------
# Scan log
# ---------------------------------------------------------------------------

class TestScanLog:

    def test_log_scan_match(self, db):
        sid = db.log_scan("000100001525", "000100001525", True)
        assert sid > 0

    def test_log_scan_mismatch(self, db):
        sid = db.log_scan("000100001525", "000100002008", False)
        assert sid > 0
