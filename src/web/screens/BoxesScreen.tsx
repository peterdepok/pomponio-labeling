/**
 * Box management screen.
 * Card-elevated boxes with left border stripe (green open, gray closed).
 * On close: generates box summary labels (one per SKU, split at 9),
 * shows preview, then prints ZPL to Zebra and finalizes the box.
 * Closed boxes can be reopened (to add items) or reprinted (labels only).
 */

import { useState } from "react";
import { TouchButton } from "../components/TouchButton.tsx";
import { ConfirmDialog } from "../components/ConfirmDialog.tsx";
import { LabelPreview } from "../components/LabelPreview.tsx";
import { generateBoxLabels } from "../data/barcode.ts";
import type { BoxLabel } from "../data/barcode.ts";
import { generateBoxLabelZpl } from "../data/zpl.ts";
import { sendToPrinter } from "../data/printer.ts";
import type { Box, Package } from "../hooks/useAppState.ts";
import type { LogEventFn } from "../hooks/useAuditLog.ts";

interface BoxesScreenProps {
  currentAnimalId: number | null;
  animalName: string | null;
  boxes: Box[];
  getPackagesForBox: (boxId: number) => Package[];
  onCloseBox: (boxId: number) => void;
  onReopenBox: (boxId: number) => void;
  onNewBox: () => void;
  showToast: (msg: string) => void;
  printDarkness: number;
  logEvent: LogEventFn;
}

type BoxFlow =
  | { step: "confirm-close"; boxId: number }
  | { step: "close-preview"; boxId: number; labels: BoxLabel[] }
  | { step: "reprint-preview"; boxId: number; labels: BoxLabel[] }
  | null;

export function BoxesScreen({
  currentAnimalId,
  animalName,
  boxes,
  getPackagesForBox,
  onCloseBox,
  onReopenBox,
  onNewBox,
  showToast,
  printDarkness,
  logEvent,
}: BoxesScreenProps) {
  const [flow, setFlow] = useState<BoxFlow>(null);
  const [isPrinting, setIsPrinting] = useState(false);

  if (currentAnimalId === null) {
    return (
      <div className="flex items-center justify-center h-full text-[#606080] text-lg">
        Select an animal from the Animals tab first.
      </div>
    );
  }

  const animalBoxes = boxes.filter(b => b.animalId === currentAnimalId);

  // --- Close flow handlers ---

  const handleConfirmClose = (boxId: number) => {
    const pkgs = getPackagesForBox(boxId);
    if (pkgs.length === 0) {
      onCloseBox(boxId);
      setFlow(null);
      showToast("Empty box closed.");
      return;
    }
    const labels = generateBoxLabels(pkgs);
    setFlow({ step: "close-preview", boxId, labels });
  };

  const handlePrintAndClose = () => {
    if (!flow || flow.step !== "close-preview" || isPrinting) return;
    setIsPrinting(true);
    const box = animalBoxes.find(b => b.id === flow.boxId);
    logEvent("box_labels_printed", {
      boxId: flow.boxId,
      boxNumber: box?.boxNumber ?? 0,
      labelCount: flow.labels.length,
    });
    printLabels(flow.labels);
    showToast(`Printing ${flow.labels.length} box label${flow.labels.length !== 1 ? "s" : ""}...`);
    onCloseBox(flow.boxId);
    setFlow(null);
    setIsPrinting(false);
  };

  // --- Reprint flow handlers ---

  const handleReprintStart = (boxId: number) => {
    const pkgs = getPackagesForBox(boxId);
    if (pkgs.length === 0) {
      showToast("No packages in this box to reprint.");
      return;
    }
    const labels = generateBoxLabels(pkgs);
    setFlow({ step: "reprint-preview", boxId, labels });
  };

  const handleReprintConfirm = () => {
    if (!flow || flow.step !== "reprint-preview" || isPrinting) return;
    setIsPrinting(true);
    const box = animalBoxes.find(b => b.id === flow.boxId);
    logEvent("box_labels_reprinted", {
      boxId: flow.boxId,
      boxNumber: box?.boxNumber ?? 0,
      labelCount: flow.labels.length,
    });
    printLabels(flow.labels);
    showToast(`Reprinting ${flow.labels.length} box label${flow.labels.length !== 1 ? "s" : ""}...`);
    setFlow(null);
    setIsPrinting(false);
  };

  // --- Shared print utility ---

  const printLabels = (labels: BoxLabel[]) => {
    for (const label of labels) {
      const zpl = generateBoxLabelZpl(
        label.barcode,
        label.productName,
        label.count,
        label.weightLb,
        { darkness: printDarkness, sku: label.sku },
      );
      sendToPrinter(zpl).then(result => {
        if (!result.ok) {
          showToast(`Print failed: ${result.error ?? "unknown"}`);
        }
      });
    }
  };

  // --- Determine preview state (shared overlay for close and reprint) ---

  const previewFlow =
    flow?.step === "close-preview" || flow?.step === "reprint-preview"
      ? flow
      : null;

  const isReprint = previewFlow?.step === "reprint-preview";

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
          <h2 className="text-2xl font-bold text-[#e8e8e8]">Boxes</h2>
          <div className="text-xs uppercase tracking-[0.15em] text-[#606080] mt-1">Animal: {animalName}</div>
        </div>
        <TouchButton text="New Box" style="success" onClick={onNewBox} width="160px" />
      </div>

      {/* Box list */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {animalBoxes.length === 0 ? (
          <div className="text-center text-[#606080] py-12 text-lg">
            No boxes yet. Create one to start.
          </div>
        ) : (
          animalBoxes.map(box => {
            const pkgs = getPackagesForBox(box.id);
            const totalWeight = pkgs.reduce((sum, p) => sum + p.weightLb, 0);

            // Group by SKU for summary
            const skuGroups: Record<string, { name: string; count: number; weight: number }> = {};
            for (const pkg of pkgs) {
              if (!skuGroups[pkg.sku]) {
                skuGroups[pkg.sku] = { name: pkg.productName, count: 0, weight: 0 };
              }
              skuGroups[pkg.sku].count += 1;
              skuGroups[pkg.sku].weight += pkg.weightLb;
            }

            const stripeColor = box.closed ? "#404060" : "#51cf66";

            return (
              <div
                key={box.id}
                className="rounded-xl p-5"
                style={{
                  background: "linear-gradient(145deg, #1e2240, #1a1a2e)",
                  borderLeft: `4px solid ${stripeColor}`,
                  boxShadow: "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
                }}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h3 className="text-xl font-bold text-[#e8e8e8]">Box #{box.boxNumber}</h3>
                    {box.closed && (
                      <span
                        className="px-2.5 py-1 text-xs rounded-md font-semibold"
                        style={{
                          background: "rgba(106, 45, 45, 0.3)",
                          color: "#ff6b6b",
                          border: "1px solid rgba(106, 45, 45, 0.4)",
                        }}
                      >
                        CLOSED
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-[#a0a0b0]">
                    {pkgs.length} packages, {totalWeight.toFixed(1)} lb
                  </div>
                </div>

                {/* Package summary */}
                {Object.entries(skuGroups).length > 0 && (
                  <div className="mb-4 space-y-1">
                    {Object.entries(skuGroups).map(([sku, data]) => (
                      <div key={sku} className="text-sm text-[#a0a0b0]">
                        {data.count}x {data.name} ({data.weight.toFixed(1)} lb)
                      </div>
                    ))}
                  </div>
                )}

                {/* Action buttons */}
                {!box.closed ? (
                  <TouchButton
                    text="Close Box"
                    style="danger"
                    onClick={() => setFlow({ step: "confirm-close", boxId: box.id })}
                    className="w-full"
                  />
                ) : (
                  <div className="flex gap-3">
                    <TouchButton
                      text="Reopen Box"
                      style="primary"
                      onClick={() => onReopenBox(box.id)}
                      className="flex-1"
                    />
                    <TouchButton
                      text="Reprint Labels"
                      style="secondary"
                      onClick={() => handleReprintStart(box.id)}
                      className="flex-1"
                    />
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Step 1: Confirm close dialog */}
      {flow?.step === "confirm-close" && (
        <ConfirmDialog
          title="Close Box"
          message={`Close Box #${animalBoxes.find(b => b.id === flow.boxId)?.boxNumber}?\nBox labels will be printed for each product.`}
          confirmText="Print Labels & Close"
          onConfirm={() => handleConfirmClose(flow.boxId)}
          onCancel={() => setFlow(null)}
        />
      )}

      {/* Step 2: Label preview overlay (shared by close and reprint flows) */}
      {previewFlow && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          style={{ background: "rgba(0,0,0,0.7)" }}
        >
          <div
            className="rounded-2xl p-6 max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col"
            style={{
              background: "linear-gradient(180deg, #1e2240, #1a1a2e)",
              border: "1px solid #2a2a4a",
              boxShadow: "0 8px 40px rgba(0,0,0,0.6)",
            }}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-4 flex-shrink-0">
              <div>
                <h3 className="text-xl font-bold text-[#e8e8e8]">
                  Box #{animalBoxes.find(b => b.id === previewFlow.boxId)?.boxNumber} Labels
                  {isReprint && (
                    <span className="text-sm font-normal text-[#ffd43b] ml-3">REPRINT</span>
                  )}
                </h3>
                <div className="text-sm text-[#a0a0b0] mt-1">
                  {previewFlow.labels.length} label{previewFlow.labels.length !== 1 ? "s" : ""} to print
                </div>
              </div>
              <TouchButton
                text="Cancel"
                style="secondary"
                size="sm"
                onClick={() => setFlow(null)}
                width="120px"
              />
            </div>

            {/* Label previews (scrollable) */}
            <div className="flex-1 overflow-y-auto min-h-0 mb-4">
              <div className="grid grid-cols-2 gap-4">
                {previewFlow.labels.map((label, i) => (
                  <div key={i} className="flex flex-col items-center gap-2">
                    <LabelPreview
                      barcode={label.barcode}
                      productName={`${label.count}x ${label.productName}`}
                      weightLb={label.weightLb}
                      scale={0.5}
                    />
                    <div className="text-xs text-[#a0a0b0] text-center">
                      {label.count}x {label.productName}
                    </div>
                    <div className="text-xs font-mono text-[#00d4ff]">
                      {label.barcode}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Print button */}
            <div className="flex-shrink-0">
              <TouchButton
                text={
                  isReprint
                    ? `Reprint ${previewFlow.labels.length} Label${previewFlow.labels.length !== 1 ? "s" : ""}`
                    : `Print ${previewFlow.labels.length} Label${previewFlow.labels.length !== 1 ? "s" : ""} & Close Box`
                }
                style="success"
                onClick={isReprint ? handleReprintConfirm : handlePrintAndClose}
                className="w-full"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
