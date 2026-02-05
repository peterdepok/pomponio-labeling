"""
Modern main application using CustomTkinter.
Slick touch-optimized UI for meat processing environment.
"""

import customtkinter as ctk
from pathlib import Path
from typing import Optional

from ..database import init_database, DB_PATH
from ..scale import Scale, MockScale
from ..printer import ZebraPrinter, MockPrinter
from ..scanner import TkinterScannerHandler, ScanEvent
from ..resilience import (
    init_resilience, get_backup_manager, get_connection_manager,
    get_state_persistence, get_error_reporter, logger
)
from ..config import CONFIG_FILE, load_config
from .theme import COLORS, FONTS, SIZES
from .labeling_safe import SafeLabelingScreen
from .boxes_modern import BoxesScreenModern
from .orders_modern import OrdersScreenModern
from .setup_wizard import SetupWizard, needs_setup
from .update_dialog import check_for_updates_ui


class ModernApp:
    """
    Modern Pomponio Ranch labeling application.
    """

    def __init__(
        self,
        scale_port: Optional[str] = None,
        printer_port: Optional[str] = None,
        printer_host: Optional[str] = None,
        mock_hardware: bool = False
    ):
        # Initialize resilience (logging, backups, state persistence)
        data_dir = DB_PATH.parent
        init_resilience(data_dir)
        logger.info("Starting Pomponio Ranch Labeling System")

        # Initialize database
        init_database()

        # Create initial backup
        backup_mgr = get_backup_manager()
        if backup_mgr:
            backup_mgr.backup_now("startup")

        # Configure CustomTkinter
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create window
        self.root = ctk.CTk()
        self.root.title("Pomponio Ranch")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 768)

        # Maximize on start
        try:
            self.root.state('zoomed')
        except:
            try:
                self.root.attributes('-zoomed', True)
            except:
                pass

        # Hardware
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

        # Register hardware with connection manager for auto-reconnect
        conn_mgr = get_connection_manager()
        if conn_mgr:
            conn_mgr.register_device('scale', self.scale)
            conn_mgr.register_device('printer', self.printer)
            conn_mgr.on_disconnect(self._on_hardware_disconnect)
            conn_mgr.on_reconnect(self._on_hardware_reconnect)
            conn_mgr.on_failure(self._on_hardware_failure)
            conn_mgr.start_monitoring()

        # Build UI
        self._build_ui()

        # Scanner
        self._setup_scanner()

        # Close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # Check for updates on startup (silent, no dialog if up to date)
        self.root.after(3000, self._check_for_updates_silent)

    def _build_ui(self):
        """Build application UI."""
        # Header bar
        header = ctk.CTkFrame(self.root, fg_color=COLORS['bg_medium'], height=70)
        header.pack(fill='x')
        header.pack_propagate(False)

        # Logo / Title
        title_frame = ctk.CTkFrame(header, fg_color='transparent')
        title_frame.pack(side='left', padx=25)

        ctk.CTkLabel(
            title_frame,
            text="POMPONIO RANCH",
            font=('Segoe UI', 26, 'bold'),
            text_color=COLORS['text_primary']
        ).pack(side='left')

        ctk.CTkLabel(
            title_frame,
            text="  Labeling System",
            font=('Segoe UI', 18),
            text_color=COLORS['text_secondary']
        ).pack(side='left')

        # Status indicators
        status_frame = ctk.CTkFrame(header, fg_color='transparent')
        status_frame.pack(side='right', padx=25)

        # Scale indicator
        scale_frame = ctk.CTkFrame(status_frame, fg_color='transparent')
        scale_frame.pack(side='left', padx=15)

        self.scale_indicator = ctk.CTkLabel(
            scale_frame,
            text="●",
            font=('Segoe UI', 20),
            text_color=COLORS['text_muted']
        )
        self.scale_indicator.pack(side='left')

        ctk.CTkLabel(
            scale_frame,
            text=" SCALE",
            font=FONTS['body_sm'],
            text_color=COLORS['text_secondary']
        ).pack(side='left')

        # Printer indicator
        printer_frame = ctk.CTkFrame(status_frame, fg_color='transparent')
        printer_frame.pack(side='left', padx=15)

        self.printer_indicator = ctk.CTkLabel(
            printer_frame,
            text="●",
            font=('Segoe UI', 20),
            text_color=COLORS['text_muted']
        )
        self.printer_indicator.pack(side='left')

        ctk.CTkLabel(
            printer_frame,
            text=" PRINTER",
            font=FONTS['body_sm'],
            text_color=COLORS['text_secondary']
        ).pack(side='left')

        # Settings button
        settings_btn = ctk.CTkButton(
            status_frame,
            text="⚙",
            font=('Segoe UI', 18),
            fg_color='transparent',
            hover_color=COLORS['bg_light'],
            text_color=COLORS['text_secondary'],
            width=45,
            height=45,
            corner_radius=8,
            command=self._open_settings
        )
        settings_btn.pack(side='left', padx=(20, 0))

        # Navigation tabs
        nav = ctk.CTkFrame(self.root, fg_color=COLORS['bg_dark'], height=70)
        nav.pack(fill='x')
        nav.pack_propagate(False)

        nav_inner = ctk.CTkFrame(nav, fg_color='transparent')
        nav_inner.pack(expand=True)

        self.tab_buttons = {}
        tabs = [
            ('labeling', 'LABELING', '📦'),
            ('boxes', 'BOXES', '📋'),
            ('orders', 'ORDERS', '🚚'),
        ]

        for tab_id, tab_name, icon in tabs:
            btn = ctk.CTkButton(
                nav_inner,
                text=f"  {tab_name}",
                font=FONTS['button'],
                fg_color='transparent',
                hover_color=COLORS['bg_light'],
                text_color=COLORS['text_secondary'],
                height=55,
                width=180,
                corner_radius=10,
                command=lambda t=tab_id: self._select_tab(t)
            )
            btn.pack(side='left', padx=8)
            self.tab_buttons[tab_id] = btn

        # Content area
        self.content = ctk.CTkFrame(self.root, fg_color=COLORS['bg_dark'])
        self.content.pack(fill='both', expand=True)

        # Create screens
        self.screens = {}
        self.screens['labeling'] = SafeLabelingScreen(
            self.content,
            scale=self.scale,
            printer=self.printer
        )
        self.screens['boxes'] = BoxesScreenModern(
            self.content,
            printer=self.printer
        )
        self.screens['orders'] = OrdersScreenModern(
            self.content,
            printer=self.printer
        )

        self.current_tab = None
        self._select_tab('labeling')

        # Update indicators
        self._update_indicators()

    def _select_tab(self, tab_id: str):
        """Select tab."""
        if tab_id == self.current_tab:
            return

        # Update button styles
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color=COLORS['primary'],
                    text_color=COLORS['text_primary']
                )
            else:
                btn.configure(
                    fg_color='transparent',
                    text_color=COLORS['text_secondary']
                )

        # Hide current
        if self.current_tab and self.current_tab in self.screens:
            self.screens[self.current_tab].pack_forget()

        # Show new
        self.current_tab = tab_id
        if tab_id in self.screens:
            self.screens[tab_id].pack(fill='both', expand=True)
            if hasattr(self.screens[tab_id], 'refresh'):
                self.screens[tab_id].refresh()

    def _setup_scanner(self):
        """Setup scanner."""
        self.scanner = TkinterScannerHandler(
            self.root,
            on_scan=self._on_scan,
            min_length=8
        )
        self.scanner.bind()

    def _on_scan(self, event: ScanEvent):
        """Route scan to active screen."""
        screen = self.screens.get(self.current_tab)
        if screen and hasattr(screen, 'handle_scan'):
            screen.handle_scan(event)

    def _update_indicators(self):
        """Update hardware indicators."""
        # Scale
        if isinstance(self.scale, MockScale):
            self.scale_indicator.configure(text_color='#6b7280')
        elif self.scale.is_connected():
            self.scale_indicator.configure(text_color=COLORS['success'])
        else:
            self.scale_indicator.configure(text_color=COLORS['error'])

        # Printer
        if isinstance(self.printer, MockPrinter):
            self.printer_indicator.configure(text_color='#6b7280')
        elif self.printer.is_connected():
            self.printer_indicator.configure(text_color=COLORS['success'])
        else:
            self.printer_indicator.configure(text_color=COLORS['error'])

        # Schedule next update
        self.root.after(5000, self._update_indicators)

    def _on_hardware_disconnect(self, device_name: str):
        """Handle hardware disconnection."""
        logger.warning(f"Hardware disconnected: {device_name}")
        # Update indicator immediately
        self.root.after(0, self._update_indicators)
        # Flash warning
        if hasattr(self, 'screens') and 'labeling' in self.screens:
            screen = self.screens['labeling']
            if hasattr(screen, 'show_warning'):
                self.root.after(0, lambda: screen.show_warning(
                    f"{device_name.upper()} disconnected, reconnecting..."
                ))

    def _on_hardware_reconnect(self, device_name: str):
        """Handle hardware reconnection."""
        logger.info(f"Hardware reconnected: {device_name}")
        self.root.after(0, self._update_indicators)
        if hasattr(self, 'screens') and 'labeling' in self.screens:
            screen = self.screens['labeling']
            if hasattr(screen, 'show_success'):
                self.root.after(0, lambda: screen.show_success(
                    f"{device_name.upper()} reconnected"
                ))

    def _on_hardware_failure(self, device_name: str):
        """Handle permanent hardware failure."""
        logger.error(f"Hardware failed to reconnect: {device_name}")
        self.root.after(0, self._update_indicators)
        # Show persistent error
        if hasattr(self, 'screens') and 'labeling' in self.screens:
            screen = self.screens['labeling']
            if hasattr(screen, 'show_error'):
                self.root.after(0, lambda: screen.show_error(
                    f"{device_name.upper()} connection failed. Check hardware."
                ))

    def _open_settings(self):
        """Open settings wizard."""
        def on_settings_complete():
            # Reload config and show message
            if hasattr(self, 'screens') and 'labeling' in self.screens:
                screen = self.screens['labeling']
                if hasattr(screen, 'status_bar'):
                    screen.status_bar.flash_success("Settings saved. Restart app to apply hardware changes.")

        SetupWizard(self.root, CONFIG_FILE, on_complete=on_settings_complete)

    def _check_for_updates_silent(self):
        """Check for updates silently on startup."""
        check_for_updates_ui(self.root, silent=True)

    def check_for_updates(self):
        """Check for updates with UI feedback (user-initiated)."""
        check_for_updates_ui(self.root, silent=False)

    def _on_close(self):
        """Handle close."""
        logger.info("Application closing")

        # Stop hardware monitoring
        conn_mgr = get_connection_manager()
        if conn_mgr:
            conn_mgr.stop_monitoring()

        # Final backup before close
        backup_mgr = get_backup_manager()
        if backup_mgr:
            backup_mgr.backup_now("shutdown")

        # Cleanup screens
        if hasattr(self.screens.get('labeling'), 'cleanup'):
            self.screens['labeling'].cleanup()
        if self.printer:
            self.printer.disconnect()

        logger.info("Application closed normally")
        self.root.destroy()

    def run(self):
        """Run application."""
        self.root.mainloop()


def main():
    """Entry point with automatic first-run setup."""
    import argparse

    parser = argparse.ArgumentParser(description='Pomponio Ranch Labeling System')
    parser.add_argument('--scale-port', help='Scale serial port')
    parser.add_argument('--printer-port', help='Printer serial port')
    parser.add_argument('--printer-host', help='Printer network address')
    parser.add_argument('--mock', action='store_true', help='Use mock hardware')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    args = parser.parse_args()

    # Check if setup is needed or requested
    if args.setup or needs_setup(CONFIG_FILE):
        # Run setup wizard first
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        root = ctk.CTk()
        root.withdraw()  # Hide main window during setup

        def on_setup_complete():
            root.destroy()
            # Restart with config
            _run_app_with_config(args)

        wizard = SetupWizard(root, CONFIG_FILE, on_complete=on_setup_complete)
        root.mainloop()
    else:
        _run_app_with_config(args)


def _run_app_with_config(args):
    """Run app using config file settings."""
    # Load config
    config = load_config()

    # Command line args override config
    scale_port = args.scale_port or config.hardware.scale_port
    printer_port = args.printer_port or config.hardware.printer_port
    printer_host = args.printer_host or config.hardware.printer_host

    # Determine mock mode
    mock_hardware = args.mock
    if not mock_hardware:
        # If no hardware configured, use mock
        if config.hardware.printer_type == 'mock':
            mock_hardware = True

    app = ModernApp(
        scale_port=scale_port,
        printer_port=printer_port,
        printer_host=printer_host,
        mock_hardware=mock_hardware
    )
    app.run()


if __name__ == '__main__':
    main()
