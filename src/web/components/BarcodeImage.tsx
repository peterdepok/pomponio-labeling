/**
 * UPC-A barcode SVG renderer.
 * Encodes a 12-digit barcode string into standard 95-module UPC-A bars.
 * Light-on-dark color scheme to match the app theme.
 * Zero external dependencies.
 */

interface BarcodeImageProps {
  barcode: string;
  width?: number;
  height?: number;
}

// L-encoding patterns for digits 0-9 (left side of UPC-A)
const L_PATTERNS: Record<string, string> = {
  "0": "0001101",
  "1": "0011001",
  "2": "0010011",
  "3": "0111101",
  "4": "0100011",
  "5": "0110001",
  "6": "0101111",
  "7": "0111011",
  "8": "0110111",
  "9": "0001011",
};

// R-encoding is the bitwise complement of L-encoding
function rPattern(digit: string): string {
  const l = L_PATTERNS[digit] ?? "0000000";
  return l
    .split("")
    .map(b => (b === "0" ? "1" : "0"))
    .join("");
}

function encodeBars(barcode: string): string {
  if (barcode.length !== 12) return "";

  const left = barcode.slice(0, 6);
  const right = barcode.slice(6, 12);

  let bits = "101"; // start guard
  for (const d of left) {
    bits += L_PATTERNS[d] ?? "0000000";
  }
  bits += "01010"; // center guard
  for (const d of right) {
    bits += rPattern(d);
  }
  bits += "101"; // end guard

  return bits;
}

const BAR_COLOR = "#e0e0e0";
const TEXT_COLOR = "#a0a0b0";

export function BarcodeImage({ barcode, width = 280, height = 100 }: BarcodeImageProps) {
  const bits = encodeBars(barcode);
  if (bits.length !== 95) return null;

  const moduleW = width / 95;
  const barH = height * 0.75;
  const guardH = height * 0.85; // guard bars extend below

  // Guard bar positions: start (0-2), center (45-49), end (92-94)
  const isGuard = (i: number) =>
    i < 3 || (i >= 45 && i <= 49) || i >= 92;

  const bars: React.ReactElement[] = [];
  for (let i = 0; i < 95; i++) {
    if (bits[i] === "1") {
      const h = isGuard(i) ? guardH : barH;
      bars.push(
        <rect
          key={i}
          x={i * moduleW}
          y={0}
          width={moduleW}
          height={h}
          fill={BAR_COLOR}
        />
      );
    }
  }

  // Digit positions: first digit far left, last digit far right,
  // left group centered under left bars, right group centered under right bars
  const fontSize = Math.max(10, width * 0.04);
  const textY = height - 2;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      xmlns="http://www.w3.org/2000/svg"
    >
      {bars}

      {/* Left group digits (positions 1-6, under bars 3-44) */}
      <text
        x={3 * moduleW + (42 * moduleW) / 2}
        y={textY}
        textAnchor="middle"
        fill={TEXT_COLOR}
        fontFamily="monospace"
        fontSize={fontSize}
        fontWeight="bold"
        letterSpacing={moduleW * 1.2}
      >
        {barcode.slice(0, 6)}
      </text>

      {/* Right group digits (positions 7-12, under bars 50-91) */}
      <text
        x={50 * moduleW + (42 * moduleW) / 2}
        y={textY}
        textAnchor="middle"
        fill={TEXT_COLOR}
        fontFamily="monospace"
        fontSize={fontSize}
        fontWeight="bold"
        letterSpacing={moduleW * 1.2}
      >
        {barcode.slice(6, 12)}
      </text>
    </svg>
  );
}
