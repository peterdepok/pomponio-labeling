/**
 * Keyboard-based barcode capture for USB scanners.
 * USB barcode scanners emulate rapid keyboard input: digits fired in quick
 * succession followed by Enter. This hook distinguishes scanner input from
 * human typing via inter-keystroke timing.
 *
 * Only active when `enabled` is true (typically when the Scanner tab is shown).
 */

import { useCallback, useEffect, useRef, useState } from "react";

interface UseBarcodeScannerOptions {
  /** Only capture input when true. */
  enabled: boolean;
  /** Called with the scanned barcode string on successful scan. */
  onScan: (barcode: string) => void;
  /** Max milliseconds between keystrokes to count as scanner input (default 80). */
  maxIntervalMs?: number;
  /** Minimum digit length for a valid scan (default 12). */
  minLength?: number;
}

export interface UseBarcodeScannerReturn {
  /** Most recently scanned barcode, or null. */
  lastScan: string | null;
  /** True while digits are actively accumulating. */
  scanning: boolean;
}

export function useBarcodeScanner(options: UseBarcodeScannerOptions): UseBarcodeScannerReturn {
  const { enabled, onScan, maxIntervalMs = 80, minLength = 12 } = options;

  const bufferRef = useRef<string>("");
  const lastKeystrokeRef = useRef<number>(0);
  const [lastScan, setLastScan] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);

  // Stable reference to onScan to avoid re-attaching listener
  const onScanRef = useRef(onScan);
  onScanRef.current = onScan;

  const resetBuffer = useCallback(() => {
    bufferRef.current = "";
    setScanning(false);
  }, []);

  useEffect(() => {
    if (!enabled) {
      resetBuffer();
      return;
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      const now = Date.now();

      // If too much time passed since last keystroke, reset (human typing)
      if (bufferRef.current.length > 0 && now - lastKeystrokeRef.current > maxIntervalMs) {
        resetBuffer();
      }

      if (e.key === "Enter") {
        if (bufferRef.current.length >= minLength) {
          const barcode = bufferRef.current;
          setLastScan(barcode);
          onScanRef.current(barcode);
        }
        resetBuffer();
        return;
      }

      // Only accumulate digit characters
      if (/^\d$/.test(e.key)) {
        bufferRef.current += e.key;
        lastKeystrokeRef.current = now;
        setScanning(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      resetBuffer();
    };
  }, [enabled, maxIntervalMs, minLength, resetBuffer]);

  return { lastScan, scanning };
}
