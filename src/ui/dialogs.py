"""
Confirmation dialogs and alerts for bullet-proof operation.
Large, clear, impossible to miss.
"""

import customtkinter as ctk
from typing import Optional, Callable
from .theme import COLORS, FONTS


class ConfirmDialog(ctk.CTkToplevel):
    """
    Large confirmation dialog.
    Requires explicit button press - no accidental confirms.
    """

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        confirm_text: str = "CONFIRM",
        cancel_text: str = "CANCEL",
        danger: bool = False,
        on_confirm: Callable = None,
        on_cancel: Callable = None
    ):
        super().__init__(parent)

        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.result = None

        # Modal setup
        self.title(title)
        self.transient(parent)
        self.grab_set()

        # Center on screen
        width, height = 500, 350
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)

        self.configure(fg_color=COLORS['bg_dark'])

        # Content
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.pack(expand=True, fill='both', padx=30, pady=30)

        # Icon
        icon = "⚠️" if danger else "❓"
        ctk.CTkLabel(
            content,
            text=icon,
            font=('Segoe UI', 60)
        ).pack(pady=(0, 20))

        # Title
        ctk.CTkLabel(
            content,
            text=title,
            font=FONTS['heading_md'],
            text_color=COLORS['error'] if danger else COLORS['text_primary']
        ).pack()

        # Message
        ctk.CTkLabel(
            content,
            text=message,
            font=FONTS['body_lg'],
            text_color=COLORS['text_secondary'],
            wraplength=400,
            justify='center'
        ).pack(pady=20)

        # Buttons
        btn_frame = ctk.CTkFrame(content, fg_color='transparent')
        btn_frame.pack(fill='x', pady=(20, 0))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=cancel_text,
            font=FONTS['button'],
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['bg_card'],
            height=60,
            command=self._on_cancel
        )
        cancel_btn.pack(side='left', expand=True, fill='x', padx=(0, 10))

        confirm_color = COLORS['error'] if danger else COLORS['success']
        confirm_hover = COLORS['error_light'] if danger else COLORS['success_light']

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text=confirm_text,
            font=FONTS['button'],
            fg_color=confirm_color,
            hover_color=confirm_hover,
            height=60,
            command=self._on_confirm
        )
        confirm_btn.pack(side='left', expand=True, fill='x')

        # Keyboard bindings
        self.bind('<Escape>', lambda e: self._on_cancel())
        self.bind('<Return>', lambda e: self._on_confirm())

        # Focus confirm button
        confirm_btn.focus_set()

    def _on_confirm(self):
        self.result = True
        if self.on_confirm:
            self.on_confirm()
        self.destroy()

    def _on_cancel(self):
        self.result = False
        if self.on_cancel:
            self.on_cancel()
        self.destroy()


class AlertDialog(ctk.CTkToplevel):
    """
    Alert dialog for errors or important messages.
    Must be acknowledged before continuing.
    """

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        alert_type: str = 'error'  # error, warning, info, success
    ):
        super().__init__(parent)

        self.title(title)
        self.transient(parent)
        self.grab_set()

        # Center
        width, height = 450, 300
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)

        colors = {
            'error': (COLORS['error_bg'], COLORS['error'], '✗'),
            'warning': (COLORS['warning_bg'], COLORS['warning'], '⚠'),
            'info': (COLORS['bg_card'], COLORS['primary'], 'ℹ'),
            'success': (COLORS['success_bg'], COLORS['success'], '✓'),
        }

        bg, accent, icon = colors.get(alert_type, colors['info'])
        self.configure(fg_color=bg)

        # Content
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.pack(expand=True, fill='both', padx=30, pady=30)

        # Icon
        ctk.CTkLabel(
            content,
            text=icon,
            font=('Segoe UI', 80, 'bold'),
            text_color=accent
        ).pack(pady=(0, 15))

        # Title
        ctk.CTkLabel(
            content,
            text=title,
            font=FONTS['heading_md'],
            text_color=accent
        ).pack()

        # Message
        ctk.CTkLabel(
            content,
            text=message,
            font=FONTS['body_lg'],
            text_color=COLORS['text_primary'],
            wraplength=380,
            justify='center'
        ).pack(pady=15)

        # OK button
        ok_btn = ctk.CTkButton(
            content,
            text="OK",
            font=FONTS['button_lg'],
            fg_color=accent,
            height=60,
            width=200,
            command=self.destroy
        )
        ok_btn.pack(pady=(15, 0))

        # Keyboard
        self.bind('<Return>', lambda e: self.destroy())
        self.bind('<Escape>', lambda e: self.destroy())
        self.bind('<space>', lambda e: self.destroy())

        ok_btn.focus_set()


class InputDialog(ctk.CTkToplevel):
    """
    Input dialog with large touch-friendly keyboard.
    """

    def __init__(
        self,
        parent,
        title: str,
        prompt: str,
        initial_value: str = "",
        on_submit: Callable[[str], None] = None
    ):
        super().__init__(parent)

        self.on_submit = on_submit
        self.result: Optional[str] = None

        self.title(title)
        self.transient(parent)
        self.grab_set()

        # Larger for keyboard
        width, height = 600, 500
        x = (self.winfo_screenwidth() - width) // 2
        y = (self.winfo_screenheight() - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.resizable(False, False)

        self.configure(fg_color=COLORS['bg_dark'])

        # Content
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.pack(expand=True, fill='both', padx=30, pady=30)

        # Prompt
        ctk.CTkLabel(
            content,
            text=prompt,
            font=FONTS['heading_sm'],
            text_color=COLORS['text_primary']
        ).pack(pady=(0, 20))

        # Input field
        self.entry = ctk.CTkEntry(
            content,
            font=FONTS['heading_md'],
            height=60,
            placeholder_text="Type here..."
        )
        self.entry.pack(fill='x', pady=(0, 20))
        self.entry.insert(0, initial_value)

        # Simple touch keyboard
        keyboard_frame = ctk.CTkFrame(content, fg_color='transparent')
        keyboard_frame.pack(fill='x')

        # Row 1: Q-P
        row1 = "QWERTYUIOP"
        self._add_key_row(keyboard_frame, row1)

        # Row 2: A-L
        row2 = "ASDFGHJKL"
        self._add_key_row(keyboard_frame, row2)

        # Row 3: Z-M + backspace
        row3 = "ZXCVBNM"
        self._add_key_row(keyboard_frame, row3, include_backspace=True)

        # Row 4: Space and action buttons
        bottom = ctk.CTkFrame(keyboard_frame, fg_color='transparent')
        bottom.pack(fill='x', pady=5)

        ctk.CTkButton(
            bottom,
            text="SPACE",
            font=FONTS['body_md'],
            fg_color=COLORS['bg_light'],
            height=50,
            width=200,
            command=lambda: self._type_char(' ')
        ).pack(side='left', padx=2, expand=True)

        ctk.CTkButton(
            bottom,
            text="CANCEL",
            font=FONTS['body_md'],
            fg_color=COLORS['bg_light'],
            height=50,
            width=100,
            command=self._on_cancel
        ).pack(side='left', padx=2)

        ctk.CTkButton(
            bottom,
            text="OK",
            font=FONTS['button'],
            fg_color=COLORS['success'],
            height=50,
            width=100,
            command=self._on_submit
        ).pack(side='left', padx=2)

        # Keyboard bindings
        self.bind('<Return>', lambda e: self._on_submit())
        self.bind('<Escape>', lambda e: self._on_cancel())

        self.entry.focus_set()

    def _add_key_row(self, parent, keys: str, include_backspace: bool = False):
        row = ctk.CTkFrame(parent, fg_color='transparent')
        row.pack(fill='x', pady=3)

        for key in keys:
            ctk.CTkButton(
                row,
                text=key,
                font=FONTS['body_lg'],
                fg_color=COLORS['bg_card'],
                hover_color=COLORS['bg_light'],
                height=50,
                width=50,
                command=lambda k=key: self._type_char(k)
            ).pack(side='left', padx=2, expand=True)

        if include_backspace:
            ctk.CTkButton(
                row,
                text="⌫",
                font=FONTS['heading_sm'],
                fg_color=COLORS['warning'],
                height=50,
                width=70,
                command=self._backspace
            ).pack(side='left', padx=2)

    def _type_char(self, char: str):
        self.entry.insert('end', char)

    def _backspace(self):
        current = self.entry.get()
        if current:
            self.entry.delete(len(current) - 1)

    def _on_submit(self):
        self.result = self.entry.get()
        if self.on_submit:
            self.on_submit(self.result)
        self.destroy()

    def _on_cancel(self):
        self.result = None
        self.destroy()


class CountdownOverlay(ctk.CTkToplevel):
    """
    Countdown overlay for timed operations.
    Shows remaining time prominently.
    """

    def __init__(
        self,
        parent,
        message: str,
        seconds: int,
        on_timeout: Callable = None,
        on_cancel: Callable = None
    ):
        super().__init__(parent)

        self.on_timeout = on_timeout
        self.on_cancel = on_cancel
        self.remaining = seconds
        self._cancelled = False

        self.overrideredirect(True)
        self.attributes('-topmost', True)

        # Full screen semi-transparent
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{screen_w}x{screen_h}+0+0")

        self.configure(fg_color=COLORS['bg_dark'])
        self.attributes('-alpha', 0.95)

        # Content
        content = ctk.CTkFrame(self, fg_color='transparent')
        content.place(relx=0.5, rely=0.5, anchor='center')

        # Message
        ctk.CTkLabel(
            content,
            text=message,
            font=FONTS['heading_lg'],
            text_color=COLORS['text_primary']
        ).pack(pady=20)

        # Countdown
        self.countdown_label = ctk.CTkLabel(
            content,
            text=str(seconds),
            font=('Segoe UI', 120, 'bold'),
            text_color=COLORS['warning']
        )
        self.countdown_label.pack(pady=20)

        # Cancel button
        ctk.CTkButton(
            content,
            text="CANCEL",
            font=FONTS['button_lg'],
            fg_color=COLORS['error'],
            height=70,
            width=200,
            command=self._on_cancel_click
        ).pack(pady=20)

        # Start countdown
        self._tick()

    def _tick(self):
        if self._cancelled:
            return

        if self.remaining <= 0:
            if self.on_timeout:
                self.on_timeout()
            self.destroy()
            return

        self.countdown_label.configure(text=str(self.remaining))

        # Color changes as time runs out
        if self.remaining <= 5:
            self.countdown_label.configure(text_color=COLORS['error'])
        elif self.remaining <= 10:
            self.countdown_label.configure(text_color=COLORS['warning'])

        self.remaining -= 1
        self.after(1000, self._tick)

    def _on_cancel_click(self):
        self._cancelled = True
        if self.on_cancel:
            self.on_cancel()
        self.destroy()


def confirm(parent, title: str, message: str, danger: bool = False) -> bool:
    """Show confirmation dialog and return result."""
    dialog = ConfirmDialog(parent, title, message, danger=danger)
    parent.wait_window(dialog)
    return dialog.result or False


def alert(parent, title: str, message: str, alert_type: str = 'error'):
    """Show alert dialog."""
    dialog = AlertDialog(parent, title, message, alert_type)
    parent.wait_window(dialog)


def get_input(parent, title: str, prompt: str, initial: str = "") -> Optional[str]:
    """Show input dialog and return result."""
    dialog = InputDialog(parent, title, prompt, initial)
    parent.wait_window(dialog)
    return dialog.result
