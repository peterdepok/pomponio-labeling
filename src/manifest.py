"""
Manifest generation and email module.
Creates detailed pickup manifests with box contents for back office printing.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from .database import (
    get_order_by_id, get_boxes_for_order, get_packages_in_box,
    get_product_by_id, Order, Box, Package
)
from .barcode import generate_code128_barcode
from src import get_app_dir

logger = logging.getLogger("pomponio.manifest")


@dataclass
class ManifestConfig:
    """Email configuration for manifests."""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = ""
    back_office_email: str = ""
    enabled: bool = False


def load_manifest_config() -> ManifestConfig:
    """Load manifest email config from config.ini."""
    import configparser
    config_path = get_app_dir() / "config.ini"

    config = ManifestConfig()

    if config_path.exists():
        parser = configparser.ConfigParser()
        parser.read(config_path)

        if 'email' in parser:
            config.smtp_server = parser.get('email', 'smtp_server', fallback='smtp.gmail.com')
            config.smtp_port = parser.getint('email', 'smtp_port', fallback=587)
            config.smtp_user = parser.get('email', 'smtp_user', fallback='')
            config.smtp_password = parser.get('email', 'smtp_password', fallback='')
            config.from_email = parser.get('email', 'from_email', fallback='')
            config.back_office_email = parser.get('email', 'back_office_email', fallback='')
            config.enabled = parser.getboolean('email', 'enabled', fallback=False)

    return config


@dataclass
class BoxContents:
    """Summary of box contents for manifest."""
    box_number: str
    box_id: int
    total_weight: float
    package_count: int
    qr_data: str
    packages: list[Package]
    products_summary: dict[str, dict]  # product_name -> {count, weight}


@dataclass
class OrderManifest:
    """Complete order manifest."""
    order_id: int
    customer_name: str
    order_date: str
    pickup_date: Optional[str]
    box_count: int
    total_packages: int
    total_weight: float
    boxes: list[BoxContents]
    generated_at: datetime


def generate_manifest(order_id: int) -> Optional[OrderManifest]:
    """Generate complete manifest for an order."""
    order = get_order_by_id(order_id)
    if not order:
        logger.error(f"Order {order_id} not found")
        return None

    boxes = get_boxes_for_order(order_id)
    if not boxes:
        logger.warning(f"No boxes found for order {order_id}")
        return None

    box_contents = []
    total_packages = 0
    total_weight = 0.0

    for box in boxes:
        packages = get_packages_in_box(box.id)

        # Summarize products in box
        products_summary = {}
        for pkg in packages:
            name = pkg.product_name or "Unknown"
            if name not in products_summary:
                products_summary[name] = {'count': 0, 'weight': 0.0, 'sku': pkg.product_sku}
            products_summary[name]['count'] += 1
            products_summary[name]['weight'] += pkg.weight_lbs

        box_contents.append(BoxContents(
            box_number=box.box_number,
            box_id=box.id,
            total_weight=box.total_weight,
            package_count=box.package_count,
            qr_data=box.qr_data or "",
            packages=packages,
            products_summary=products_summary
        ))

        total_packages += box.package_count
        total_weight += box.total_weight

    return OrderManifest(
        order_id=order_id,
        customer_name=order.customer_name,
        order_date=str(order.order_date),
        pickup_date=str(order.pickup_date) if order.pickup_date else None,
        box_count=len(boxes),
        total_packages=total_packages,
        total_weight=round(total_weight, 2),
        boxes=box_contents,
        generated_at=datetime.now()
    )


def manifest_to_text(manifest: OrderManifest) -> str:
    """Convert manifest to plain text format."""
    lines = []
    lines.append("=" * 60)
    lines.append("POMPONIO RANCH - ORDER PICKUP MANIFEST")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Customer: {manifest.customer_name}")
    lines.append(f"Order ID: {manifest.order_id}")
    lines.append(f"Order Date: {manifest.order_date}")
    if manifest.pickup_date:
        lines.append(f"Pickup Date: {manifest.pickup_date}")
    lines.append(f"Generated: {manifest.generated_at.strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("-" * 60)
    lines.append("ORDER SUMMARY")
    lines.append("-" * 60)
    lines.append(f"Total Boxes: {manifest.box_count}")
    lines.append(f"Total Packages: {manifest.total_packages}")
    lines.append(f"Total Weight: {manifest.total_weight:.2f} lbs")
    lines.append("")

    for i, box in enumerate(manifest.boxes, 1):
        lines.append("=" * 60)
        lines.append(f"BOX {i}: {box.box_number}")
        lines.append(f"Scan Code: {box.qr_data}")
        lines.append("-" * 60)
        lines.append(f"Packages: {box.package_count} | Weight: {box.total_weight:.2f} lbs")
        lines.append("")
        lines.append("Contents:")

        for product_name, summary in sorted(box.products_summary.items()):
            sku = summary.get('sku', '?????')
            count = summary['count']
            weight = summary['weight']
            lines.append(f"  [{sku}] {product_name}")
            lines.append(f"         {count} pkg(s) @ {weight:.2f} lbs total")

        lines.append("")
        lines.append("Individual Packages (for scanning):")
        for pkg in box.packages:
            lines.append(f"  [ ] {pkg.barcode} - {pkg.product_name} ({pkg.weight_lbs:.2f} lb)")

        lines.append("")

    lines.append("=" * 60)
    lines.append("PICKUP VERIFICATION")
    lines.append("=" * 60)
    lines.append("")
    lines.append("Customer Signature: ____________________________")
    lines.append("")
    lines.append("Date/Time: __________________")
    lines.append("")
    lines.append("Verified By: ____________________________")
    lines.append("")
    lines.append("=" * 60)
    lines.append("")

    return "\n".join(lines)


def manifest_to_html(manifest: OrderManifest) -> str:
    """Convert manifest to HTML format for printing."""
    html = []
    html.append("""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Order Manifest - {customer}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            font-size: 12pt;
            margin: 20px;
            color: #333;
        }}
        h1 {{
            text-align: center;
            font-size: 18pt;
            margin-bottom: 5px;
        }}
        h2 {{
            font-size: 14pt;
            border-bottom: 2px solid #333;
            padding-bottom: 5px;
            margin-top: 20px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #000;
        }}
        .summary {{
            background: #f5f5f5;
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
        }}
        .summary-item {{
            text-align: center;
        }}
        .summary-value {{
            font-size: 24pt;
            font-weight: bold;
            color: #2563eb;
        }}
        .summary-label {{
            font-size: 10pt;
            color: #666;
        }}
        .box {{
            border: 2px solid #333;
            margin: 15px 0;
            page-break-inside: avoid;
        }}
        .box-header {{
            background: #333;
            color: white;
            padding: 10px 15px;
            font-weight: bold;
            font-size: 14pt;
        }}
        .box-body {{
            padding: 15px;
        }}
        .box-summary {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ddd;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f0f0f0;
            font-weight: bold;
        }}
        .barcode {{
            font-family: 'Courier New', monospace;
            font-size: 11pt;
            background: #fff;
            padding: 2px 5px;
            border: 1px solid #ccc;
        }}
        .checkbox {{
            width: 18px;
            height: 18px;
            border: 2px solid #333;
            display: inline-block;
            vertical-align: middle;
            margin-right: 5px;
        }}
        .signature-section {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #333;
        }}
        .signature-line {{
            border-bottom: 1px solid #333;
            width: 300px;
            display: inline-block;
            margin: 10px;
        }}
        .qr-code {{
            font-family: 'Courier New', monospace;
            font-size: 10pt;
            background: #eee;
            padding: 5px 10px;
            margin: 5px 0;
        }}
        @media print {{
            .box {{
                page-break-inside: avoid;
            }}
            body {{
                margin: 10px;
            }}
        }}
    </style>
</head>
<body>
""".format(customer=manifest.customer_name))

    # Header
    html.append(f"""
    <div class="header">
        <h1>POMPONIO RANCH</h1>
        <div style="font-size: 14pt;">Order Pickup Manifest</div>
    </div>

    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
        <div>
            <strong>Customer:</strong> {manifest.customer_name}<br>
            <strong>Order ID:</strong> {manifest.order_id}<br>
            <strong>Order Date:</strong> {manifest.order_date}
        </div>
        <div style="text-align: right;">
            <strong>Generated:</strong> {manifest.generated_at.strftime('%Y-%m-%d %H:%M')}<br>
            {f'<strong>Pickup Date:</strong> {manifest.pickup_date}' if manifest.pickup_date else ''}
        </div>
    </div>
    """)

    # Summary
    html.append(f"""
    <div class="summary">
        <div class="summary-grid">
            <div class="summary-item">
                <div class="summary-value">{manifest.box_count}</div>
                <div class="summary-label">BOXES</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{manifest.total_packages}</div>
                <div class="summary-label">PACKAGES</div>
            </div>
            <div class="summary-item">
                <div class="summary-value">{manifest.total_weight:.1f}</div>
                <div class="summary-label">TOTAL LBS</div>
            </div>
        </div>
    </div>
    """)

    # Boxes
    for i, box in enumerate(manifest.boxes, 1):
        html.append(f"""
    <div class="box">
        <div class="box-header">
            BOX {i} of {manifest.box_count}: {box.box_number}
        </div>
        <div class="box-body">
            <div class="box-summary">
                <span><strong>Packages:</strong> {box.package_count}</span>
                <span><strong>Weight:</strong> {box.total_weight:.2f} lbs</span>
            </div>
            <div class="qr-code">Scan: {box.qr_data}</div>

            <h3 style="margin: 15px 0 10px 0;">Contents Summary</h3>
            <table>
                <tr>
                    <th>SKU</th>
                    <th>Product</th>
                    <th>Qty</th>
                    <th>Weight</th>
                </tr>
        """)

        for product_name, summary in sorted(box.products_summary.items()):
            sku = summary.get('sku', '?????')
            count = summary['count']
            weight = summary['weight']
            html.append(f"""
                <tr>
                    <td>{sku}</td>
                    <td>{product_name}</td>
                    <td style="text-align: center;">{count}</td>
                    <td style="text-align: right;">{weight:.2f} lb</td>
                </tr>
            """)

        html.append("""
            </table>

            <h3 style="margin: 15px 0 10px 0;">Package Verification Checklist</h3>
            <table>
                <tr>
                    <th style="width: 30px;"></th>
                    <th>Barcode</th>
                    <th>Product</th>
                    <th>Weight</th>
                </tr>
        """)

        for pkg in box.packages:
            html.append(f"""
                <tr>
                    <td><div class="checkbox"></div></td>
                    <td><span class="barcode">{pkg.barcode}</span></td>
                    <td>{pkg.product_name}</td>
                    <td style="text-align: right;">{pkg.weight_lbs:.2f} lb</td>
                </tr>
            """)

        html.append("""
            </table>
        </div>
    </div>
        """)

    # Signature section
    html.append("""
    <div class="signature-section">
        <h2>Pickup Verification</h2>
        <p>I confirm receipt of the above items in good condition.</p>
        <p>
            <strong>Customer Signature:</strong> <span class="signature-line"></span>
        </p>
        <p>
            <strong>Date/Time:</strong> <span class="signature-line" style="width: 200px;"></span>
        </p>
        <p>
            <strong>Verified By:</strong> <span class="signature-line"></span>
        </p>
    </div>
</body>
</html>
    """)

    return "\n".join(html)


def generate_zpl_manifest(manifest: OrderManifest) -> str:
    """Generate ZPL for a manifest summary label."""
    zpl_lines = []
    zpl_lines.append("^XA")
    zpl_lines.append("^CF0,40")  # Default font

    # Header
    zpl_lines.append("^FO50,30^A0N,50,50^FDPICKUP MANIFEST^FS")
    zpl_lines.append("^FO50,90^A0N,35,35^FD" + manifest.customer_name[:25] + "^FS")

    # Order info
    zpl_lines.append("^FO50,140^A0N,25,25^FDOrder: " + str(manifest.order_id) + "^FS")
    zpl_lines.append("^FO300,140^A0N,25,25^FDDate: " + manifest.order_date + "^FS")

    # Summary
    zpl_lines.append("^FO50,190^GB500,2,2^FS")  # Line
    zpl_lines.append("^FO50,210^A0N,35,35^FDBoxes: " + str(manifest.box_count) + "^FS")
    zpl_lines.append("^FO250,210^A0N,35,35^FDPkgs: " + str(manifest.total_packages) + "^FS")
    zpl_lines.append("^FO450,210^A0N,35,35^FD" + f"{manifest.total_weight:.1f} lb^FS")

    # Box list
    y_pos = 270
    for i, box in enumerate(manifest.boxes[:6], 1):  # Max 6 boxes on label
        zpl_lines.append(f"^FO50,{y_pos}^A0N,25,25^FDBox {i}: {box.box_number}^FS")
        zpl_lines.append(f"^FO350,{y_pos}^A0N,25,25^FD{box.package_count} pkgs, {box.total_weight:.1f}lb^FS")
        y_pos += 35

    if manifest.box_count > 6:
        zpl_lines.append(f"^FO50,{y_pos}^A0N,25,25^FD+{manifest.box_count - 6} more boxes...^FS")

    # QR code with order info
    qr_data = f"ORDER|{manifest.order_id}|{manifest.customer_name}|{manifest.box_count}"
    zpl_lines.append(f"^FO450,300^BQN,2,5^FDQA,{qr_data}^FS")

    zpl_lines.append("^XZ")
    return "\n".join(zpl_lines)


def send_manifest_email(manifest: OrderManifest, config: ManifestConfig = None) -> bool:
    """Send manifest to back office via email."""
    if config is None:
        config = load_manifest_config()

    if not config.enabled:
        logger.info("Email disabled, skipping manifest send")
        return False

    if not config.back_office_email:
        logger.error("No back office email configured")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Pickup Manifest: {manifest.customer_name} - Order #{manifest.order_id}"
        msg['From'] = config.from_email
        msg['To'] = config.back_office_email

        # Plain text version
        text_content = manifest_to_text(manifest)
        msg.attach(MIMEText(text_content, 'plain'))

        # HTML version
        html_content = manifest_to_html(manifest)
        msg.attach(MIMEText(html_content, 'html'))

        # Send
        with smtplib.SMTP(config.smtp_server, config.smtp_port) as server:
            server.starttls()
            server.login(config.smtp_user, config.smtp_password)
            server.send_message(msg)

        logger.info(f"Manifest sent for order {manifest.order_id} to {config.back_office_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send manifest email: {e}")
        return False


def save_manifest_pdf(manifest: OrderManifest, output_path: Path) -> bool:
    """Save manifest as HTML file (can be printed to PDF)."""
    try:
        html_content = manifest_to_html(manifest)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"Manifest saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save manifest: {e}")
        return False


def auto_send_manifest(order_id: int) -> bool:
    """Auto-generate and send manifest when order is ready."""
    manifest = generate_manifest(order_id)
    if not manifest:
        return False

    # Save local copy
    data_dir = get_app_dir() / "data" / "manifests"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"manifest_{order_id}_{timestamp}.html"
    save_manifest_pdf(manifest, data_dir / filename)

    # Send email
    return send_manifest_email(manifest)
