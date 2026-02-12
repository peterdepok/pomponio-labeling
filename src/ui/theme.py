"""Dark theme configuration for the Pomponio Ranch Labeling System.

Design constraints:
    - Dark theme to reduce glare in processing environment
    - 80px minimum touch targets for gloved hands
    - 16pt minimum labels, 24pt primary info, 48pt weight display
    - Category color coding for product grid
"""

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

BG_PRIMARY = "#1a1a2e"       # deep navy, main background
BG_SECONDARY = "#16213e"     # slightly lighter, card/panel background
BG_TERTIARY = "#0f3460"      # accent background, headers
BG_INPUT = "#202040"         # input fields

TEXT_PRIMARY = "#e8e8e8"     # primary text
TEXT_SECONDARY = "#a0a0b0"   # secondary/muted text
TEXT_ACCENT = "#00d4ff"      # accent highlights
TEXT_WARNING = "#ff6b6b"     # errors, mismatches
TEXT_SUCCESS = "#51cf66"     # verified, success states

BORDER_DEFAULT = "#2a2a4a"   # default borders
BORDER_ACTIVE = "#00d4ff"    # focused/active borders

# Button colors
BTN_PRIMARY_BG = "#0f3460"
BTN_PRIMARY_HOVER = "#1a4a7a"
BTN_PRIMARY_TEXT = "#ffffff"

BTN_SUCCESS_BG = "#2d6a2d"
BTN_SUCCESS_HOVER = "#3d8a3d"
BTN_SUCCESS_TEXT = "#ffffff"

BTN_DANGER_BG = "#6a2d2d"
BTN_DANGER_HOVER = "#8a3d3d"
BTN_DANGER_TEXT = "#ffffff"

BTN_SECONDARY_BG = "#2a2a4a"
BTN_SECONDARY_HOVER = "#3a3a5a"
BTN_SECONDARY_TEXT = "#e8e8e8"

# Category colors for product grid
CATEGORY_COLORS = {
    "Steaks": {"bg": "#4a1a1a", "hover": "#6a2a2a", "accent": "#ff6b6b"},
    "Roasts": {"bg": "#3a2a1a", "hover": "#5a3a2a", "accent": "#e8a850"},
    "Ground": {"bg": "#2a2a2a", "hover": "#3a3a3a", "accent": "#a0a0a0"},
    "Offal/Specialty": {"bg": "#1a2a3a", "hover": "#2a3a4a", "accent": "#6bb5ff"},
    "Bones": {"bg": "#2a2a1a", "hover": "#3a3a2a", "accent": "#d4c090"},
    "Sausage/Processed": {"bg": "#2a1a2a", "hover": "#3a2a3a", "accent": "#c090d4"},
}

# Workflow state colors
STATE_COLORS = {
    "idle": TEXT_SECONDARY,
    "product_selected": "#00d4ff",
    "weight_captured": "#ffa500",
    "label_printed": "#e8a850",
    "awaiting_scan": "#ff6b6b",
    "verified": "#51cf66",
}

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

FONT_FAMILY = "Segoe UI"  # Windows default; fallback handled by Tk

FONT_WEIGHT_DISPLAY = (FONT_FAMILY, 48, "bold")   # scale weight readout
FONT_HEADING_LARGE = (FONT_FAMILY, 32, "bold")     # screen titles
FONT_HEADING = (FONT_FAMILY, 24, "bold")            # section headings, primary info
FONT_BODY_LARGE = (FONT_FAMILY, 20)                 # product buttons, important text
FONT_BODY = (FONT_FAMILY, 16)                       # standard labels, descriptions
FONT_SMALL = (FONT_FAMILY, 14)                      # secondary info, timestamps
FONT_MONO = ("Consolas", 18)                         # barcodes, SKU codes

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

TOUCH_TARGET_MIN = 80        # minimum height in pixels for touch targets
TOUCH_TARGET_LARGE = 100     # large buttons (Print, Verify)
BUTTON_CORNER_RADIUS = 8     # rounded corners
PADDING_SMALL = 8
PADDING_MEDIUM = 16
PADDING_LARGE = 24
GRID_GAP = 12                # gap between product grid buttons
TAB_HEIGHT = 60              # category tab bar height

# Product grid
PRODUCT_GRID_COLUMNS = 3     # columns in product grid (17" screen)
PRODUCT_BUTTON_HEIGHT = 90   # height of each product button


def get_category_color(category_name: str) -> dict:
    """Get color scheme for a product category.

    Maps product categories from the database to UI color groups.
    """
    # Map database categories to UI groups
    CATEGORY_MAP = {
        "Beef": "Steaks",  # default; overridden per subcategory below
    }

    # Try direct match first, then mapped, then default
    if category_name in CATEGORY_COLORS:
        return CATEGORY_COLORS[category_name]
    mapped = CATEGORY_MAP.get(category_name, "Steaks")
    return CATEGORY_COLORS.get(mapped, CATEGORY_COLORS["Steaks"])


# SKU-based category assignment for the product grid
# These ranges are based on the Pomponio price sheet structure
def classify_product(sku: str, name: str) -> str:
    """Classify a product into a UI category based on SKU and name.

    Returns one of: Steaks, Roasts, Ground, Offal/Specialty, Bones, Sausage/Processed.
    """
    name_lower = name.lower()

    # Bones
    if any(k in name_lower for k in ["bone", "marrow", "stock bone"]):
        if "steak" not in name_lower and "short rib" not in name_lower and "prime rib" not in name_lower:
            return "Bones"

    # Ground and burger
    if any(k in name_lower for k in ["ground", "burger", "patties", "patty"]):
        return "Ground"

    # Sausage and processed
    if any(k in name_lower for k in [
        "sausage", "chorizo", "hot dog", "bacon", "jerky", "summer", "trim"
    ]):
        return "Sausage/Processed"

    # Offal and specialty
    if any(k in name_lower for k in [
        "liver", "heart", "kidney", "tongue", "cheek", "oxtail",
        "sweet bread", "tendon", "navel", "fat",
    ]):
        return "Offal/Specialty"

    # Roasts
    if any(k in name_lower for k in [
        "roast", "brisket", "prime rib", "tri-tip", "picanha roast",
    ]):
        return "Roasts"

    # Everything else is a steak
    return "Steaks"
