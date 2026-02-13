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

export function useScaleApi(config?: ScaleApiConfig) {
  const maxWeight = config?.maxWeight ?? 30;
  const enabled = config?.enabled ?? true;

  const [weight, setWeight] = useState(0);
  const [stable, setStable] = useState(false);
  const [locked, setLocked] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll the bridge scale endpoint
  useEffect(() => {
    if (!enabled || locked) return;

    const poll = async () => {
      try {
        const res = await fetch("/api/scale");
        if (!res.ok) {
          setStable(false);
          return;
        }
        const data: ScaleApiResponse = await res.json();
        if (data.error) {
          setStable(false);
          return;
        }
        setWeight(data.weight);
        setStable(data.stable);
      } catch {
        // Flask not running or network error; silently degrade
        setStable(false);
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
    updateWeight,
    lockWeight,
    reset,
  };
}
