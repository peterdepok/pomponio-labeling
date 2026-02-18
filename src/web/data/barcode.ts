/**
 * Code 128 barcode generation for Pomponio Ranch weight-embedded labels.
 *
 * Format (14 digits): [4-digit count][5-digit SKU][5-digit weight x 100]
 *
 * Individual packages use count 0001.
 * Box labels use actual piece count (1-9999).
 * No application-level check digit; Code 128 symbology provides its own.
 */

export class BarcodeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BarcodeError";
  }
}

export function validateSku(sku: string): string {
  if (!/^\d+$/.test(sku)) {
    throw new BarcodeError(`SKU must be numeric, got: '${sku}'`);
  }
  if (sku.length > 5) {
    throw new BarcodeError(`SKU must be 5 digits or fewer, got: '${sku}'`);
  }
  return sku.padStart(5, "0");
}

export function encodeWeight(weightLb: number): string {
  if (weightLb <= 0) {
    throw new BarcodeError(`Weight must be positive, got: ${weightLb}`);
  }

  const hundredths = Math.round(weightLb * 100);

  if (hundredths < 1) {
    throw new BarcodeError(`Weight too small to encode: ${weightLb} lb`);
  }
  if (hundredths > 99999) {
    throw new BarcodeError(`Weight exceeds maximum encodable value (999.99 lb): ${weightLb} lb`);
  }

  return hundredths.toString().padStart(5, "0");
}

function encodeCount(count: number): string {
  if (count < 1 || count > 9999) {
    throw new BarcodeError(`Count must be 1-9999, got: ${count}`);
  }
  return count.toString().padStart(4, "0");
}

/**
 * Generate a 14-digit barcode for an individual package label.
 * Format: 0001 + SKU(5) + weight_encoded(5)
 */
export function generateBarcode(sku: string, weightLb: number): string {
  const sku5 = validateSku(sku);
  const weight5 = encodeWeight(weightLb);
  return "0001" + sku5 + weight5;
}

/**
 * Generate a 14-digit barcode for a box summary label.
 * Format: count(4) + SKU(5) + weight_encoded(5)
 */
export function generateBoxBarcode(sku: string, count: number, totalWeightLb: number): string {
  const count4 = encodeCount(count);
  const sku5 = validateSku(sku);
  const weight5 = encodeWeight(totalWeightLb);
  return count4 + sku5 + weight5;
}

/**
 * A single box summary label to print.
 */
export interface BoxLabel {
  sku: string;
  productName: string;
  count: number;
  weightLb: number;
  barcode: string;
}

/**
 * Given a list of packages in a box, generate box summary labels.
 * Groups by SKU. One label per SKU with full count and total weight.
 */
export function generateBoxLabels(
  packages: Array<{ sku: string; productName: string; weightLb: number }>,
): BoxLabel[] {
  // Group by SKU
  const groups: Record<string, { productName: string; count: number; totalWeight: number }> = {};
  for (const pkg of packages) {
    if (!groups[pkg.sku]) {
      groups[pkg.sku] = { productName: pkg.productName, count: 0, totalWeight: 0 };
    }
    groups[pkg.sku].count += 1;
    groups[pkg.sku].totalWeight += pkg.weightLb;
  }

  const labels: BoxLabel[] = [];

  for (const [sku, group] of Object.entries(groups)) {
    // Round to 2 decimal places
    const roundedWeight = Math.round(group.totalWeight * 100) / 100;
    const barcode = generateBoxBarcode(sku, group.count, roundedWeight);

    labels.push({
      sku,
      productName: group.productName,
      count: group.count,
      weightLb: roundedWeight,
      barcode,
    });
  }

  return labels;
}

export interface ParsedBarcode {
  count: number;
  sku: string;
  weightEncoded: string;
  weightLb: number;
}

export function parseBarcode(barcode: string): ParsedBarcode {
  if (barcode.length !== 14 || !/^\d{14}$/.test(barcode)) {
    throw new BarcodeError(`Barcode must be exactly 14 digits, got: '${barcode}'`);
  }

  const count = parseInt(barcode.slice(0, 4), 10);
  const weightHundredths = parseInt(barcode.slice(9, 14), 10);

  return {
    count,
    sku: barcode.slice(4, 9),
    weightEncoded: barcode.slice(9, 14),
    weightLb: weightHundredths / 100,
  };
}
