/**
 * ZPL label generator for Zebra ZP 230D (203 DPI).
 * Pre-printed 4x4" label stock. System prints three dynamic fields:
 *   1. UPC-A barcode (middle-left zone)
 *   2. Product name (right of barcode)
 *   3. Net weight in lb (middle-right zone, below product name)
 *
 * Coordinate reference (203 DPI, 812 x 812 dots):
 *   Top ~250 dots: pre-printed logo + company info
 *   Middle band (~250-550 dots): barcode left, product name + weight right
 *   Bottom ~260 dots: pre-printed safe handling + USDA stamp
 */

const DPI = 203;
const LABEL_WIDTH_DOTS = DPI * 4;   // 812
const LABEL_HEIGHT_DOTS = DPI * 4;  // 812

// --- Barcode zone (left side, vertically centered in the middle band) ---
// The barcode sits roughly from x=30 to x=350, y=270 to y=480
const BARCODE_X = 30;
const BARCODE_Y = 280;
const BARCODE_MODULE_WIDTH = 2;    // 2-dot module for scannable UPC-A at 203 DPI
const BARCODE_HEIGHT = 150;        // dots tall (about 0.74")

// "Keep Refrigerated or Frozen" is pre-printed below barcode, so we skip that.

// --- Product name zone (right of barcode) ---
const PRODUCT_NAME_X = 400;
const PRODUCT_NAME_Y = 300;

// --- Net weight zone (centered above the pre-printed USDA bug in bottom-right) ---
// USDA circle center is roughly x=660, y=700. Weight sits above it.
// Using ^FB (field block) with ^FO for centering over the USDA stamp.
const WEIGHT_BLOCK_X = 500;        // left edge of centering block
const WEIGHT_BLOCK_WIDTH = 300;    // width of centering block (covers USDA area)
const WEIGHT_LABEL_Y = 480;
const WEIGHT_VALUE_Y = 520;

/**
 * Generate ZPL for the dynamic portion of the Pomponio Ranch 4x4 label.
 *
 * @param barcode   12-digit UPC-A barcode string
 * @param productName   Human-readable product name (e.g. "Ribeye Steak")
 * @param weightLb  Net weight in pounds
 * @returns ZPL command string ready to send to printer
 */
export function generateLabelZpl(
  barcode: string,
  productName: string,
  weightLb: number,
  options?: { darkness?: number },
): string {
  const darkness = options?.darkness ?? 15;
  const weightStr = weightLb.toFixed(2) + " lb";

  // Truncate product name if it would overflow the label width
  // At font size 35, roughly 18 chars fit in the right half
  const displayName = productName.length > 24
    ? productName.slice(0, 23) + "..."
    : productName;

  const zpl = [
    // --- Label start ---
    "^XA",

    // Print darkness (0-30, configurable via settings)
    `~SD${darkness}`,

    // Label dimensions
    `^PW${LABEL_WIDTH_DOTS}`,
    `^LL${LABEL_HEIGHT_DOTS}`,

    // --- UPC-A Barcode ---
    `^FO${BARCODE_X},${BARCODE_Y}`,
    `^BY${BARCODE_MODULE_WIDTH}`,           // module width
    `^BU${BARCODE_HEIGHT},Y,N,Y`,           // UPC-A: height, interpretation line, check digit, interpretation above
    `^FD${barcode}^FS`,

    // --- Product Name ---
    `^FO${PRODUCT_NAME_X},${PRODUCT_NAME_Y}`,
    "^A0N,35,35",                            // Font 0, normal rotation, 35 dot height/width
    `^FD${displayName}^FS`,

    // --- Net Weight label (centered above USDA bug) ---
    `^FO${WEIGHT_BLOCK_X},${WEIGHT_LABEL_Y}`,
    "^A0N,28,28",                            // Smaller font for label
    `^FB${WEIGHT_BLOCK_WIDTH},1,0,C`,        // Field block: width, max lines, line spacing, Center
    "^FDNetWeight^FS",

    // --- Net Weight value (centered above USDA bug) ---
    `^FO${WEIGHT_BLOCK_X},${WEIGHT_VALUE_Y}`,
    "^A0N,50,50",                            // Large bold weight value
    `^FB${WEIGHT_BLOCK_WIDTH},1,0,C`,        // Field block: Center aligned
    `^FD${weightStr}^FS`,

    // --- Label end ---
    "^XZ",
  ];

  return zpl.join("\n");
}

/**
 * Generate ZPL for a box summary label.
 * Same physical layout as individual labels, but the product name
 * includes the quantity (e.g., "5x Filet Mignon") and the weight
 * is the total for that SKU group.
 */
export function generateBoxLabelZpl(
  barcode: string,
  productName: string,
  count: number,
  totalWeightLb: number,
  options?: { darkness?: number },
): string {
  const boxDarkness = options?.darkness ?? 15;
  const weightStr = totalWeightLb.toFixed(2) + " lb";
  const countLine = `${count}x ${productName}`;
  const displayName = countLine.length > 24
    ? countLine.slice(0, 23) + "..."
    : countLine;

  const zpl = [
    "^XA",
    `~SD${boxDarkness}`,
    `^PW${LABEL_WIDTH_DOTS}`,
    `^LL${LABEL_HEIGHT_DOTS}`,

    // --- UPC-A Barcode ---
    `^FO${BARCODE_X},${BARCODE_Y}`,
    `^BY${BARCODE_MODULE_WIDTH}`,
    `^BU${BARCODE_HEIGHT},Y,N,Y`,
    `^FD${barcode}^FS`,

    // --- Product Name with count ---
    `^FO${PRODUCT_NAME_X},${PRODUCT_NAME_Y}`,
    "^A0N,35,35",
    `^FD${displayName}^FS`,

    // --- Net Weight label (centered above USDA bug) ---
    `^FO${WEIGHT_BLOCK_X},${WEIGHT_LABEL_Y}`,
    "^A0N,28,28",
    `^FB${WEIGHT_BLOCK_WIDTH},1,0,C`,
    "^FDNetWeight^FS",

    // --- Net Weight value (centered above USDA bug) ---
    `^FO${WEIGHT_BLOCK_X},${WEIGHT_VALUE_Y}`,
    "^A0N,50,50",
    `^FB${WEIGHT_BLOCK_WIDTH},1,0,C`,
    `^FD${weightStr}^FS`,

    "^XZ",
  ];

  return zpl.join("\n");
}

/**
 * Label field positions for on-screen preview rendering.
 * All values in inches (4x4 label).
 */
export const LABEL_PREVIEW = {
  labelWidth: 4,
  labelHeight: 4,
  dpi: DPI,
  barcode: {
    xIn: BARCODE_X / DPI,
    yIn: BARCODE_Y / DPI,
    heightIn: BARCODE_HEIGHT / DPI,
  },
  productName: {
    xIn: PRODUCT_NAME_X / DPI,
    yIn: PRODUCT_NAME_Y / DPI,
    fontSizePt: 14,
  },
  weightBlock: {
    xIn: WEIGHT_BLOCK_X / DPI,
    widthIn: WEIGHT_BLOCK_WIDTH / DPI,
    labelYIn: WEIGHT_LABEL_Y / DPI,
    valueYIn: WEIGHT_VALUE_Y / DPI,
    fontSizePt: 20,
  },
} as const;
