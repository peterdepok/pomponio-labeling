/**
 * Lightweight packages-per-minute tracker for gamification.
 * Rolling 60-second window with cooldown-gated encouragement trigger.
 * Standalone hook, no dependency on useAppState.
 */

import { useCallback, useEffect, useRef, useState } from "react";

interface UseSpeedTrackerOptions {
  /** PPM threshold to qualify as "fast" (default 4). */
  threshold?: number;
  /** Seconds between encouragement popups (default 45). */
  cooldownSec?: number;
}

export interface UseSpeedTrackerReturn {
  recordPackage: () => void;
  packagesPerMinute: number;
  isFast: boolean;
  shouldShowEncouragement: boolean;
  dismissEncouragement: () => void;
}

const WINDOW_MS = 60_000; // 60-second rolling window

export function useSpeedTracker(options?: UseSpeedTrackerOptions): UseSpeedTrackerReturn {
  const threshold = options?.threshold ?? 4;
  const cooldownMs = (options?.cooldownSec ?? 45) * 1000;

  // Timestamps of recent package completions
  const timestampsRef = useRef<number[]>([]);
  // Last time an encouragement was shown
  const lastShownRef = useRef<number>(0);
  // Force re-render when PPM changes
  const [ppm, setPpm] = useState(0);
  const [showEncouragement, setShowEncouragement] = useState(false);

  const recordPackage = useCallback(() => {
    const now = Date.now();
    const cutoff = now - WINDOW_MS;

    // Prune old entries and add new timestamp
    timestampsRef.current = timestampsRef.current.filter(t => t > cutoff);
    timestampsRef.current.push(now);

    const currentPpm = timestampsRef.current.length;
    setPpm(currentPpm);

    // Check if operator qualifies for encouragement
    const isFast = currentPpm >= threshold;
    const cooldownElapsed = now - lastShownRef.current > cooldownMs;

    if (isFast && cooldownElapsed) {
      lastShownRef.current = now;
      setShowEncouragement(true);
    }
  }, [threshold, cooldownMs]);

  // Periodically prune old timestamps so PPM decays to zero
  // when the operator stops scanning. Without this, PPM only
  // updates on the next recordPackage() call.
  useEffect(() => {
    const interval = setInterval(() => {
      const cutoff = Date.now() - WINDOW_MS;
      const pruned = timestampsRef.current.filter(t => t > cutoff);
      // Only trigger re-render if count actually changed
      if (pruned.length !== timestampsRef.current.length) {
        timestampsRef.current = pruned;
        setPpm(pruned.length);
      }
    }, 5_000); // check every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const dismissEncouragement = useCallback(() => {
    setShowEncouragement(false);
  }, []);

  const isFast = ppm >= threshold;

  return {
    recordPackage,
    packagesPerMinute: ppm,
    isFast,
    shouldShowEncouragement: showEncouragement,
    dismissEncouragement,
  };
}
