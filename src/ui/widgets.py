"""
Touch-optimized custom widgets for Pomponio Ranch labeling system.
Designed for glove-friendly operation with 60px minimum touch targets.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


# Color scheme
COLORS = {
    'bg': '#f5f5f5',
    'fg': '#1a1a1a',
    'primary': '#2563eb',
    'primary_hover': '#1d4ed8',
    'success': '#16a34a',
    'success_bg': '#dcfce7',
    'error': '#dc2626',
    'error_bg': '#fee2e2',
    'warning': '#ca8a04',
    'warning_bg': '#fef9c3',
    'border': '#d1d5db',
    'card_bg': '#ffffff',
    'disabled': '#9ca3af',
}

# Touch-friendly dimensions
MIN_TOUCH_TARGET = 60
BUTTON_PADDING = 15
FONT_LARGE = ('Segoe UI', 24, 'bold')
FONT_MEDIUM = ('Segoe UI', 18)
FONT_SMALL = ('Segoe UI', 14)
FONT_MONO = ('Consolas', 16)


class TouchButton(tk.Button):
    """
    Large touch-friendly button.
    Minimum 60px height for glove operation.
    """

    def __init__(
        self,
        parent,
        text: str,
        command: Callable = None,
        style: str = 'default',
        width: int = None,
        **kwargs
    ):
        bg_color = {
            'default': COLORS['primary'],
            'success': COLORS['success'],
            'error': COLORS['error'],
            'warning': COLORS['warning'],
        }.get(style, COLORS['primary'])

        super().__init__(
            parent,
            text=text,
            command=command,
            font=FONT_MEDIUM,
            bg=bg_color,
            fg='white',
            activebackground=self._darken(bg_color),
            activeforeground='white',
            relief='flat',
            cursor='hand2',
            padx=BUTTON_PADDING,
            pady=BUTTON_PADDING,
            **kwargs
        )

        if width:
            self.config(width=width)

        # Ensure minimum touch target
        self.bind('<Configure>', self._ensure_min_height)

    def _ensure_min_height(self, event):
        if event.height < MIN_TOUCH_TARGET:
            self.config(height=2)

    @staticmethod
    def _darken(color: str) -> str:
        """Darken a hex color by 15%."""
        color = color.lstrip('#')
        r, g, b = int(color[:2], 16), int(color[2:4], 16), int(color[4:], 16)
        factor = 0.85
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f'#{r:02x}{g:02x}{b:02x}'


class ProductButton(tk.Frame):
    """
    Product selection button for the product grid.
    Shows product name and price, with large touch target.
    """

    def __init__(
        self,
        parent,
        product_name: str,
        price_per_lb: float,
        on_select: Callable = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.on_select = on_select
        self._selected = False

        self.config(
            bg=COLORS['card_bg'],
            relief='solid',
            bd=1,
            cursor='hand2'
        )

        # Name label
        self.name_label = tk.Label(
            self,
            text=product_name,
            font=FONT_MEDIUM,
            bg=COLORS['card_bg'],
            fg=COLORS['fg'],
            wraplength=180
        )
        self.name_label.pack(pady=(15, 5), padx=10)

        # Price label
        self.price_label = tk.Label(
            self,
            text=f"${price_per_lb:.2f}/lb",
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=COLORS['disabled']
        )
        self.price_label.pack(pady=(0, 15))

        # Bind click to all elements
        for widget in [self, self.name_label, self.price_label]:
            widget.bind('<Button-1>', self._on_click)
            widget.bind('<Enter>', self._on_enter)
            widget.bind('<Leave>', self._on_leave)

    def _on_click(self, event):
        if self.on_select:
            self.on_select()

    def _on_enter(self, event):
        if not self._selected:
            self.config(bg=COLORS['bg'])
            self.name_label.config(bg=COLORS['bg'])
            self.price_label.config(bg=COLORS['bg'])

    def _on_leave(self, event):
        if not self._selected:
            self.config(bg=COLORS['card_bg'])
            self.name_label.config(bg=COLORS['card_bg'])
            self.price_label.config(bg=COLORS['card_bg'])

    def set_selected(self, selected: bool):
        """Set selection state."""
        self._selected = selected
        bg = COLORS['primary'] if selected else COLORS['card_bg']
        fg = 'white' if selected else COLORS['fg']
        price_fg = 'white' if selected else COLORS['disabled']

        self.config(bg=bg)
        self.name_label.config(bg=bg, fg=fg)
        self.price_label.config(bg=bg, fg=price_fg)


class WeightDisplay(tk.Frame):
    """
    Large weight display with stability indicator.
    Shows current scale reading prominently.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS['card_bg'], relief='solid', bd=1)

        # Title
        tk.Label(
            self,
            text="WEIGHT",
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=COLORS['disabled']
        ).pack(pady=(15, 5))

        # Weight value
        self.weight_var = tk.StringVar(value="0.00")
        self.weight_label = tk.Label(
            self,
            textvariable=self.weight_var,
            font=('Segoe UI', 48, 'bold'),
            bg=COLORS['card_bg'],
            fg=COLORS['fg']
        )
        self.weight_label.pack()

        # Unit label
        tk.Label(
            self,
            text="LB",
            font=FONT_MEDIUM,
            bg=COLORS['card_bg'],
            fg=COLORS['disabled']
        ).pack()

        # Stability indicator
        self.stable_var = tk.StringVar(value="")
        self.stable_label = tk.Label(
            self,
            textvariable=self.stable_var,
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=COLORS['success']
        )
        self.stable_label.pack(pady=(5, 15))

    def set_weight(self, weight: float, stable: bool = True):
        """Update displayed weight."""
        self.weight_var.set(f"{weight:.2f}")
        if stable and weight > 0:
            self.stable_var.set("STABLE")
            self.stable_label.config(fg=COLORS['success'])
        elif weight > 0:
            self.stable_var.set("READING...")
            self.stable_label.config(fg=COLORS['warning'])
        else:
            self.stable_var.set("")


class StatusBar(tk.Frame):
    """
    Status bar with feedback for scans and actions.
    Provides visual and textual feedback.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS['bg'], height=80)
        self.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = tk.Label(
            self,
            textvariable=self.status_var,
            font=FONT_MEDIUM,
            bg=COLORS['bg'],
            fg=COLORS['fg']
        )
        self.status_label.pack(expand=True)

        self._flash_after_id = None

    def set_status(self, message: str, status_type: str = 'info'):
        """Set status message."""
        self._cancel_flash()

        colors = {
            'info': (COLORS['bg'], COLORS['fg']),
            'success': (COLORS['success_bg'], COLORS['success']),
            'error': (COLORS['error_bg'], COLORS['error']),
            'warning': (COLORS['warning_bg'], COLORS['warning']),
        }
        bg, fg = colors.get(status_type, colors['info'])

        self.config(bg=bg)
        self.status_label.config(bg=bg, fg=fg)
        self.status_var.set(message)

    def flash_success(self, message: str = "Success"):
        """Flash green for success."""
        self.set_status(message, 'success')
        self._flash_after_id = self.after(2000, self._reset)

    def flash_error(self, message: str = "Error"):
        """Flash red for error."""
        self.set_status(message, 'error')
        self._flash_after_id = self.after(3000, self._reset)

    def _reset(self):
        """Reset to default state."""
        self.set_status("Ready", 'info')

    def _cancel_flash(self):
        """Cancel pending flash reset."""
        if self._flash_after_id:
            self.after_cancel(self._flash_after_id)
            self._flash_after_id = None


class PackageList(tk.Frame):
    """
    Scrollable list of packages in current box.
    Shows product, weight, and verification status.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS['card_bg'], relief='solid', bd=1)

        # Header
        header = tk.Frame(self, bg=COLORS['bg'])
        header.pack(fill='x')
        tk.Label(
            header,
            text="PACKAGES IN BOX",
            font=FONT_SMALL,
            bg=COLORS['bg'],
            fg=COLORS['disabled'],
            pady=10
        ).pack()

        # Scrollable container
        self.canvas = tk.Canvas(self, bg=COLORS['card_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)

        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS['card_bg'])
        self.scroll_frame.bind(
            '<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        )

        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Touch scrolling
        self.canvas.bind('<ButtonPress-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self._drag_y = 0

        self.items = []

    def _on_press(self, event):
        self._drag_y = event.y

    def _on_drag(self, event):
        delta = self._drag_y - event.y
        self.canvas.yview_scroll(int(delta / 20), 'units')
        self._drag_y = event.y

    def add_package(self, product_name: str, weight: float, verified: bool = False):
        """Add package to list."""
        row = tk.Frame(self.scroll_frame, bg=COLORS['card_bg'])
        row.pack(fill='x', padx=10, pady=5)

        # Product name
        tk.Label(
            row,
            text=product_name,
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=COLORS['fg'],
            anchor='w',
            width=20
        ).pack(side='left')

        # Weight
        tk.Label(
            row,
            text=f"{weight:.2f} lb",
            font=FONT_MONO,
            bg=COLORS['card_bg'],
            fg=COLORS['fg']
        ).pack(side='left', padx=10)

        # Verification status
        status_text = "OK" if verified else ""
        status_color = COLORS['success'] if verified else COLORS['disabled']
        tk.Label(
            row,
            text=status_text,
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=status_color
        ).pack(side='right')

        self.items.append(row)

    def clear(self):
        """Clear all packages from list."""
        for item in self.items:
            item.destroy()
        self.items.clear()


class BoxSummary(tk.Frame):
    """
    Summary display for current box.
    Shows box number, count, and total weight.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS['card_bg'], relief='solid', bd=1)

        # Box number
        self.box_var = tk.StringVar(value="No Active Box")
        tk.Label(
            self,
            textvariable=self.box_var,
            font=FONT_MEDIUM,
            bg=COLORS['card_bg'],
            fg=COLORS['fg']
        ).pack(pady=(15, 10))

        # Stats row
        stats = tk.Frame(self, bg=COLORS['card_bg'])
        stats.pack(fill='x', padx=20, pady=(0, 15))

        # Count
        count_frame = tk.Frame(stats, bg=COLORS['card_bg'])
        count_frame.pack(side='left', expand=True)
        tk.Label(
            count_frame,
            text="Packages",
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=COLORS['disabled']
        ).pack()
        self.count_var = tk.StringVar(value="0")
        tk.Label(
            count_frame,
            textvariable=self.count_var,
            font=FONT_LARGE,
            bg=COLORS['card_bg'],
            fg=COLORS['fg']
        ).pack()

        # Weight
        weight_frame = tk.Frame(stats, bg=COLORS['card_bg'])
        weight_frame.pack(side='left', expand=True)
        tk.Label(
            weight_frame,
            text="Total Weight",
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=COLORS['disabled']
        ).pack()
        self.weight_var = tk.StringVar(value="0.00 lb")
        tk.Label(
            weight_frame,
            textvariable=self.weight_var,
            font=FONT_LARGE,
            bg=COLORS['card_bg'],
            fg=COLORS['fg']
        ).pack()

    def set_box(self, box_number: Optional[str], count: int = 0, weight: float = 0.0):
        """Update box display."""
        if box_number:
            self.box_var.set(f"Box: {box_number}")
        else:
            self.box_var.set("No Active Box")
        self.count_var.set(str(count))
        self.weight_var.set(f"{weight:.2f} lb")


class VerificationPopup(tk.Toplevel):
    """
    Full-screen verification overlay.
    Shows success (green) or failure (red) feedback.
    """

    def __init__(
        self,
        parent,
        success: bool,
        message: str,
        duration_ms: int = 1500
    ):
        super().__init__(parent)

        self.overrideredirect(True)
        self.attributes('-topmost', True)

        # Full screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")

        bg_color = COLORS['success_bg'] if success else COLORS['error_bg']
        fg_color = COLORS['success'] if success else COLORS['error']
        icon = "OK" if success else "X"

        self.config(bg=bg_color)

        # Center content
        content = tk.Frame(self, bg=bg_color)
        content.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(
            content,
            text=icon,
            font=('Segoe UI', 120, 'bold'),
            bg=bg_color,
            fg=fg_color
        ).pack()

        tk.Label(
            content,
            text=message,
            font=FONT_LARGE,
            bg=bg_color,
            fg=fg_color
        ).pack(pady=20)

        # Auto-close
        self.after(duration_ms, self.destroy)

        # Click to dismiss
        self.bind('<Button-1>', lambda e: self.destroy())


def show_verification(parent, success: bool, message: str):
    """Show verification popup."""
    VerificationPopup(parent, success, message)
