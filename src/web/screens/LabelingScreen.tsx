/**
 * Streamlined labeling workflow screen.
 * Auto-flow: select product -> auto-weigh -> auto-print -> show barcode -> return to products.
 * Optimized for 1280x1024 kiosk with game-style UI.
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { WorkflowState } from "../hooks/useWorkflow.ts";
import type { WorkflowContext } from "../hooks/useWorkflow.ts";
import { useSimulatedScale } from "../hooks/useSimulatedScale.ts";
import { useScaleApi } from "../hooks/useScaleApi.ts";
import { generateBarcode } from "../data/barcode.ts";
import { generateLabelZpl } from "../data/zpl.ts";
import { sendToPrinter } from "../data/printer.ts";
import { StatusIndicator } from "../components/StatusIndicator.tsx";
import { WeightDisplay } from "../components/WeightDisplay.tsx";
import { TouchButton } from "../components/TouchButton.tsx";
import { LabelPreview } from "../components/LabelPreview.tsx";
import { PrintAnimation } from "../components/PrintAnimation.tsx";
import { CelebrationOverlay } from "../components/CelebrationOverlay.tsx";
import { KeyboardModal } from "../components/KeyboardModal.tsx";
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
  scaleMode: "simulated" | "serial";
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
  scaleMode,
  logEvent,
}: LabelingScreenProps) {
  // Both hooks must be called unconditionally (React rules).
  // The `enabled` flag on useScaleApi prevents fetch calls when not active.
  const simulatedScale = useSimulatedScale({
    stabilityDelayMs: scaleStabilityDelayMs,
    maxWeight: scaleMaxWeightLb,
  });
  const apiScale = useScaleApi({
    maxWeight: scaleMaxWeightLb,
    enabled: scaleMode === "serial",
  });
  const scale = scaleMode === "serial" ? apiScale : simulatedScale;

  // Track whether we already fired the package-complete for this label cycle
  const completedRef = useRef(false);

  // Store the generated ZPL for potential USB/serial transmission
  const zplRef = useRef<string | null>(null);

  // Print failure gate: prevent workflow from advancing if printer fails
  const [isPrinting, setIsPrinting] = useState(false);
  const [printFailed, setPrintFailed] = useState(false);
  const [printError, setPrintError] = useState<string | null>(null);

  // Scale manual override: shows after 10s of instability
  const [showWeightOverride, setShowWeightOverride] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const overrideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Reset tracking ref, print state, and override state on workflow reset
  useEffect(() => {
    if (workflowState === WorkflowState.IDLE || workflowState === WorkflowState.PRODUCT_SELECTED) {
      completedRef.current = false;
      setIsPrinting(false);
      setPrintFailed(false);
      setPrintError(null);
      setShowWeightOverride(false);
      setShowManualEntry(false);
      if (overrideTimerRef.current) {
        clearTimeout(overrideTimerRef.current);
        overrideTimerRef.current = null;
      }
    }
  }, [workflowState]);

  // 10-second instability timer: if scale has weight > 0 but is not stable
  // and not locked for 10 consecutive seconds, show override buttons.
  useEffect(() => {
    if (
      workflowState === WorkflowState.PRODUCT_SELECTED &&
      scale.weight > 0 &&
      !scale.stable &&
      !scale.locked
    ) {
      // Start timer if not already running
      if (!overrideTimerRef.current) {
        overrideTimerRef.current = setTimeout(() => {
          setShowWeightOverride(true);
        }, 10_000);
      }
    } else {
      // Conditions no longer met: clear timer and hide override
      if (overrideTimerRef.current) {
        clearTimeout(overrideTimerRef.current);
        overrideTimerRef.current = null;
      }
      // Only hide if the scale stabilized or weight dropped to 0
      // (don't hide if we're still in PRODUCT_SELECTED with override showing)
      if (scale.stable || scale.weight <= 0 || scale.locked) {
        setShowWeightOverride(false);
      }
    }

    return () => {
      if (overrideTimerRef.current) {
        clearTimeout(overrideTimerRef.current);
        overrideTimerRef.current = null;
      }
    };
  }, [workflowState, scale.weight, scale.stable, scale.locked]);

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

  // Store the barcode generated for the current print cycle
  const barcodeRef = useRef<string | null>(null);

  // Auto-print: when weight is captured, generate barcode + ZPL and print.
  // Awaits the printer response. Only advances workflow if print succeeds.
  useEffect(() => {
    if (
      workflowState === WorkflowState.WEIGHT_CAPTURED &&
      context.sku &&
      context.weightLb &&
      context.productName &&
      !isPrinting &&
      !printFailed
    ) {
      const barcode = generateBarcode(context.sku, context.weightLb);
      const zpl = generateLabelZpl(barcode, context.productName, context.weightLb, { darkness: printDarkness, sku: context.sku });

      // Store for retry
      zplRef.current = zpl;
      barcodeRef.current = barcode;

      console.log("[ZPL Label Command]\n" + zpl);

      setIsPrinting(true);
      setPrintFailed(false);
      setPrintError(null);

      (async () => {
        try {
          const result = await sendToPrinter(zpl);
          if (result.ok) {
            setIsPrinting(false);
            onPrintLabel(barcode);
          } else {
            logEvent("print_failed", { error: result.error, sku: context.sku, barcode });
            setIsPrinting(false);
            setPrintFailed(true);
            setPrintError(result.error ?? "Unknown print error");
            console.error("[Print Error]", result.error);
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : "Printer communication error";
          logEvent("print_failed", { error: msg, sku: context.sku ?? "", barcode });
          setIsPrinting(false);
          setPrintFailed(true);
          setPrintError(msg);
          console.error("[Print Error]", err);
        }
      })();
    }
  }, [workflowState, context.sku, context.weightLb, context.productName, onPrintLabel, printDarkness, isPrinting, printFailed, logEvent]);

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

  // Retry a failed print using the stored ZPL
  const handleRetryPrint = useCallback(async () => {
    if (!zplRef.current || !barcodeRef.current) return;
    setIsPrinting(true);
    setPrintFailed(false);
    setPrintError(null);
    logEvent("print_retry", { sku: context.sku ?? "", barcode: barcodeRef.current });

    try {
      const result = await sendToPrinter(zplRef.current);
      if (result.ok) {
        setIsPrinting(false);
        onPrintLabel(barcodeRef.current);
      } else {
        logEvent("print_failed", { error: result.error, sku: context.sku ?? "", barcode: barcodeRef.current });
        setIsPrinting(false);
        setPrintFailed(true);
        setPrintError(result.error ?? "Unknown print error");
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Printer communication error";
      logEvent("print_failed", { error: msg, sku: context.sku ?? "", barcode: barcodeRef.current ?? "" });
      setIsPrinting(false);
      setPrintFailed(true);
      setPrintError(msg);
    }
  }, [context.sku, logEvent, onPrintLabel]);

  // Cancel after a print failure: abort the entire workflow
  const handleCancelPrint = useCallback(() => {
    logEvent("print_cancel_after_failure", { sku: context.sku ?? null, error: printError });
    setPrintFailed(false);
    setPrintError(null);
    setIsPrinting(false);
    onCancel();
    scale.reset();
  }, [context.sku, printError, logEvent, onCancel, scale]);

  // Save without print: record the package even though the label failed.
  // This preserves the weight data in the manifest. The operator can apply
  // a hand-written label or reprint from the box view later.
  const handleSaveWithoutPrint = useCallback(() => {
    if (!barcodeRef.current || !context.sku || !context.weightLb || !context.productName) return;
    logEvent("print_skipped_save", {
      sku: context.sku,
      barcode: barcodeRef.current,
      weightLb: context.weightLb,
      error: printError,
    });
    // Record the package via the same path as a successful print
    onPackageComplete({
      sku: context.sku,
      productName: context.productName,
      weightLb: context.weightLb,
      barcode: barcodeRef.current,
    });
    showToast(`Saved WITHOUT label: ${context.productName} at ${context.weightLb.toFixed(2)} lb`);
    // Reset workflow
    setPrintFailed(false);
    setPrintError(null);
    setIsPrinting(false);
    onComplete();
    scale.reset();
    onNavigateToProducts();
  }, [context.sku, context.weightLb, context.productName, printError, logEvent, onPackageComplete, showToast, onComplete, scale, onNavigateToProducts]);

  // Force-lock: accept the current (unstable) reading
  const handleForceLock = useCallback(() => {
    if (scale.weight <= 0) return;
    logEvent("weight_override_forced", {
      weightLb: scale.weight,
      sku: context.sku ?? "",
      productName: context.productName ?? "",
    });
    scale.lockWeight({ force: true });
    onCaptureWeight(scale.weight);
    setShowWeightOverride(false);
  }, [scale, logEvent, context.sku, context.productName, onCaptureWeight]);

  // Manual weight entry: validate and capture
  const handleManualWeight = useCallback((value: string) => {
    const parsed = parseFloat(value);
    if (isNaN(parsed) || parsed <= 0) {
      showToast("Weight must be greater than 0.");
      return;
    }
    if (parsed > scaleMaxWeightLb) {
      showToast(`Weight cannot exceed ${scaleMaxWeightLb} lb.`);
      return;
    }
    logEvent("weight_manual_entry", {
      weightLb: parsed,
      sku: context.sku ?? "",
      productName: context.productName ?? "",
    });
    setShowManualEntry(false);
    setShowWeightOverride(false);
    // Bypass scale entirely: capture the manually entered weight
    onCaptureWeight(parsed);
  }, [scaleMaxWeightLb, logEvent, context.sku, context.productName, onCaptureWeight, showToast]);

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
            {scaleMode === "simulated" ? (
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
            ) : (
              <div className="px-3 card-recessed rounded-xl py-3 flex-shrink-0 text-center">
                <div className="text-xs uppercase tracking-[0.15em] text-[#606080] mb-1">
                  Brecknell 6710U
                </div>
                {"scaleError" in scale && (scale as { scaleError: string | null }).scaleError ? (
                  <div
                    className="text-sm font-bold py-2 px-4 rounded-lg mt-1"
                    style={{
                      color: "#ff6b6b",
                      background: "rgba(255, 107, 107, 0.1)",
                      border: "1px solid rgba(255, 107, 107, 0.3)",
                    }}
                  >
                    SCALE ERROR: {(scale as { scaleError: string | null }).scaleError}
                  </div>
                ) : (
                  <div className="text-sm text-[#a0a0b0]">
                    Reading from scale...
                  </div>
                )}
              </div>
            )}
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

            {/* Scale override buttons: appear after 10s of instability */}
            {showWeightOverride && !scale.locked && (
              <div
                className="flex gap-3 flex-shrink-0 px-2"
                style={{ animation: "toast-slide-in 300ms ease-out" }}
              >
                <button
                  onClick={handleForceLock}
                  className="flex-1 rounded-xl font-bold text-base"
                  style={{
                    height: "56px",
                    color: "#ffffff",
                    background: "linear-gradient(180deg, #ffa500, #e68a00)",
                    border: "none",
                    cursor: "pointer",
                    boxShadow: "0 4px 0 0 #b36b00, 0 6px 10px rgba(0,0,0,0.3)",
                  }}
                >
                  Lock at {scale.weight.toFixed(2)} lb
                </button>
                <button
                  onClick={() => setShowManualEntry(true)}
                  className="flex-1 rounded-xl font-bold text-base"
                  style={{
                    height: "56px",
                    color: "#ffffff",
                    background: "linear-gradient(180deg, #7c4dff, #651fff)",
                    border: "none",
                    cursor: "pointer",
                    boxShadow: "0 4px 0 0 #4a148c, 0 6px 10px rgba(0,0,0,0.3)",
                  }}
                >
                  Manual Entry
                </button>
              </div>
            )}

            {/* Manual weight entry keyboard modal */}
            <KeyboardModal
              isOpen={showManualEntry}
              title="Enter Weight (lb)"
              initialValue=""
              placeholder="0.00"
              onConfirm={handleManualWeight}
              onCancel={() => setShowManualEntry(false)}
              showNumbers
            />
          </div>
        )}

        {/* WEIGHT_CAPTURED: print animation, or print failure overlay */}
        {workflowState === WorkflowState.WEIGHT_CAPTURED && (
          <div className="flex-1 flex items-center justify-center relative">
            {printFailed ? (
              /* Print failure: large retry/cancel buttons for gloved hands */
              <div
                className="rounded-2xl p-6 text-center max-w-md w-full mx-4"
                style={{
                  background: "rgba(255, 107, 107, 0.08)",
                  border: "2px solid rgba(255, 107, 107, 0.4)",
                  boxShadow: "0 0 40px rgba(255, 107, 107, 0.1)",
                }}
              >
                <div className="text-4xl mb-3" style={{ color: "#ff6b6b" }}>&#x26A0;</div>
                <div className="text-xl font-bold mb-2" style={{ color: "#ff6b6b" }}>
                  Print Failed
                </div>
                <div
                  className="text-sm font-mono mb-4 px-3 py-2 rounded-lg"
                  style={{
                    color: "#a08080",
                    background: "rgba(0,0,0,0.3)",
                    wordBreak: "break-word",
                  }}
                >
                  {printError}
                </div>
                <div className="text-xs text-[#606080] mb-4">
                  Package will NOT be recorded until label prints or you save without print.
                </div>
                <div className="flex gap-3 mb-3">
                  <button
                    onClick={handleRetryPrint}
                    className="flex-1 rounded-xl font-bold text-lg"
                    style={{
                      height: "64px",
                      color: "#ffffff",
                      background: "linear-gradient(180deg, #ffa500, #e68a00)",
                      border: "none",
                      cursor: "pointer",
                      boxShadow: "0 4px 0 0 #b36b00, 0 6px 10px rgba(0,0,0,0.3)",
                    }}
                  >
                    Retry Print
                  </button>
                  <button
                    onClick={handleCancelPrint}
                    className="flex-1 rounded-xl font-bold text-lg"
                    style={{
                      height: "64px",
                      color: "#ffffff",
                      background: "linear-gradient(180deg, #e53935, #c62828)",
                      border: "none",
                      cursor: "pointer",
                      boxShadow: "0 4px 0 0 #8e0000, 0 6px 10px rgba(0,0,0,0.3)",
                    }}
                  >
                    Cancel
                  </button>
                </div>
                <button
                  onClick={handleSaveWithoutPrint}
                  className="w-full rounded-xl font-bold text-base"
                  style={{
                    height: "56px",
                    color: "#ffffff",
                    background: "linear-gradient(180deg, #7c4dff, #651fff)",
                    border: "none",
                    cursor: "pointer",
                    boxShadow: "0 4px 0 0 #4a148c, 0 6px 10px rgba(0,0,0,0.3)",
                  }}
                >
                  Save Without Print
                </button>
              </div>
            ) : (
              /* Normal print animation */
              <>
                <PrintAnimation visible={true} />
                <div className="text-center">
                  <WeightDisplay weight={context.weightLb ?? 0} stable locked />

                  {/* Live preview of the label about to print */}
                  {context.sku && context.weightLb && context.productName && (
                    <div className="flex justify-center mt-3 mb-2">
                      <LabelPreview
                        barcode={generateBarcode(context.sku, context.weightLb)}
                        productName={context.productName}
                        weightLb={context.weightLb}
                        scale={0.55}
                      />
                    </div>
                  )}

                  <div
                    className="text-lg font-bold mt-4"
                    style={{
                      color: "#ffa500",
                      animation: "hud-pulse 1s ease-in-out infinite",
                    }}
                  >
                    {isPrinting ? "Sending to printer..." : "Generating label..."}
                  </div>
                </div>
              </>
            )}
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
