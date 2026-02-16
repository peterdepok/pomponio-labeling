/**
 * Auto-email shift report after prolonged inactivity.
 *
 * Tracks the timestamp of the last label print (via `recordActivity`).
 * If no activity occurs for `timeoutMs` (default 2 hours), fires
 * the `onInactivityTimeout` callback once. Resets on next activity.
 *
 * The timer only runs when `enabled` is true and there is at least
 * one animal in the session (no point emailing an empty report).
 */

import { useRef, useEffect, useCallback } from "react";

interface UseInactivityEmailConfig {
  enabled: boolean;
  hasData: boolean;
  timeoutMs?: number;
  onInactivityTimeout: () => void;
}

const DEFAULT_TIMEOUT_MS = 2 * 60 * 60 * 1000; // 2 hours

export function useInactivityEmail({
  enabled,
  hasData,
  timeoutMs = DEFAULT_TIMEOUT_MS,
  onInactivityTimeout,
}: UseInactivityEmailConfig) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const firedRef = useRef(false);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startTimer = useCallback(() => {
    clearTimer();
    if (!enabled || !hasData || firedRef.current) return;
    timerRef.current = setTimeout(() => {
      firedRef.current = true;
      onInactivityTimeout();
    }, timeoutMs);
  }, [enabled, hasData, timeoutMs, onInactivityTimeout, clearTimer]);

  // Restart timer whenever enabled/hasData change
  useEffect(() => {
    startTimer();
    return clearTimer;
  }, [startTimer, clearTimer]);

  // Called by the parent when a label is printed (resets the clock)
  const recordActivity = useCallback(() => {
    firedRef.current = false;
    startTimer();
  }, [startTimer]);

  return { recordActivity };
}
