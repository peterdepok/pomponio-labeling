/**
 * Periodic state backup to disk via Flask endpoint.
 *
 * Every 60 seconds, POSTs the current app state (animals, boxes, packages,
 * currentAnimalId, currentBoxId) to /api/backup. The Flask endpoint writes
 * this to exports/state_backup.json, overwriting each time.
 *
 * This creates a second persistence lane alongside localStorage, protecting
 * against localStorage corruption, accidental clearing, or browser crashes.
 *
 * Fire-and-forget: errors are caught silently (backup is best-effort).
 * Only backs up if there is data worth saving (animals.length > 0).
 *
 * Uses refs for the state snapshot to avoid re-creating the interval
 * every time state changes (which would defeat the purpose of a stable
 * 60-second cadence).
 */

import { useEffect, useRef } from "react";
import type { Animal, Box, Package } from "./useAppState.ts";

const BACKUP_INTERVAL_MS = 60_000; // 60 seconds

interface BackupState {
  animals: Animal[];
  boxes: Box[];
  packages: Package[];
  currentAnimalId: number | null;
  currentBoxId: number | null;
}

export function useAutoBackup(state: BackupState): void {
  // Keep a mutable ref to the latest state so the interval callback
  // always reads fresh data without causing effect re-runs.
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    const timer = setInterval(() => {
      const current = stateRef.current;

      // Nothing to back up
      if (current.animals.length === 0) return;

      fetch("/api/backup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          animals: current.animals,
          boxes: current.boxes,
          packages: current.packages,
          currentAnimalId: current.currentAnimalId,
          currentBoxId: current.currentBoxId,
        }),
      }).catch(() => {
        // Silently ignore backup failures (best-effort)
      });
    }, BACKUP_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []); // Stable interval: never re-created
}
