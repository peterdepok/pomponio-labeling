/**
 * Offline indicator banner: shown when the Flask bridge is unreachable.
 * Polls /api/health every 5 seconds. If 3 consecutive polls fail,
 * shows a fixed red banner across the top of the screen.
 * Auto-hides when connectivity is restored.
 *
 * Also surfaces config warnings (from /api/health configWarnings field)
 * as a yellow banner below the red offline banner when config.ini has
 * issues (missing, default printer name, blank API key, etc.).
 */

import { useState, useEffect, useRef } from "react";

const POLL_INTERVAL_MS = 5000;
const FAILURE_THRESHOLD = 3;

export function OfflineBanner() {
  const [offline, setOffline] = useState(false);
  const [configWarnings, setConfigWarnings] = useState<string[]>([]);
  const failCountRef = useRef(0);

  useEffect(() => {
    let mounted = true;

    const check = async () => {
      try {
        const res = await fetch("/api/health", { signal: AbortSignal.timeout(3000) });
        if (res.ok) {
          failCountRef.current = 0;
          if (mounted) {
            setOffline(false);
            try {
              const data = await res.json();
              setConfigWarnings(data.configWarnings ?? []);
            } catch {
              // JSON parse failure, ignore
            }
          }
        } else {
          failCountRef.current += 1;
        }
      } catch {
        failCountRef.current += 1;
      }
      if (failCountRef.current >= FAILURE_THRESHOLD && mounted) {
        setOffline(true);
      }
    };

    check();
    const interval = setInterval(check, POLL_INTERVAL_MS);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <>
      {offline && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9999,
            background: "linear-gradient(90deg, #b71c1c, #d32f2f)",
            color: "#ffffff",
            textAlign: "center",
            padding: "10px 16px",
            fontSize: 14,
            fontWeight: 700,
            letterSpacing: "0.05em",
            boxShadow: "0 2px 12px rgba(183, 28, 28, 0.6)",
            animation: "offline-slide-in 300ms ease-out",
          }}
        >
          BRIDGE OFFLINE -- Server not responding. Check kiosk.log for errors.
        </div>
      )}
      {!offline && configWarnings.length > 0 && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9997,
            background: "linear-gradient(90deg, #f57f17, #fbc02d)",
            color: "#212121",
            textAlign: "center",
            padding: "8px 16px",
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: "0.03em",
            boxShadow: "0 2px 8px rgba(245, 127, 23, 0.5)",
          }}
        >
          CONFIG WARNING -- {configWarnings[0]}
          {configWarnings.length > 1 && ` (+${configWarnings.length - 1} more)`}
        </div>
      )}
    </>
  );
}
