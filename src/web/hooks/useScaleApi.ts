/**
 * Real scale hook: polls GET /api/scale (Flask bridge) at 200ms intervals.
 *
 * Returns the same interface as useSimulatedScale so LabelingScreen can
 * swap between them based on scaleMode setting.
 *
 * The `enabled` flag prevents fetch calls when Flask is not running
 * (e.g. Vite dev mode on Mac with scaleMode="simulated").
 */

import { useState, useRef, useCallback, useEffect } from "react";

interface ScaleApiConfig {
  maxWeight?: number;
  enabled?: boolean;
}

interface ScaleApiResponse {
  weight: number;
  stable: boolean;
  unit: string;
  error?: string;
}

const POLL_MS = 200;
const ERROR_THRESHOLD = 15; // consecutive failures before surfacing error (~3 seconds)

export function useScaleApi(config?: ScaleApiConfig) {
  const maxWeight = config?.maxWeight ?? 30;
  const enabled = config?.enabled ?? true;

  const [weight, setWeight] = useState(0);
  const [stable, setStable] = useState(false);
  const [locked, setLocked] = useState(false);
  const [scaleError, setScaleError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const failCountRef = useRef(0);

  // Poll the bridge scale endpoint
  useEffect(() => {
    if (!enabled || locked) return;

    const poll = async () => {
      try {
        const res = await fetch("/api/scale");
        if (!res.ok) {
          failCountRef.current += 1;
          setStable(false);
          if (failCountRef.current >= ERROR_THRESHOLD) {
            setScaleError("Scale API not responding");
          }
          return;
        }
        const data: ScaleApiResponse = await res.json();
        if (data.error) {
          failCountRef.current += 1;
          setStable(false);
          if (failCountRef.current >= ERROR_THRESHOLD) {
            setScaleError(data.error);
          }
          return;
        }
        failCountRef.current = 0;
        setScaleError(null);
        setWeight(data.weight);
        setStable(data.stable);
      } catch {
        failCountRef.current += 1;
        setStable(false);
        if (failCountRef.current >= ERROR_THRESHOLD) {
          setScaleError("Bridge offline or scale disconnected");
        }
      }
    };

    poll(); // immediate first read
    intervalRef.current = setInterval(poll, POLL_MS);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, locked]);

  // updateWeight is a no-op for the real scale (hardware provides weight)
  const updateWeight = useCallback((_newWeight: number) => {}, []);

  const lockWeight = useCallback(() => {
    if (weight > 0 && stable) {
      setLocked(true);
    }
  }, [weight, stable]);

  const reset = useCallback(() => {
    setWeight(0);
    setStable(false);
    setLocked(false);
  }, []);

  return {
    weight,
    stable,
    locked,
    maxWeight,
    scaleError,
    updateWeight,
    lockWeight,
    reset,
  };
}
