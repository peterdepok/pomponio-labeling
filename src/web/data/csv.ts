/**
 * CSV report generation for Pomponio Ranch.
 * Pure functions with no network dependency. Works offline.
 *
 * Two report types:
 *   1. Animal manifest: per-animal SKU breakdown + box summary
 *   2. Daily production: all animals/boxes/packages for the session
 */

import type { Animal, Box, Package } from "../hooks/useAppState.ts";
import type { AuditEntry } from "../hooks/useAuditLog.ts";

// ── Shared types ───────────────────────────────────────────────

interface ManifestItem {
  sku: string;
  productName: string;
  quantity: number;
  weights: number[];
  totalWeight: number;
}

// ── CSV escaping ───────────────────────────────────────────────

/** Escape a field for CSV. Wraps in quotes if it contains commas, quotes, or newlines. */
function esc(value: string | number): string {
  const s = String(value);
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return '"' + s.replace(/"/g, '""') + '"';
  }
  return s;
}

function row(...cells: (string | number)[]): string {
  return cells.map(esc).join(",");
}

// ── SKU grouping (mirrors useAppState.getManifestData) ─────────

function groupBysku(pkgs: Package[]): ManifestItem[] {
  const grouped: Record<string, ManifestItem> = {};
  for (const pkg of pkgs) {
    if (!grouped[pkg.sku]) {
      grouped[pkg.sku] = {
        sku: pkg.sku,
        productName: pkg.productName,
        quantity: 0,
        weights: [],
        totalWeight: 0,
      };
    }
    grouped[pkg.sku].quantity += 1;
    grouped[pkg.sku].weights.push(pkg.weightLb);
    grouped[pkg.sku].totalWeight += pkg.weightLb;
  }
  return Object.values(grouped);
}

// ── Animal Manifest CSV ────────────────────────────────────────

export function generateAnimalManifestCsv(
  animal: Animal,
  boxes: Box[],
  packages: Package[],
  operatorName: string = "",
): string {
  const animalBoxes = boxes.filter(b => b.animalId === animal.id);
  const animalPkgs = packages.filter(p => p.animalId === animal.id && !p.voided);
  const manifestItems = groupBysku(animalPkgs);
  const totalWeight = animalPkgs.reduce((s, p) => s + p.weightLb, 0);
  const now = new Date().toLocaleString();

  const lines: string[] = [];

  // Header
  lines.push("Pomponio Ranch - Animal Manifest");
  if (operatorName) lines.push(row("Operator", operatorName));
  lines.push(row("Animal", animal.name));
  lines.push(row("Started", animal.startedAt));
  lines.push(row("Generated", now));
  lines.push(row("Total Packages", animalPkgs.length));
  lines.push(row("Total Weight (lb)", totalWeight.toFixed(2)));
  lines.push("");

  // SKU table
  lines.push(row("SKU", "Product Name", "Qty", "Individual Weights (lb)", "Total Weight (lb)"));
  for (const item of manifestItems) {
    const weightsStr = item.weights.map(w => w.toFixed(2)).join(", ");
    lines.push(row(
      item.sku,
      item.productName,
      item.quantity,
      weightsStr,
      item.totalWeight.toFixed(2),
    ));
  }
  lines.push(row("TOTAL", "", animalPkgs.length, "", totalWeight.toFixed(2)));
  lines.push("");

  // Box summary
  lines.push("Box Summary");
  lines.push(row("Box #", "Packages", "Total Weight (lb)", "Status"));
  for (const box of animalBoxes) {
    const boxPkgs = animalPkgs.filter(p => p.boxId === box.id);
    const boxWeight = boxPkgs.reduce((s, p) => s + p.weightLb, 0);
    lines.push(row(
      box.boxNumber,
      boxPkgs.length,
      boxWeight.toFixed(2),
      box.closed ? "Closed" : "Open",
    ));
  }

  return lines.join("\n");
}

// ── Daily Production CSV ───────────────────────────────────────

export function generateDailyProductionCsv(
  animals: Animal[],
  boxes: Box[],
  packages: Package[],
  operatorName: string = "",
): string {
  const activePkgs = packages.filter(p => !p.voided);
  const totalWeight = activePkgs.reduce((s, p) => s + p.weightLb, 0);
  const today = new Date().toLocaleDateString();
  const now = new Date().toLocaleString();

  const lines: string[] = [];

  // Header
  lines.push("Pomponio Ranch - Daily Production Report");
  if (operatorName) lines.push(row("Operator", operatorName));
  lines.push(row("Date", today));
  lines.push(row("Generated", now));
  lines.push(row("Animals", animals.length));
  lines.push(row("Boxes", boxes.length));
  lines.push(row("Packages", activePkgs.length));
  lines.push(row("Total Weight (lb)", totalWeight.toFixed(2)));
  lines.push("");

  // Per-animal sections
  for (const animal of animals) {
    const animalPkgs = activePkgs.filter(p => p.animalId === animal.id);
    const animalBoxes = boxes.filter(b => b.animalId === animal.id);
    const items = groupBysku(animalPkgs);
    const animalWeight = animalPkgs.reduce((s, p) => s + p.weightLb, 0);

    lines.push(`--- ${animal.name} ---`);
    lines.push(row("Started", animal.startedAt));
    lines.push(row("Status", animal.closedAt ? `Closed ${animal.closedAt}` : "Open"));
    lines.push(row("Boxes", animalBoxes.length));
    lines.push("");

    lines.push(row("SKU", "Product Name", "Qty", "Total Weight (lb)"));
    for (const item of items) {
      lines.push(row(item.sku, item.productName, item.quantity, item.totalWeight.toFixed(2)));
    }
    lines.push(row("Subtotal", "", animalPkgs.length, animalWeight.toFixed(2)));
    lines.push("");
  }

  // Grand total
  lines.push(row("GRAND TOTAL", "", activePkgs.length, totalWeight.toFixed(2)));

  return lines.join("\n");
}

// ── Audit Log CSV ─────────────────────────────────────────────

export function generateAuditLogCsv(entries: AuditEntry[], operatorName: string = ""): string {
  const lines: string[] = [];
  lines.push("Pomponio Ranch - Shift Audit Log");
  if (operatorName) lines.push(row("Operator", operatorName));
  lines.push(row("Generated", new Date().toLocaleString()));
  lines.push(row("Events", entries.length));
  lines.push("");
  lines.push(row("Timestamp", "Event Type", "Details"));
  for (const e of entries) {
    const details = Object.entries(e.payload)
      .map(([k, v]) => `${k}=${v}`)
      .join("; ");
    lines.push(row(e.timestamp, e.eventType, details));
  }
  return lines.join("\n");
}

// ── Server-side CSV export ─────────────────────────────────────

export interface ExportCsvResult {
  ok: boolean;
  path?: string;
  error?: string;
}

/**
 * Export CSV to disk via the Flask bridge.
 * Writes to USB drive if present, otherwise falls back to
 * C:\pomponio-labeling\exports\ (Windows) or PROJECT_ROOT/exports/ (dev).
 * No browser dialog is triggered.
 */
export async function exportCsv(
  content: string,
  filename: string,
): Promise<ExportCsvResult> {
  try {
    const res = await fetch("/api/export-csv", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csvContent: content, filename }),
    });
    const data = await res.json();
    return { ok: data.ok, path: data.path, error: data.error };
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    return { ok: false, error: msg };
  }
}
