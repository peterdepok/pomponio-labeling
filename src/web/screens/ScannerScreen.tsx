/**
 * Barcode Scanner screen.
 * Two primary functions:
 *   1. Package voiding: scan a package barcode, mark it as void with a reason
 *   2. Box audit: scan a box barcode, view contents, resend manifest email
 *
 * USB barcode scanners emulate keyboard: rapid digits + Enter.
 * The useBarcodeScanner hook captures this input when the tab is active.
 */

import { useState, useCallback } from "react";
import { useBarcodeScanner } from "../hooks/useBarcodeScanner.ts";
import { parseBarcode } from "../data/barcode.ts";
import { generateAnimalManifestCsv } from "../data/csv.ts";
import { sendReport } from "../data/email.ts";
import { TouchButton } from "../components/TouchButton.tsx";
import type { Package, Animal, Box } from "../hooks/useAppState.ts";
import type { LogEventFn } from "../hooks/useAuditLog.ts";

interface ScannerScreenProps {
  packages: Package[];
  boxes: Box[];
  animals: Animal[];
  onVoidPackage: (packageId: number, reason: string) => void;
  getAllPackagesForBox: (boxId: number) => Package[];
  emailRecipient: string;
  showToast: (msg: string) => void;
  logEvent: LogEventFn;
}

type ScannerMode =
  | { mode: "ready" }
  | { mode: "package-found"; pkg: Package }
  | { mode: "box-found"; boxId: number; box: Box; animal: Animal; packages: Package[] }
  | { mode: "void-confirm"; pkg: Package; reason: string }
  | { mode: "not-found"; barcode: string; message: string };

export function ScannerScreen({
  packages,
  boxes,
  animals,
  onVoidPackage,
  getAllPackagesForBox,
  emailRecipient,
  showToast,
  logEvent,
}: ScannerScreenProps) {
  const [scanMode, setScanMode] = useState<ScannerMode>({ mode: "ready" });
  const [lastBarcode, setLastBarcode] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const handleScan = useCallback((barcode: string) => {
    setLastBarcode(barcode);

    try {
      const parsed = parseBarcode(barcode);

      if (!parsed.valid) {
        setScanMode({ mode: "not-found", barcode, message: "Invalid check digit." });
        return;
      }

      if (parsed.quantityFlag === "0") {
        // Individual package barcode
        const pkg = packages.find(p => p.barcode === barcode);
        if (pkg) {
          setScanMode({ mode: "package-found", pkg });
        } else {
          setScanMode({ mode: "not-found", barcode, message: "Package not found in system." });
        }
      } else {
        // Box summary barcode: find matching box by SKU and weight
        const sku = parsed.sku;
        const targetWeight = parsed.weightLb;
        // Tolerance accounts for cumulative rounding across split box labels.
        // A box with 9 items averaging 1.12 lb each can drift ~0.04 lb per label
        // from barcode encoding (hundredths precision). 0.5 lb covers realistic
        // accumulation across multi-label splits.
        const tolerance = 0.5;

        let foundBox: Box | null = null;
        let foundAnimal: Animal | null = null;
        let foundPkgs: Package[] = [];

        for (const box of boxes) {
          const boxPkgs = getAllPackagesForBox(box.id);
          const skuPkgs = boxPkgs.filter(p => p.sku === sku && !p.voided);
          const skuWeight = skuPkgs.reduce((s, p) => s + p.weightLb, 0);

          if (Math.abs(skuWeight - targetWeight) <= tolerance && skuPkgs.length > 0) {
            foundBox = box;
            foundPkgs = boxPkgs; // all packages in box (including voided, for audit view)
            foundAnimal = animals.find(a => a.id === box.animalId) ?? null;
            break;
          }
        }

        if (foundBox && foundAnimal) {
          logEvent("box_audited", {
            boxId: foundBox.id,
            boxNumber: foundBox.boxNumber,
            packageCount: foundPkgs.filter(p => !p.voided).length,
            voidedCount: foundPkgs.filter(p => p.voided).length,
          });
          setScanMode({
            mode: "box-found",
            boxId: foundBox.id,
            box: foundBox,
            animal: foundAnimal,
            packages: foundPkgs,
          });
        } else {
          setScanMode({ mode: "not-found", barcode, message: "Box not found in system." });
        }
      }
    } catch {
      setScanMode({ mode: "not-found", barcode, message: "Invalid barcode format." });
    }
  }, [packages, boxes, animals, getAllPackagesForBox, logEvent]);

  useBarcodeScanner({
    enabled: true,
    onScan: handleScan,
  });

  const handleVoidStart = (pkg: Package) => {
    setScanMode({ mode: "void-confirm", pkg, reason: "" });
  };

  const handleVoidConfirm = () => {
    if (scanMode.mode !== "void-confirm") return;
    const reason = scanMode.reason.trim();
    if (!reason) {
      showToast("Please enter a reason for voiding.");
      return;
    }
    onVoidPackage(scanMode.pkg.id, reason);
    setScanMode({ mode: "ready" });
  };

  const handleResendManifest = async () => {
    if (scanMode.mode !== "box-found") return;
    if (!emailRecipient) {
      showToast("No email recipient configured. Go to Settings.");
      return;
    }

    const animal = scanMode.animal;
    setSending(true);

    const csv = generateAnimalManifestCsv(animal, boxes, packages);
    const safeName = animal.name.replace(/[^a-zA-Z0-9]/g, "_");
    const filename = `manifest_${safeName}_${Date.now()}.csv`;

    const result = await sendReport({
      to: emailRecipient,
      subject: `Pomponio Ranch Manifest (Updated): ${animal.name}`,
      csvContent: csv,
      filename,
    });

    setSending(false);

    logEvent("manifest_resent", {
      animalId: animal.id,
      animalName: animal.name,
      recipient: emailRecipient,
      success: result.ok,
    });

    if (result.ok) {
      showToast(`Manifest resent to ${emailRecipient}`);
    } else {
      showToast(`Email failed: ${result.error || "unknown"}`);
    }
  };

  const handleBack = () => setScanMode({ mode: "ready" });

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="flex items-center justify-between p-5 flex-shrink-0"
        style={{
          background: "linear-gradient(180deg, #1e2240 0%, #1a1a2e 100%)",
          borderBottom: "1px solid #2a2a4a",
        }}
      >
        <div>
          <h2 className="text-2xl font-bold text-[#e8e8e8]">Scanner</h2>
          <div className="text-xs uppercase tracking-[0.15em] text-[#606080] mt-1">
            Scan barcodes to audit or void packages
          </div>
        </div>
        {lastBarcode && (
          <div className="text-sm font-mono text-[#606080]">
            Last scan: {lastBarcode}
          </div>
        )}
      </div>

      {/* Content area */}
      <div className="flex-1 overflow-y-auto p-5">
        {/* READY mode: scan prompt */}
        {scanMode.mode === "ready" && (
          <div className="flex flex-col items-center justify-center h-full gap-6">
            <div
              className="text-8xl select-none"
              style={{
                animation: "anim-scan-pulse 2s ease-in-out infinite",
                filter: "drop-shadow(0 0 20px rgba(255, 109, 0, 0.3))",
              }}
            >
              {"\uD83D\uDCF7"}
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-[#e8e8e8] mb-2">
                Scan a Barcode
              </div>
              <div className="text-[#606080] text-lg max-w-md">
                Point the scanner at a package label to void it, or at a box label to audit contents.
              </div>
            </div>
            {/* Manual entry hint */}
            <div
              className="card-recessed rounded-xl px-6 py-3 text-center"
              style={{ maxWidth: "400px" }}
            >
              <div className="text-xs uppercase tracking-[0.15em] text-[#606080] mb-1">
                Manual Entry
              </div>
              <div className="text-sm text-[#a0a0b0]">
                Type 12 digits and press Enter to simulate a scan
              </div>
            </div>
          </div>
        )}

        {/* PACKAGE FOUND */}
        {scanMode.mode === "package-found" && (
          <div className="max-w-lg mx-auto">
            <div
              className="rounded-xl p-6"
              style={{
                background: "linear-gradient(145deg, #1e2240, #1a1a2e)",
                borderLeft: scanMode.pkg.voided ? "4px solid #ff6b6b" : "4px solid #00d4ff",
                boxShadow: "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
              }}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-[#e8e8e8]">
                  {scanMode.pkg.productName}
                </h3>
                {scanMode.pkg.voided && (
                  <span
                    className="px-2.5 py-1 text-xs rounded-md font-semibold"
                    style={{
                      background: "rgba(106, 45, 45, 0.3)",
                      color: "#ff6b6b",
                      border: "1px solid rgba(106, 45, 45, 0.4)",
                    }}
                  >
                    VOIDED
                  </span>
                )}
              </div>

              <div className="space-y-2 mb-4">
                <DetailRow label="SKU" value={scanMode.pkg.sku} accent />
                <DetailRow label="Weight" value={`${scanMode.pkg.weightLb.toFixed(2)} lb`} />
                <DetailRow label="Barcode" value={scanMode.pkg.barcode} accent mono />
                <DetailRow
                  label="Box"
                  value={`#${boxes.find(b => b.id === scanMode.pkg.boxId)?.boxNumber ?? "?"}`}
                />
                <DetailRow
                  label="Animal"
                  value={animals.find(a => a.id === scanMode.pkg.animalId)?.name ?? "Unknown"}
                />
                {scanMode.pkg.voided && scanMode.pkg.voidReason && (
                  <DetailRow label="Void reason" value={scanMode.pkg.voidReason} red />
                )}
              </div>

              <div className="flex gap-3">
                <TouchButton
                  text="Back"
                  style="secondary"
                  onClick={handleBack}
                  className="flex-1"
                />
                {!scanMode.pkg.voided && (
                  <TouchButton
                    text="Void Package"
                    style="danger"
                    onClick={() => handleVoidStart(scanMode.pkg)}
                    className="flex-1"
                  />
                )}
              </div>
            </div>
          </div>
        )}

        {/* BOX FOUND (audit view) */}
        {scanMode.mode === "box-found" && (
          <div className="max-w-2xl mx-auto">
            <div
              className="rounded-xl p-6"
              style={{
                background: "linear-gradient(145deg, #1e2240, #1a1a2e)",
                borderLeft: "4px solid #2e7d32",
                boxShadow: "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
              }}
            >
              {/* Box header */}
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-[#e8e8e8]">
                    Box #{scanMode.box.boxNumber}
                  </h3>
                  <div className="text-sm text-[#a0a0b0] mt-1">
                    Animal: {scanMode.animal.name}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-[#a0a0b0]">
                    {scanMode.packages.filter(p => !p.voided).length} active packages
                  </div>
                  <div className="text-sm text-[#a0a0b0]">
                    {scanMode.packages.filter(p => !p.voided).reduce((s, p) => s + p.weightLb, 0).toFixed(1)} lb
                  </div>
                  {scanMode.packages.some(p => p.voided) && (
                    <div className="text-xs text-[#ff6b6b] mt-1">
                      {scanMode.packages.filter(p => p.voided).length} voided
                    </div>
                  )}
                </div>
              </div>

              {/* Package list */}
              <div
                className="rounded-lg mb-4 overflow-y-auto"
                style={{
                  background: "#0d0d1a",
                  boxShadow: "inset 0 2px 8px rgba(0,0,0,0.6)",
                  maxHeight: "360px",
                }}
              >
                {scanMode.packages.length === 0 ? (
                  <div className="text-center text-[#606080] py-8">
                    No packages in this box.
                  </div>
                ) : (
                  <div className="divide-y divide-[#1a1a2e]">
                    {scanMode.packages.map(pkg => (
                      <div
                        key={pkg.id}
                        className="flex items-center justify-between px-4 py-3"
                        style={{
                          opacity: pkg.voided ? 0.5 : 1,
                          textDecoration: pkg.voided ? "line-through" : "none",
                        }}
                      >
                        <div className="flex-1">
                          <span className="text-sm text-[#e8e8e8]">
                            {pkg.productName}
                          </span>
                          <span className="text-xs font-mono text-[#00d4ff] ml-3">
                            {pkg.sku}
                          </span>
                        </div>
                        <div className="text-sm text-[#a0a0b0] w-24 text-right">
                          {pkg.weightLb.toFixed(2)} lb
                        </div>
                        {pkg.voided ? (
                          <span
                            className="text-xs text-[#ff6b6b] w-16 text-right"
                          >
                            VOID
                          </span>
                        ) : (
                          <span className="w-16" />
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                <TouchButton
                  text="Back"
                  style="secondary"
                  onClick={handleBack}
                  className="flex-1"
                />
                {emailRecipient && (
                  <TouchButton
                    text={sending ? "Sending..." : "Resend Manifest"}
                    style="primary"
                    onClick={handleResendManifest}
                    className="flex-1"
                  />
                )}
              </div>
            </div>
          </div>
        )}

        {/* VOID CONFIRM */}
        {scanMode.mode === "void-confirm" && (
          <div className="max-w-lg mx-auto">
            <div
              className="rounded-xl p-6"
              style={{
                background: "linear-gradient(145deg, #1e2240, #1a1a2e)",
                borderLeft: "4px solid #ff6b6b",
                boxShadow: "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
              }}
            >
              <h3 className="text-xl font-bold text-[#ff6b6b] mb-4">
                Void Package
              </h3>

              <div className="space-y-2 mb-4">
                <DetailRow label="Product" value={scanMode.pkg.productName} />
                <DetailRow label="SKU" value={scanMode.pkg.sku} accent />
                <DetailRow label="Weight" value={`${scanMode.pkg.weightLb.toFixed(2)} lb`} />
                <DetailRow label="Barcode" value={scanMode.pkg.barcode} mono />
              </div>

              <div className="mb-4">
                <label className="text-xs uppercase tracking-[0.15em] text-[#606080] mb-2 block">
                  Reason for voiding (required)
                </label>
                <input
                  type="text"
                  value={scanMode.reason}
                  onChange={e =>
                    setScanMode({ ...scanMode, reason: e.target.value })
                  }
                  onKeyDown={e => {
                    if (e.key === "Enter") handleVoidConfirm();
                  }}
                  placeholder="e.g. Damaged label, wrong weight, barcode unreadable"
                  className="w-full h-14 px-4 text-base rounded-xl bg-[#0d0d1a] text-[#e8e8e8] focus:outline-none"
                  style={{
                    border: "2px solid #2a2a4a",
                    boxShadow: "inset 0 2px 6px rgba(0,0,0,0.4)",
                  }}
                  onFocus={e => {
                    e.currentTarget.style.borderColor = "#ff6b6b";
                  }}
                  onBlur={e => {
                    e.currentTarget.style.borderColor = "#2a2a4a";
                  }}
                  autoFocus
                />
              </div>

              <div className="flex gap-3">
                <TouchButton
                  text="Cancel"
                  style="secondary"
                  onClick={handleBack}
                  className="flex-1"
                />
                <TouchButton
                  text="Confirm Void"
                  style="danger"
                  onClick={handleVoidConfirm}
                  className="flex-1"
                />
              </div>
            </div>
          </div>
        )}

        {/* NOT FOUND */}
        {scanMode.mode === "not-found" && (
          <div className="max-w-lg mx-auto">
            <div
              className="rounded-xl p-6 text-center"
              style={{
                background: "linear-gradient(145deg, #1e2240, #1a1a2e)",
                borderLeft: "4px solid #ffa500",
                boxShadow: "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
              }}
            >
              <div
                className="text-5xl mb-4 select-none"
                style={{ filter: "drop-shadow(0 0 12px rgba(255, 165, 0, 0.3))" }}
              >
                {"\u26A0\uFE0F"}
              </div>
              <h3 className="text-xl font-bold text-[#ffa500] mb-2">
                {scanMode.message}
              </h3>
              <div className="text-sm font-mono text-[#606080] mb-6">
                Scanned: {scanMode.barcode}
              </div>
              <TouchButton
                text="Scan Again"
                style="primary"
                onClick={handleBack}
                className="mx-auto"
                width="200px"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Helper component for detail rows ─────────────────────────

function DetailRow({
  label,
  value,
  accent,
  mono,
  red,
}: {
  label: string;
  value: string;
  accent?: boolean;
  mono?: boolean;
  red?: boolean;
}) {
  return (
    <div className="flex items-baseline gap-3">
      <span className="text-xs uppercase tracking-[0.15em] text-[#606080] w-24 flex-shrink-0">
        {label}
      </span>
      <span
        className={`text-sm ${mono ? "font-mono" : ""}`}
        style={{
          color: red ? "#ff6b6b" : accent ? "#00d4ff" : "#a0a0b0",
        }}
      >
        {value}
      </span>
    </div>
  );
}
