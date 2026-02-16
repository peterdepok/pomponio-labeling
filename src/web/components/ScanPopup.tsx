/**
 * Global barcode scan popup.
 * Appears when a barcode is scanned while on any tab other than Scanner.
 * Shows package details with options to dismiss or void the package.
 * Reuses the same visual language as ConfirmDialog and ScannerScreen.
 */

import { useState } from "react";
import { TouchButton } from "./TouchButton.tsx";
import { KeyboardModal } from "./KeyboardModal.tsx";
import type { Package, Animal, Box } from "../hooks/useAppState.ts";

interface ScanPopupProps {
  /** The scanned package, or null if barcode was not found. */
  pkg: Package | null;
  /** Raw barcode string that was scanned. */
  barcode: string;
  /** Error message when barcode is invalid or not found. */
  errorMessage?: string;
  /** Lookup helpers for display context. */
  animals: Animal[];
  boxes: Box[];
  /** Void callback. */
  onVoid: (packageId: number, reason: string) => void;
  /** Close the popup. */
  onDismiss: () => void;
}

export function ScanPopup({
  pkg,
  barcode,
  errorMessage,
  animals,
  boxes,
  onVoid,
  onDismiss,
}: ScanPopupProps) {
  const [showVoidReason, setShowVoidReason] = useState(false);
  const [voidReason, setVoidReason] = useState("");
  const [showReasonKeyboard, setShowReasonKeyboard] = useState(false);

  const animal = pkg ? animals.find(a => a.id === pkg.animalId) : null;
  const box = pkg ? boxes.find(b => b.id === pkg.boxId) : null;

  const handleVoidConfirm = () => {
    if (!pkg || !voidReason.trim()) return;
    onVoid(pkg.id, voidReason.trim());
    onDismiss();
  };

  // Not found / error state
  if (!pkg) {
    return (
      <div
        className="fixed inset-0 flex items-center justify-center z-50"
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(4px)",
          WebkitBackdropFilter: "blur(4px)",
        }}
      >
        <div
          className="max-w-md w-full mx-4 rounded-2xl overflow-hidden"
          style={{
            background: "linear-gradient(145deg, #1e2240, #141428)",
            boxShadow: "0 8px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255,255,255,0.06)",
            animation: "dialog-scale-in 200ms ease-out",
          }}
        >
          <div
            className="h-1"
            style={{ background: "linear-gradient(90deg, #6a4a00, #ffa500, #6a4a00)" }}
          />
          <div className="p-8 text-center">
            <div className="text-4xl mb-3 select-none">&#x26A0;&#xFE0F;</div>
            <h2 className="text-2xl font-bold text-[#ffa500] mb-2">
              {errorMessage || "Not Found"}
            </h2>
            <div className="text-base font-mono text-[#a0a0b0] mb-6">
              Scanned: {barcode}
            </div>
            <TouchButton
              text="Dismiss"
              style="secondary"
              size="lg"
              onClick={onDismiss}
              width="200px"
              className="mx-auto"
            />
          </div>
        </div>
      </div>
    );
  }

  // Package found state
  return (
    <>
      <div
        className="fixed inset-0 flex items-center justify-center z-50"
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.75)",
          backdropFilter: "blur(4px)",
          WebkitBackdropFilter: "blur(4px)",
        }}
      >
        <div
          className="max-w-lg w-full mx-4 rounded-2xl overflow-hidden"
          style={{
            background: "linear-gradient(145deg, #1e2240, #141428)",
            boxShadow: "0 8px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255,255,255,0.06)",
            animation: "dialog-scale-in 200ms ease-out",
          }}
        >
          {/* Accent bar: cyan for active, red for voided */}
          <div
            className="h-1"
            style={{
              background: pkg.voided
                ? "linear-gradient(90deg, #6a2d2d, #ff6b6b, #6a2d2d)"
                : "linear-gradient(90deg, #0f3460, #00d4ff, #0f3460)",
            }}
          />

          <div className="p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-[#e8e8e8]">
                {pkg.productName}
              </h2>
              {pkg.voided && (
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

            {/* Detail rows */}
            <div className="space-y-2 mb-5">
              <Row label="SKU" value={pkg.sku} color="#00d4ff" />
              <Row label="Weight" value={`${pkg.weightLb.toFixed(2)} lb`} />
              <Row label="Barcode" value={pkg.barcode} mono color="#00d4ff" />
              <Row label="Box" value={`#${box?.boxNumber ?? "?"}`} />
              <Row label="Animal" value={animal?.name ?? "Unknown"} />
              {pkg.voided && pkg.voidReason && (
                <Row label="Void reason" value={pkg.voidReason} color="#ff6b6b" />
              )}
            </div>

            {/* Void reason input (shown when user starts void flow) */}
            {showVoidReason && !pkg.voided && (
              <div className="mb-4">
                <label className="text-xs uppercase tracking-[0.15em] text-[#606080] mb-2 block">
                  Reason for voiding (required)
                </label>
                <div
                  onClick={() => setShowReasonKeyboard(true)}
                  className="w-full h-14 px-4 text-lg rounded-xl bg-[#0d0d1a] flex items-center cursor-pointer"
                  style={{
                    border: "2px solid #2a2a4a",
                    boxShadow: "inset 0 2px 6px rgba(0,0,0,0.4)",
                    color: voidReason ? "#e8e8e8" : "#404060",
                  }}
                >
                  {voidReason || "Tap to enter reason..."}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <TouchButton
                text="Dismiss"
                style="secondary"
                size="lg"
                onClick={onDismiss}
                className="flex-1"
              />
              {!pkg.voided && !showVoidReason && (
                <TouchButton
                  text="Void Package"
                  style="danger"
                  size="lg"
                  onClick={() => setShowVoidReason(true)}
                  className="flex-1"
                />
              )}
              {!pkg.voided && showVoidReason && (
                <TouchButton
                  text="Confirm Void"
                  style="danger"
                  size="lg"
                  onClick={handleVoidConfirm}
                  className="flex-1"
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Keyboard modal for void reason */}
      <KeyboardModal
        isOpen={showReasonKeyboard}
        title="Void Reason"
        initialValue={voidReason}
        placeholder="e.g. Damaged label, wrong weight"
        onConfirm={(val) => {
          setVoidReason(val);
          setShowReasonKeyboard(false);
        }}
        onCancel={() => setShowReasonKeyboard(false)}
      />
    </>
  );
}

/** Compact detail row for the popup. */
function Row({
  label,
  value,
  mono,
  color,
}: {
  label: string;
  value: string;
  mono?: boolean;
  color?: string;
}) {
  return (
    <div className="flex items-baseline gap-3">
      <span className="text-sm uppercase tracking-[0.15em] text-[#808098] w-20 flex-shrink-0">
        {label}
      </span>
      <span
        className={`text-base ${mono ? "font-mono" : ""}`}
        style={{ color: color ?? "#a0a0b0" }}
      >
        {value}
      </span>
    </div>
  );
}
