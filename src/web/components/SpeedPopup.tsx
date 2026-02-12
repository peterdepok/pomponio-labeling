/**
 * Speed encouragement popup for fast operators.
 * Auto-dismisses after 3 seconds. Rendered at App level.
 */

import { useEffect } from "react";

interface SpeedPopupProps {
  message: string;
  icon: string;
  onDismiss: () => void;
}

export function SpeedPopup({ message, icon, onDismiss }: SpeedPopupProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 3000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      className="fixed z-50 rounded-xl px-6 py-4 max-w-sm"
      style={{
        bottom: "80px",
        left: "24px",
        background: "linear-gradient(145deg, #2a1f00, #1a1500)",
        border: "2px solid rgba(232, 168, 80, 0.4)",
        boxShadow: "0 4px 24px rgba(232, 168, 80, 0.2), 0 0 40px rgba(232, 168, 80, 0.08)",
        animation: "toast-slide-in 300ms ease-out",
      }}
    >
      <div className="flex items-center gap-3">
        <span
          className="select-none"
          style={{
            fontSize: "32px",
            filter: "drop-shadow(0 0 8px rgba(232, 168, 80, 0.5))",
          }}
        >
          {icon}
        </span>
        <div>
          <div
            className="text-xs uppercase tracking-[0.15em] mb-1"
            style={{ color: "#e8a850" }}
          >
            Speed Bonus
          </div>
          <div className="text-base font-bold text-[#e8e8e8]">
            {message}
          </div>
        </div>
      </div>
    </div>
  );
}
