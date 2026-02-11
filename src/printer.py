"""
Zebra ZPL label printing module.
Generates ZPL commands for package and box labels.
"""

import socket
from typing import Optional
from pathlib import Path

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class PrinterError(Exception):
    """Printer communication error."""
    pass


class ZebraPrinter:
    """
    Zebra label printer interface.

    Supports connection via:
    - USB (serial port)
    - Network (TCP socket, typically port 9100)
    - File (for testing/preview)
    """

    def __init__(
        self,
        port: Optional[str] = None,
        host: Optional[str] = None,
        tcp_port: int = 9100,
        output_file: Optional[str] = None
    ):
        """
        Initialize printer connection.

        Args:
            port: Serial port for USB connection (e.g., COM3, /dev/ttyUSB0)
            host: IP address for network connection
            tcp_port: TCP port for network connection (default 9100)
            output_file: File path to write ZPL instead of printing
        """
        self.serial_port = port
        self.host = host
        self.tcp_port = tcp_port
        self.output_file = output_file
        self._serial: Optional[serial.Serial] = None
        self._socket: Optional[socket.socket] = None

    @staticmethod
    def list_ports() -> list[str]:
        """List available serial ports."""
        if not SERIAL_AVAILABLE:
            return []
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]

    def connect(self) -> bool:
        """Connect to printer. Returns True on success."""
        if self.output_file:
            return True

        if self.host:
            try:
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._socket.settimeout(5.0)
                self._socket.connect((self.host, self.tcp_port))
                return True
            except socket.error as e:
                raise PrinterError(f"Network connection failed: {e}")

        if self.serial_port:
            if not SERIAL_AVAILABLE:
                raise PrinterError("pyserial not installed")
            try:
                self._serial = serial.Serial(
                    port=self.serial_port,
                    baudrate=9600,
                    timeout=5.0
                )
                return True
            except serial.SerialException as e:
                raise PrinterError(f"Serial connection failed: {e}")

        raise PrinterError("No connection method specified")

    def disconnect(self):
        """Disconnect from printer."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        if self._socket:
            self._socket.close()
        self._serial = None
        self._socket = None

    def is_connected(self) -> bool:
        """Check if connected to printer."""
        if self.output_file:
            return True
        if self._socket:
            return True
        return self._serial is not None and self._serial.is_open

    def send_zpl(self, zpl: str):
        """Send raw ZPL commands to printer."""
        if self.output_file:
            with open(self.output_file, 'a') as f:
                f.write(zpl + "\n")
            return

        zpl_bytes = zpl.encode('utf-8')

        if self._socket:
            try:
                self._socket.sendall(zpl_bytes)
            except socket.error as e:
                raise PrinterError(f"Network send failed: {e}")
        elif self._serial and self._serial.is_open:
            try:
                self._serial.write(zpl_bytes)
            except serial.SerialException as e:
                raise PrinterError(f"Serial send failed: {e}")
        else:
            raise PrinterError("Not connected to printer")


class LabelGenerator:
    """
    Generate ZPL labels for Pomponio Ranch.

    Label sizes:
    - Package label: 4" x 2" (typical shipping label)
    - Box label: 4" x 3" (with QR code)
    """

    # Label dimensions in dots (assuming 203 dpi)
    DOTS_PER_INCH = 203
    PACKAGE_WIDTH = 4 * DOTS_PER_INCH   # 812 dots
    PACKAGE_HEIGHT = 2 * DOTS_PER_INCH  # 406 dots
    BOX_WIDTH = 4 * DOTS_PER_INCH       # 812 dots
    BOX_HEIGHT = 3 * DOTS_PER_INCH      # 609 dots

    @staticmethod
    def sanitize_zpl(text: str) -> str:
        """
        Sanitize user-provided strings to prevent ZPL injection.
        Strips ZPL control characters (^ and ~) that could inject commands.
        """
        if not text:
            return ""
        return text.replace("^", "").replace("~", "")

    @staticmethod
    def package_label(
        product_name: str,
        sku: str,
        weight_lbs: float,
        price_per_lb: float,
        barcode: str,
        date_packed: str = None
    ) -> str:
        """
        Generate ZPL for package label.

        Layout:
        +----------------------------------+
        | POMPONIO RANCH                   |
        | [Product Name]                   |
        | Weight: X.XX LB    $XX.XX        |
        | |||||||||||||||||||||||||||||||  |
        | [barcode number]                 |
        +----------------------------------+
        """
        total_price = weight_lbs * price_per_lb
        date_str = LabelGenerator.sanitize_zpl(date_packed or "")
        product_name_safe = LabelGenerator.sanitize_zpl(product_name)

        zpl = f"""^XA
^CF0,30
^FO30,20^FDPOMPONIO RANCH^FS

^CF0,45
^FO30,60^FD{product_name_safe[:25]}^FS

^CF0,35
^FO30,120^FDWeight: {weight_lbs:.2f} LB^FS
^FO450,120^FD${total_price:.2f}^FS

^CF0,25
^FO30,165^FD${price_per_lb:.2f}/LB^FS
^FO450,165^FD{date_str}^FS

^BY3,2,100
^FO100,210^BC^FD{barcode}^FS

^CF0,25
^FO270,330^FD{barcode}^FS

^XZ"""
        return zpl

    @staticmethod
    def box_label(
        box_number: str,
        total_weight: float,
        package_count: int,
        qr_data: str,
        customer_name: str = None
    ) -> str:
        """
        Generate ZPL for box label with QR code.

        Layout:
        +----------------------------------+
        | POMPONIO RANCH                   |
        | Box: YYYYMMDD-XXX                |
        | [QR CODE]    Weight: XX.XX LB    |
        |              Packages: XX        |
        |              [Customer]          |
        +----------------------------------+
        """
        customer_line = LabelGenerator.sanitize_zpl(customer_name or "")
        box_number_safe = LabelGenerator.sanitize_zpl(box_number)

        # QR code data needs to be escaped for ZPL
        qr_escaped = qr_data.replace("^", "").replace("~", "")

        zpl = f"""^XA
^CF0,35
^FO30,20^FDPOMPONIO RANCH^FS

^CF0,45
^FO30,70^FDBox: {box_number_safe}^FS

^BQN,2,6
^FO30,130^FDQA,{qr_escaped}^FS

^CF0,35
^FO350,140^FDWeight: {total_weight:.2f} LB^FS
^FO350,190^FDPackages: {package_count}^FS

^CF0,30
^FO350,250^FD{customer_line[:20]}^FS

^XZ"""
        return zpl

    @staticmethod
    def manifest_label(
        order_id: int,
        customer_name: str,
        box_count: int,
        total_weight: float,
        box_numbers: list[str]
    ) -> str:
        """
        Generate ZPL for order manifest label.

        Layout:
        +----------------------------------+
        | POMPONIO RANCH - ORDER MANIFEST  |
        | Customer: [Name]                 |
        | Boxes: X    Total: XX.XX LB      |
        | Box List:                        |
        | YYYYMMDD-001, YYYYMMDD-002, ...  |
        +----------------------------------+
        """
        # Sanitize box numbers and customer name
        box_numbers_safe = [LabelGenerator.sanitize_zpl(bn) for bn in box_numbers[:6]]
        box_list = ", ".join(box_numbers_safe)
        if len(box_numbers) > 6:
            box_list += f" +{len(box_numbers) - 6} more"
        customer_name_safe = LabelGenerator.sanitize_zpl(customer_name)

        zpl = f"""^XA
^CF0,30
^FO30,20^FDPOMPONIO RANCH - ORDER MANIFEST^FS

^CF0,40
^FO30,70^FDCustomer: {customer_name_safe[:25]}^FS

^CF0,35
^FO30,130^FDBoxes: {box_count}^FS
^FO300,130^FDTotal: {total_weight:.2f} LB^FS

^CF0,30
^FO30,180^FDBox List:^FS

^CF0,25
^FO30,220^FD{box_list}^FS

^XZ"""
        return zpl


class MockPrinter(ZebraPrinter):
    """Mock printer for testing without hardware."""

    def __init__(self):
        super().__init__()
        self.print_log: list[str] = []

    def connect(self) -> bool:
        return True

    def disconnect(self):
        pass

    def is_connected(self) -> bool:
        return True

    def send_zpl(self, zpl: str):
        self.print_log.append(zpl)
        print(f"[MockPrinter] Received {len(zpl)} bytes")

    def get_last_label(self) -> Optional[str]:
        return self.print_log[-1] if self.print_log else None

    def clear_log(self):
        self.print_log.clear()


if __name__ == "__main__":
    # Test label generation
    gen = LabelGenerator()

    package_zpl = gen.package_label(
        product_name="Ground Beef 80/20",
        sku="00123",
        weight_lbs=2.45,
        price_per_lb=8.99,
        barcode="000123002455",
        date_packed="02/04/26"
    )
    print("Package Label ZPL:")
    print(package_zpl)
    print()

    box_zpl = gen.box_label(
        box_number="20260204-001",
        total_weight=24.50,
        package_count=8,
        qr_data="BOX|20260204-001|24.50\n00123|2.45\n00124|3.20",
        customer_name="Smith Family Farm"
    )
    print("Box Label ZPL:")
    print(box_zpl)
