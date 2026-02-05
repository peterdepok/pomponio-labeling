"""
Theme and styling constants for Pomponio Ranch UI.
Modern, sleek design optimized for touchscreen workers with gloves.
"""

# Color Palette - Modern dark theme with high contrast
COLORS = {
    # Backgrounds - Rich dark tones
    'bg_dark': '#0f0f0f',           # Near black
    'bg_medium': '#1a1a1a',         # Dark gray
    'bg_light': '#2a2a2a',          # Medium gray
    'bg_card': '#252525',           # Card background
    'bg_elevated': '#333333',       # Elevated surfaces

    # Text - High contrast
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'text_muted': '#707070',
    'text_inverse': '#000000',

    # Primary - Vibrant blue
    'primary': '#3b82f6',
    'primary_hover': '#60a5fa',
    'primary_dark': '#2563eb',
    'primary_glow': '#3b82f640',

    # Success - Bright green
    'success': '#22c55e',
    'success_bg': '#14532d',
    'success_light': '#4ade80',
    'success_glow': '#22c55e40',

    # Error - Vivid red
    'error': '#ef4444',
    'error_bg': '#7f1d1d',
    'error_light': '#f87171',
    'error_glow': '#ef444440',

    # Warning - Bright amber
    'warning': '#f59e0b',
    'warning_bg': '#78350f',
    'warning_light': '#fbbf24',

    # Category colors - Vibrant, easily distinguishable
    'cat_rib': '#ef4444',           # Red
    'cat_loin': '#f97316',          # Orange
    'cat_sirloin': '#eab308',       # Yellow
    'cat_round': '#22c55e',         # Green
    'cat_chuck': '#14b8a6',         # Teal
    'cat_brisket': '#06b6d4',       # Cyan
    'cat_plate': '#3b82f6',         # Blue
    'cat_flank': '#8b5cf6',         # Purple
    'cat_shank': '#a855f7',         # Violet
    'cat_ground': '#ec4899',        # Pink
    'cat_offal': '#f43f5e',         # Rose
    'cat_processed': '#64748b',     # Slate
    'cat_other': '#6b7280',         # Gray
}

# Category to color mapping
CATEGORY_COLORS = {
    'Rib': COLORS['cat_rib'],
    'Loin': COLORS['cat_loin'],
    'Sirloin': COLORS['cat_sirloin'],
    'Round': COLORS['cat_round'],
    'Chuck': COLORS['cat_chuck'],
    'Brisket': COLORS['cat_brisket'],
    'Plate': COLORS['cat_plate'],
    'Flank': COLORS['cat_flank'],
    'Shank': COLORS['cat_shank'],
    'Ground': COLORS['cat_ground'],
    'Stew/Kabob': COLORS['cat_ground'],
    'Offal': COLORS['cat_offal'],
    'Rendered': COLORS['cat_offal'],
    'Processed': COLORS['cat_processed'],
    'Whole/Half': COLORS['cat_other'],
}

# Typography - Large, clear, bold for visibility
FONTS = {
    'heading_xl': ('Segoe UI', 56, 'bold'),
    'heading_lg': ('Segoe UI', 40, 'bold'),
    'heading_md': ('Segoe UI', 32, 'bold'),
    'heading_sm': ('Segoe UI', 24, 'bold'),
    'body_xl': ('Segoe UI', 22),
    'body_lg': ('Segoe UI', 20),
    'body_md': ('Segoe UI', 18),
    'body_sm': ('Segoe UI', 16),
    'mono_lg': ('Consolas', 28, 'bold'),
    'mono_md': ('Consolas', 22),
    'mono_sm': ('Consolas', 18),
    'weight_display': ('Segoe UI', 96, 'bold'),
    'button': ('Segoe UI', 22, 'bold'),
    'button_lg': ('Segoe UI', 28, 'bold'),
    'button_sm': ('Segoe UI', 18, 'bold'),
    'label': ('Segoe UI', 14),
    'product_name': ('Segoe UI', 18, 'bold'),
    'product_price': ('Segoe UI', 16),
}

# Sizing - Extra large touch targets for gloved hands
SIZES = {
    'touch_target_min': 80,         # Minimum touch target (larger for gloves)
    'touch_target_lg': 100,         # Large touch target
    'button_height': 80,            # Standard button height
    'button_height_lg': 100,        # Large button height
    'button_height_sm': 60,         # Small button height
    'card_padding': 24,
    'grid_gap': 16,
    'border_radius': 16,
    'border_radius_lg': 20,
    'border_radius_sm': 12,
    'product_card_width': 200,
    'product_card_height': 140,
    'category_tab_height': 56,
    'header_height': 80,
    'status_bar_height': 70,
}

# Animation timing (ms)
TIMING = {
    'flash_success': 1200,
    'flash_error': 2000,
    'status_reset': 2500,
    'weight_stable_delay': 400,
    'button_press': 100,
}

# Shadows and effects (for modern look)
EFFECTS = {
    'card_shadow': '#00000040',
    'glow_radius': 20,
    'border_width': 2,
}
