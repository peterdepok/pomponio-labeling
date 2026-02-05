"""
Main application window for Pomponio Ranch Labeling System.
Combines all screens with tab navigation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
import sys

from ..database import init_database
from ..scale import Scale, MockScale
from ..printer import ZebraPrinter, MockPrinter
from ..scanner import TkinterScannerHandler, ScanEvent, MockScanner
from .widgets import COLORS, FONT_MEDIUM, FONT_SMALL, TouchButton
from .labeling import LabelingScreen
from .boxes import BoxesScreen
from .orders import OrdersScreen


class PomponioApp:
    """
    Main application class.

    Manages:
    - Root window and tab navigation
    - Hardware connections (scale, printer, scanner)
    - Routing scan events to active screen
    """

    def __init__(
        self,
        scale_port: Optional[str] = None,
        printer_port: Optional[str] = None,
        printer_host: Optional[str] = None,
        mock_hardware: bool = False
    ):
        """
        Initialize the application.

        Args:
            scale_port: Serial port for USB scale
            printer_port: Serial port for Zebra printer (USB)
            printer_host: IP address for Zebra printer (network)
            mock_hardware: Use mock hardware for testing
        """
        # Initialize database
        init_database()

        # Create root window
        self.root = tk.Tk()
        self.root.title("Pomponio Ranch Labeling System")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 768)
        self.root.config(bg=COLORS['bg'])

        # For touchscreen: maximize on start
        try:
            self.root.state('zoomed')  # Windows
        except tk.TclError:
            try:
                self.root.attributes('-zoomed', True)  # Linux
            except tk.TclError:
                pass  # macOS doesn't support this

        # Initialize hardware
        if mock_hardware:
            self.scale = MockScale()
            self.printer = MockPrinter()
        else:
            self.scale = Scale(port=scale_port) if scale_port else MockScale()
            if printer_host:
                self.printer = ZebraPrinter(host=printer_host)
            elif printer_port:
                self.printer = ZebraPrinter(port=printer_port)
            else:
                self.printer = MockPrinter()

        # Scanner handler
        self.scanner_handler: Optional[TkinterScannerHandler] = None

        # Build UI
        self._build_ui()

        # Setup scanner
        self._setup_scanner()

        # Bind close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Build the main application UI."""
        # Header
        header = tk.Frame(self.root, bg=COLORS['primary'], height=60)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="POMPONIO RANCH",
            font=('Segoe UI', 20, 'bold'),
            bg=COLORS['primary'],
            fg='white'
        ).pack(side='left', padx=20, pady=15)

        # Connection status indicators
        status_frame = tk.Frame(header, bg=COLORS['primary'])
        status_frame.pack(side='right', padx=20)

        # Scale status
        self.scale_status = tk.Label(
            status_frame,
            text="SCALE",
            font=FONT_SMALL,
            bg=COLORS['primary'],
            fg='white',
            padx=10
        )
        self.scale_status.pack(side='left', padx=5)

        # Printer status
        self.printer_status = tk.Label(
            status_frame,
            text="PRINTER",
            font=FONT_SMALL,
            bg=COLORS['primary'],
            fg='white',
            padx=10
        )
        self.printer_status.pack(side='left', padx=5)

        # Tab navigation
        tab_frame = tk.Frame(self.root, bg=COLORS['bg'])
        tab_frame.pack(fill='x', padx=20, pady=10)

        self.tab_buttons = {}
        self.current_tab = None

        tabs = [
            ('labeling', 'LABELING'),
            ('boxes', 'BOXES'),
            ('orders', 'ORDERS')
        ]

        for tab_id, tab_name in tabs:
            btn = tk.Button(
                tab_frame,
                text=tab_name,
                font=FONT_MEDIUM,
                bg=COLORS['bg'],
                fg=COLORS['fg'],
                activebackground=COLORS['primary'],
                activeforeground='white',
                relief='flat',
                cursor='hand2',
                padx=30,
                pady=10,
                command=lambda t=tab_id: self._select_tab(t)
            )
            btn.pack(side='left', padx=5)
            self.tab_buttons[tab_id] = btn

        # Content area
        self.content = tk.Frame(self.root, bg=COLORS['bg'])
        self.content.pack(fill='both', expand=True)

        # Create screens (lazy loading would be better for large apps)
        self.screens = {}
        self.screens['labeling'] = LabelingScreen(
            self.content,
            scale=self.scale,
            printer=self.printer
        )
        self.screens['boxes'] = BoxesScreen(
            self.content,
            printer=self.printer
        )
        self.screens['orders'] = OrdersScreen(
            self.content,
            printer=self.printer
        )

        # Select default tab
        self._select_tab('labeling')

        # Update status indicators
        self._update_status_indicators()

    def _select_tab(self, tab_id: str):
        """Select and display a tab."""
        if tab_id == self.current_tab:
            return

        # Update button styling
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.config(bg=COLORS['primary'], fg='white')
            else:
                btn.config(bg=COLORS['bg'], fg=COLORS['fg'])

        # Hide current screen
        if self.current_tab and self.current_tab in self.screens:
            self.screens[self.current_tab].pack_forget()

        # Show new screen
        self.current_tab = tab_id
        if tab_id in self.screens:
            self.screens[tab_id].pack(fill='both', expand=True)
            # Refresh screen data
            if hasattr(self.screens[tab_id], 'refresh'):
                self.screens[tab_id].refresh()

    def _setup_scanner(self):
        """Setup barcode scanner input handling."""
        self.scanner_handler = TkinterScannerHandler(
            self.root,
            on_scan=self._on_scan,
            min_length=8
        )
        self.scanner_handler.bind()

    def _on_scan(self, event: ScanEvent):
        """Route scan event to active screen."""
        screen = self.screens.get(self.current_tab)
        if screen and hasattr(screen, 'handle_scan'):
            screen.handle_scan(event)

    def _update_status_indicators(self):
        """Update hardware status indicators."""
        # Scale
        if isinstance(self.scale, MockScale):
            self.scale_status.config(bg='#6b7280')  # Gray for mock
        elif self.scale.is_connected():
            self.scale_status.config(bg=COLORS['success'])
        else:
            self.scale_status.config(bg=COLORS['error'])

        # Printer
        if isinstance(self.printer, MockPrinter):
            self.printer_status.config(bg='#6b7280')  # Gray for mock
        elif self.printer.is_connected():
            self.printer_status.config(bg=COLORS['success'])
        else:
            self.printer_status.config(bg=COLORS['error'])

        # Schedule next update
        self.root.after(5000, self._update_status_indicators)

    def _on_close(self):
        """Handle application close."""
        # Cleanup
        if hasattr(self.screens.get('labeling'), 'cleanup'):
            self.screens['labeling'].cleanup()

        if self.printer:
            self.printer.disconnect()

        self.root.destroy()

    def run(self):
        """Run the application main loop."""
        self.root.mainloop()


def main():
    """Application entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Pomponio Ranch Labeling System')
    parser.add_argument('--scale-port', help='Serial port for USB scale')
    parser.add_argument('--printer-port', help='Serial port for Zebra printer')
    parser.add_argument('--printer-host', help='IP address for network Zebra printer')
    parser.add_argument('--mock', action='store_true', help='Use mock hardware for testing')
    args = parser.parse_args()

    app = PomponioApp(
        scale_port=args.scale_port,
        printer_port=args.printer_port,
        printer_host=args.printer_host,
        mock_hardware=args.mock
    )
    app.run()


if __name__ == '__main__':
    main()
