/**
 * Periodic state backup to disk via Flask endpoint.
 *
 * Every 15 seconds, POSTs the current app state (animals, boxes, packages,
 * currentAnimalId, currentBoxId) to /api/backup. The Flask endpoint writes
 * this to exports/state_backup.json, overwriting each time.
 *
 * Also exposes a `triggerBackup()` function for immediate, on-demand
 * backup after critical events (e.g. package labeled, box closed).
 *
 * This creates a second persistence lane alongside localStorage, protecting
 * against localStorage corruption, accidental clearing, or browser crashes.
 *
 * Fire-and-forget: errors are caught silently (backup is best-effort).
 * Only backs up if there is data worth saving (animals.length > 0).
 *
 * Uses refs for the state snapshot to avoid re-creating the interval
 * every time state changes (which would defeat the purpose of a stable
 * cadence).
 */

import { useCallback, useEffect, useRef } from "react";
import type { Animal, Box, Package } from "./useAppState.ts";

const BACKUP_INTERVAL_MS = 15_000; // 15 seconds

interface BackupState {
  animals: Animal[];
  boxes: Box[];
  packages: Package[];
  currentAnimalId: number | null;
  currentBoxId: number | null;
}

function doBackup(state: BackupState): void {
  if (state.animals.length === 0) return;

  fetch("/api/backup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      animals: state.animals,
      boxes: state.boxes,
      packages: state.packages,
      currentAnimalId: state.currentAnimalId,
      currentBoxId: state.currentBoxId,
    }),
  }).catch(() => {
    // Silently ignore backup failures (best-effort)
  });
}

export function useAutoBackup(state: BackupState): { triggerBackup: () => void } {
  // Keep a mutable ref to the latest state so the interval callback
  // always reads fresh data without causing effect re-runs.
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    const timer = setInterval(() => {
      doBackup(stateRef.current);
    }, BACKUP_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []); // Stable interval: never re-created

  // On-demand backup for critical events (package labeled, box closed, etc.)
  const triggerBackup = useCallback(() => {
    doBackup(stateRef.current);
  }, []);

  return { triggerBackup };
}
