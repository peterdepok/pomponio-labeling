/**
 * EAN-13 barcode generation for Pomponio Ranch weight-embedded labels.
 *
 * Format (13 digits): [0][SKU padded to 6][weight*100 padded to 5][EAN-13 check digit]
 *
 * Matches the processor's barcode system. Each sales channel (Shopify retail,
 * wholesale, distributor) applies its own per-pound rate against the
 * weight encoded in the barcode.
 *
 * Position 1:    Always 0 (system prefix)
 * Positions 2-7: SKU zero-padded to 6 digits
 * Positions 8-12: Weight in hundredths of a pound (1.49 lb = 00149)
 * Position 13:   EAN-13 check digit (auto-calculated)
 *
 * Box labels use the same format with aggregate weight. The piece count
 * is displayed in the printed label text but not encoded in the barcode.
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

/**
 * Calculate the EAN-13 check digit for a 12-digit data string.
 *
 * Algorithm: multiply each of the 12 digits by alternating weights 1,3,1,3...
 * Sum the products. Check digit = (10 - (sum mod 10)) mod 10.
 *
 * This catches all single-digit transcription errors and most adjacent
 * transposition errors, which is why retail standards mandate it.
 */
export function calculateEan13CheckDigit(digits12: string): number {
  if (digits12.length !== 12 || !/^\d{12}$/.test(digits12)) {
    throw new BarcodeError(`Check digit input must be exactly 12 digits, got: '${digits12}'`);
  }

  let sum = 0;
  for (let i = 0; i < 12; i++) {
    const digit = parseInt(digits12[i], 10);
    const weight = i % 2 === 0 ? 1 : 3;
    sum += digit * weight;
  }

  return (10 - (sum % 10)) % 10;
}

/**
 * Generate a 13-digit EAN-13 barcode for an individual package label.
 * Format: 0 + SKU(6) + weight_encoded(5) + check_digit(1)
 */
export function generateBarcode(sku: string, weightLb: number): string {
  const sku5 = validateSku(sku);
  const sku6 = sku5.padStart(6, "0");
  const weight5 = encodeWeight(weightLb);
  const data12 = "0" + sku6 + weight5;
  const check = calculateEan13CheckDigit(data12);
  return data12 + check.toString();
}

/**
 * Generate a 13-digit EAN-13 barcode for a box summary label.
 * Same format as individual labels but with aggregate weight.
 * The count parameter is accepted for API compatibility but is NOT
 * encoded in the barcode (EAN-13 has no room for it). Count is
 * displayed in the printed label text instead.
 */
export function generateBoxBarcode(sku: string, _count: number, totalWeightLb: number): string {
  const sku5 = validateSku(sku);
  const sku6 = sku5.padStart(6, "0");
  const weight5 = encodeWeight(totalWeightLb);
  const data12 = "0" + sku6 + weight5;
  const check = calculateEan13CheckDigit(data12);
  return data12 + check.toString();
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
  sku: string;
  weightEncoded: string;
  weightLb: number;
  checkDigit: number;
}

export function parseBarcode(barcode: string): ParsedBarcode {
  if (barcode.length !== 13 || !/^\d{13}$/.test(barcode)) {
    throw new BarcodeError(`Barcode must be exactly 13 digits, got: '${barcode}'`);
  }

  // Validate check digit
  const data12 = barcode.slice(0, 12);
  const expectedCheck = calculateEan13CheckDigit(data12);
  const actualCheck = parseInt(barcode[12], 10);

  if (expectedCheck !== actualCheck) {
    throw new BarcodeError(
      `Invalid check digit: expected ${expectedCheck}, got ${actualCheck} in barcode '${barcode}'`,
    );
  }

  const weightHundredths = parseInt(barcode.slice(7, 12), 10);

  return {
    sku: barcode.slice(1, 7),
    weightEncoded: barcode.slice(7, 12),
    weightLb: weightHundredths / 100,
    checkDigit: actualCheck,
  };
}
