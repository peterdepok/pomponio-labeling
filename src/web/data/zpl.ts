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

// --- Barcode zone (lower-left, where the FPO placeholder sits in the artwork) ---
// Coordinate system with ^POI: X increases left-to-right, Y increases top-to-bottom.
// Physical position: ~0.4" from left edge, ~2.5" from top.
const BARCODE_X = 55;
const BARCODE_Y = 404;
const BARCODE_MODULE_WIDTH = 3;    // 3-dot module for reliable scanning at arm's length
const BARCODE_HEIGHT = 100;        // dots tall (about 0.49")

// --- Product name zone (centered, where "GRASS-FED & FINISHED / WAGYU BEEF" sits) ---
// Physical position: centered horizontally, ~1.35" from top.
const PRODUCT_NAME_Y = 238;

// --- Net weight zone (lower-right quadrant box in the artwork) ---
// Physical center: ~3.0" from left, ~2.6" from top.
// Using ^FB (field block) for center alignment within the zone.
const WEIGHT_BLOCK_X = 480;
const WEIGHT_BLOCK_WIDTH = 320;    // width of centering block
const WEIGHT_LABEL_Y = 596;
const WEIGHT_VALUE_Y = 631;
const WEIGHT_OZ_Y = 686;

/**
 * SKU-keyed overrides for printed product names.
 * The full name in skus.ts includes sizing info useful for product selection
 * but inappropriate on certain printed labels:
 *   00100: strip "1.5in Thick" from Ribeye Steak Bone-In
 *   00101: strip "1.25in Thick" from New York Steak Boneless
 *   00103: strip "8oz" from Filet Mignon
 */
const PRINT_NAME_OVERRIDES: Record<string, string> = {
  "00100": "Ribeye Steak Bone-In",
  "00101": "New York Steak Boneless",
  "00103": "Filet Mignon",
  "00140": "Beef Shank",
};

function printName(productName: string, sku?: string): string {
  if (sku && PRINT_NAME_OVERRIDES[sku]) return PRINT_NAME_OVERRIDES[sku];
  return productName;
}

/**
 * Generate ZPL for the dynamic portion of the Pomponio Ranch 4x4 label.
 *
 * @param barcode   12-digit UPC-A barcode string
 * @param productName   Human-readable product name (e.g. "Ribeye Steak")
 * @param weightLb  Net weight in pounds
 * @param options.darkness  ZPL print darkness (0-30)
 * @param options.sku  SKU code; used to apply print-name overrides
 * @returns ZPL command string ready to send to printer
 */
export function generateLabelZpl(
  barcode: string,
  productName: string,
  weightLb: number,
  options?: { darkness?: number; sku?: string },
): string {
  const darkness = options?.darkness ?? 15;
  const weightStr = weightLb.toFixed(2) + " lb";
  const wholeLb = Math.floor(weightLb);
  const oz = ((weightLb - wholeLb) * 16).toFixed(1);
  const ozStr = `${wholeLb} lb ${oz} oz`;

  // Apply print-name override, then truncate if needed
  const resolvedName = printName(productName, options?.sku);
  const displayName = resolvedName.length > 24
    ? resolvedName.slice(0, 23) + "..."
    : resolvedName;

  const zpl = [
    // --- Label start ---
    "^XA",

    // Print darkness (0-30, configurable via settings)
    `~SD${darkness}`,

    // Label dimensions
    `^PW${LABEL_WIDTH_DOTS}`,
    `^LL${LABEL_HEIGHT_DOTS}`,
    "^POI",                                  // Invert orientation (180 degrees) for ZP 230D feed direction

    // --- UPC-A Barcode ---
    `^FO${BARCODE_X},${BARCODE_Y}`,
    `^BY${BARCODE_MODULE_WIDTH}`,           // module width
    `^BCN,${BARCODE_HEIGHT},Y,N,N`,         // Code 128: normal orientation, height, interpretation below, no check in data, no interpretation above
    `^FD${barcode}^FS`,

    // --- Product Name (cut), centered on label ---
    // Sits in the zone where the artwork shows "GRASS-FED & FINISHED / WAGYU BEEF"
    `^FO0,${PRODUCT_NAME_Y}`,
    "^A0N,45,45",                            // Font 0, normal rotation, 45 dot height/width
    `^FB${LABEL_WIDTH_DOTS},2,0,C`,          // Field block: full label width, up to 2 lines, centered
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

    // --- Net Weight in pounds + ounces (smaller, below decimal weight) ---
    `^FO${WEIGHT_BLOCK_X},${WEIGHT_OZ_Y}`,
    "^A0N,24,24",
    `^FB${WEIGHT_BLOCK_WIDTH},1,0,C`,
    `^FD${ozStr}^FS`,

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
  options?: { darkness?: number; sku?: string },
): string {
  const boxDarkness = options?.darkness ?? 15;
  const weightStr = totalWeightLb.toFixed(2) + " lb";
  const wholeLb = Math.floor(totalWeightLb);
  const oz = ((totalWeightLb - wholeLb) * 16).toFixed(1);
  const ozStr = `${wholeLb} lb ${oz} oz`;
  const resolvedName = printName(productName, options?.sku);
  const countLine = `${count}x ${resolvedName}`;
  const displayName = countLine.length > 24
    ? countLine.slice(0, 23) + "..."
    : countLine;

  const zpl = [
    "^XA",
    `~SD${boxDarkness}`,
    `^PW${LABEL_WIDTH_DOTS}`,
    `^LL${LABEL_HEIGHT_DOTS}`,
    "^POI",                                  // Invert orientation (180 degrees) for ZP 230D feed direction

    // --- UPC-A Barcode ---
    `^FO${BARCODE_X},${BARCODE_Y}`,
    `^BY${BARCODE_MODULE_WIDTH}`,
    `^BCN,${BARCODE_HEIGHT},Y,N,N`,         // Code 128: normal orientation, height, interpretation below, no check in data, no interpretation above
    `^FD${barcode}^FS`,

    // --- Product Name with count (cut), centered on label ---
    `^FO0,${PRODUCT_NAME_Y}`,
    "^A0N,45,45",
    `^FB${LABEL_WIDTH_DOTS},2,0,C`,          // Field block: full label width, up to 2 lines, centered
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

    // --- Net Weight in pounds + ounces (smaller, below decimal weight) ---
    `^FO${WEIGHT_BLOCK_X},${WEIGHT_OZ_Y}`,
    "^A0N,24,24",
    `^FB${WEIGHT_BLOCK_WIDTH},1,0,C`,
    `^FD${ozStr}^FS`,

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
    xIn: 0,
    yIn: PRODUCT_NAME_Y / DPI,
    fontSizePt: 14,
  },
  weightBlock: {
    xIn: WEIGHT_BLOCK_X / DPI,
    widthIn: WEIGHT_BLOCK_WIDTH / DPI,
    labelYIn: WEIGHT_LABEL_Y / DPI,
    valueYIn: WEIGHT_VALUE_Y / DPI,
    ozYIn: WEIGHT_OZ_Y / DPI,
    fontSizePt: 20,
  },
} as const;
