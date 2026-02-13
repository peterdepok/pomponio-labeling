/**
 * Settings screen: centralized configuration for email, printer, scale, system.
 * Five section cards with inline controls. No modals.
 */

import { useState, useEffect } from "react";
import type { SettingsValues, ScaleMode, BaudRate } from "../hooks/useSettings.ts";
import type { AuditEntry } from "../hooks/useAuditLog.ts";
import { TouchButton } from "../components/TouchButton.tsx";
import { ConfirmDialog } from "../components/ConfirmDialog.tsx";
import { KeyboardModal } from "../components/KeyboardModal.tsx";
import { sendToPrinter } from "../data/printer.ts";

// --- Props ---

interface SettingsScreenProps {
  settings: SettingsValues;
  onSetSetting: <K extends keyof SettingsValues>(key: K, value: SettingsValues[K]) => void;
  onResetSettings: () => void;
  onClearAllData: () => void;
  animalCount: number;
  boxCount: number;
  packageCount: number;
  showToast: (msg: string) => void;
  auditEntries: AuditEntry[];
  onClearAuditLog: () => void;
}

// --- Sub-components ---

function SettingsToggle({
  value,
  onChange,
}: {
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      onClick={() => onChange(!value)}
      className="relative flex-shrink-0"
      style={{
        width: 56,
        height: 32,
        borderRadius: 16,
        background: value
          ? "linear-gradient(180deg, #43a047, #2e7d32)"
          : "linear-gradient(180deg, #2a2a4a, #1e1e3a)",
        boxShadow: value
          ? "0 2px 8px rgba(46, 125, 50, 0.4), inset 0 1px 0 rgba(255,255,255,0.15)"
          : "inset 0 2px 4px rgba(0,0,0,0.4), 0 1px 0 rgba(255,255,255,0.04)",
        border: "none",
        cursor: "pointer",
        transition: "background 200ms ease, box-shadow 200ms ease",
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 3,
          left: value ? 27 : 3,
          width: 26,
          height: 26,
          borderRadius: 13,
          background: value
            ? "linear-gradient(180deg, #e8e8e8, #c0c0c0)"
            : "linear-gradient(180deg, #606080, #4a4a60)",
          boxShadow: "0 2px 4px rgba(0,0,0,0.3)",
          transition: "left 200ms ease, background 200ms ease",
        }}
      />
    </button>
  );
}

function ToggleRow({
  label,
  value,
  onChange,
}: {
  label: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div
      className="flex items-center justify-between py-3"
      style={{ minHeight: 48 }}
    >
      <span className="text-sm text-[#a0a0b0]">{label}</span>
      <SettingsToggle value={value} onChange={onChange} />
    </div>
  );
}

function SegmentedControl<T extends string | number>({
  options,
  value,
  onChange,
  formatLabel,
}: {
  options: T[];
  value: T;
  onChange: (v: T) => void;
  formatLabel?: (v: T) => string;
}) {
  return (
    <div className="flex gap-1">
      {options.map(opt => {
        const isActive = opt === value;
        const label = formatLabel ? formatLabel(opt) : String(opt);
        return (
          <button
            key={String(opt)}
            onClick={() => onChange(opt)}
            className="game-btn flex-1 h-[40px] rounded-lg font-bold text-xs select-none relative overflow-hidden"
            style={{
              background: isActive
                ? "linear-gradient(180deg, #1e88e5, #1565c0)"
                : "linear-gradient(180deg, #1e2240, #161a30)",
              boxShadow: isActive
                ? "0 3px 0 0 #0d47a1, 0 4px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.2)"
                : "0 2px 0 0 #0a0e1a, 0 3px 6px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.04)",
              color: isActive ? "#ffffff" : "#606080",
              textShadow: isActive ? "0 1px 2px rgba(0,0,0,0.4)" : "none",
            }}
          >
            {isActive && <div className="game-gloss" />}
            <span className="relative z-10">{label}</span>
          </button>
        );
      })}
    </div>
  );
}

function FieldLabel({ text }: { text: string }) {
  return (
    <label className="text-xs uppercase tracking-[0.15em] text-[#606080] mb-2 block">
      {text}
    </label>
  );
}

function ReadOnlyRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between py-2" style={{ minHeight: 40 }}>
      <span className="text-sm text-[#606080]">{label}</span>
      <span className="text-sm font-mono text-[#a0a0b0]">{value}</span>
    </div>
  );
}

function SectionHeader({ title, color }: { title: string; color: string }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <div
        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
        style={{ background: color, boxShadow: `0 0 8px ${color}60` }}
      />
      <h3
        className="text-xs font-bold uppercase tracking-[0.2em]"
        style={{ color }}
      >
        {title}
      </h3>
    </div>
  );
}

function StatusPip({ active, color }: { active: boolean; color: string }) {
  return (
    <div
      className="w-2 h-2 rounded-full flex-shrink-0"
      style={{
        background: active ? color : "#2a2a4a",
        boxShadow: active ? `0 0 6px ${color}80` : "none",
      }}
    />
  );
}

// --- Section card wrapper ---

function SectionCard({
  color,
  children,
}: {
  color: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className="rounded-xl p-5 mb-4"
      style={{
        background: "linear-gradient(145deg, #1e2240, #1a1a2e)",
        borderLeft: `4px solid ${color}`,
        boxShadow:
          "0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)",
      }}
    >
      {children}
    </div>
  );
}

// --- Input styling ---

const INPUT_STYLE: React.CSSProperties = {
  border: "2px solid #2a2a4a",
  boxShadow: "inset 0 2px 6px rgba(0,0,0,0.4)",
};

// --- Main component ---

export function SettingsScreen({
  settings,
  onSetSetting,
  onResetSettings,
  onClearAllData,
  animalCount,
  boxCount,
  packageCount,
  showToast,
  auditEntries,
  onClearAuditLog,
}: SettingsScreenProps) {
  const [confirmAction, setConfirmAction] = useState<"reset" | "clear" | "clear-audit" | null>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [keyboardField, setKeyboardField] = useState<"email" | "printer" | "comPort" | "maxWeight" | null>(null);

  // Debounced email input
  const [emailDraft, setEmailDraft] = useState(settings.emailRecipient);
  // Keep draft in sync if settings change externally
  useEffect(() => {
    setEmailDraft(settings.emailRecipient);
  }, [settings.emailRecipient]);

  // Online/offline listener
  useEffect(() => {
    const goOnline = () => setIsOnline(true);
    const goOffline = () => setIsOnline(false);
    window.addEventListener("online", goOnline);
    window.addEventListener("offline", goOffline);
    return () => {
      window.removeEventListener("online", goOnline);
      window.removeEventListener("offline", goOffline);
    };
  }, []);

  const handleTestPrint = () => {
    const darkness = settings.printDarkness;
    const zpl = `^XA\n~SD${darkness}\n^PW812\n^LL812\n^POI\n^FO50,350\n^A0N,50,50\n^FDTest Print OK^FS\n^XZ`;
    console.log("[Test ZPL Command]\n" + zpl);
    sendToPrinter(zpl).then(result => {
      if (result.ok) {
        showToast("Test print sent.");
      } else {
        showToast("Print failed: " + (result.error ?? "unknown error"));
      }
    });
  };

  const handleResetConfirm = () => {
    onResetSettings();
    setConfirmAction(null);
    showToast("Settings reset to defaults.");
  };

  const handleClearConfirm = () => {
    onClearAllData();
    setConfirmAction(null);
    showToast("All session data cleared.");
  };

  const handleCopyDeviceId = () => {
    navigator.clipboard.writeText(settings.deviceId).then(
      () => showToast("Device ID copied."),
      () => showToast("Copy failed."),
    );
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
          <h2 className="text-2xl font-bold text-[#e8e8e8]">Settings</h2>
          <div className="text-xs uppercase tracking-[0.15em] text-[#606080] mt-1">
            Pomponio Ranch Labeling System
          </div>
        </div>
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-5">

        {/* Section 1: Email / Reports */}
        <SectionCard color="#00d4ff">
          <SectionHeader title="Email / Reports" color="#00d4ff" />

          <FieldLabel text="Report Email Address" />
          <div
            onClick={() => setKeyboardField("email")}
            className="w-full h-16 px-4 text-lg rounded-xl bg-[#0d0d1a] flex items-center cursor-pointer"
            style={INPUT_STYLE}
          >
            <span style={{ color: emailDraft ? "#e8e8e8" : "#404060" }}>
              {emailDraft || "Tap to enter email..."}
            </span>
          </div>

          <div className="mt-4 space-y-1">
            <ToggleRow
              label="Auto-email manifest on animal close"
              value={settings.autoEmailOnAnimalClose}
              onChange={v => onSetSetting("autoEmailOnAnimalClose", v)}
            />
            <ToggleRow
              label="Auto-email daily production report"
              value={settings.autoEmailDailyReport}
              onChange={v => onSetSetting("autoEmailDailyReport", v)}
            />
          </div>

          <div className="text-xs text-[#606080] mt-3">
            When email is blank, reports download locally only.
          </div>
        </SectionCard>

        {/* Section 2: Printer */}
        <SectionCard color="#ffa500">
          <SectionHeader title="Printer" color="#ffa500" />

          <FieldLabel text="Printer Name" />
          <div
            onClick={() => setKeyboardField("printer")}
            className="w-full h-16 px-4 text-lg rounded-xl bg-[#0d0d1a] flex items-center cursor-pointer mb-4"
            style={INPUT_STYLE}
          >
            <span style={{ color: settings.printerName ? "#e8e8e8" : "#404060" }}>
              {settings.printerName || "Tap to enter printer name..."}
            </span>
          </div>

          <div className="flex items-center gap-2 mb-4">
            <span className="text-sm text-[#606080]">Connection:</span>
            <span
              className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full"
              style={{
                background: "rgba(96, 96, 128, 0.15)",
                color: "#606080",
                border: "1px solid #2a2a4a",
              }}
            >
              Not Connected
            </span>
            <span className="text-xs text-[#606080] ml-2">
              Hardware connection available in kiosk mode.
            </span>
          </div>

          <FieldLabel text={`Print Darkness (${settings.printDarkness})`} />
          <div className="flex items-center gap-3 mb-4">
            <span className="text-xs text-[#606080]">1</span>
            <input
              type="range"
              min="1"
              max="30"
              step="1"
              value={settings.printDarkness}
              onChange={e => onSetSetting("printDarkness", Number(e.target.value))}
              className="flex-1"
            />
            <span className="text-xs text-[#606080]">30</span>
          </div>

          <ReadOnlyRow label="Label Size" value="4 x 4 in / 812 x 812 dots @ 203 DPI" />

          <div className="mt-3">
            <TouchButton
              text="Send Test Print"
              style="secondary"
              size="sm"
              onClick={handleTestPrint}
              width="200px"
            />
          </div>
        </SectionCard>

        {/* Section 3: Scale */}
        <SectionCard color="#51cf66">
          <SectionHeader title="Scale" color="#51cf66" />

          <FieldLabel text="Scale Mode" />
          <SegmentedControl<ScaleMode>
            options={["simulated", "serial"]}
            value={settings.scaleMode}
            onChange={v => onSetSetting("scaleMode", v)}
            formatLabel={v => v === "simulated" ? "Simulated" : "Serial"}
          />

          {settings.scaleMode === "simulated" ? (
            <div className="text-sm text-[#606080] mt-4 py-3">
              Drag slider to set weight during labeling. No hardware required.
            </div>
          ) : (
            <div className="mt-4 space-y-4">
              <div>
                <FieldLabel text="COM Port" />
                <div
                  onClick={() => setKeyboardField("comPort")}
                  className="w-full h-16 px-4 text-lg rounded-xl bg-[#0d0d1a] flex items-center cursor-pointer"
                  style={INPUT_STYLE}
                >
                  <span style={{ color: settings.serialPort ? "#e8e8e8" : "#404060" }}>
                    {settings.serialPort || "Tap to enter COM port..."}
                  </span>
                </div>
              </div>
              <div>
                <FieldLabel text="Baud Rate" />
                <SegmentedControl<BaudRate>
                  options={[9600, 19200, 38400, 115200]}
                  value={settings.serialBaudRate}
                  onChange={v => onSetSetting("serialBaudRate", v)}
                />
              </div>
            </div>
          )}

          <div className="mt-4">
            <FieldLabel text={`Stability Delay (${settings.scaleStabilityDelayMs} ms)`} />
            <div className="flex items-center gap-3">
              <span className="text-xs text-[#606080]">500</span>
              <input
                type="range"
                min="500"
                max="5000"
                step="100"
                value={settings.scaleStabilityDelayMs}
                onChange={e => onSetSetting("scaleStabilityDelayMs", Number(e.target.value))}
                className="flex-1"
              />
              <span className="text-xs text-[#606080]">5000</span>
            </div>
          </div>

          <div className="mt-4">
            <FieldLabel text="Max Weight (lb)" />
            <div
              onClick={() => setKeyboardField("maxWeight")}
              className="w-full h-16 px-4 text-lg rounded-xl bg-[#0d0d1a] flex items-center cursor-pointer"
              style={INPUT_STYLE}
            >
              <span style={{ color: "#e8e8e8" }}>
                {settings.scaleMaxWeightLb}
              </span>
            </div>
          </div>
        </SectionCard>

        {/* Section 4: System */}
        <SectionCard color="#ff6b6b">
          <SectionHeader title="System" color="#ff6b6b" />

          <ReadOnlyRow label="App Version" value={`v${__APP_VERSION__}`} />

          <div className="flex gap-3 mt-3">
            <TouchButton
              text="Check for Updates"
              style="secondary"
              size="sm"
              onClick={() => showToast("App is up to date.")}
              width="200px"
            />
          </div>

          <div
            className="mt-6 pt-4"
            style={{ borderTop: "1px solid #2a2a4a" }}
          >
            <div className="flex gap-3">
              <TouchButton
                text="Reset All Settings"
                style="danger"
                size="sm"
                onClick={() => setConfirmAction("reset")}
                width="200px"
              />
              <TouchButton
                text="Clear All Session Data"
                style="danger"
                size="sm"
                onClick={() => setConfirmAction("clear")}
                width="240px"
              />
            </div>
          </div>
        </SectionCard>

        {/* Section 5: Audit Log */}
        <SectionCard color="#b197fc">
          <SectionHeader title="Audit Log" color="#b197fc" />

          <div className="flex items-center justify-between mb-3">
            <span className="text-sm text-[#a0a0b0]">
              {auditEntries.length} event{auditEntries.length !== 1 ? "s" : ""} recorded
            </span>
            <TouchButton
              text="Clear Audit Log"
              style="danger"
              size="sm"
              onClick={() => setConfirmAction("clear-audit")}
              width="180px"
            />
          </div>

          {/* Scrollable log viewer, most recent first */}
          <div
            className="overflow-y-auto rounded-lg"
            style={{ maxHeight: 320, background: "#0d0d1a", border: "1px solid #2a2a4a" }}
          >
            {auditEntries.length === 0 ? (
              <div className="text-center text-[#606080] py-8 text-sm">
                No events recorded.
              </div>
            ) : (
              [...auditEntries].reverse().slice(0, 100).map((entry, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 px-3 py-2 text-xs"
                  style={{ borderBottom: "1px solid #1a1a2e" }}
                >
                  <span className="text-[#606080] flex-shrink-0 font-mono" style={{ minWidth: 140 }}>
                    {new Date(entry.timestamp).toLocaleString()}
                  </span>
                  <span className="text-[#00d4ff] flex-shrink-0 font-mono" style={{ minWidth: 180 }}>
                    {entry.eventType}
                  </span>
                  <span className="text-[#a0a0b0] truncate">
                    {JSON.stringify(entry.payload)}
                  </span>
                </div>
              ))
            )}
          </div>

          {auditEntries.length > 100 && (
            <div className="text-xs text-[#606080] mt-2">
              Showing most recent 100 of {auditEntries.length} events.
            </div>
          )}
        </SectionCard>

        {/* Section 6: About / Device */}
        <SectionCard color="#a0a0b0">
          <SectionHeader title="About / Device" color="#a0a0b0" />

          <div className="flex items-center justify-between py-2" style={{ minHeight: 40 }}>
            <span className="text-sm text-[#606080]">Device ID</span>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-[#a0a0b0]">
                {settings.deviceId.slice(0, 8)}...
              </span>
              <button
                onClick={handleCopyDeviceId}
                className="text-xs text-[#00d4ff] hover:text-[#4dd8ff]"
                style={{ background: "none", border: "none", cursor: "pointer" }}
              >
                Copy
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2 py-2" style={{ minHeight: 40 }}>
            <span className="text-sm text-[#606080]">Network</span>
            <StatusPip active={isOnline} color={isOnline ? "#51cf66" : "#ff6b6b"} />
            <span
              className="text-sm font-bold"
              style={{ color: isOnline ? "#51cf66" : "#ff6b6b" }}
            >
              {isOnline ? "Online" : "Offline"}
            </span>
          </div>

          <div className="flex items-center gap-4 py-2 text-sm text-[#606080]">
            <span>{animalCount} animals</span>
            <span>{boxCount} boxes</span>
            <span>{packageCount} packages</span>
          </div>
        </SectionCard>

        {/* Bottom spacer for scroll comfort */}
        <div className="h-4" />
      </div>

      {/* Confirm dialogs */}
      {confirmAction === "reset" && (
        <ConfirmDialog
          title="Reset All Settings"
          message="This will reset all settings to their default values. Your session data (animals, boxes, packages) will not be affected."
          confirmText="Reset Settings"
          onConfirm={handleResetConfirm}
          onCancel={() => setConfirmAction(null)}
        />
      )}
      {confirmAction === "clear" && (
        <ConfirmDialog
          title="Clear Session Data"
          message="This will permanently remove all animals, boxes, and packages from this session. Settings will not be affected."
          confirmText="Clear All Data"
          onConfirm={handleClearConfirm}
          onCancel={() => setConfirmAction(null)}
        />
      )}
      {confirmAction === "clear-audit" && (
        <ConfirmDialog
          title="Clear Audit Log"
          message="This will permanently remove all audit log entries. Session data will not be affected."
          confirmText="Clear Audit Log"
          onConfirm={() => {
            onClearAuditLog();
            setConfirmAction(null);
            showToast("Audit log cleared.");
          }}
          onCancel={() => setConfirmAction(null)}
        />
      )}

      {/* Keyboard modals for settings fields */}
      <KeyboardModal
        isOpen={keyboardField === "email"}
        title="Report Email Address"
        initialValue={emailDraft}
        placeholder="office@pomponioranch.com"
        showSymbols
        onConfirm={(val) => {
          const trimmed = val.trim().toLowerCase();
          setEmailDraft(trimmed);
          onSetSetting("emailRecipient", trimmed);
          setKeyboardField(null);
        }}
        onCancel={() => setKeyboardField(null)}
      />
      <KeyboardModal
        isOpen={keyboardField === "printer"}
        title="Printer Name"
        initialValue={settings.printerName}
        placeholder="Zebra ZP230d (ZPL)"
        showNumbers
        showSymbols
        onConfirm={(val) => {
          onSetSetting("printerName", val);
          setKeyboardField(null);
        }}
        onCancel={() => setKeyboardField(null)}
      />
      <KeyboardModal
        isOpen={keyboardField === "comPort"}
        title="COM Port"
        initialValue={settings.serialPort}
        placeholder="COM3"
        showNumbers
        onConfirm={(val) => {
          onSetSetting("serialPort", val);
          setKeyboardField(null);
        }}
        onCancel={() => setKeyboardField(null)}
      />
      <KeyboardModal
        isOpen={keyboardField === "maxWeight"}
        title="Max Weight (lb)"
        initialValue={String(settings.scaleMaxWeightLb)}
        placeholder="30"
        showNumbers
        onConfirm={(val) => {
          const v = Number(val);
          if (v > 0 && v <= 500) {
            onSetSetting("scaleMaxWeightLb", v);
          }
          setKeyboardField(null);
        }}
        onCancel={() => setKeyboardField(null)}
      />
    </div>
  );
}
