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
  const { settings, setSetting, resetToDefaults } = useSettings();
  const audit = useAuditLog(undefined, settings.operatorName || undefined);
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
    enabled: !!settings.emailRecipient,
    hasData: app.animals.length > 0,
    onInactivityTimeout: handleInactivityTimeout,
  });

  // Periodic backup: writes state snapshot to disk every 60s via Flask
  useAutoBackup({
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

  // Change operator mid-shift: logs the switch and clears operator name,
  // which automatically reopens OperatorGateModal (gated on !operatorName).
  const handleChangeOperator = useCallback(() => {
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
      const parsed = parseBarcode(barcode);
      if (!parsed.valid) {
        setScanPopup({ pkg: null, barcode, errorMessage: "Invalid check digit." });
        return;
      }
      // Only handle individual package barcodes (quantity flag 0)
      if (parsed.quantityFlag !== "0") {
        setScanPopup({ pkg: null, barcode, errorMessage: "Box barcode. Use the Scanner tab for box audit." });
        return;
      }
      const pkg = app.packages.find(p => p.barcode === barcode) ?? null;
      if (pkg) {
        setScanPopup({ pkg, barcode });
      } else {
        setScanPopup({ pkg: null, barcode, errorMessage: "Package not found in system." });
      }
    } catch {
      setScanPopup({ pkg: null, barcode, errorMessage: "Invalid barcode format." });
    }
  }, [app.packages]);

  useBarcodeScanner({
    enabled: activeTab !== "Scanner",
    onScan: handleGlobalScan,
  });

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
  }, [app, audit, speed, inactivity]);

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
  }, [app, audit]);

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

  const handleExitConfirm = useCallback(async () => {
    setShowExitConfirm(false);
    audit.logEvent("app_exit_initiated", {});

    // Send shift report (production data + audit log) if there is data.
    // Wrapped in try/catch so the exit always proceeds even if email fails.
    if (app.animals.length > 0) {
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
      } catch (err) {
        console.error("Shift report failed, proceeding with exit:", err);
        app.showToast("Shift report failed to send. Exiting anyway.");
      }
    }

    // Clear operator so the gate re-appears on next launch.
    // Production data (animals, boxes, packages) and audit log are
    // intentionally preserved across restarts so the day shift is not lost.
    // Data is cleaned up naturally when animals are closed and purged.
    setSetting("operatorName", "");

    // Small delay to let final writes flush to localStorage
    await new Promise(r => setTimeout(r, 100));

    // Tell the server to shut down. The /api/shutdown endpoint calls
    // os._exit(42), which the watchdog recognises as an intentional
    // operator exit and does NOT relaunch.
    try {
      await fetch("/api/shutdown", { method: "POST" });
    } catch {
      // Server may already be down; proceed to close Chrome anyway
    }

    // Give the server a moment to flush the response, then close Chrome.
    // window.close() often fails in kiosk mode; about:blank is fallback.
    await new Promise(r => setTimeout(r, 300));
    try {
      window.close();
    } catch { /* browser may block */ }
    setTimeout(() => {
      window.location.href = "about:blank";
    }, 500);
  }, [app, settings, audit]);

  return (
    <div className="h-screen flex flex-col overflow-hidden" style={{ backgroundColor: "#0d0d1a" }}>
      <OfflineBanner />
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

      {/* Operator identification gate */}
      <OperatorGateModal
        isOpen={!settings.operatorName}
        onConfirm={handleOperatorConfirm}
      />

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
