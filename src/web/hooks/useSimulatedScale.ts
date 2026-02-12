/**
 * Simulated scale for webapp testing.
 * Slider input with configurable max weight and stability delay.
 * Auto-locks after stability period of no change.
 */

import { useState, useRef, useCallback, useEffect } from "react";

export interface ScaleState {
  weight: number;
  stable: boolean;
  locked: boolean;
}

interface ScaleConfig {
  stabilityDelayMs?: number;
  maxWeight?: number;
}

export function useSimulatedScale(config?: ScaleConfig) {
  const stabilityDelay = config?.stabilityDelayMs ?? 2000;
  const maxWeight = config?.maxWeight ?? 30;

  const [weight, setWeight] = useState(0);
  const [stable, setStable] = useState(false);
  const [locked, setLocked] = useState(false);
  const stabilityTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const updateWeight = useCallback((newWeight: number) => {
    if (locked) return;
    setWeight(newWeight);
    setStable(false);

    if (stabilityTimer.current) {
      clearTimeout(stabilityTimer.current);
    }

    if (newWeight > 0) {
      stabilityTimer.current = setTimeout(() => {
        setStable(true);
      }, stabilityDelay);
    }
  }, [locked, stabilityDelay]);

  const lockWeight = useCallback(() => {
    if (weight > 0 && stable) {
      setLocked(true);
    }
  }, [weight, stable]);

  const reset = useCallback(() => {
    setWeight(0);
    setStable(false);
    setLocked(false);
    if (stabilityTimer.current) {
      clearTimeout(stabilityTimer.current);
      stabilityTimer.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      if (stabilityTimer.current) {
        clearTimeout(stabilityTimer.current);
      }
    };
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
