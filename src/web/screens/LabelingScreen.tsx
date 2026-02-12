/**
 * Streamlined labeling workflow screen.
 * Auto-flow: select product -> auto-weigh -> auto-print -> show barcode -> return to products.
 * Optimized for 1280x1024 kiosk with game-style UI.
 */

import { useCallback, useEffect, useRef } from "react";
import { WorkflowState } from "../hooks/useWorkflow.ts";
import type { WorkflowContext } from "../hooks/useWorkflow.ts";
import { useSimulatedScale } from "../hooks/useSimulatedScale.ts";
import { generateBarcode } from "../data/barcode.ts";
import { generateLabelZpl } from "../data/zpl.ts";
import { StatusIndicator } from "../components/StatusIndicator.tsx";
import { WeightDisplay } from "../components/WeightDisplay.tsx";
import { TouchButton } from "../components/TouchButton.tsx";
import { LabelPreview } from "../components/LabelPreview.tsx";
import { PrintAnimation } from "../components/PrintAnimation.tsx";
import { CelebrationOverlay } from "../components/CelebrationOverlay.tsx";
import type { LogEventFn } from "../hooks/useAuditLog.ts";

interface LabelingScreenProps {
  workflowState: WorkflowState;
  context: WorkflowContext;
  onCaptureWeight: (w: number) => void;
  onPrintLabel: (barcode: string) => void;
  onComplete: () => void;
  onCancel: () => void;
  onPackageComplete: (data: {
    sku: string;
    productName: string;
    weightLb: number;
    barcode: string;
  }) => void;
  onNavigateToProducts: () => void;
  showToast: (msg: string) => void;
  scaleStabilityDelayMs: number;
  scaleMaxWeightLb: number;
  printDarkness: number;
  logEvent: LogEventFn;
}

export function LabelingScreen({
  workflowState,
  context,
  onCaptureWeight,
  onPrintLabel,
  onComplete,
  onCancel,
  onPackageComplete,
  onNavigateToProducts,
  showToast,
  scaleStabilityDelayMs,
  scaleMaxWeightLb,
  printDarkness,
  logEvent,
}: LabelingScreenProps) {
  const scale = useSimulatedScale({
    stabilityDelayMs: scaleStabilityDelayMs,
    maxWeight: scaleMaxWeightLb,
  });

  // Track whether we already fired the package-complete for this label cycle
  const completedRef = useRef(false);

  // Store the generated ZPL for potential USB/serial transmission
  const zplRef = useRef<string | null>(null);

  // Reset tracking ref when workflow returns to idle or product_selected
  useEffect(() => {
    if (workflowState === WorkflowState.IDLE || workflowState === WorkflowState.PRODUCT_SELECTED) {
      completedRef.current = false;
    }
  }, [workflowState]);

  // Auto-lock: when scale stabilizes with weight > 0, lock and capture
  useEffect(() => {
    if (
      workflowState === WorkflowState.PRODUCT_SELECTED &&
      scale.stable &&
      scale.weight > 0 &&
      !scale.locked
    ) {
      scale.lockWeight();
      logEvent("weight_captured", {
        weightLb: scale.weight,
        sku: context.sku ?? "",
        productName: context.productName ?? "",
      });
      onCaptureWeight(scale.weight);
    }
  }, [workflowState, scale.stable, scale.weight, scale.locked, onCaptureWeight, scale, logEvent, context.sku, context.productName]);

  // Auto-print: when weight is captured, generate barcode + ZPL and print
  useEffect(() => {
    if (
      workflowState === WorkflowState.WEIGHT_CAPTURED &&
      context.sku &&
      context.weightLb &&
      context.productName
    ) {
      const barcode = generateBarcode(context.sku, context.weightLb);
      const zpl = generateLabelZpl(barcode, context.productName, context.weightLb, { darkness: printDarkness });

      // Store ZPL for future USB/serial transmission to Zebra ZP 230D
      zplRef.current = zpl;

      // Log ZPL to console for development/debugging
      console.log("[ZPL Label Command]\n" + zpl);

      onPrintLabel(barcode);
    }
  }, [workflowState, context.sku, context.weightLb, context.productName, onPrintLabel, printDarkness]);

  // Auto-complete: show barcode for 2.5s, record package, then return to products
  useEffect(() => {
    if (
      workflowState === WorkflowState.LABEL_PRINTED &&
      context.barcode &&
      !completedRef.current
    ) {
      completedRef.current = true;

      onPackageComplete({
        sku: context.sku!,
        productName: context.productName!,
        weightLb: context.weightLb!,
        barcode: context.barcode,
      });
      showToast(`Label printed: ${context.productName} at ${context.weightLb?.toFixed(2)} lb`);

      const timer = setTimeout(() => {
        onComplete();
        scale.reset();
        onNavigateToProducts();
      }, 2500);

      return () => clearTimeout(timer);
    }
  }, [workflowState, context.barcode]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleCancel = useCallback(() => {
    logEvent("workflow_cancelled", {
      fromState: workflowState,
      sku: context.sku ?? null,
      productName: context.productName ?? null,
    });
    onCancel();
    scale.reset();
  }, [onCancel, scale, logEvent, workflowState, context.sku, context.productName]);

  return (
    <div className="flex flex-col h-full p-4 gap-3">
      {/* Status bar row: progress indicator + cancel button inline */}
      <div className="flex items-center gap-3 flex-shrink-0">
        <div className="flex-1">
          <StatusIndicator state={workflowState} />
        </div>
        {workflowState !== WorkflowState.IDLE && (
          <TouchButton
            text="Cancel"
            style="danger"
            size="sm"
            onClick={handleCancel}
            width="140px"
          />
        )}
      </div>

      {/* Main content area */}
      <div className="flex-1 flex flex-col gap-3 min-h-0">
        {/* IDLE: prompt to select product */}
        {workflowState === WorkflowState.IDLE && (
          <div className="card-elevated rounded-xl p-4 text-center text-[#606080] text-lg flex-shrink-0">
            Select a product from the Products tab to begin.
          </div>
        )}

        {/* Product info card (shown when a product is selected) */}
        {context.productName && workflowState !== WorkflowState.IDLE && (
          <div className="card-elevated rounded-xl p-4 flex-shrink-0">
            <div className="text-xs uppercase tracking-[0.15em] text-[#606080] mb-1">Selected Product</div>
            <div className="text-xl font-bold text-[#e8e8e8]">{context.productName}</div>
            <div className="text-sm font-mono text-[#00d4ff] mt-1">SKU: {context.sku}</div>
          </div>
        )}

        {/* PRODUCT_SELECTED: scale + auto-lock indicator */}
        {workflowState === WorkflowState.PRODUCT_SELECTED && (
          <div className="flex flex-col gap-3 flex-1 min-h-0">
            <WeightDisplay
              weight={scale.weight}
              stable={scale.stable}
              locked={scale.locked}
            />
            <div className="px-3 card-recessed rounded-xl py-3 flex-shrink-0">
              <label className="text-xs uppercase tracking-[0.15em] text-[#606080] mb-2 block">
                Simulated Scale (drag to set weight)
              </label>
              <input
                type="range"
                min="0"
                max={scale.maxWeight}
                step="0.01"
                value={scale.weight}
                onChange={e => scale.updateWeight(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-[#606080] mt-1">
                <span>0 lb</span>
                <span>{scale.maxWeight} lb</span>
              </div>
            </div>
            <div
              className="text-center text-sm py-3 rounded-xl flex-shrink-0"
              style={{
                color: scale.stable && scale.weight > 0 ? "#00d4ff" : "#606080",
                background: scale.stable && scale.weight > 0 ? "rgba(0,212,255,0.08)" : "transparent",
              }}
            >
              {scale.weight <= 0
                ? "Place item on scale..."
                : scale.stable
                  ? "Locking weight..."
                  : "Stabilizing..."}
            </div>
          </div>
        )}

        {/* WEIGHT_CAPTURED: brief transient state with print animation */}
        {workflowState === WorkflowState.WEIGHT_CAPTURED && (
          <div className="flex-1 flex items-center justify-center relative">
            <PrintAnimation visible={true} />
            <div className="text-center">
              <WeightDisplay weight={context.weightLb ?? 0} stable locked />
              <div
                className="text-lg font-bold mt-4"
                style={{
                  color: "#ffa500",
                  animation: "hud-pulse 1s ease-in-out infinite",
                }}
              >
                Generating label...
              </div>
            </div>
          </div>
        )}

        {/* LABEL_PRINTED: show label preview with countdown */}
        {workflowState === WorkflowState.LABEL_PRINTED && context.barcode && (
          <div className="flex-1 flex items-center justify-center">
            <div
              className="rounded-2xl p-6 text-center"
              style={{
                background: "rgba(45, 106, 45, 0.12)",
                border: "2px solid rgba(81, 207, 102, 0.3)",
                boxShadow: "0 0 40px rgba(81, 207, 102, 0.1)",
                animation: "scale-verified 400ms ease-out",
              }}
            >
              <div className="flex items-center justify-center gap-2 mb-4">
                <span
                  className="text-3xl"
                  style={{ textShadow: "0 0 20px rgba(81, 207, 102, 0.5)" }}
                >
                  &#x2713;
                </span>
                <span className="text-xl font-bold text-[#51cf66]">Label Printed</span>
              </div>

              {/* Physical label preview */}
              <div className="flex justify-center mb-4">
                <LabelPreview
                  barcode={context.barcode}
                  productName={context.productName!}
                  weightLb={context.weightLb!}
                  scale={0.7}
                />
              </div>

              {/* Numeric barcode readout */}
              <div
                className="text-lg font-mono font-bold tracking-[0.2em] mb-1"
                style={{
                  color: "#00d4ff",
                  textShadow: "0 0 20px rgba(0, 212, 255, 0.3)",
                }}
              >
                {context.barcode}
              </div>
              <div className="text-xs text-[#606080] mb-3">
                UPC-A: [0][{context.sku}][{context.barcode.slice(6, 11)}][{context.barcode.slice(11)}]
              </div>

              {/* Randomized celebration */}
              <CelebrationOverlay visible={true} />

              <div
                className="text-sm mt-3"
                style={{ color: "#606080" }}
              >
                Returning to products...
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
