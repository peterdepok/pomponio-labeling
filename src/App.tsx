/**
 * Pomponio Ranch Labeling System - Web UI
 * Main application with tab navigation between screens.
 */

import { useState, useCallback, useRef, useEffect } from "react";
import { TabNav } from "./web/components/TabNav.tsx";
import type { TabId } from "./web/components/TabNav.tsx";
import { InfoBar } from "./web/components/InfoBar.tsx";
import { LabelingScreen } from "./web/screens/LabelingScreen.tsx";
import { ProductsScreen } from "./web/screens/ProductsScreen.tsx";
import { BoxesScreen } from "./web/screens/BoxesScreen.tsx";
import { AnimalsScreen } from "./web/screens/AnimalsScreen.tsx";
import { ScannerScreen } from "./web/screens/ScannerScreen.tsx";
import { SettingsScreen } from "./web/screens/SettingsScreen.tsx";
import { SpeedPopup } from "./web/components/SpeedPopup.tsx";
import { useWorkflow } from "./web/hooks/useWorkflow.ts";
import { useAppState } from "./web/hooks/useAppState.ts";
import { useSettings } from "./web/hooks/useSettings.ts";
import { useAuditLog } from "./web/hooks/useAuditLog.ts";
import { useSpeedTracker } from "./web/hooks/useSpeedTracker.ts";
import { SPEED_ENCOURAGEMENTS, CELEBRATION_ICONS } from "./web/data/celebrations.ts";
import { ConfirmDialog } from "./web/components/ConfirmDialog.tsx";
import { ScanPopup } from "./web/components/ScanPopup.tsx";
import { OfflineBanner } from "./web/components/OfflineBanner.tsx";
import { OperatorGateModal } from "./web/components/OperatorGateModal.tsx";
import { sendDailyReport } from "./web/data/reports.ts";
import { useBarcodeScanner } from "./web/hooks/useBarcodeScanner.ts";
import { useInactivityEmail } from "./web/hooks/useInactivityEmail.ts";
import { parseBarcode } from "./web/data/barcode.ts";
import { useAutoBackup } from "./web/hooks/useAutoBackup.ts";
import type { Product } from "./web/data/skus.ts";
import type { Package } from "./web/hooks/useAppState.ts";

function App() {
  const [activeTab, setActiveTab] = useState<TabId>("Animals");
  const [activeProductCategory, setActiveProductCategory] = useState<string>(() => {
    try {
      return localStorage.getItem("pomponio_activeCategory") || "Steaks";
    } catch { return "Steaks"; }
  });
  const [lastUsedProduct, setLastUsedProduct] = useState<Product | null>(null);
  const [showExitConfirm, setShowExitConfirm] = useState(false);
  const [scanPopup, setScanPopup] = useState<{
    pkg: Package | null;
    barcode: string;
    errorMessage?: string;
  } | null>(null);

  // Persist active category across page reloads
  useEffect(() => {
    try { localStorage.setItem("pomponio_activeCategory", activeProductCategory); }
    catch { /* quota exceeded, non-fatal */ }
  }, [activeProductCategory]);

  const workflow = useWorkflow();
  const app = useAppState();
  const { settings, setSetting, resetToDefaults, hydrated } = useSettings();
  const audit = useAuditLog(undefined, settings.operatorName || undefined);
  const { auditSyncOk } = audit;
  const speed = useSpeedTracker({ threshold: 4 });

  // Auto-email shift report after 2 hours of inactivity (safety net)
  const handleInactivityTimeout = useCallback(async () => {
    if (app.animals.length === 0 || !settings.emailRecipient) return;
    audit.logEvent("inactivity_auto_report", { timeoutHours: 2 });
    try {
      await sendDailyReport({
        animals: app.animals,
        boxes: app.boxes,
        packages: app.packages,
        emailRecipient: settings.emailRecipient,
        operatorName: settings.operatorName,
        logEvent: audit.logEvent,
        showToast: app.showToast,
        auditEntries: audit.entries,
      });
      app.showToast("Inactivity detected. Shift report auto-sent.");
    } catch {
      app.showToast("Inactivity report failed to send.", "error");
    }
  }, [app, settings.emailRecipient, audit]);

  const inactivity = useInactivityEmail({
    enabled: !!settings.emailRecipient && !!settings.operatorName,
    hasData: app.animals.length > 0,
    onInactivityTimeout: handleInactivityTimeout,
  });

  // Periodic backup: writes state snapshot to disk every 15s via Flask.
  // triggerBackup() fires an immediate backup after critical state changes.
  const { triggerBackup } = useAutoBackup({
    animals: app.animals,
    boxes: app.boxes,
    packages: app.packages,
    currentAnimalId: app.currentAnimalId,
    currentBoxId: app.currentBoxId,
  });

  // Operator gate: require name before allowing app interaction
  const handleOperatorConfirm = useCallback((name: string) => {
    setSetting("operatorName", name);
    audit.logEvent("operator_shift_started", { operatorName: name });
  }, [setSetting, audit]);

  // Change operator mid-shift: confirmation prevents accidental tap.
  const [showOperatorConfirm, setShowOperatorConfirm] = useState(false);

  const handleChangeOperator = useCallback(() => {
    setShowOperatorConfirm(true);
  }, []);

  const handleConfirmOperatorChange = useCallback(() => {
    setShowOperatorConfirm(false);
    const oldName = settings.operatorName;
    if (oldName) {
      audit.logEvent("operator_changed", { oldName, newName: "" });
    }
    setSetting("operatorName", "");
  }, [settings.operatorName, audit, setSetting]);

  // Global barcode scanner: active on all tabs except Scanner (which has its own).
  // When a scan is detected, shows a popup with package details and void option.
  const handleGlobalScan = useCallback((barcode: string) => {
    try {
      parseBarcode(barcode); // validate format and check digit
      // EAN-13 has no count field. Try matching as individual package first.
      const pkg = app.packages.find(p => p.barcode === barcode) ?? null;
      if (pkg) {
        setScanPopup({ pkg, barcode });
      } else {
        // Not a known individual package; could be a box barcode.
        setScanPopup({ pkg: null, barcode, errorMessage: "Package not found. Use the Scanner tab for box audit." });
      }
    } catch {
      setScanPopup({ pkg: null, barcode, errorMessage: "Invalid barcode format." });
    }
  }, [app.packages]);

  useBarcodeScanner({
    enabled: activeTab !== "Scanner",
    onScan: handleGlobalScan,
  });

  // Dismiss speed popup when operator switches tabs (prevents overlay blocking UI)
  useEffect(() => {
    if (speed.shouldShowEncouragement) {
      speed.dismissEncouragement();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // Stable random message for speed popup (pick new on each show)
  const speedMsgRef = useRef({ message: "", icon: "" });
  if (speed.shouldShowEncouragement && !speedMsgRef.current.message) {
    speedMsgRef.current = {
      message: SPEED_ENCOURAGEMENTS[Math.floor(Math.random() * SPEED_ENCOURAGEMENTS.length)],
      icon: CELEBRATION_ICONS[Math.floor(Math.random() * CELEBRATION_ICONS.length)],
    };
  } else if (!speed.shouldShowEncouragement) {
    speedMsgRef.current = { message: "", icon: "" };
  }

  const currentAnimal = app.animals.find(a => a.id === app.currentAnimalId) ?? null;
  const currentBox = app.boxes.find(b => b.id === app.currentBoxId) ?? null;
  const packageCount = app.currentBoxId ? app.getPackagesForBox(app.currentBoxId).length : 0;

  const handleNavigateToProducts = useCallback(() => {
    setActiveTab("Products");
  }, []);

  const handleProductSelect = useCallback((product: Product) => {
    // Cancel any current workflow, then select product
    if (workflow.state !== "idle") {
      workflow.cancel();
    }
    workflow.selectProduct(product.id, product.name, product.sku);
    audit.logEvent("product_selected", { sku: product.sku, productName: product.name });
    setLastUsedProduct(product);
    setActiveTab("Label");
  }, [workflow, audit]);

  const handlePackageComplete = useCallback((data: {
    sku: string;
    productName: string;
    weightLb: number;
    barcode: string;
  }) => {
    if (app.currentAnimalId === null || app.currentBoxId === null) {
      app.showToast("No animal/box selected. Go to Animals tab first.");
      return;
    }
    const product = app.getPackagesForBox(app.currentBoxId); // just to verify context
    void product;
    app.createPackage({
      productId: 0,
      productName: data.productName,
      sku: data.sku,
      animalId: app.currentAnimalId,
      boxId: app.currentBoxId,
      weightLb: data.weightLb,
      barcode: data.barcode,
    });
    audit.logEvent("label_printed", {
      barcode: data.barcode,
      sku: data.sku,
      productName: data.productName,
      weightLb: data.weightLb,
    });
    audit.logEvent("package_recorded", {
      barcode: data.barcode,
      sku: data.sku,
      productName: data.productName,
      weightLb: data.weightLb,
      animalId: app.currentAnimalId,
      boxId: app.currentBoxId,
    });
    speed.recordPackage();
    inactivity.recordActivity();
    triggerBackup();
  }, [app, audit, speed, inactivity, triggerBackup]);

  const handleCloseBox = useCallback((boxId: number) => {
    const box = app.boxes.find(b => b.id === boxId);
    const pkgs = app.getPackagesForBox(boxId);
    const totalWeight = pkgs.reduce((s, p) => s + p.weightLb, 0);
    audit.logEvent("box_closed", {
      boxId,
      boxNumber: box?.boxNumber ?? 0,
      packageCount: pkgs.length,
      totalWeight,
      labelCount: pkgs.length,
    });
    app.closeBox(boxId);
    triggerBackup();
    // Auto-create new box. The new box number is derived from the count
    // of existing boxes for this animal, rather than looking up the new
    // box in state (which hasn't re-rendered yet).
    if (app.currentAnimalId) {
      const existingCount = app.boxes.filter(b => b.animalId === app.currentAnimalId).length;
      const newBoxId = app.createBox(app.currentAnimalId);
      audit.logEvent("box_created", {
        boxId: newBoxId,
        animalId: app.currentAnimalId,
        boxNumber: existingCount + 1,
      });
      app.setCurrentBoxId(newBoxId);
    }
    app.showToast("Box closed. New box opened.");
  }, [app, audit, triggerBackup]);

  const handleReopenBox = useCallback((boxId: number) => {
    const box = app.boxes.find(b => b.id === boxId);
    audit.logEvent("box_reopened", { boxId, boxNumber: box?.boxNumber ?? 0 });
    app.reopenBox(boxId);
    app.setCurrentBoxId(boxId);
    app.showToast(`Box #${box?.boxNumber ?? "?"} reopened.`);
  }, [app, audit]);

  const handleVoidPackage = useCallback((packageId: number, reason: string) => {
    const pkg = app.packages.find(p => p.id === packageId);
    if (!pkg) return;
    app.voidPackage(packageId, reason);
    audit.logEvent("package_voided", {
      packageId,
      barcode: pkg.barcode,
      sku: pkg.sku,
      productName: pkg.productName,
      reason,
    });
    app.showToast(`Package voided: ${pkg.productName}`);
  }, [app, audit]);

  const handleNewBox = useCallback(() => {
    if (app.currentAnimalId) {
      const existingCount = app.boxes.filter(b => b.animalId === app.currentAnimalId).length;
      const newBoxId = app.createBox(app.currentAnimalId);
      audit.logEvent("box_created", {
        boxId: newBoxId,
        animalId: app.currentAnimalId,
        boxNumber: existingCount + 1,
      });
      app.setCurrentBoxId(newBoxId);
      app.showToast("New box created");
    }
  }, [app, audit]);

  const [isShuttingDown, setIsShuttingDown] = useState(false);

  const handleExitConfirm = useCallback(async () => {
    setShowExitConfirm(false);
    setIsShuttingDown(true);
    audit.logEvent("app_exit_initiated", {});

    // Fire shift report in background (do NOT await; exit must never hang
    // on a 30-second email timeout). The email will be queued for retry
    // on the server side if delivery fails.
    if (app.animals.length > 0 && settings.emailRecipient) {
      sendDailyReport({
        animals: app.animals,
        boxes: app.boxes,
        packages: app.packages,
        emailRecipient: settings.emailRecipient,
        operatorName: settings.operatorName,
        logEvent: audit.logEvent,
        showToast: app.showToast,
        auditEntries: audit.entries,
      }).catch(() => { /* queued for retry by server */ });
    }

    // Clear operator so the gate re-appears on next launch.
    setSetting("operatorName", "");

    // Brief pause to let final writes flush to localStorage
    await new Promise(r => setTimeout(r, 200));

    // Tell the server to shut down with a 5-second timeout. The
    // /api/shutdown endpoint kills the Chrome process tree and calls
    // os._exit(42), which the watchdog recognises as intentional.
    try {
      await fetch("/api/shutdown", {
        method: "POST",
        signal: AbortSignal.timeout(5000),
      });
    } catch {
      // Server may be down or timed out. The shutdown thread on the
      // server side is already running; Chrome will be killed shortly.
    }

    // The server kills Chrome from the backend (taskkill /T /F /PID on
    // Windows). No need for window.close() or about:blank; the browser
    // process will be terminated by the server within seconds.
  }, [app, settings, audit]);

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ backgroundColor: "#0d0d1a" }}>
      <OfflineBanner />
      {app.storageWarning && workflow.state === "idle" && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9998,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "rgba(0, 0, 0, 0.85)",
            backdropFilter: "blur(4px)",
            WebkitBackdropFilter: "blur(4px)",
          }}
        >
          <div
            style={{
              maxWidth: 440,
              width: "90%",
              borderRadius: 16,
              overflow: "hidden",
              background: "linear-gradient(145deg, #1e2240, #141428)",
              boxShadow: "0 8px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255,255,255,0.06)",
            }}
          >
            <div style={{ height: 4, background: "linear-gradient(90deg, #e65100, #ff6d00, #e65100)" }} />
            <div style={{ padding: 32, textAlign: "center" }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>&#x26A0;</div>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: "#ff6d00", marginBottom: 8 }}>
                Storage Full
              </h2>
              <p style={{ fontSize: 14, color: "#a0a0b0", marginBottom: 24, lineHeight: 1.5 }}>
                Browser storage is full. New packages cannot be saved safely.
                Close the current animal to free space, then continue.
              </p>
              <div style={{ display: "flex", gap: 12 }}>
                <button
                  onClick={() => setActiveTab("Animals")}
                  style={{
                    flex: 1,
                    height: 56,
                    borderRadius: 12,
                    border: "none",
                    cursor: "pointer",
                    fontSize: 16,
                    fontWeight: 700,
                    color: "#ffffff",
                    background: "linear-gradient(180deg, #ffa500, #e68a00)",
                    boxShadow: "0 4px 0 0 #b36b00, 0 6px 10px rgba(0,0,0,0.3)",
                  }}
                >
                  Go to Animals
                </button>
                <button
                  onClick={() => setActiveTab("Settings")}
                  style={{
                    flex: 1,
                    height: 56,
                    borderRadius: 12,
                    border: "none",
                    cursor: "pointer",
                    fontSize: 16,
                    fontWeight: 700,
                    color: "#a0a0b0",
                    background: "linear-gradient(180deg, #2a2a4a, #1e1e3a)",
                    boxShadow: "0 4px 0 0 #14142a, 0 6px 10px rgba(0,0,0,0.3)",
                  }}
                >
                  Settings
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {!auditSyncOk && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9997,
            background: "linear-gradient(90deg, #4a148c, #7b1fa2)",
            color: "#ffffff",
            textAlign: "center",
            padding: "8px 16px",
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: "0.03em",
            boxShadow: "0 2px 8px rgba(74, 20, 140, 0.5)",
          }}
        >
          AUDIT SYNC -- Some audit events have not reached the server. They will retry automatically.
        </div>
      )}
      <TabNav activeTab={activeTab} onTabChange={setActiveTab} onExit={() => setShowExitConfirm(true)} />

      <main className="flex-1 overflow-hidden">
        {activeTab === "Label" && (
          <LabelingScreen
            workflowState={workflow.state}
            context={workflow.context}
            onCaptureWeight={workflow.captureWeight}
            onPrintLabel={workflow.printLabel}
            onComplete={workflow.complete}
            onCancel={workflow.cancel}
            onPackageComplete={handlePackageComplete}
            onNavigateToProducts={handleNavigateToProducts}
            showToast={app.showToast}
            scaleStabilityDelayMs={settings.scaleStabilityDelayMs}
            scaleMaxWeightLb={settings.scaleMaxWeightLb}
            printDarkness={settings.printDarkness}
            scaleMode={settings.scaleMode}
            logEvent={audit.logEvent}
          />
        )}
        {activeTab === "Products" && (
          <ProductsScreen
            onSelectProduct={handleProductSelect}
            activeCategory={activeProductCategory}
            onCategoryChange={setActiveProductCategory}
            lastUsedProduct={lastUsedProduct}
          />
        )}
        {activeTab === "Boxes" && (
          <BoxesScreen
            currentAnimalId={app.currentAnimalId}
            animalName={currentAnimal?.name ?? null}
            boxes={app.boxes}
            getPackagesForBox={app.getPackagesForBox}
            onCloseBox={handleCloseBox}
            onReopenBox={handleReopenBox}
            onNewBox={handleNewBox}
            showToast={app.showToast}
            printDarkness={settings.printDarkness}
            logEvent={audit.logEvent}
          />
        )}
        {activeTab === "Animals" && (
          <AnimalsScreen
            animals={app.animals}
            boxes={app.boxes}
            packages={app.packages}
            operatorName={settings.operatorName}
            getPackagesForAnimal={app.getPackagesForAnimal}
            getManifestData={app.getManifestData}
            onCreateAnimal={app.createAnimal}
            onSelectAnimal={(id) => {
              const name = app.animals.find(a => a.id === id)?.name ?? "Unknown";
              audit.logEvent("animal_selected", { animalId: id, name });
              app.selectAnimal(id);
              app.showToast(`Active animal: ${name}`);
              setActiveTab("Products");
            }}
            onCloseAnimal={app.closeAnimal}
            onPurgeAnimal={app.purgeAnimal}
            emailRecipient={settings.emailRecipient}
            autoEmailOnAnimalClose={settings.autoEmailOnAnimalClose}
            autoEmailDailyReport={settings.autoEmailDailyReport}
            onNavigateToSettings={() => setActiveTab("Settings")}
            showToast={app.showToast}
            logEvent={audit.logEvent}
          />
        )}
        {activeTab === "Scanner" && (
          <ScannerScreen
            packages={app.packages}
            boxes={app.boxes}
            animals={app.animals}
            operatorName={settings.operatorName}
            onVoidPackage={handleVoidPackage}
            getAllPackagesForBox={app.getAllPackagesForBox}
            emailRecipient={settings.emailRecipient}
            showToast={app.showToast}
            logEvent={audit.logEvent}
          />
        )}
        {activeTab === "Settings" && (
          <SettingsScreen
            settings={settings}
            onSetSetting={setSetting}
            onResetSettings={resetToDefaults}
            onClearAllData={() => {
              audit.logEvent("data_cleared", {
                animalCount: app.animals.length,
                boxCount: app.boxes.length,
                packageCount: app.packages.length,
              });
              app.clearAllData();
            }}
            animalCount={app.animals.length}
            boxCount={app.boxes.length}
            packageCount={app.packages.length}
            showToast={app.showToast}
            auditEntries={audit.entries}
            onClearAuditLog={audit.clearLog}
            logEvent={audit.logEvent}
          />
        )}
      </main>

      <InfoBar
        animalName={currentAnimal?.name ?? null}
        boxNumber={currentBox?.boxNumber ?? null}
        packageCount={packageCount}
        operatorName={settings.operatorName || null}
        onChangeOperator={handleChangeOperator}
      />

      {/* Speed encouragement popup */}
      {speed.shouldShowEncouragement && speedMsgRef.current.message && (
        <SpeedPopup
          message={speedMsgRef.current.message}
          icon={speedMsgRef.current.icon}
          onDismiss={speed.dismissEncouragement}
        />
      )}

      {/* Global barcode scan popup */}
      {scanPopup && (
        <ScanPopup
          pkg={scanPopup.pkg}
          barcode={scanPopup.barcode}
          errorMessage={scanPopup.errorMessage}
          animals={app.animals}
          boxes={app.boxes}
          onVoid={handleVoidPackage}
          onDismiss={() => setScanPopup(null)}
        />
      )}

      {/* Exit confirmation dialog */}
      {showExitConfirm && (
        <ConfirmDialog
          title="End Shift"
          message="Send shift report with audit log and close?"
          confirmText="End Shift"
          onConfirm={handleExitConfirm}
          onCancel={() => setShowExitConfirm(false)}
        />
      )}

      {/* Change operator confirmation */}
      {showOperatorConfirm && (
        <ConfirmDialog
          title="Change Operator"
          message={`Log out ${settings.operatorName || "current operator"}?`}
          confirmText="Change"
          onConfirm={handleConfirmOperatorChange}
          onCancel={() => setShowOperatorConfirm(false)}
        />
      )}

      {/* Operator identification gate */}
      <OperatorGateModal
        isOpen={hydrated && !settings.operatorName}
        onConfirm={handleOperatorConfirm}
      />

      {/* Full-screen shutdown overlay (inline styles survive broken CSS pipeline) */}
      {isShuttingDown && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 10000,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#0d0d1a",
          }}
        >
          <div
            style={{
              width: 48,
              height: 48,
              border: "4px solid #2a2a4a",
              borderTopColor: "#00d4ff",
              borderRadius: "50%",
              animation: "spin 1s linear infinite",
            }}
          />
          <p
            style={{
              marginTop: 24,
              fontSize: 24,
              fontWeight: 700,
              color: "#e8e8e8",
              letterSpacing: "0.05em",
            }}
          >
            Shutting Down...
          </p>
          <p style={{ marginTop: 8, fontSize: 14, color: "#606080" }}>
            Sending report and closing. Please wait.
          </p>
        </div>
      )}

      {/* Floating toast */}
      {app.toast && (
        <div
          className="fixed bottom-20 right-6 z-50 glass-surface rounded-xl px-6 py-4 max-w-sm"
          style={{
            borderLeft: `3px solid ${app.toast.type === "error" ? "#ff6b6b" : "#51cf66"}`,
            animation: "toast-slide-in 300ms ease-out",
          }}
        >
          <span
            className="text-sm font-semibold"
            style={{ color: app.toast.type === "error" ? "#ff6b6b" : "#51cf66" }}
          >
            {app.toast.msg}
          </span>
        </div>
      )}
    </div>
  );
}

export default App;
