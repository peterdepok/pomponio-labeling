#!/usr/bin/env python3
"""
Pomponio Ranch Labeling System - Entry Point

Usage:
    python run.py                    # Auto-load from config.ini (or mock if missing)
    python run.py --mock             # Force mock hardware (testing)
    python run.py --scale-port COM3  # Specify scale port
    python run.py --printer-host 192.168.1.100  # Network printer
    python run.py --classic          # Use classic Tkinter UI

See --help for all options.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def main():
    import argparse
    from src.config import load_config, CONFIG_FILE

    parser = argparse.ArgumentParser(description='Pomponio Ranch Labeling System')
    parser.add_argument('--scale-port', help='Scale serial port')
    parser.add_argument('--printer-port', help='Printer serial port')
    parser.add_argument('--printer-host', help='Printer network address')
    parser.add_argument('--mock', action='store_true', help='Use mock hardware')
    parser.add_argument('--classic', action='store_true', help='Use classic Tkinter UI')
    args = parser.parse_args()

    # Determine hardware settings
    scale_port = args.scale_port
    printer_port = args.printer_port
    printer_host = args.printer_host
    mock_hardware = args.mock

    # If no command line args provided, try to load from config.ini
    if not any([args.scale_port, args.printer_port, args.printer_host, args.mock]):
        if CONFIG_FILE.exists():
            print(f"Loading configuration from {CONFIG_FILE}")
            config = load_config()
            scale_port = config.hardware.scale_port
            printer_port = config.hardware.printer_port
            printer_host = config.hardware.printer_host
            # Use mock if no hardware configured
            if config.hardware.printer_type == 'mock':
                mock_hardware = True
            elif not any([printer_port, printer_host]):
                mock_hardware = True
        else:
            print("No config.ini found - running in mock hardware mode")
            print("Copy config.ini.example to config.ini to configure hardware")
            mock_hardware = True

    if args.classic:
        from src.ui.app import PomponioApp
        app = PomponioApp(
            scale_port=scale_port,
            printer_port=printer_port,
            printer_host=printer_host,
            mock_hardware=mock_hardware
        )
    else:
        from src.ui.app_modern import ModernApp
        app = ModernApp(
            scale_port=scale_port,
            printer_port=printer_port,
            printer_host=printer_host,
            mock_hardware=mock_hardware
        )

    app.run()


if __name__ == '__main__':
    main()
