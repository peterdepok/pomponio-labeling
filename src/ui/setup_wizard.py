"""
First-run setup wizard for Pomponio Ranch Labeling System.
Industrial-grade configuration with hardware testing and validation.
"""

import customtkinter as ctk
import threading
import time
from pathlib import Path
from typing import Optional, Callable
import configparser

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

from .theme import COLORS, FONTS, SIZES


class SetupWizard(ctk.CTkToplevel):
    """
    Industrial-grade setup wizard.
    Tests hardware before saving, validates all inputs.
    """

    def __init__(self, parent, config_path: Path, on_complete: Callable = None):
        super().__init__(parent)

        self.config_path = config_path
        self.on_complete = on_complete
        self.config = {}
        self.test_in_progress = False

        # Window setup
        self.title("Pomponio Ranch Setup")
        self.geometry("900x700")
        self.resizable(False, False)

        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 900) // 2
        y = (self.winfo_screenheight() - 700) // 2
        self.geometry(f"+{x}+{y}")

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Prevent close during test
        self.protocol("WM_DELETE_WINDOW", self._on_close_request)

        # Build wizard pages
        self.pages = []
        self.current_page = 0

        self._build_ui()
        self._show_page(0)

    def _on_close_request(self):
        """Handle close button."""
        if self.test_in_progress:
            return  # Don't allow close during test
        self.destroy()

    def _build_ui(self):
        """Build wizard UI."""
        # Header
        header = ctk.CTkFrame(self, fg_color=COLORS['primary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="POMPONIO RANCH SETUP",
            font=('Segoe UI', 24, 'bold'),
            text_color='white'
        ).pack(expand=True)

        # Progress indicator
        self.progress_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], height=60)
        self.progress_frame.pack(fill='x')
        self.progress_frame.pack_propagate(False)

        self.progress_inner = ctk.CTkFrame(self.progress_frame, fg_color='transparent')
        self.progress_inner.pack(expand=True)

        self.step_labels = []
        steps = ['Welcome', 'Scale', 'Printer', 'Email', 'Review']
        for i, step in enumerate(steps):
            frame = ctk.CTkFrame(self.progress_inner, fg_color='transparent')
            frame.pack(side='left', padx=15)

            num = ctk.CTkLabel(
                frame,
                text=str(i + 1),
                font=('Segoe UI', 14, 'bold'),
                text_color=COLORS['text_muted'],
                width=30,
                height=30,
                corner_radius=15,
                fg_color=COLORS['bg_light']
            )
            num.pack(side='left')

            lbl = ctk.CTkLabel(
                frame,
                text=step,
                font=('Segoe UI', 13),
                text_color=COLORS['text_muted']
            )
            lbl.pack(side='left', padx=5)

            self.step_labels.append((num, lbl))

        # Content area
        self.content = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'])
        self.content.pack(fill='both', expand=True, padx=30, pady=20)

        # Create pages
        self._create_welcome_page()
        self._create_scale_page()
        self._create_printer_page()
        self._create_email_page()
        self._create_review_page()

        # Navigation buttons
        nav = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], height=80)
        nav.pack(fill='x', side='bottom')
        nav.pack_propagate(False)

        nav_inner = ctk.CTkFrame(nav, fg_color='transparent')
        nav_inner.pack(expand=True, fill='x', padx=30, pady=15)

        self.back_btn = ctk.CTkButton(
            nav_inner,
            text="← BACK",
            font=('Segoe UI', 14, 'bold'),
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['bg_card'],
            text_color=COLORS['text_secondary'],
            width=140,
            height=50,
            corner_radius=8,
            command=self._prev_page
        )
        self.back_btn.pack(side='left')

        self.skip_btn = ctk.CTkButton(
            nav_inner,
            text="SKIP",
            font=('Segoe UI', 12),
            fg_color='transparent',
            hover_color=COLORS['bg_light'],
            text_color=COLORS['text_muted'],
            width=100,
            height=40,
            command=self._skip_page
        )
        self.skip_btn.pack(side='left', padx=20)

        self.next_btn = ctk.CTkButton(
            nav_inner,
            text="NEXT →",
            font=('Segoe UI', 14, 'bold'),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            width=160,
            height=50,
            corner_radius=8,
            command=self._next_page
        )
        self.next_btn.pack(side='right')

    def _create_welcome_page(self):
        """Create welcome page."""
        page = ctk.CTkFrame(self.content, fg_color='transparent')

        # Big welcome
        ctk.CTkLabel(
            page,
            text="Welcome",
            font=('Segoe UI', 36, 'bold'),
            text_color=COLORS['text_primary']
        ).pack(pady=(50, 5))

        ctk.CTkLabel(
            page,
            text="Pomponio Ranch Labeling System",
            font=('Segoe UI', 20),
            text_color=COLORS['text_secondary']
        ).pack(pady=(0, 40))

        # What we'll configure
        config_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)
        config_frame.pack(fill='x', padx=50, pady=10)

        ctk.CTkLabel(
            config_frame,
            text="This wizard will help you configure:",
            font=('Segoe UI', 14),
            text_color=COLORS['text_secondary']
        ).pack(anchor='w', padx=25, pady=(20, 15))

        items = [
            ("🔌", "USB Scale", "For weighing packages"),
            ("🖨", "Label Printer", "Zebra ZPL printer for labels"),
            ("📧", "Email Settings", "Send manifests to back office"),
        ]

        for icon, title, desc in items:
            row = ctk.CTkFrame(config_frame, fg_color='transparent')
            row.pack(fill='x', padx=25, pady=8)

            ctk.CTkLabel(row, text=icon, font=('Segoe UI', 20), width=40).pack(side='left')
            ctk.CTkLabel(row, text=title, font=('Segoe UI', 14, 'bold'), text_color=COLORS['text_primary']).pack(side='left')
            ctk.CTkLabel(row, text=f"  {desc}", font=('Segoe UI', 12), text_color=COLORS['text_muted']).pack(side='left')

        ctk.CTkLabel(
            config_frame,
            text="",
            height=15
        ).pack()

        # Note
        ctk.CTkLabel(
            page,
            text="You can skip any step and configure later using the ⚙ button",
            font=('Segoe UI', 12),
            text_color=COLORS['text_muted']
        ).pack(pady=30)

        self.pages.append(page)

    def _create_scale_page(self):
        """Create scale configuration page with test button."""
        page = ctk.CTkFrame(self.content, fg_color='transparent')

        ctk.CTkLabel(
            page,
            text="Scale Configuration",
            font=('Segoe UI', 28, 'bold'),
            text_color=COLORS['text_primary']
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            page,
            text="Connect your USB scale and select the port below",
            font=('Segoe UI', 13),
            text_color=COLORS['text_muted']
        ).pack(pady=(0, 25))

        # Port selection card
        port_card = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)
        port_card.pack(fill='x', pady=10)

        port_inner = ctk.CTkFrame(port_card, fg_color='transparent')
        port_inner.pack(fill='x', padx=25, pady=20)

        # Port row
        port_row = ctk.CTkFrame(port_inner, fg_color='transparent')
        port_row.pack(fill='x')

        ctk.CTkLabel(
            port_row,
            text="Serial Port",
            font=('Segoe UI', 13, 'bold'),
            text_color=COLORS['text_secondary'],
            width=100,
            anchor='w'
        ).pack(side='left')

        # Detect available ports
        ports = self._get_serial_ports()
        port_options = ["None (simulated scale)"] + ports

        self.scale_port_var = ctk.StringVar(value=port_options[0])
        self.scale_port_menu = ctk.CTkOptionMenu(
            port_row,
            values=port_options,
            variable=self.scale_port_var,
            font=('Segoe UI', 13),
            width=350,
            height=45,
            corner_radius=6
        )
        self.scale_port_menu.pack(side='left', padx=10)

        # Refresh button
        ctk.CTkButton(
            port_row,
            text="🔄 Refresh",
            font=('Segoe UI', 12),
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['bg_medium'],
            text_color=COLORS['text_secondary'],
            width=100,
            height=40,
            corner_radius=6,
            command=self._refresh_scale_ports
        ).pack(side='left', padx=5)

        # Baud rate row
        baud_row = ctk.CTkFrame(port_inner, fg_color='transparent')
        baud_row.pack(fill='x', pady=(15, 0))

        ctk.CTkLabel(
            baud_row,
            text="Baud Rate",
            font=('Segoe UI', 13, 'bold'),
            text_color=COLORS['text_secondary'],
            width=100,
            anchor='w'
        ).pack(side='left')

        self.scale_baud_var = ctk.StringVar(value="9600")
        ctk.CTkOptionMenu(
            baud_row,
            values=["9600", "19200", "38400", "115200"],
            variable=self.scale_baud_var,
            font=('Segoe UI', 13),
            width=150,
            height=45,
            corner_radius=6
        ).pack(side='left', padx=10)

        ctk.CTkLabel(
            baud_row,
            text="(most scales use 9600)",
            font=('Segoe UI', 11),
            text_color=COLORS['text_muted']
        ).pack(side='left', padx=10)

        # Test section
        test_card = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)
        test_card.pack(fill='x', pady=15)

        test_inner = ctk.CTkFrame(test_card, fg_color='transparent')
        test_inner.pack(fill='x', padx=25, pady=20)

        test_row = ctk.CTkFrame(test_inner, fg_color='transparent')
        test_row.pack(fill='x')

        self.scale_test_btn = ctk.CTkButton(
            test_row,
            text="TEST CONNECTION",
            font=('Segoe UI', 13, 'bold'),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            width=180,
            height=50,
            corner_radius=8,
            command=self._test_scale
        )
        self.scale_test_btn.pack(side='left')

        self.scale_status_label = ctk.CTkLabel(
            test_row,
            text="Not tested",
            font=('Segoe UI', 13),
            text_color=COLORS['text_muted']
        )
        self.scale_status_label.pack(side='left', padx=20)

        # Result display
        self.scale_result_frame = ctk.CTkFrame(test_inner, fg_color=COLORS['bg_dark'], corner_radius=8)
        self.scale_result_frame.pack(fill='x', pady=(15, 0))

        self.scale_result_label = ctk.CTkLabel(
            self.scale_result_frame,
            text="Click TEST CONNECTION to verify your scale is working",
            font=('Courier New', 12),
            text_color=COLORS['text_muted'],
            height=60
        )
        self.scale_result_label.pack(expand=True, pady=15)

        self.pages.append(page)

    def _create_printer_page(self):
        """Create printer configuration page with test button."""
        page = ctk.CTkFrame(self.content, fg_color='transparent')

        ctk.CTkLabel(
            page,
            text="Printer Configuration",
            font=('Segoe UI', 28, 'bold'),
            text_color=COLORS['text_primary']
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            page,
            text="Configure your Zebra label printer connection",
            font=('Segoe UI', 13),
            text_color=COLORS['text_muted']
        ).pack(pady=(0, 25))

        # Connection type card
        type_card = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)
        type_card.pack(fill='x', pady=10)

        type_inner = ctk.CTkFrame(type_card, fg_color='transparent')
        type_inner.pack(fill='x', padx=25, pady=20)

        type_row = ctk.CTkFrame(type_inner, fg_color='transparent')
        type_row.pack(fill='x')

        ctk.CTkLabel(
            type_row,
            text="Connection",
            font=('Segoe UI', 13, 'bold'),
            text_color=COLORS['text_secondary'],
            width=100,
            anchor='w'
        ).pack(side='left')

        self.printer_type_var = ctk.StringVar(value="mock")

        types = [
            ("mock", "None (simulated)"),
            ("network", "Network (IP)"),
            ("serial", "USB/Serial"),
        ]

        for val, text in types:
            ctk.CTkRadioButton(
                type_row,
                text=text,
                variable=self.printer_type_var,
                value=val,
                font=('Segoe UI', 13),
                command=self._on_printer_type_change
            ).pack(side='left', padx=15)

        # Network settings frame
        self.printer_network_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)

        net_inner = ctk.CTkFrame(self.printer_network_frame, fg_color='transparent')
        net_inner.pack(fill='x', padx=25, pady=20)

        ip_row = ctk.CTkFrame(net_inner, fg_color='transparent')
        ip_row.pack(fill='x')

        ctk.CTkLabel(ip_row, text="IP Address", font=('Segoe UI', 13, 'bold'), text_color=COLORS['text_secondary'], width=100, anchor='w').pack(side='left')
        self.printer_host_var = ctk.StringVar(value="")
        ctk.CTkEntry(ip_row, textvariable=self.printer_host_var, font=('Segoe UI', 13), width=200, height=45, placeholder_text="192.168.1.100").pack(side='left', padx=10)

        ctk.CTkLabel(ip_row, text="Port", font=('Segoe UI', 13, 'bold'), text_color=COLORS['text_secondary'], width=50).pack(side='left', padx=(20, 0))
        self.printer_tcp_port_var = ctk.StringVar(value="9100")
        ctk.CTkEntry(ip_row, textvariable=self.printer_tcp_port_var, font=('Segoe UI', 13), width=100, height=45).pack(side='left', padx=10)

        # Serial settings frame
        self.printer_serial_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)

        ser_inner = ctk.CTkFrame(self.printer_serial_frame, fg_color='transparent')
        ser_inner.pack(fill='x', padx=25, pady=20)

        ser_row = ctk.CTkFrame(ser_inner, fg_color='transparent')
        ser_row.pack(fill='x')

        ctk.CTkLabel(ser_row, text="Serial Port", font=('Segoe UI', 13, 'bold'), text_color=COLORS['text_secondary'], width=100, anchor='w').pack(side='left')

        ports = self._get_serial_ports()
        port_options = ["Select port..."] + ports
        self.printer_port_var = ctk.StringVar(value=port_options[0])
        self.printer_port_menu = ctk.CTkOptionMenu(ser_row, values=port_options, variable=self.printer_port_var, font=('Segoe UI', 13), width=350, height=45).pack(side='left', padx=10)

        # Test section
        test_card = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)
        test_card.pack(fill='x', pady=15)

        test_inner = ctk.CTkFrame(test_card, fg_color='transparent')
        test_inner.pack(fill='x', padx=25, pady=20)

        test_row = ctk.CTkFrame(test_inner, fg_color='transparent')
        test_row.pack(fill='x')

        self.printer_test_btn = ctk.CTkButton(
            test_row,
            text="TEST PRINT",
            font=('Segoe UI', 13, 'bold'),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            width=180,
            height=50,
            corner_radius=8,
            command=self._test_printer
        )
        self.printer_test_btn.pack(side='left')

        self.printer_status_label = ctk.CTkLabel(
            test_row,
            text="Not tested",
            font=('Segoe UI', 13),
            text_color=COLORS['text_muted']
        )
        self.printer_status_label.pack(side='left', padx=20)

        ctk.CTkLabel(
            test_inner,
            text="Test will print a small test label to verify connection",
            font=('Segoe UI', 11),
            text_color=COLORS['text_muted']
        ).pack(anchor='w', pady=(10, 0))

        # Initially hide settings frames
        self._on_printer_type_change()

        self.pages.append(page)

    def _create_email_page(self):
        """Create email configuration page with test button."""
        page = ctk.CTkFrame(self.content, fg_color='transparent')

        ctk.CTkLabel(
            page,
            text="Email Configuration",
            font=('Segoe UI', 28, 'bold'),
            text_color=COLORS['text_primary']
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            page,
            text="Optional: Send pickup manifests to back office automatically",
            font=('Segoe UI', 13),
            text_color=COLORS['text_muted']
        ).pack(pady=(0, 20))

        # Enable toggle
        enable_card = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)
        enable_card.pack(fill='x', pady=5)

        enable_inner = ctk.CTkFrame(enable_card, fg_color='transparent')
        enable_inner.pack(fill='x', padx=25, pady=15)

        self.email_enabled_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            enable_inner,
            text="Enable email manifests",
            font=('Segoe UI', 14, 'bold'),
            variable=self.email_enabled_var,
            onvalue=True,
            offvalue=False,
            command=self._on_email_toggle
        ).pack(anchor='w')

        # Settings card
        self.email_settings_card = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)
        self.email_settings_card.pack(fill='x', pady=10)

        email_inner = ctk.CTkFrame(self.email_settings_card, fg_color='transparent')
        email_inner.pack(fill='x', padx=25, pady=15)

        # SMTP row
        smtp_row = ctk.CTkFrame(email_inner, fg_color='transparent')
        smtp_row.pack(fill='x', pady=5)

        ctk.CTkLabel(smtp_row, text="SMTP Server", font=('Segoe UI', 12), text_color=COLORS['text_muted'], width=100, anchor='w').pack(side='left')
        self.smtp_server_var = ctk.StringVar(value="smtp.gmail.com")
        self.smtp_server_entry = ctk.CTkEntry(smtp_row, textvariable=self.smtp_server_var, font=('Segoe UI', 12), width=220, height=38)
        self.smtp_server_entry.pack(side='left', padx=5)

        ctk.CTkLabel(smtp_row, text="Port", font=('Segoe UI', 12), text_color=COLORS['text_muted'], width=40).pack(side='left', padx=(10, 0))
        self.smtp_port_var = ctk.StringVar(value="587")
        self.smtp_port_entry = ctk.CTkEntry(smtp_row, textvariable=self.smtp_port_var, font=('Segoe UI', 12), width=70, height=38)
        self.smtp_port_entry.pack(side='left', padx=5)

        # User row
        user_row = ctk.CTkFrame(email_inner, fg_color='transparent')
        user_row.pack(fill='x', pady=5)

        ctk.CTkLabel(user_row, text="Username", font=('Segoe UI', 12), text_color=COLORS['text_muted'], width=100, anchor='w').pack(side='left')
        self.smtp_user_var = ctk.StringVar(value="")
        self.smtp_user_entry = ctk.CTkEntry(user_row, textvariable=self.smtp_user_var, font=('Segoe UI', 12), width=360, height=38, placeholder_text="your.email@gmail.com")
        self.smtp_user_entry.pack(side='left', padx=5)

        # Password row
        pass_row = ctk.CTkFrame(email_inner, fg_color='transparent')
        pass_row.pack(fill='x', pady=5)

        ctk.CTkLabel(pass_row, text="Password", font=('Segoe UI', 12), text_color=COLORS['text_muted'], width=100, anchor='w').pack(side='left')
        self.smtp_password_var = ctk.StringVar(value="")
        self.smtp_password_entry = ctk.CTkEntry(pass_row, textvariable=self.smtp_password_var, font=('Segoe UI', 12), width=360, height=38, show="*", placeholder_text="App password (not account password)")
        self.smtp_password_entry.pack(side='left', padx=5)

        # Gmail note
        ctk.CTkLabel(
            email_inner,
            text="Gmail: Use App Password from myaccount.google.com/apppasswords",
            font=('Segoe UI', 10),
            text_color=COLORS['warning']
        ).pack(anchor='w', pady=(2, 8))

        # From/To row
        from_row = ctk.CTkFrame(email_inner, fg_color='transparent')
        from_row.pack(fill='x', pady=5)

        ctk.CTkLabel(from_row, text="From Email", font=('Segoe UI', 12), text_color=COLORS['text_muted'], width=100, anchor='w').pack(side='left')
        self.from_email_var = ctk.StringVar(value="")
        self.from_email_entry = ctk.CTkEntry(from_row, textvariable=self.from_email_var, font=('Segoe UI', 12), width=360, height=38, placeholder_text="labeling@sintonandsons.com")
        self.from_email_entry.pack(side='left', padx=5)

        to_row = ctk.CTkFrame(email_inner, fg_color='transparent')
        to_row.pack(fill='x', pady=5)

        ctk.CTkLabel(to_row, text="Back Office", font=('Segoe UI', 12), text_color=COLORS['text_muted'], width=100, anchor='w').pack(side='left')
        self.back_office_email_var = ctk.StringVar(value="")
        self.back_office_email_entry = ctk.CTkEntry(to_row, textvariable=self.back_office_email_var, font=('Segoe UI', 12), width=360, height=38, placeholder_text="office@sintonandsons.com")
        self.back_office_email_entry.pack(side='left', padx=5)

        # Test button
        test_row = ctk.CTkFrame(email_inner, fg_color='transparent')
        test_row.pack(fill='x', pady=(10, 5))

        self.email_test_btn = ctk.CTkButton(
            test_row,
            text="SEND TEST EMAIL",
            font=('Segoe UI', 12, 'bold'),
            fg_color=COLORS['primary'],
            hover_color=COLORS['primary_hover'],
            width=160,
            height=42,
            corner_radius=6,
            command=self._test_email
        )
        self.email_test_btn.pack(side='left')

        self.email_status_label = ctk.CTkLabel(
            test_row,
            text="Not tested",
            font=('Segoe UI', 12),
            text_color=COLORS['text_muted']
        )
        self.email_status_label.pack(side='left', padx=15)

        # Initially disable
        self._on_email_toggle()

        self.pages.append(page)

    def _create_review_page(self):
        """Create review/confirmation page."""
        page = ctk.CTkFrame(self.content, fg_color='transparent')

        ctk.CTkLabel(
            page,
            text="Review Configuration",
            font=('Segoe UI', 28, 'bold'),
            text_color=COLORS['text_primary']
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            page,
            text="Please review your settings before saving",
            font=('Segoe UI', 13),
            text_color=COLORS['text_muted']
        ).pack(pady=(0, 25))

        # Summary card
        summary_card = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)
        summary_card.pack(fill='x', pady=10)

        summary_inner = ctk.CTkFrame(summary_card, fg_color='transparent')
        summary_inner.pack(fill='x', padx=25, pady=20)

        self.summary_text = ctk.CTkTextbox(
            summary_inner,
            font=('Courier New', 13),
            fg_color=COLORS['bg_dark'],
            text_color=COLORS['text_primary'],
            height=200,
            corner_radius=8
        )
        self.summary_text.pack(fill='x')
        self.summary_text.configure(state='disabled')

        # Warning
        warning_frame = ctk.CTkFrame(page, fg_color=COLORS['bg_card'], corner_radius=12)
        warning_frame.pack(fill='x', pady=15)

        warning_inner = ctk.CTkFrame(warning_frame, fg_color='transparent')
        warning_inner.pack(fill='x', padx=25, pady=15)

        ctk.CTkLabel(
            warning_inner,
            text="⚠️  Restart the application after saving to apply hardware changes",
            font=('Segoe UI', 12),
            text_color=COLORS['warning']
        ).pack(anchor='w')

        ctk.CTkLabel(
            warning_inner,
            text="Settings are saved to config.ini and can be edited manually if needed",
            font=('Segoe UI', 11),
            text_color=COLORS['text_muted']
        ).pack(anchor='w', pady=(5, 0))

        self.pages.append(page)

    def _get_serial_ports(self) -> list[str]:
        """Get available serial ports."""
        if not SERIAL_AVAILABLE:
            return []
        try:
            ports = serial.tools.list_ports.comports()
            return [f"{p.device} - {p.description}" for p in ports]
        except:
            return []

    def _refresh_scale_ports(self):
        """Refresh scale port list."""
        ports = self._get_serial_ports()
        port_options = ["None (simulated scale)"] + ports
        self.scale_port_menu.configure(values=port_options)
        self.scale_status_label.configure(text="Ports refreshed", text_color=COLORS['text_secondary'])

    def _on_printer_type_change(self, *args):
        """Handle printer type change."""
        ptype = self.printer_type_var.get()
        self.printer_network_frame.pack_forget()
        self.printer_serial_frame.pack_forget()

        if ptype == "network":
            self.printer_network_frame.pack(fill='x', pady=10)
        elif ptype == "serial":
            self.printer_serial_frame.pack(fill='x', pady=10)

    def _on_email_toggle(self):
        """Handle email enable toggle."""
        enabled = self.email_enabled_var.get()
        state = 'normal' if enabled else 'disabled'

        for entry in [self.smtp_server_entry, self.smtp_port_entry, self.smtp_user_entry,
                      self.smtp_password_entry, self.from_email_entry, self.back_office_email_entry]:
            entry.configure(state=state)

        self.email_test_btn.configure(state=state)

    def _test_scale(self):
        """Test scale connection."""
        port_str = self.scale_port_var.get()
        if "None" in port_str:
            self.scale_status_label.configure(text="Using simulated scale", text_color=COLORS['text_secondary'])
            self.scale_result_label.configure(text="Simulated scale will generate random weights for testing")
            return

        port = port_str.split(' - ')[0]
        baud = int(self.scale_baud_var.get())

        self.test_in_progress = True
        self.scale_test_btn.configure(state='disabled', text="TESTING...")
        self.scale_status_label.configure(text="Connecting...", text_color=COLORS['warning'])

        def test_thread():
            try:
                if not SERIAL_AVAILABLE:
                    raise Exception("pyserial not installed")

                ser = serial.Serial(port, baud, timeout=3)
                time.sleep(0.5)

                # Try to read from scale
                ser.write(b'\r\n')
                time.sleep(0.3)
                response = ser.read(100)
                ser.close()

                if response:
                    self.after(0, lambda: self._scale_test_success(response.decode('ascii', errors='ignore')))
                else:
                    self.after(0, lambda: self._scale_test_success("Connected (no data received)"))

            except Exception as e:
                self.after(0, lambda: self._scale_test_fail(str(e)))

        threading.Thread(target=test_thread, daemon=True).start()

    def _scale_test_success(self, data: str):
        """Handle successful scale test."""
        self.test_in_progress = False
        self.scale_test_btn.configure(state='normal', text="TEST CONNECTION")
        self.scale_status_label.configure(text="✓ Connected", text_color=COLORS['success'])
        self.scale_result_label.configure(text=f"Response: {data.strip()[:50]}", text_color=COLORS['text_primary'])

    def _scale_test_fail(self, error: str):
        """Handle failed scale test."""
        self.test_in_progress = False
        self.scale_test_btn.configure(state='normal', text="TEST CONNECTION")
        self.scale_status_label.configure(text="✗ Failed", text_color=COLORS['error'])
        self.scale_result_label.configure(text=f"Error: {error}", text_color=COLORS['error'])

    def _test_printer(self):
        """Test printer connection."""
        ptype = self.printer_type_var.get()

        if ptype == "mock":
            self.printer_status_label.configure(text="Using simulated printer", text_color=COLORS['text_secondary'])
            return

        self.test_in_progress = True
        self.printer_test_btn.configure(state='disabled', text="TESTING...")
        self.printer_status_label.configure(text="Connecting...", text_color=COLORS['warning'])

        def test_thread():
            try:
                # Test ZPL
                test_zpl = "^XA^FO50,50^A0N,30,30^FDTEST LABEL^FS^XZ"

                if ptype == "network":
                    import socket
                    host = self.printer_host_var.get()
                    port = int(self.printer_tcp_port_var.get())

                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect((host, port))
                    sock.sendall(test_zpl.encode())
                    sock.close()

                elif ptype == "serial":
                    if not SERIAL_AVAILABLE:
                        raise Exception("pyserial not installed")

                    port_str = self.printer_port_var.get()
                    if "Select" in port_str:
                        raise Exception("No port selected")

                    port = port_str.split(' - ')[0]
                    ser = serial.Serial(port, 9600, timeout=3)
                    ser.write(test_zpl.encode())
                    ser.close()

                self.after(0, self._printer_test_success)

            except Exception as e:
                self.after(0, lambda: self._printer_test_fail(str(e)))

        threading.Thread(target=test_thread, daemon=True).start()

    def _printer_test_success(self):
        """Handle successful printer test."""
        self.test_in_progress = False
        self.printer_test_btn.configure(state='normal', text="TEST PRINT")
        self.printer_status_label.configure(text="✓ Test label printed", text_color=COLORS['success'])

    def _printer_test_fail(self, error: str):
        """Handle failed printer test."""
        self.test_in_progress = False
        self.printer_test_btn.configure(state='normal', text="TEST PRINT")
        self.printer_status_label.configure(text=f"✗ {error[:30]}", text_color=COLORS['error'])

    def _test_email(self):
        """Test email connection."""
        self.test_in_progress = True
        self.email_test_btn.configure(state='disabled', text="SENDING...")
        self.email_status_label.configure(text="Connecting...", text_color=COLORS['warning'])

        def test_thread():
            try:
                import smtplib
                from email.mime.text import MIMEText

                server = self.smtp_server_var.get()
                port = int(self.smtp_port_var.get())
                user = self.smtp_user_var.get()
                password = self.smtp_password_var.get()
                from_email = self.from_email_var.get()
                to_email = self.back_office_email_var.get()

                if not all([server, user, password, from_email, to_email]):
                    raise Exception("All fields required")

                msg = MIMEText("This is a test email from Pomponio Ranch Labeling System.\n\nIf you received this, email is configured correctly.")
                msg['Subject'] = "Pomponio Ranch - Email Test"
                msg['From'] = from_email
                msg['To'] = to_email

                with smtplib.SMTP(server, port, timeout=10) as smtp:
                    smtp.starttls()
                    smtp.login(user, password)
                    smtp.send_message(msg)

                self.after(0, self._email_test_success)

            except Exception as e:
                self.after(0, lambda: self._email_test_fail(str(e)))

        threading.Thread(target=test_thread, daemon=True).start()

    def _email_test_success(self):
        """Handle successful email test."""
        self.test_in_progress = False
        self.email_test_btn.configure(state='normal', text="SEND TEST EMAIL")
        self.email_status_label.configure(text="✓ Email sent", text_color=COLORS['success'])

    def _email_test_fail(self, error: str):
        """Handle failed email test."""
        self.test_in_progress = False
        self.email_test_btn.configure(state='normal', text="SEND TEST EMAIL")
        self.email_status_label.configure(text=f"✗ {error[:35]}", text_color=COLORS['error'])

    def _show_page(self, index: int):
        """Show specific page."""
        # Hide all pages
        for page in self.pages:
            page.pack_forget()

        # Show current page
        self.pages[index].pack(fill='both', expand=True)
        self.current_page = index

        # Update progress indicators
        for i, (num, lbl) in enumerate(self.step_labels):
            if i < index:
                num.configure(fg_color=COLORS['success'], text_color='white')
                lbl.configure(text_color=COLORS['success'])
            elif i == index:
                num.configure(fg_color=COLORS['primary'], text_color='white')
                lbl.configure(text_color=COLORS['primary'])
            else:
                num.configure(fg_color=COLORS['bg_light'], text_color=COLORS['text_muted'])
                lbl.configure(text_color=COLORS['text_muted'])

        # Update navigation buttons
        self.back_btn.configure(state='normal' if index > 0 else 'disabled')

        if index == len(self.pages) - 1:
            self.next_btn.configure(text="SAVE & FINISH", fg_color=COLORS['success'])
            self.skip_btn.pack_forget()
            self._update_summary()
        else:
            self.next_btn.configure(text="NEXT →", fg_color=COLORS['primary'])
            if index > 0:
                self.skip_btn.pack(side='left', padx=20)
            else:
                self.skip_btn.pack_forget()

    def _next_page(self):
        """Go to next page."""
        if self.test_in_progress:
            return

        if self.current_page < len(self.pages) - 1:
            self._collect_page_config()
            self._show_page(self.current_page + 1)
        else:
            self._save_config()
            self.destroy()
            if self.on_complete:
                self.on_complete()

    def _prev_page(self):
        """Go to previous page."""
        if self.test_in_progress:
            return
        if self.current_page > 0:
            self._show_page(self.current_page - 1)

    def _skip_page(self):
        """Skip current page."""
        if self.test_in_progress:
            return
        if self.current_page < len(self.pages) - 1:
            self._show_page(self.current_page + 1)

    def _collect_page_config(self):
        """Collect config from current page."""
        if self.current_page == 1:  # Scale
            port = self.scale_port_var.get()
            if port and "None" not in port:
                self.config['scale_port'] = port.split(' - ')[0]
            else:
                self.config['scale_port'] = ''
            self.config['scale_baudrate'] = self.scale_baud_var.get()

        elif self.current_page == 2:  # Printer
            self.config['printer_type'] = self.printer_type_var.get()
            self.config['printer_host'] = self.printer_host_var.get()
            self.config['printer_tcp_port'] = self.printer_tcp_port_var.get()
            port = self.printer_port_var.get()
            if port and "Select" not in port:
                self.config['printer_port'] = port.split(' - ')[0]
            else:
                self.config['printer_port'] = ''

        elif self.current_page == 3:  # Email
            self.config['email_enabled'] = str(self.email_enabled_var.get()).lower()
            self.config['smtp_server'] = self.smtp_server_var.get()
            self.config['smtp_port'] = self.smtp_port_var.get()
            self.config['smtp_user'] = self.smtp_user_var.get()
            self.config['smtp_password'] = self.smtp_password_var.get()
            self.config['from_email'] = self.from_email_var.get()
            self.config['back_office_email'] = self.back_office_email_var.get()

    def _update_summary(self):
        """Update summary on review page."""
        self._collect_page_config()

        lines = []
        lines.append("=" * 50)
        lines.append("CONFIGURATION SUMMARY")
        lines.append("=" * 50)
        lines.append("")

        # Scale
        lines.append("SCALE")
        lines.append("-" * 20)
        if self.config.get('scale_port'):
            lines.append(f"  Port: {self.config['scale_port']}")
            lines.append(f"  Baud: {self.config.get('scale_baudrate', '9600')}")
        else:
            lines.append("  Mode: Simulated (mock)")
        lines.append("")

        # Printer
        lines.append("PRINTER")
        lines.append("-" * 20)
        ptype = self.config.get('printer_type', 'mock')
        if ptype == 'network':
            lines.append(f"  Type: Network")
            lines.append(f"  Host: {self.config.get('printer_host', '')}:{self.config.get('printer_tcp_port', '9100')}")
        elif ptype == 'serial':
            lines.append(f"  Type: Serial")
            lines.append(f"  Port: {self.config.get('printer_port', '')}")
        else:
            lines.append("  Mode: Simulated (mock)")
        lines.append("")

        # Email
        lines.append("EMAIL")
        lines.append("-" * 20)
        if self.config.get('email_enabled') == 'true':
            lines.append(f"  Status: Enabled")
            lines.append(f"  Server: {self.config.get('smtp_server', '')}:{self.config.get('smtp_port', '')}")
            lines.append(f"  From: {self.config.get('from_email', '')}")
            lines.append(f"  To: {self.config.get('back_office_email', '')}")
        else:
            lines.append("  Status: Disabled")
        lines.append("")
        lines.append("=" * 50)

        self.summary_text.configure(state='normal')
        self.summary_text.delete('1.0', 'end')
        self.summary_text.insert('1.0', "\n".join(lines))
        self.summary_text.configure(state='disabled')

    def _save_config(self):
        """Save configuration to file."""
        parser = configparser.ConfigParser()

        # Read existing config if present
        if self.config_path.exists():
            parser.read(self.config_path)

        # Ensure sections exist
        for section in ['hardware', 'application', 'database', 'labels', 'email']:
            if section not in parser:
                parser[section] = {}

        # Set hardware
        parser['hardware']['scale_port'] = self.config.get('scale_port', '')
        parser['hardware']['scale_baudrate'] = self.config.get('scale_baudrate', '9600')
        parser['hardware']['printer_type'] = self.config.get('printer_type', 'mock')
        parser['hardware']['printer_port'] = self.config.get('printer_port', '')
        parser['hardware']['printer_host'] = self.config.get('printer_host', '')
        parser['hardware']['printer_tcp_port'] = self.config.get('printer_tcp_port', '9100')

        # Set email
        parser['email']['enabled'] = self.config.get('email_enabled', 'false')
        parser['email']['smtp_server'] = self.config.get('smtp_server', 'smtp.gmail.com')
        parser['email']['smtp_port'] = self.config.get('smtp_port', '587')
        parser['email']['smtp_user'] = self.config.get('smtp_user', '')
        parser['email']['smtp_password'] = self.config.get('smtp_password', '')
        parser['email']['from_email'] = self.config.get('from_email', '')
        parser['email']['back_office_email'] = self.config.get('back_office_email', '')

        # Set defaults for other sections
        if 'window_mode' not in parser['application']:
            parser['application']['window_mode'] = 'maximized'
            parser['application']['touch_target_size'] = '60'
            parser['application']['audio_enabled'] = 'true'

        if 'db_path' not in parser['database']:
            parser['database']['db_path'] = 'data/pomponio.db'

        if 'printer_dpi' not in parser['labels']:
            parser['labels']['printer_dpi'] = '203'
            parser['labels']['package_label_width'] = '4'
            parser['labels']['package_label_height'] = '2'
            parser['labels']['box_label_width'] = '4'
            parser['labels']['box_label_height'] = '3'

        # Write config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            parser.write(f)


def needs_setup(config_path: Path) -> bool:
    """Check if setup wizard should run."""
    return not config_path.exists()
