/**
 * Centralized settings hook with localStorage persistence.
 * All keys prefixed `pomponio_` to avoid collisions.
 * Migrates old `emailRecipient` key on first mount.
 */

import { useState, useCallback } from "react";

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
  scaleMode: "simulated",
  serialPort: "COM3",
  serialBaudRate: 9600,
  scaleStabilityDelayMs: 2000,
  scaleMaxWeightLb: 30,
  deviceId: "",
  operatorName: "",
};

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

// --- Migration ---

function migrateOldKeys(): void {
  const oldEmail = localStorage.getItem("emailRecipient");
  if (oldEmail !== null && localStorage.getItem(storageKey("emailRecipient")) === null) {
    localStorage.setItem(storageKey("emailRecipient"), oldEmail);
    localStorage.removeItem("emailRecipient");
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

  const setSetting = useCallback(<K extends keyof SettingsValues>(key: K, value: SettingsValues[K]) => {
    writeValue(key, value as string | number | boolean);
    setSettings(prev => ({ ...prev, [key]: value }));
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
  }, [settings.deviceId]);

  return { settings, setSetting, resetToDefaults };
}
