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
  /** Minimum character length for a valid scan (default 14). */
  minLength?: number;
  /** When true, accept letters and digits. When false (default), digits only. */
  alphanumeric?: boolean;
}

export interface UseBarcodeScannerReturn {
  /** Most recently scanned barcode, or null. */
  lastScan: string | null;
  /** True while digits are actively accumulating. */
  scanning: boolean;
}

export function useBarcodeScanner(options: UseBarcodeScannerOptions): UseBarcodeScannerReturn {
  const { enabled, onScan, maxIntervalMs = 80, minLength = 14, alphanumeric = false } = options;

  const bufferRef = useRef<string>("");
  const lastKeystrokeRef = useRef<number>(0);
  const [lastScan, setLastScan] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);

  // Debounce: ignore repeated scans of the same barcode within 2 seconds
  const lastEmittedRef = useRef<{ barcode: string; time: number }>({ barcode: "", time: 0 });
  const DEBOUNCE_MS = 2000;

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
      // Skip events originating from text inputs to avoid capturing typed text
      // (e.g., void reason field). Scanner events target the document body.
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
        resetBuffer();
        return;
      }

      // Skip when the on-screen KeyboardModal is open. The modal sets a
      // data attribute on document.body so we can detect it globally.
      if (document.body.hasAttribute("data-keyboard-modal-open")) {
        resetBuffer();
        return;
      }

      const now = Date.now();

      // If too much time passed since last keystroke, reset (human typing)
      if (bufferRef.current.length > 0 && now - lastKeystrokeRef.current > maxIntervalMs) {
        resetBuffer();
      }

      if (e.key === "Enter") {
        if (bufferRef.current.length >= minLength) {
          const barcode = bufferRef.current;
          const prev = lastEmittedRef.current;
          // Suppress duplicate scans of the same barcode within 2s
          if (barcode !== prev.barcode || now - prev.time > DEBOUNCE_MS) {
            lastEmittedRef.current = { barcode, time: now };
            setLastScan(barcode);
            onScanRef.current(barcode);
          }
        }
        resetBuffer();
        return;
      }

      // Accumulate characters (digits only, or alphanumeric if enabled)
      const charPattern = alphanumeric ? /^[a-zA-Z0-9]$/ : /^\d$/;
      if (charPattern.test(e.key)) {
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
  }, [enabled, maxIntervalMs, minLength, alphanumeric, resetBuffer]);

  return { lastScan, scanning };
}
