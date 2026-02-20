/**
 * EAN-13 barcode SVG renderer.
 * Encodes a 13-digit EAN-13 barcode as an SVG image.
 * Light-on-dark color scheme to match the app theme.
 * Zero external dependencies.
 *
 * EAN-13 structure (95 modules total):
 *   3 (start guard) + 42 (left 6 digits) + 5 (center guard) + 42 (right 6 digits) + 3 (end guard)
 *
 * The first digit selects the parity pattern for the left-hand digits.
 * All Pomponio barcodes start with 0, which uses LLLLLL parity.
 */

interface BarcodeImageProps {
  barcode: string;
  width?: number;
  height?: number;
}

/**
 * EAN-13 digit encoding patterns. Each digit is 7 modules wide.
 * L-code: odd parity, used for left-hand digits
 * G-code: even parity, also used for left-hand digits (parity varies by first digit)
 * R-code: even parity, used for right-hand digits (complement of L-code)
 *
 * 1 = bar (dark), 0 = space (light)
 */
const L_PATTERNS: string[] = [
  "0001101", // 0
  "0011001", // 1
  "0010011", // 2
  "0111101", // 3
  "0100011", // 4
  "0110001", // 5
  "0101111", // 6
  "0111011", // 7
  "0110111", // 8
  "0001011", // 9
];

const G_PATTERNS: string[] = [
  "0100111", // 0
  "0110011", // 1
  "0011011", // 2
  "0100001", // 3
  "0011101", // 4
  "0111001", // 5
  "0000101", // 6
  "0010001", // 7
  "0001001", // 8
  "0010111", // 9
];

const R_PATTERNS: string[] = [
  "1110010", // 0
  "1100110", // 1
  "1101100", // 2
  "1000010", // 3
  "1011100", // 4
  "1001110", // 5
  "1010000", // 6
  "1000100", // 7
  "1001000", // 8
  "1110100", // 9
];

/**
 * Parity patterns for left-hand digits, indexed by the first digit (0-9).
 * L = L-code, G = G-code.
 * For first digit 0: LLLLLL (all L encoding).
 */
const PARITY_PATTERNS: string[] = [
  "LLLLLL", // 0
  "LLGLGG", // 1
  "LLGGLG", // 2
  "LLGGGL", // 3
  "LGLLGG", // 4
  "LGGLLG", // 5
  "LGGGLL", // 6
  "LGLGLG", // 7
  "LGLGGL", // 8
  "LGGLGL", // 9
];

// Guard patterns
const START_GUARD = "101";
const CENTER_GUARD = "01010";
const END_GUARD = "101";

/**
 * Encode a 13-digit EAN-13 barcode into a bit string (1 = bar, 0 = space).
 * Total: 95 modules.
 */
function encodeEan13(barcode: string): string {
  const firstDigit = parseInt(barcode[0], 10);
  const parity = PARITY_PATTERNS[firstDigit];

  let bits = START_GUARD;

  // Left-hand digits (positions 1-6), using parity determined by first digit
  for (let i = 0; i < 6; i++) {
    const digit = parseInt(barcode[i + 1], 10);
    if (parity[i] === "L") {
      bits += L_PATTERNS[digit];
    } else {
      bits += G_PATTERNS[digit];
    }
  }

  bits += CENTER_GUARD;

  // Right-hand digits (positions 7-12), always R encoding
  for (let i = 0; i < 6; i++) {
    const digit = parseInt(barcode[i + 7], 10);
    bits += R_PATTERNS[digit];
  }

  bits += END_GUARD;

  return bits;
}

const BAR_COLOR = "#e0e0e0";
const TEXT_COLOR = "#a0a0b0";

export function BarcodeImage({ barcode, width = 280, height = 100 }: BarcodeImageProps) {
  if (!/^\d{13}$/.test(barcode)) return null;

  const bits = encodeEan13(barcode);
  if (bits.length !== 95) return null;

  const moduleW = width / (95 + 14); // 95 modules + 7 quiet zone each side
  const quietZone = 7 * moduleW;
  const barH = height * 0.75;
  const guardBarH = barH + height * 0.06; // Guard bars extend slightly below

  const bars: React.ReactElement[] = [];

  // Render each module, with taller bars for guard patterns
  for (let i = 0; i < bits.length; i++) {
    if (bits[i] === "1") {
      // Guard bars are taller: start (0-2), center (45-49), end (92-94)
      const isGuard =
        i < 3 ||
        (i >= 45 && i <= 49) ||
        i >= 92;

      bars.push(
        <rect
          key={i}
          x={quietZone + i * moduleW}
          y={0}
          width={moduleW}
          height={isGuard ? guardBarH : barH}
          fill={BAR_COLOR}
        />,
      );
    }
  }

  // Text: standard EAN-13 grouping: "X XXXXXX XXXXXX"
  const fontSize = Math.max(9, width * 0.035);
  const textY = height - 2;

  // First digit sits outside the bars to the left
  const firstDigitX = quietZone - moduleW * 2;
  // Left group (6 digits) centered under left half bars
  const leftGroupX = quietZone + 3 * moduleW + (42 * moduleW) / 2;
  // Right group (6 digits) centered under right half bars
  const rightGroupX = quietZone + 50 * moduleW + (42 * moduleW) / 2;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      xmlns="http://www.w3.org/2000/svg"
    >
      {bars}

      {/* First digit (outside left guard) */}
      <text
        x={firstDigitX}
        y={textY}
        textAnchor="middle"
        fill={TEXT_COLOR}
        fontFamily="monospace"
        fontSize={fontSize}
        fontWeight="bold"
      >
        {barcode[0]}
      </text>

      {/* Left group of 6 digits */}
      <text
        x={leftGroupX}
        y={textY}
        textAnchor="middle"
        fill={TEXT_COLOR}
        fontFamily="monospace"
        fontSize={fontSize}
        fontWeight="bold"
      >
        {barcode.slice(1, 7)}
      </text>

      {/* Right group of 6 digits */}
      <text
        x={rightGroupX}
        y={textY}
        textAnchor="middle"
        fill={TEXT_COLOR}
        fontFamily="monospace"
        fontSize={fontSize}
        fontWeight="bold"
      >
        {barcode.slice(7, 13)}
      </text>
    </svg>
  );
}
