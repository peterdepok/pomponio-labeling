/**
 * Monitor localStorage usage and warn when approaching the 5MB browser limit.
 *
 * Returns current usage in bytes and a percentage (0-100).
 * Recalculates every 30 seconds and on demand via `refresh()`.
 */

import { useState, useEffect, useCallback } from "react";

const CHECK_INTERVAL_MS = 30_000;
const ESTIMATED_LIMIT_BYTES = 5 * 1024 * 1024; // 5MB typical browser limit

function measureUsage(): number {
  try {
    let total = 0;
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key) {
        // Each char in JS is 2 bytes (UTF-16), but localStorage typically
        // counts as 1 byte per char for quota purposes.
        total += key.length + (localStorage.getItem(key)?.length ?? 0);
      }
    }
    return total;
  } catch {
    return 0;
  }
}

export function useStorageMonitor() {
  const [usageBytes, setUsageBytes] = useState(() => measureUsage());

  const refresh = useCallback(() => {
    setUsageBytes(measureUsage());
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, CHECK_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  const usagePercent = Math.min(100, Math.round((usageBytes / ESTIMATED_LIMIT_BYTES) * 100));
  const usageMB = (usageBytes / (1024 * 1024)).toFixed(2);

  return {
    usageBytes,
    usagePercent,
    usageMB,
    limitMB: "5.00",
    refresh,
  };
}
