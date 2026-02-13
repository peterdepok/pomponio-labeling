/**
 * On-screen preview of the physical 4x4" label.
 * Shows the pre-printed elements as static placeholders and
 * renders the three dynamic fields (barcode, product name, weight)
 * in their actual positions matching the ZPL template.
 *
 * This is a visual confirmation for the line worker, not a print-exact replica.
 */

import { BarcodeImage } from "./BarcodeImage.tsx";

interface LabelPreviewProps {
  barcode: string;
  productName: string;
  weightLb: number;
  /** Scale factor for rendering. 1.0 = 4" displayed as 4" (too large). Default 0.6. */
  scale?: number;
}

export function LabelPreview({ barcode, productName, weightLb, scale = 0.6 }: LabelPreviewProps) {
  // Base dimensions in px at scale=1 (roughly 1" = 96px for screen display)
  const basePx = 96;
  const w = 4 * basePx * scale;
  const h = 4 * basePx * scale;
  const s = scale; // shorthand

  return (
    <div
      style={{
        width: w,
        height: h,
        background: "#f5f0eb",
        borderRadius: 6 * s,
        border: "1px solid #d0c8c0",
        position: "relative",
        overflow: "hidden",
        fontFamily: "sans-serif",
        boxShadow: "0 2px 12px rgba(0,0,0,0.15)",
      }}
    >
      {/* === PRE-PRINTED ELEMENTS (dimmed to show they are on the stock) === */}

      {/* Logo placeholder (top-left) */}
      <div
        style={{
          position: "absolute",
          left: 12 * s,
          top: 10 * s,
          width: 80 * s,
          height: 80 * s,
          borderRadius: "50%",
          border: `${1.5 * s}px solid #7a8a9a`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: 0.35,
        }}
      >
        <span style={{ fontSize: 14 * s, color: "#4a5a6a", fontWeight: "bold" }}>PR</span>
      </div>

      {/* Company info (top-right) */}
      <div
        style={{
          position: "absolute",
          left: 110 * s,
          top: 16 * s,
          opacity: 0.3,
          fontSize: 9 * s,
          color: "#4a4a4a",
          lineHeight: 1.3,
        }}
      >
        <div style={{ fontWeight: "bold", fontSize: 10 * s }}>Pomponio Ranch LLC</div>
        <div>650-726-2925</div>
        <div>San Gregorio, Ca.</div>
      </div>

      {/* Safe handling box (bottom-left) */}
      <div
        style={{
          position: "absolute",
          left: 8 * s,
          bottom: 10 * s,
          width: 180 * s,
          height: 80 * s,
          border: `${1 * s}px solid #999`,
          borderRadius: 3 * s,
          opacity: 0.2,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 7 * s,
          color: "#666",
          padding: 4 * s,
          textAlign: "center",
          lineHeight: 1.2,
        }}
      >
        SAFE HANDLING INSTRUCTIONS
      </div>

      {/* USDA stamp (bottom-right) */}
      <div
        style={{
          position: "absolute",
          right: 20 * s,
          bottom: 30 * s,
          width: 50 * s,
          height: 50 * s,
          borderRadius: "50%",
          border: `${1.5 * s}px solid #888`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          opacity: 0.25,
          fontSize: 6 * s,
          color: "#555",
          textAlign: "center",
          lineHeight: 1.1,
        }}
      >
        USDA<br/>EST.40268
      </div>

      {/* "Packed by" line (very bottom) */}
      <div
        style={{
          position: "absolute",
          right: 10 * s,
          bottom: 6 * s,
          opacity: 0.2,
          fontSize: 6.5 * s,
          color: "#666",
        }}
      >
        Packed by: Sinton and Sons
      </div>

      {/* === DYNAMIC FIELDS (full opacity, these are what the printer adds) === */}

      {/* UPC-A Barcode */}
      <div
        style={{
          position: "absolute",
          left: 14 * s,
          top: 120 * s,
        }}
      >
        <BarcodeImage
          barcode={barcode}
          width={170 * s}
          height={80 * s}
        />
      </div>

      {/* "Keep Refrigerated or Frozen" (pre-printed but near barcode) */}
      <div
        style={{
          position: "absolute",
          left: 14 * s,
          top: 205 * s,
          fontSize: 7 * s,
          color: "#666",
          opacity: 0.3,
        }}
      >
        Keep Refrigerated or Frozen
      </div>

      {/* Product Name (right of barcode) */}
      <div
        style={{
          position: "absolute",
          left: 200 * s,
          top: 130 * s,
          fontSize: 13 * s,
          fontWeight: "bold",
          color: "#1a1a1a",
          maxWidth: 170 * s,
          lineHeight: 1.2,
          wordWrap: "break-word",
        }}
      >
        {productName}
      </div>

      {/* Net Weight (centered above USDA bug) */}
      <div
        style={{
          position: "absolute",
          right: 0,
          bottom: 85 * s,
          width: 140 * s,
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 8 * s, color: "#666", marginBottom: 2 * s }}>NetWeight</div>
        <div style={{ fontSize: 18 * s, fontWeight: "bold", color: "#1a1a1a" }}>
          {weightLb.toFixed(2)} lb
        </div>
        <div style={{ fontSize: 10 * s, color: "#444", marginTop: 1 * s }}>
          {Math.floor(weightLb)} lb {((weightLb - Math.floor(weightLb)) * 16).toFixed(1)} oz
        </div>
      </div>
    </div>
  );
}
