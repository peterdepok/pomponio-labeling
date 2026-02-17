/**
 * Audit log hook: typed event tracking with localStorage persistence
 * and confirmed server-side sync.
 *
 * Every audit event is:
 *   1. Written synchronously to localStorage (immediate, survives page refresh)
 *   2. POSTed to /api/audit on the Flask server (durable, survives browser reset)
 *
 * If the server POST fails, the event is added to a localStorage retry queue.
 * The retry queue is drained on the next successful POST. This guarantees
 * eventual delivery to the server-side log as long as the Flask bridge is
 * reachable at some point before localStorage is cleared.
 *
 * Exposes `auditSyncOk` boolean: false when the retry queue has entries,
 * meaning the server-side log is behind. The UI renders a warning banner.
 *
 * FIFO eviction at configurable max entries. Events are written synchronously
 * inside the state updater to guarantee persistence even on abrupt page close.
 */

import { useState, useCallback, useEffect, useRef } from "react";

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
  | "animal_purged"
  | "operator_shift_started"
  | "operator_changed"
  | "inactivity_auto_report"
  | "app_exit_initiated"
  | "print_failed"
  | "print_retry"
  | "print_cancel_after_failure"
  | "print_skipped_save"
  | "weight_override_forced"
  | "weight_manual_entry"
  | "audit_log_emailed"
  | "audit_log_cleared";

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
  animal_purged: { animalId: number; animalName: string };
  operator_shift_started: { operatorName: string };
  operator_changed: { oldName: string; newName: string };
  inactivity_auto_report: { timeoutHours: number };
  app_exit_initiated: Record<string, never>;
  print_failed: { error: string | undefined; sku: string | null | undefined; barcode: string };
  print_retry: { sku: string; barcode: string };
  print_cancel_after_failure: { sku: string | null; error: string | null };
  print_skipped_save: { sku: string; barcode: string; weightLb: number; error: string | null };
  weight_override_forced: { weightLb: number; sku: string; productName: string };
  weight_manual_entry: { weightLb: number; sku: string; productName: string };
  audit_log_emailed: { recipient: string; entryCount: number };
  audit_log_cleared: { entryCount: number };
}

// --- Entry stored in localStorage ---

export interface AuditEntry {
  timestamp: string; // ISO 8601
  eventType: AuditEventType;
  payload: AuditPayloads[AuditEventType];
}

// --- Storage helpers ---

const AUDIT_KEY = "pomponio_audit_log";
const AUDIT_RETRY_KEY = "pomponio_audit_retry";
const DEFAULT_MAX_ENTRIES = 5000;
const MAX_RETRY_QUEUE = 200; // cap retry queue to prevent runaway growth

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

function readRetryQueue(): AuditEntry[] {
  try {
    return JSON.parse(localStorage.getItem(AUDIT_RETRY_KEY) || "[]");
  } catch {
    return [];
  }
}

function writeRetryQueue(entries: AuditEntry[]): void {
  // Cap at MAX_RETRY_QUEUE, dropping oldest if exceeded
  const capped = entries.length > MAX_RETRY_QUEUE
    ? entries.slice(entries.length - MAX_RETRY_QUEUE)
    : entries;
  localStorage.setItem(AUDIT_RETRY_KEY, JSON.stringify(capped));
}

/**
 * POST an audit entry to the server. Returns true on confirmed
 * persistence, false on any failure.
 */
async function sendToServer(entry: AuditEntry): Promise<boolean> {
  try {
    const res = await fetch("/api/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(entry),
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) return false;
    const data = await res.json();
    return data.ok === true;
  } catch {
    return false;
  }
}

/**
 * Attempt to drain the retry queue. Sends entries one at a time,
 * stopping on first failure. Returns the number of entries remaining.
 */
async function drainRetryQueue(): Promise<number> {
  const queue = readRetryQueue();
  if (queue.length === 0) return 0;

  let sent = 0;
  for (const entry of queue) {
    const ok = await sendToServer(entry);
    if (!ok) break; // stop on first failure; server is likely down
    sent++;
  }

  if (sent > 0) {
    const remaining = queue.slice(sent);
    writeRetryQueue(remaining);
    return remaining.length;
  }
  return queue.length;
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
  /** False when retry queue has entries (server-side log is behind). */
  auditSyncOk: boolean;
}

export function useAuditLog(
  maxEntries: number = DEFAULT_MAX_ENTRIES,
  operatorName?: string,
): UseAuditLogReturn {
  const [entries, setEntries] = useState<AuditEntry[]>(readLog);
  const [auditSyncOk, setAuditSyncOk] = useState(
    () => readRetryQueue().length === 0
  );

  // Ref to prevent concurrent drain operations
  const drainingRef = useRef(false);

  // Periodic retry: drain the queue every 30 seconds
  useEffect(() => {
    const timer = setInterval(async () => {
      if (drainingRef.current) return;
      drainingRef.current = true;
      try {
        const remaining = await drainRetryQueue();
        setAuditSyncOk(remaining === 0);
      } finally {
        drainingRef.current = false;
      }
    }, 30_000);

    return () => clearInterval(timer);
  }, []);

  const logEvent = useCallback(<T extends AuditEventType>(
    eventType: T,
    payload: AuditPayloads[T],
  ) => {
    const entry: AuditEntry = {
      timestamp: new Date().toISOString(),
      eventType,
      payload: {
        ...payload,
        ...(operatorName ? { operator: operatorName } : {}),
      } as AuditPayloads[T],
    };

    // 1. Persist to localStorage immediately (synchronous, survives page refresh)
    setEntries(prev => {
      const updated = [...prev, entry];
      const trimmed = updated.length > maxEntries
        ? updated.slice(updated.length - maxEntries)
        : updated;
      writeLog(trimmed);
      return trimmed;
    });

    // 2. POST to server; on failure, queue for retry
    sendToServer(entry).then(async (ok) => {
      if (ok) {
        // Server confirmed. Try to drain any backlog.
        if (!drainingRef.current) {
          drainingRef.current = true;
          try {
            const remaining = await drainRetryQueue();
            setAuditSyncOk(remaining === 0);
          } finally {
            drainingRef.current = false;
          }
        }
      } else {
        // Server did not confirm. Queue for retry.
        const queue = readRetryQueue();
        queue.push(entry);
        writeRetryQueue(queue);
        setAuditSyncOk(false);
      }
    });
  }, [maxEntries, operatorName]);

  const clearLog = useCallback(() => {
    localStorage.removeItem(AUDIT_KEY);
    setEntries([]);
  }, []);

  return { entries, logEvent, clearLog, auditSyncOk };
}
