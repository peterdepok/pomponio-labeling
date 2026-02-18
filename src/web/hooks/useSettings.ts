/**
 * Centralized settings hook with dual persistence:
 *   1. localStorage for fast, synchronous reads (primary)
 *   2. Server-side settings.json for durability across reboots
 *
 * On startup, settings load from localStorage (instant). After mount,
 * hydrateFromServer() fetches the server copy and fills any gaps left
 * by a cleared localStorage (e.g., after Chrome profile deletion).
 *
 * On every change, settings are written to both localStorage (immediate)
 * and the server (fire-and-forget POST).
 *
 * All localStorage keys prefixed `pomponio_` to avoid collisions.
 */

import { useState, useCallback, useEffect, useRef } from "react";

// --- Types ---

export type ScaleMode = "simulated" | "serial";
export type BaudRate = 9600 | 19200 | 38400 | 115200;

export interface SettingsValues {
  // Email / Reports
  emailRecipient: string;
  autoEmailOnAnimalClose: boolean;
  autoEmailDailyReport: boolean;
  // Printer
  printerName: string;
  printDarkness: number;
  // Scale
  scaleMode: ScaleMode;
  serialPort: string;
  serialBaudRate: BaudRate;
  scaleStabilityDelayMs: number;
  scaleMaxWeightLb: number;
  // System
  deviceId: string;
  // Operator
  operatorName: string;
}

// --- Defaults ---

const DEFAULTS: SettingsValues = {
  emailRecipient: "",
  autoEmailOnAnimalClose: true,
  autoEmailDailyReport: true,
  printerName: "Zebra ZP230d (ZPL)",
  printDarkness: 15,
  scaleMode: "serial",
  serialPort: "COM3",
  serialBaudRate: 9600,
  scaleStabilityDelayMs: 2000,
  scaleMaxWeightLb: 30,
  deviceId: "",
  operatorName: "",
};

// Settings keys that should be persisted to the server and restored
// on reboot. deviceId is excluded (auto-generated per browser instance).
const PERSISTENT_KEYS: (keyof SettingsValues)[] = [
  "emailRecipient", "autoEmailOnAnimalClose", "autoEmailDailyReport",
  "printerName", "printDarkness",
  "scaleMode", "serialPort", "serialBaudRate", "scaleStabilityDelayMs", "scaleMaxWeightLb",
  "operatorName",
];

// --- localStorage helpers ---

const PREFIX = "pomponio_";

function storageKey(key: string): string {
  return PREFIX + key;
}

function readString(key: keyof SettingsValues, fallback: string): string {
  return localStorage.getItem(storageKey(key)) ?? fallback;
}

function readNumber(key: keyof SettingsValues, fallback: number): number {
  const raw = localStorage.getItem(storageKey(key));
  if (raw === null) return fallback;
  const parsed = Number(raw);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function readBoolean(key: keyof SettingsValues, fallback: boolean): boolean {
  const raw = localStorage.getItem(storageKey(key));
  if (raw === null) return fallback;
  return raw === "true";
}

function writeValue(key: keyof SettingsValues, value: string | number | boolean): void {
  localStorage.setItem(storageKey(key), String(value));
}

/** True if localStorage has a saved value for this key (not relying on default). */
function hasLocalValue(key: keyof SettingsValues): boolean {
  return localStorage.getItem(storageKey(key)) !== null;
}

// --- Migration ---

function migrateOldKeys(): void {
  const oldEmail = localStorage.getItem("emailRecipient");
  if (oldEmail !== null && localStorage.getItem(storageKey("emailRecipient")) === null) {
    localStorage.setItem(storageKey("emailRecipient"), oldEmail);
    localStorage.removeItem("emailRecipient");
  }
}

// --- Server persistence ---

/** Fire-and-forget save of all settings + MRU lists to server. */
export function saveSettingsToServer(): void {
  const blob: Record<string, unknown> = {};

  // Settings values
  for (const key of PERSISTENT_KEYS) {
    const raw = localStorage.getItem(storageKey(key));
    if (raw !== null) blob[key] = raw;
  }

  // MRU lists (stored as JSON arrays in localStorage)
  const recentOps = localStorage.getItem("pomponio_recentOperators");
  if (recentOps) blob._recentOperators = recentOps;

  const recentEmails = localStorage.getItem("pomponio_recentAuditEmails");
  if (recentEmails) blob._recentAuditEmails = recentEmails;

  fetch("/api/settings", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(blob),
  }).catch(() => {
    // Best-effort; server may not be available during shutdown
  });
}

/** Fetch saved settings from server. Returns null on failure. */
async function loadFromServer(): Promise<Record<string, unknown> | null> {
  try {
    const res = await fetch("/api/settings");
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

// --- Init ---

function initSettings(): SettingsValues {
  migrateOldKeys();

  let deviceId = readString("deviceId", "");
  if (!deviceId) {
    deviceId = crypto.randomUUID();
    writeValue("deviceId", deviceId);
  }

  return {
    emailRecipient: readString("emailRecipient", DEFAULTS.emailRecipient),
    autoEmailOnAnimalClose: readBoolean("autoEmailOnAnimalClose", DEFAULTS.autoEmailOnAnimalClose),
    autoEmailDailyReport: readBoolean("autoEmailDailyReport", DEFAULTS.autoEmailDailyReport),
    printerName: readString("printerName", DEFAULTS.printerName),
    printDarkness: readNumber("printDarkness", DEFAULTS.printDarkness),
    scaleMode: readString("scaleMode", DEFAULTS.scaleMode) as ScaleMode,
    serialPort: readString("serialPort", DEFAULTS.serialPort),
    serialBaudRate: readNumber("serialBaudRate", DEFAULTS.serialBaudRate) as BaudRate,
    scaleStabilityDelayMs: readNumber("scaleStabilityDelayMs", DEFAULTS.scaleStabilityDelayMs),
    scaleMaxWeightLb: readNumber("scaleMaxWeightLb", DEFAULTS.scaleMaxWeightLb),
    deviceId,
    operatorName: readString("operatorName", DEFAULTS.operatorName),
  };
}

// --- Hook ---

export interface UseSettingsReturn {
  settings: SettingsValues;
  setSetting: <K extends keyof SettingsValues>(key: K, value: SettingsValues[K]) => void;
  resetToDefaults: () => void;
}

export function useSettings(): UseSettingsReturn {
  const [settings, setSettings] = useState<SettingsValues>(initSettings);
  const hydratedRef = useRef(false);

  // After mount, fetch server settings and fill any localStorage gaps.
  // This restores settings that were lost when the Chrome profile was deleted.
  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;

    loadFromServer().then(serverData => {
      if (!serverData) return;

      const updates: Partial<SettingsValues> = {};

      for (const key of PERSISTENT_KEYS) {
        // Only fill gaps: if localStorage already has a value, it wins
        if (hasLocalValue(key)) continue;

        const serverVal = serverData[key];
        if (serverVal === undefined || serverVal === null) continue;

        // Write server value to localStorage so future reads find it
        localStorage.setItem(storageKey(key), String(serverVal));

        // Build React state update
        const def = DEFAULTS[key];
        if (typeof def === "boolean") {
          (updates as Record<string, unknown>)[key] = String(serverVal) === "true";
        } else if (typeof def === "number") {
          const n = Number(serverVal);
          if (Number.isFinite(n)) (updates as Record<string, unknown>)[key] = n;
        } else {
          (updates as Record<string, unknown>)[key] = String(serverVal);
        }
      }

      // Restore MRU lists
      if (serverData._recentOperators && !localStorage.getItem("pomponio_recentOperators")) {
        localStorage.setItem("pomponio_recentOperators", String(serverData._recentOperators));
      }
      if (serverData._recentAuditEmails && !localStorage.getItem("pomponio_recentAuditEmails")) {
        localStorage.setItem("pomponio_recentAuditEmails", String(serverData._recentAuditEmails));
      }

      if (Object.keys(updates).length > 0) {
        setSettings(prev => ({ ...prev, ...updates }));
      }
    });
  }, []);

  const setSetting = useCallback(<K extends keyof SettingsValues>(key: K, value: SettingsValues[K]) => {
    writeValue(key, value as string | number | boolean);
    setSettings(prev => {
      const next = { ...prev, [key]: value };
      // Fire-and-forget save to server after state update
      // Use setTimeout to ensure localStorage is written first
      setTimeout(saveSettingsToServer, 0);
      return next;
    });
  }, []);

  const resetToDefaults = useCallback(() => {
    const preservedDeviceId = settings.deviceId;
    // Clear all pomponio_ keys
    const keysToRemove: (keyof SettingsValues)[] = [
      "emailRecipient", "autoEmailOnAnimalClose", "autoEmailDailyReport",
      "printerName", "printDarkness",
      "scaleMode", "serialPort", "serialBaudRate", "scaleStabilityDelayMs", "scaleMaxWeightLb",
      "operatorName",
    ];
    for (const key of keysToRemove) {
      localStorage.removeItem(storageKey(key));
    }
    setSettings({ ...DEFAULTS, deviceId: preservedDeviceId });
    // Also clear server settings
    saveSettingsToServer();
  }, [settings.deviceId]);

  return { settings, setSetting, resetToDefaults };
}
