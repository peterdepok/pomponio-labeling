/**
 * UPC-A barcode generation matching Python src/barcode.py exactly.
 *
 * Format (12 digits): [0][5-digit SKU][5-digit weight x 100][check digit]
 */

export class BarcodeError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "BarcodeError";
  }
}

export function calculateCheckDigit(digits11: string): number {
  if (digits11.length !== 11 || !/^\d{11}$/.test(digits11)) {
    throw new BarcodeError(`Check digit input must be exactly 11 digits, got: '${digits11}'`);
  }

  let oddSum = 0;
  let evenSum = 0;
  for (let i = 0; i < 11; i++) {
    const d = parseInt(digits11[i], 10);
    if (i % 2 === 0) {
      oddSum += d;
    } else {
      evenSum += d;
    }
  }
  const total = oddSum * 3 + evenSum;
  return (10 - (total % 10)) % 10;
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

export function generateBarcode(sku: string, weightLb: number): string {
  const sku5 = validateSku(sku);
  const weight5 = encodeWeight(weightLb);
  const first11 = "0" + sku5 + weight5;
  const check = calculateCheckDigit(first11);
  return first11 + check.toString();
}

/**
 * Generate a box summary barcode.
 * Format: [count 1-9][5-digit SKU][5-digit totalWeight x 100][check digit]
 * The leading digit is the item count (1-9) instead of 0.
 */
export function generateBoxBarcode(sku: string, count: number, totalWeightLb: number): string {
  if (count < 1 || count > 9) {
    throw new BarcodeError(`Box barcode count must be 1-9, got: ${count}`);
  }
  const sku5 = validateSku(sku);
  const weight5 = encodeWeight(totalWeightLb);
  const first11 = count.toString() + sku5 + weight5;
  const check = calculateCheckDigit(first11);
  return first11 + check.toString();
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
 * Groups by SKU. If a SKU group exceeds 9 items, splits into
 * multiple labels (max 9 per label) with weight proportionally divided.
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
    let remaining = group.count;
    let remainingWeight = group.totalWeight;

    while (remaining > 0) {
      const batch = Math.min(remaining, 9);
      // Proportional weight: use remaining count and remaining weight
      // so rounding errors don't accumulate across splits.
      // The last batch gets whatever weight is left (avoids drift).
      const isLastBatch = remaining - batch === 0;
      const batchWeight = isLastBatch
        ? remainingWeight
        : (batch / remaining) * remainingWeight;
      // Round to 2 decimal places
      const roundedWeight = Math.round(batchWeight * 100) / 100;

      const barcode = generateBoxBarcode(sku, batch, roundedWeight);

      labels.push({
        sku,
        productName: group.productName,
        count: batch,
        weightLb: roundedWeight,
        barcode,
      });

      remaining -= batch;
      remainingWeight -= roundedWeight;
    }
  }

  return labels;
}

export interface ParsedBarcode {
  quantityFlag: string;
  sku: string;
  weightEncoded: string;
  weightLb: number;
  checkDigit: number;
  valid: boolean;
}

export function parseBarcode(barcode: string): ParsedBarcode {
  if (barcode.length !== 12 || !/^\d{12}$/.test(barcode)) {
    throw new BarcodeError(`Barcode must be exactly 12 digits, got: '${barcode}'`);
  }

  const expectedCheck = calculateCheckDigit(barcode.slice(0, 11));
  const actualCheck = parseInt(barcode[11], 10);
  const weightHundredths = parseInt(barcode.slice(6, 11), 10);

  return {
    quantityFlag: barcode[0],
    sku: barcode.slice(1, 6),
    weightEncoded: barcode.slice(6, 11),
    weightLb: weightHundredths / 100,
    checkDigit: actualCheck,
    valid: expectedCheck === actualCheck,
  };
}
