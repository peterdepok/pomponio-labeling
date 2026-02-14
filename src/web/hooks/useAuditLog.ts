/**
 * Audit log hook: typed event tracking with localStorage persistence.
 * FIFO eviction at configurable max entries. Events are written synchronously
 * inside the state updater to guarantee persistence even on abrupt page close.
 */

import { useState, useCallback } from "react";

// --- Event types ---

export type AuditEventType =
  | "animal_created"
  | "animal_selected"
  | "animal_closed"
  | "box_created"
  | "box_closed"
  | "box_reopened"
  | "product_selected"
  | "weight_captured"
  | "label_printed"
  | "package_recorded"
  | "workflow_cancelled"
  | "box_labels_printed"
  | "box_labels_reprinted"
  | "manifest_exported"
  | "manifest_emailed"
  | "daily_report_exported"
  | "daily_report_emailed"
  | "data_cleared"
  | "package_voided"
  | "box_audited"
  | "manifest_resent"
  | "app_exit_initiated";

// --- Payload map (discriminated by eventType) ---

export interface AuditPayloads {
  animal_created: { animalId: number; name: string };
  animal_selected: { animalId: number; name: string };
  animal_closed: { animalId: number; name: string; packageCount: number; totalWeight: number };
  box_created: { boxId: number; animalId: number; boxNumber: number };
  box_closed: { boxId: number; boxNumber: number; packageCount: number; totalWeight: number; labelCount: number };
  box_reopened: { boxId: number; boxNumber: number };
  product_selected: { sku: string; productName: string };
  weight_captured: { weightLb: number; sku: string; productName: string };
  label_printed: { barcode: string; sku: string; productName: string; weightLb: number };
  package_recorded: { barcode: string; sku: string; productName: string; weightLb: number; animalId: number; boxId: number };
  workflow_cancelled: { fromState: string; sku: string | null; productName: string | null };
  box_labels_printed: { boxId: number; boxNumber: number; labelCount: number };
  box_labels_reprinted: { boxId: number; boxNumber: number; labelCount: number };
  manifest_exported: { animalId: number; animalName: string; filename: string; path?: string };
  manifest_emailed: { animalId: number; animalName: string; recipient: string; success: boolean };
  daily_report_exported: { filename: string; path?: string };
  daily_report_emailed: { recipient: string; success: boolean };
  data_cleared: { animalCount: number; boxCount: number; packageCount: number };
  package_voided: { packageId: number; barcode: string; sku: string; productName: string; reason: string };
  box_audited: { boxId: number; boxNumber: number; packageCount: number; voidedCount: number };
  manifest_resent: { animalId: number; animalName: string; recipient: string; success: boolean };
  app_exit_initiated: Record<string, never>;
}

// --- Entry stored in localStorage ---

export interface AuditEntry {
  timestamp: string; // ISO 8601
  eventType: AuditEventType;
  payload: AuditPayloads[AuditEventType];
}

// --- Storage helpers ---

const AUDIT_KEY = "pomponio_audit_log";
const DEFAULT_MAX_ENTRIES = 5000;

function readLog(): AuditEntry[] {
  try {
    return JSON.parse(localStorage.getItem(AUDIT_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeLog(entries: AuditEntry[]): void {
  localStorage.setItem(AUDIT_KEY, JSON.stringify(entries));
}

// --- Hook ---

export type LogEventFn = <T extends AuditEventType>(
  eventType: T,
  payload: AuditPayloads[T],
) => void;

export interface UseAuditLogReturn {
  entries: AuditEntry[];
  logEvent: LogEventFn;
  clearLog: () => void;
}

export function useAuditLog(maxEntries: number = DEFAULT_MAX_ENTRIES): UseAuditLogReturn {
  const [entries, setEntries] = useState<AuditEntry[]>(readLog);

  const logEvent = useCallback(<T extends AuditEventType>(
    eventType: T,
    payload: AuditPayloads[T],
  ) => {
    const entry: AuditEntry = {
      timestamp: new Date().toISOString(),
      eventType,
      payload,
    };
    setEntries(prev => {
      const updated = [...prev, entry];
      // FIFO eviction: keep only the most recent maxEntries
      const trimmed = updated.length > maxEntries
        ? updated.slice(updated.length - maxEntries)
        : updated;
      // Write synchronously to guarantee persistence
      writeLog(trimmed);
      return trimmed;
    });
  }, [maxEntries]);

  const clearLog = useCallback(() => {
    localStorage.removeItem(AUDIT_KEY);
    setEntries([]);
  }, []);

  return { entries, logEvent, clearLog };
}
