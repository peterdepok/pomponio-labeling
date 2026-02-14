/**
 * Animal tracking screen.
 * Card-elevated animals with cyan stripe, glass dialog for new animal.
 * On close: downloads manifest CSV locally, attempts email delivery.
 * Daily production report can be emailed from the header.
 */

import { useState } from "react";
import { TouchButton } from "../components/TouchButton.tsx";
import { ConfirmDialog } from "../components/ConfirmDialog.tsx";
import { KeyboardModal } from "../components/KeyboardModal.tsx";
import { ScanGunIcon } from "../components/ScanGunIcon.tsx";
import { useBarcodeScanner } from "../hooks/useBarcodeScanner.ts";
import type { Animal, Box, Package } from "../hooks/useAppState.ts";
import { generateAnimalManifestCsv, generateDailyProductionCsv, downloadCsv } from "../data/csv.ts";
import { sendReport } from "../data/email.ts";
import type { LogEventFn } from "../hooks/useAuditLog.ts";

interface ManifestItem {
  sku: string;
  productName: string;
  quantity: number;
  weights: number[];
  totalWeight: number;
}

interface AnimalsScreenProps {
  animals: Animal[];
  boxes: Box[];
  packages: Package[];
  getPackagesForAnimal: (animalId: number) => Package[];
  getManifestData: (animalId: number) => ManifestItem[];
  onCreateAnimal: (name: string) => number;
  onSelectAnimal: (animalId: number) => void;
  onCloseAnimal: (animalId: number) => void;
  emailRecipient: string;
  autoEmailOnAnimalClose: boolean;
  autoEmailDailyReport: boolean;
  onNavigateToSettings: () => void;
  showToast: (msg: string) => void;
  logEvent: LogEventFn;
}

export function AnimalsScreen({
  animals,
  boxes,
  packages,
  getPackagesForAnimal,
  getManifestData,
  onCreateAnimal,
  onSelectAnimal,
  onCloseAnimal,
  emailRecipient,
  autoEmailOnAnimalClose,
  autoEmailDailyReport,
  onNavigateToSettings,
  showToast,
  logEvent,
}: AnimalsScreenProps) {
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [newName, setNewName] = useState("");
  const [showNameKeyboard, setShowNameKeyboard] = useState(false);
  const [newAnimalPhase, setNewAnimalPhase] = useState<"scan-ready" | "confirm">("scan-ready");
  const [confirmCloseId, setConfirmCloseId] = useState<number | null>(null);
  const [sending, setSending] = useState(false);

  const openAnimals = animals.filter(a => a.closedAt === null);

  // Listen for USB barcode scanner while the new animal dialog is in scan-ready phase.
  // Disabled when KeyboardModal is open to avoid keystroke conflicts.
  useBarcodeScanner({
    enabled: showNewDialog && !showNameKeyboard && newAnimalPhase === "scan-ready",
    minLength: 4,
    alphanumeric: true,
    onScan: (barcode: string) => {
      setNewName(barcode);
      setNewAnimalPhase("confirm");
    },
  });

  const handleCreate = () => {
    setNewName("");
    setNewAnimalPhase("scan-ready");
    setShowNewDialog(true);
  };

  const handleTypeName = () => {
    const today = new Date().toLocaleDateString();
    const defaultName = `Beef #${openAnimals.length + 1} - ${today}`;
    setNewName(defaultName);
    setShowNameKeyboard(true);
  };

  const doCreate = () => {
    const name = newName.trim();
    if (!name) return;
    const id = onCreateAnimal(name);
    logEvent("animal_created", { animalId: id, name });
    onSelectAnimal(id);
    setShowNewDialog(false);
    setNewName("");
    showToast(`Started: ${name}`);
  };

  /** Close animal, download manifest CSV, attempt email. */
  const handleCloseAnimal = async (animalId: number) => {
    const animal = animals.find(a => a.id === animalId);
    if (!animal) return;

    // Compute stats for audit before closing
    const pkgs = getPackagesForAnimal(animalId);
    const totalWeight = pkgs.reduce((s, p) => s + p.weightLb, 0);
    logEvent("animal_closed", {
      animalId,
      name: animal.name,
      packageCount: pkgs.length,
      totalWeight,
    });

    // Generate manifest CSV
    const csv = generateAnimalManifestCsv(animal, boxes, packages);
    const safeName = animal.name.replace(/[^a-zA-Z0-9]/g, "_");
    const filename = `manifest_${safeName}_${Date.now()}.csv`;

    // Always download locally first
    downloadCsv(csv, filename);
    logEvent("manifest_downloaded", { animalId, animalName: animal.name, filename });

    // Close the animal in state
    onCloseAnimal(animalId);
    setConfirmCloseId(null);
    showToast("Animal closed. Manifest downloaded.");

    // Attempt email if configured and enabled
    if (emailRecipient && autoEmailOnAnimalClose) {
      setSending(true);
      const result = await sendReport({
        to: emailRecipient,
        subject: `Pomponio Ranch Manifest: ${animal.name}`,
        csvContent: csv,
        filename,
      });
      setSending(false);

      if (result.ok && result.queued) {
        logEvent("manifest_emailed", { animalId, animalName: animal.name, recipient: emailRecipient, success: true });
        showToast("Email queued, will retry when online.");
      } else if (result.ok) {
        logEvent("manifest_emailed", { animalId, animalName: animal.name, recipient: emailRecipient, success: true });
        showToast(`Manifest emailed to ${emailRecipient}`);
      } else {
        logEvent("manifest_emailed", { animalId, animalName: animal.name, recipient: emailRecipient, success: false });
        showToast(`Email failed: ${result.error || "unknown"}. CSV saved locally.`);
      }
    }
  };

  /** Generate and send daily production report. */
  const handleDailyReport = async () => {
    if (animals.length === 0) {
      showToast("No animals to report.");
      return;
    }

    const csv = generateDailyProductionCsv(animals, boxes, packages);
    const today = new Date().toLocaleDateString().replace(/\//g, "-");
    const filename = `daily_production_${today}.csv`;

    // Always download locally
    downloadCsv(csv, filename);
    logEvent("daily_report_downloaded", { filename });
    showToast("Daily report downloaded.");

    // Attempt email if configured and enabled
    if (emailRecipient && autoEmailDailyReport) {
      setSending(true);
      const result = await sendReport({
        to: emailRecipient,
        subject: `Pomponio Ranch Daily Production: ${today}`,
        csvContent: csv,
        filename,
      });
      setSending(false);

      if (result.ok && result.queued) {
        logEvent("daily_report_emailed", { recipient: emailRecipient, success: true });
        showToast("Email queued, will retry when online.");
      } else if (result.ok) {
        logEvent("daily_report_emailed", { recipient: emailRecipient, success: true });
        showToast(`Daily report emailed to ${emailRecipient}`);
      } else {
        logEvent("daily_report_emailed", { recipient: emailRecipient, success: false });
        showToast(`Email failed: ${result.error || "unknown"}. CSV saved locally.`);
      }
    }
  };

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
          <h2 className="text-2xl font-bold text-[#e8e8e8]">Animal Tracking</h2>
          {/* Email config indicator (read-only, links to Settings) */}
          <button
            onClick={onNavigateToSettings}
            className="text-xs text-[#606080] hover:text-[#a0a0b0] mt-1 text-left"
            style={{ background: "none", border: "none", cursor: "pointer" }}
          >
            {emailRecipient
              ? `Reports: ${emailRecipient} [Settings]`
              : "Reports: local only [Settings]"
            }
          </button>
        </div>
        <div className="flex gap-3">
          <TouchButton
            text={sending ? "Sending..." : "Daily Report"}
            style="secondary"
            onClick={handleDailyReport}
            width="180px"
          />
          <TouchButton text="Start Animal" style="success" onClick={handleCreate} width="200px" />
        </div>
      </div>

      {/* Animal list */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {openAnimals.length === 0 ? (
          <div className="text-center text-[#606080] py-12 text-lg">
            No active animals. Tap "Start Animal" to begin.
          </div>
        ) : (
          openAnimals.map(animal => {
            const pkgs = getPackagesForAnimal(animal.id);
            const manifestData = getManifestData(animal.id);
            const totalWeight = pkgs.reduce((s, p) => s + p.weightLb, 0);

            return (
              <div
                key={animal.id}
                className="rounded-xl p-5"
                style={{
                  background: "linear-gradient(145deg, #1e2240, #1a1a2e)",
                  borderLeft: "4px solid #00d4ff",
                  boxShadow: "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
                }}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xl font-bold text-[#e8e8e8]">{animal.name}</h3>
                  <span className="text-xs uppercase tracking-[0.15em] text-[#606080]">Started: {animal.startedAt}</span>
                </div>

                {/* Stats */}
                <div className="text-[#a0a0b0] mb-3">
                  {pkgs.length} packages | {manifestData.length} SKUs | {totalWeight.toFixed(1)} lb total
                </div>

                {/* SKU breakdown */}
                {manifestData.length > 0 && (
                  <div className="mb-4 space-y-1">
                    {manifestData.slice(0, 8).map(item => (
                      <div key={item.sku} className="text-sm text-[#a0a0b0] pl-2">
                        {item.quantity}x {item.productName} ({item.totalWeight.toFixed(1)} lb)
                      </div>
                    ))}
                    {manifestData.length > 8 && (
                      <div className="text-sm text-[#606080] pl-2">
                        ... and {manifestData.length - 8} more SKUs
                      </div>
                    )}
                  </div>
                )}

                {/* Actions */}
                <div className="flex gap-3">
                  <TouchButton
                    text="Use This Animal"
                    style="primary"
                    onClick={() => onSelectAnimal(animal.id)}
                    className="flex-1"
                  />
                  <TouchButton
                    text="Close and Generate Manifest"
                    style="danger"
                    onClick={() => setConfirmCloseId(animal.id)}
                    className="flex-1"
                  />
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* New animal dialog (two-phase: scan-ready then confirm) */}
      {showNewDialog && (
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
            {/* Cyan accent bar */}
            <div
              className="h-1"
              style={{
                background: "linear-gradient(90deg, #0f3460, #00d4ff, #0f3460)",
              }}
            />

            <div className="p-8">
              <h2 className="text-2xl font-bold text-[#e8e8e8] mb-6">Start New Animal</h2>

              {newAnimalPhase === "scan-ready" && (
                <>
                  {/* Scan prompt */}
                  <div className="flex flex-col items-center gap-4 mb-8">
                    <div
                      className="select-none"
                      style={{
                        animation: "anim-scan-pulse 2s ease-in-out infinite",
                        filter: "drop-shadow(0 0 16px rgba(0, 212, 255, 0.3))",
                      }}
                    >
                      <ScanGunIcon size={72} color="#e8e8e8" />
                    </div>
                    <div className="text-lg text-[#a0a0b0] text-center">
                      Scan animal tag barcode
                    </div>
                    <div className="text-sm text-[#606080]">or</div>
                  </div>

                  {/* Action buttons */}
                  <div className="flex gap-4">
                    <TouchButton
                      text="Cancel"
                      style="secondary"
                      onClick={() => setShowNewDialog(false)}
                      className="flex-1"
                    />
                    <TouchButton
                      text="Type Name"
                      style="primary"
                      onClick={handleTypeName}
                      className="flex-1"
                    />
                  </div>
                </>
              )}

              {newAnimalPhase === "confirm" && (
                <>
                  <label className="text-xs uppercase tracking-[0.15em] text-[#606080] mb-2 block">Animal ID</label>
                  <div
                    onClick={() => setShowNameKeyboard(true)}
                    className="w-full h-16 px-4 text-lg rounded-xl bg-[#0d0d1a] flex items-center cursor-pointer mb-6"
                    style={{
                      border: "2px solid #00d4ff",
                      boxShadow: "inset 0 2px 6px rgba(0,0,0,0.4), 0 0 8px rgba(0, 212, 255, 0.15)",
                      color: newName ? "#e8e8e8" : "#404060",
                    }}
                  >
                    {newName || "Tap to edit..."}
                  </div>
                  <div className="flex gap-4">
                    <TouchButton
                      text="Cancel"
                      style="secondary"
                      onClick={() => {
                        setShowNewDialog(false);
                        setNewName("");
                      }}
                      className="flex-1"
                    />
                    <TouchButton
                      text="Rescan"
                      style="secondary"
                      onClick={() => {
                        setNewName("");
                        setNewAnimalPhase("scan-ready");
                      }}
                      className="flex-1"
                    />
                    <TouchButton
                      text="Start"
                      style="success"
                      onClick={doCreate}
                      className="flex-1"
                    />
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Keyboard modal for animal name */}
      <KeyboardModal
        isOpen={showNameKeyboard}
        title="Animal Name"
        initialValue={newName}
        placeholder="Enter animal name..."
        showNumbers
        onConfirm={(val) => {
          setNewName(val);
          setShowNameKeyboard(false);
          setNewAnimalPhase("confirm");
        }}
        onCancel={() => setShowNameKeyboard(false)}
      />

      {/* Confirm close dialog */}
      {confirmCloseId !== null && (
        <ConfirmDialog
          title="Close Animal"
          message={`Close "${openAnimals.find(a => a.id === confirmCloseId)?.name}"?\nManifest CSV will be downloaded${emailRecipient ? ` and emailed to ${emailRecipient}` : ""}.`}
          confirmText="Close and Generate Manifest"
          onConfirm={() => handleCloseAnimal(confirmCloseId)}
          onCancel={() => setConfirmCloseId(null)}
        />
      )}
    </div>
  );
}
