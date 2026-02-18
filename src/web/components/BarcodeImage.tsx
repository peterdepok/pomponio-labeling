/**
 * Code 128 barcode SVG renderer.
 * Encodes a numeric string using Code 128 subset C (digit pairs)
 * for compact representation. Falls back to subset B for odd-length strings.
 * Light-on-dark color scheme to match the app theme.
 * Zero external dependencies.
 */

interface BarcodeImageProps {
  barcode: string;
  width?: number;
  height?: number;
}

/**
 * Code 128 bar patterns. Each symbol is defined by 6 alternating
 * bar/space widths that sum to 11 modules.
 *
 * Index 0-102: data/function values
 * Index 103-105: START A, START B, START C
 */
const CODE128_PATTERNS: string[] = [
  "212222", "222122", "222221", "121223", "121322", // 0-4
  "131222", "122213", "122312", "132212", "221213", // 5-9
  "221312", "231212", "112232", "122132", "122231", // 10-14
  "113222", "123122", "123221", "223211", "221132", // 15-19
  "221231", "213212", "223112", "312131", "311222", // 20-24
  "321122", "321221", "312212", "322112", "322211", // 25-29
  "212123", "212321", "232121", "111323", "131123", // 30-34
  "131321", "112313", "132113", "132311", "211313", // 35-39
  "231113", "231311", "112133", "112331", "132131", // 40-44
  "113123", "113321", "133121", "313121", "211331", // 45-49
  "231131", "213113", "213311", "213131", "311123", // 50-54
  "311321", "331121", "312113", "312311", "332111", // 55-59
  "314111", "221411", "431111", "111224", "111422", // 60-64
  "121124", "121421", "141122", "141221", "112214", // 65-69
  "112412", "122114", "122411", "142112", "142211", // 70-74
  "241211", "221114", "413111", "241112", "134111", // 75-79
  "111242", "121142", "121241", "114212", "124112", // 80-84
  "124211", "411212", "421112", "421211", "212141", // 85-89
  "214121", "412121", "111143", "111341", "131141", // 90-94
  "114113", "114311", "411113", "411311", "113141", // 95-99
  "114131", "311141", "411131",                     // 100-102
  "211412", "211214", "211232",                     // 103 (START A), 104 (START B), 105 (START C)
];

// Stop pattern: 7 elements summing to 13 modules (includes terminal bar)
const STOP_PATTERN = "2331112";

const START_C = 105;

/**
 * Encode a numeric string using Code 128 subset C.
 * Subset C encodes digit pairs (00-99) as single symbols.
 * For odd-length input, switches to subset B for the last digit.
 * Returns the list of Code 128 symbol values including start, data, check, (no stop).
 */
function encodeCode128(data: string): number[] {
  const values: number[] = [START_C];

  let i = 0;
  const pairEnd = data.length % 2 === 0 ? data.length : data.length - 1;

  while (i < pairEnd) {
    values.push(parseInt(data.slice(i, i + 2), 10));
    i += 2;
  }

  // Odd trailing digit: switch to subset B
  if (i < data.length) {
    values.push(100); // CODE B
    values.push(data.charCodeAt(i) - 32);
  }

  // Check digit: (start + sum(pos * value)) mod 103
  let checksum = values[0];
  for (let j = 1; j < values.length; j++) {
    checksum += j * values[j];
  }
  values.push(checksum % 103);

  return values;
}

/**
 * Convert Code 128 symbol values to a bit string (1 = bar, 0 = space).
 */
function valuesToBits(values: number[]): string {
  let bits = "";

  for (const val of values) {
    const pattern = CODE128_PATTERNS[val];
    if (!pattern) continue;
    let isBar = true;
    for (const ch of pattern) {
      const w = parseInt(ch, 10);
      bits += (isBar ? "1" : "0").repeat(w);
      isBar = !isBar;
    }
  }

  // Append stop pattern
  let isBar = true;
  for (const ch of STOP_PATTERN) {
    const w = parseInt(ch, 10);
    bits += (isBar ? "1" : "0").repeat(w);
    isBar = !isBar;
  }

  return bits;
}

const BAR_COLOR = "#e0e0e0";
const TEXT_COLOR = "#a0a0b0";

export function BarcodeImage({ barcode, width = 280, height = 100 }: BarcodeImageProps) {
  if (!/^\d+$/.test(barcode) || barcode.length < 1) return null;

  const values = encodeCode128(barcode);
  const bits = valuesToBits(values);
  if (bits.length === 0) return null;

  const moduleW = width / bits.length;
  const barH = height * 0.78;

  const bars: React.ReactElement[] = [];
  for (let i = 0; i < bits.length; i++) {
    if (bits[i] === "1") {
      bars.push(
        <rect
          key={i}
          x={i * moduleW}
          y={0}
          width={moduleW}
          height={barH}
          fill={BAR_COLOR}
        />,
      );
    }
  }

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

      {/* Full barcode digits centered below bars */}
      <text
        x={width / 2}
        y={textY}
        textAnchor="middle"
        fill={TEXT_COLOR}
        fontFamily="monospace"
        fontSize={fontSize}
        fontWeight="bold"
      >
        {barcode}
      </text>
    </svg>
  );
}
