"""
Modern touch-optimized widgets using CustomTkinter.
Sleek, minimal design for meat processing line workers.
Large touch targets, high contrast, glove-friendly.
"""

import customtkinter as ctk
from typing import Callable, Optional
from .theme import COLORS, FONTS, SIZES, CATEGORY_COLORS, EFFECTS


# Configure CustomTkinter defaults
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class BigButton(ctk.CTkButton):
    """
    Large touch-friendly button with modern styling.
    Minimum 80px height, bold text, rounded corners.
    """

    def __init__(
        self,
        parent,
        text: str,
        command: Callable = None,
        style: str = 'primary',
        size: str = 'normal',
        **kwargs
    ):
        colors = {
            'primary': (COLORS['primary'], COLORS['primary_hover'], COLORS['text_primary']),
            'success': (COLORS['success'], COLORS['success_light'], COLORS['text_inverse']),
            'error': (COLORS['error'], COLORS['error_light'], COLORS['text_primary']),
            'warning': (COLORS['warning'], COLORS['warning_light'], COLORS['text_inverse']),
            'secondary': (COLORS['bg_elevated'], COLORS['bg_light'], COLORS['text_primary']),
            'outline': ('transparent', COLORS['bg_light'], COLORS['text_primary']),
        }

        fg_color, hover_color, text_color = colors.get(style, colors['primary'])

        heights = {
            'small': SIZES['button_height_sm'],
            'normal': SIZES['button_height'],
            'large': SIZES['button_height_lg'],
        }
        fonts = {
            'small': FONTS['button_sm'],
            'normal': FONTS['button'],
            'large': FONTS['button_lg'],
        }

        height = heights.get(size, heights['normal'])
        font = fonts.get(size, fonts['normal'])

        # Add border for outline style
        border_width = EFFECTS['border_width'] if style == 'outline' else 0
        border_color = COLORS['primary'] if style == 'outline' else None

        super().__init__(
            parent,
            text=text.upper(),
            command=command,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            font=font,
            height=height,
            corner_radius=SIZES['border_radius'],
            border_width=border_width,
            border_color=border_color,
            **kwargs
        )


class ProductCard(ctk.CTkFrame):
    """
    Modern product selection card.
    Large touch target with category color accent and clear typography.
    """

    def __init__(
        self,
        parent,
        product_name: str,
        price_per_lb: float,
        category: str,
        on_select: Callable = None,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=SIZES['border_radius'],
            border_width=0,
            **kwargs
        )

        self.on_select = on_select
        self._selected = False
        self.category = category
        self._default_fg = COLORS['bg_card']

        # Minimum size for touch
        self.configure(width=SIZES['product_card_width'], height=SIZES['product_card_height'])

        # Category color accent bar (left side)
        cat_color = CATEGORY_COLORS.get(category, COLORS['cat_other'])
        self.color_bar = ctk.CTkFrame(
            self,
            fg_color=cat_color,
            width=8,
            corner_radius=4
        )
        self.color_bar.pack(side='left', fill='y', padx=(4, 0), pady=4)

        # Content
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.pack(fill='both', expand=True, padx=16, pady=16)

        # Product name - bold, wrapped
        self.name_label = ctk.CTkLabel(
            content,
            text=product_name,
            font=FONTS['product_name'],
            text_color=COLORS['text_primary'],
            wraplength=160,
            justify='left',
            anchor='w'
        )
        self.name_label.pack(anchor='w', fill='x')

        # Spacer
        ctk.CTkFrame(content, fg_color='transparent', height=8).pack()

        # Price - secondary color
        self.price_label = ctk.CTkLabel(
            content,
            text=f"${price_per_lb:.2f}/lb",
            font=FONTS['product_price'],
            text_color=COLORS['text_secondary'],
            anchor='w'
        )
        self.price_label.pack(anchor='w')

        # Make entire card clickable
        for widget in [self, content, self.name_label, self.price_label]:
            widget.bind('<Button-1>', self._on_click)
            widget.bind('<Enter>', self._on_hover_enter)
            widget.bind('<Leave>', self._on_hover_leave)

    def _on_click(self, event):
        if self.on_select:
            self.on_select()

    def _on_hover_enter(self, event):
        if not self._selected:
            self.configure(fg_color=COLORS['bg_elevated'])

    def _on_hover_leave(self, event):
        if not self._selected:
            self.configure(fg_color=self._default_fg)

    def set_selected(self, selected: bool):
        self._selected = selected
        if selected:
            self.configure(fg_color=COLORS['primary_dark'], border_width=3, border_color=COLORS['primary'])
            self.name_label.configure(text_color=COLORS['text_primary'])
        else:
            self.configure(fg_color=self._default_fg, border_width=0)
            self.name_label.configure(text_color=COLORS['text_primary'])


class WeightDisplay(ctk.CTkFrame):
    """
    Large, prominent weight display.
    Designed to be readable from several feet away.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=SIZES['border_radius_lg'],
            **kwargs
        )

        # Inner container with padding
        inner = ctk.CTkFrame(self, fg_color='transparent')
        inner.pack(fill='both', expand=True, padx=24, pady=20)

        # Label
        ctk.CTkLabel(
            inner,
            text="SCALE",
            font=FONTS['label'],
            text_color=COLORS['text_muted']
        ).pack(anchor='w')

        # Weight value container
        weight_row = ctk.CTkFrame(inner, fg_color='transparent')
        weight_row.pack(fill='x', pady=(8, 4))

        # Weight value - massive
        self.weight_var = ctk.StringVar(value="0.00")
        self.weight_label = ctk.CTkLabel(
            weight_row,
            textvariable=self.weight_var,
            font=FONTS['weight_display'],
            text_color=COLORS['text_primary']
        )
        self.weight_label.pack(side='left')

        # Unit
        ctk.CTkLabel(
            weight_row,
            text=" lb",
            font=FONTS['heading_lg'],
            text_color=COLORS['text_secondary']
        ).pack(side='left', anchor='s', pady=(0, 16))

        # Stability indicator
        self.stable_frame = ctk.CTkFrame(inner, fg_color='transparent')
        self.stable_frame.pack(anchor='w')

        self.stable_dot = ctk.CTkLabel(
            self.stable_frame,
            text="",
            font=('Segoe UI', 14),
            text_color=COLORS['text_muted'],
            width=20
        )
        self.stable_dot.pack(side='left')

        self.stable_text = ctk.CTkLabel(
            self.stable_frame,
            text="Place item on scale",
            font=FONTS['body_sm'],
            text_color=COLORS['text_muted']
        )
        self.stable_text.pack(side='left')

    def set_weight(self, weight: float, stable: bool = True):
        self.weight_var.set(f"{weight:.2f}")

        if weight > 0:
            if stable:
                self.weight_label.configure(text_color=COLORS['success'])
                self.stable_dot.configure(text="●", text_color=COLORS['success'])
                self.stable_text.configure(text="STABLE", text_color=COLORS['success'])
            else:
                self.weight_label.configure(text_color=COLORS['warning'])
                self.stable_dot.configure(text="◐", text_color=COLORS['warning'])
                self.stable_text.configure(text="Reading...", text_color=COLORS['warning'])
        else:
            self.weight_label.configure(text_color=COLORS['text_muted'])
            self.stable_dot.configure(text="", text_color=COLORS['text_muted'])
            self.stable_text.configure(text="Place item on scale", text_color=COLORS['text_muted'])


class StatusBar(ctk.CTkFrame):
    """
    Modern status bar with clean typography.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS['bg_medium'],
            height=SIZES['status_bar_height'],
            corner_radius=0,
            **kwargs
        )
        self.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self,
            text="Ready",
            font=FONTS['body_lg'],
            text_color=COLORS['text_secondary']
        )
        self.status_label.pack(expand=True)

        self._reset_after_id = None

    def set_status(self, message: str, status_type: str = 'info'):
        self._cancel_reset()

        colors = {
            'info': (COLORS['bg_medium'], COLORS['text_secondary']),
            'success': (COLORS['success_bg'], COLORS['success_light']),
            'error': (COLORS['error_bg'], COLORS['error_light']),
            'warning': (COLORS['warning_bg'], COLORS['warning_light']),
        }

        bg, fg = colors.get(status_type, colors['info'])
        self.configure(fg_color=bg)
        self.status_label.configure(text=message, text_color=fg)

    def flash_success(self, message: str = "Success"):
        self.set_status(message, 'success')
        self._reset_after_id = self.after(2000, self._reset)

    def flash_error(self, message: str = "Error"):
        self.set_status(message, 'error')
        self._reset_after_id = self.after(3000, self._reset)

    def _reset(self):
        self.set_status("Ready", 'info')

    def _cancel_reset(self):
        if self._reset_after_id:
            self.after_cancel(self._reset_after_id)
            self._reset_after_id = None


class BoxSummaryCard(ctk.CTkFrame):
    """
    Clean box summary with key metrics.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS['bg_card'],
            corner_radius=SIZES['border_radius'],
            **kwargs
        )

        inner = ctk.CTkFrame(self, fg_color='transparent')
        inner.pack(fill='both', expand=True, padx=20, pady=16)

        # Header row
        header = ctk.CTkFrame(inner, fg_color='transparent')
        header.pack(fill='x')

        ctk.CTkLabel(
            header,
            text="CURRENT BOX",
            font=FONTS['label'],
            text_color=COLORS['text_muted']
        ).pack(side='left')

        self.box_number_label = ctk.CTkLabel(
            header,
            text="—",
            font=FONTS['heading_sm'],
            text_color=COLORS['primary']
        )
        self.box_number_label.pack(side='right')

        # Divider
        ctk.CTkFrame(inner, fg_color=COLORS['bg_light'], height=1).pack(fill='x', pady=12)

        # Stats row
        stats = ctk.CTkFrame(inner, fg_color='transparent')
        stats.pack(fill='x')

        # Package count
        count_frame = ctk.CTkFrame(stats, fg_color='transparent')
        count_frame.pack(side='left', expand=True)

        self.count_label = ctk.CTkLabel(
            count_frame,
            text="0",
            font=FONTS['heading_lg'],
            text_color=COLORS['text_primary']
        )
        self.count_label.pack()

        ctk.CTkLabel(
            count_frame,
            text="packages",
            font=FONTS['body_sm'],
            text_color=COLORS['text_muted']
        ).pack()

        # Divider
        ctk.CTkFrame(stats, fg_color=COLORS['bg_light'], width=1).pack(side='left', fill='y', padx=20)

        # Weight
        weight_frame = ctk.CTkFrame(stats, fg_color='transparent')
        weight_frame.pack(side='left', expand=True)

        self.weight_label = ctk.CTkLabel(
            weight_frame,
            text="0.00",
            font=FONTS['heading_lg'],
            text_color=COLORS['text_primary']
        )
        self.weight_label.pack()

        ctk.CTkLabel(
            weight_frame,
            text="lbs total",
            font=FONTS['body_sm'],
            text_color=COLORS['text_muted']
        ).pack()

    def set_box(self, box_number: Optional[str], count: int = 0, weight: float = 0.0):
        if box_number:
            self.box_number_label.configure(text=box_number, text_color=COLORS['primary'])
        else:
            self.box_number_label.configure(text="No box", text_color=COLORS['text_muted'])
        self.count_label.configure(text=str(count))
        self.weight_label.configure(text=f"{weight:.1f}")


class PackageListItem(ctk.CTkFrame):
    """
    Clean package list row.
    """

    def __init__(
        self,
        parent,
        product_name: str,
        weight: float,
        verified: bool = False,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=COLORS['bg_elevated'] if verified else 'transparent',
            height=48,
            corner_radius=SIZES['border_radius_sm'],
            **kwargs
        )
        self.pack_propagate(False)

        # Verified indicator
        status_color = COLORS['success'] if verified else COLORS['text_muted']
        ctk.CTkLabel(
            self,
            text="●" if verified else "○",
            font=('Segoe UI', 12),
            text_color=status_color,
            width=24
        ).pack(side='left', padx=(12, 4))

        # Product name
        ctk.CTkLabel(
            self,
            text=product_name[:28],
            font=FONTS['body_sm'],
            text_color=COLORS['text_primary'],
            anchor='w'
        ).pack(side='left', fill='x', expand=True)

        # Weight
        ctk.CTkLabel(
            self,
            text=f"{weight:.2f} lb",
            font=FONTS['mono_sm'],
            text_color=COLORS['text_secondary'],
            width=80
        ).pack(side='right', padx=12)


class CategoryTab(ctk.CTkButton):
    """
    Modern category tab with pill shape.
    """

    def __init__(
        self,
        parent,
        text: str,
        command: Callable = None,
        **kwargs
    ):
        super().__init__(
            parent,
            text=text.upper(),
            command=command,
            fg_color='transparent',
            hover_color=COLORS['bg_elevated'],
            text_color=COLORS['text_secondary'],
            font=FONTS['button_sm'],
            height=SIZES['category_tab_height'],
            corner_radius=SIZES['category_tab_height'] // 2,
            border_width=0,
            **kwargs
        )
        self._active = False

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(
                fg_color=COLORS['primary'],
                text_color=COLORS['text_primary'],
                hover_color=COLORS['primary_hover']
            )
        else:
            self.configure(
                fg_color='transparent',
                text_color=COLORS['text_secondary'],
                hover_color=COLORS['bg_elevated']
            )


class VerificationOverlay(ctk.CTkToplevel):
    """
    Full-screen verification feedback.
    Modern, minimal design with large icon.
    """

    def __init__(
        self,
        parent,
        success: bool,
        message: str,
        duration_ms: int = 1200
    ):
        super().__init__(parent)

        # Full screen, no decorations
        self.overrideredirect(True)
        self.attributes('-topmost', True)

        # Get screen dimensions
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")

        # Colors
        if success:
            bg = COLORS['success_bg']
            accent = COLORS['success']
            icon = "✓"
        else:
            bg = COLORS['error_bg']
            accent = COLORS['error']
            icon = "✕"

        self.configure(fg_color=bg)

        # Center content
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.place(relx=0.5, rely=0.5, anchor='center')

        # Large icon in circle
        icon_frame = ctk.CTkFrame(
            content,
            fg_color=accent,
            width=200,
            height=200,
            corner_radius=100
        )
        icon_frame.pack()
        icon_frame.pack_propagate(False)

        ctk.CTkLabel(
            icon_frame,
            text=icon,
            font=('Segoe UI', 120, 'bold'),
            text_color=COLORS['text_primary'] if success else COLORS['text_primary']
        ).place(relx=0.5, rely=0.5, anchor='center')

        # Message
        ctk.CTkLabel(
            content,
            text=message.upper(),
            font=FONTS['heading_lg'],
            text_color=accent
        ).pack(pady=(40, 0))

        # Auto-close
        self.after(duration_ms, self.destroy)

        # Click to dismiss
        self.bind('<Button-1>', lambda e: self.destroy())


def show_verification(parent, success: bool, message: str):
    """Show verification overlay."""
    VerificationOverlay(parent, success, message)


class ProgressIndicator(ctk.CTkFrame):
    """
    Step progress indicator showing workflow state.
    """

    def __init__(self, parent, steps: list[tuple[str, str]], **kwargs):
        super().__init__(parent, fg_color='transparent', **kwargs)

        self.steps = steps
        self.step_widgets = {}

        for i, (step_id, step_name) in enumerate(steps):
            # Step container
            step_frame = ctk.CTkFrame(self, fg_color='transparent')
            step_frame.pack(side='left', padx=8)

            # Step number circle
            num_frame = ctk.CTkFrame(
                step_frame,
                fg_color=COLORS['bg_light'],
                width=36,
                height=36,
                corner_radius=18
            )
            num_frame.pack()
            num_frame.pack_propagate(False)

            num_label = ctk.CTkLabel(
                num_frame,
                text=str(i + 1),
                font=FONTS['button_sm'],
                text_color=COLORS['text_muted']
            )
            num_label.place(relx=0.5, rely=0.5, anchor='center')

            # Step name
            name_label = ctk.CTkLabel(
                step_frame,
                text=step_name,
                font=FONTS['body_sm'],
                text_color=COLORS['text_muted']
            )
            name_label.pack(pady=(4, 0))

            self.step_widgets[step_id] = {
                'frame': num_frame,
                'num': num_label,
                'name': name_label
            }

            # Connector line (except last)
            if i < len(steps) - 1:
                connector = ctk.CTkFrame(
                    self,
                    fg_color=COLORS['bg_light'],
                    height=2,
                    width=40
                )
                connector.pack(side='left', pady=(0, 20))

    def set_active(self, active_step: str):
        for step_id, widgets in self.step_widgets.items():
            if step_id == active_step:
                widgets['frame'].configure(fg_color=COLORS['primary'])
                widgets['num'].configure(text_color=COLORS['text_primary'])
                widgets['name'].configure(text_color=COLORS['primary'])
            else:
                widgets['frame'].configure(fg_color=COLORS['bg_light'])
                widgets['num'].configure(text_color=COLORS['text_muted'])
                widgets['name'].configure(text_color=COLORS['text_muted'])
