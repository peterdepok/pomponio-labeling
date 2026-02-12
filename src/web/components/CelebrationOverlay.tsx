/**
 * Randomized celebration message shown during LABEL_PRINTED state.
 * Picks a random message + icon on each appearance.
 */

import { useEffect, useRef, useState } from "react";
import { PRINT_CELEBRATIONS, CELEBRATION_ICONS } from "../data/celebrations.ts";

interface CelebrationOverlayProps {
  visible: boolean;
}

export function CelebrationOverlay({ visible }: CelebrationOverlayProps) {
  // Generate new random indices each time visible transitions to true
  const [message, setMessage] = useState("");
  const [icon, setIcon] = useState("");
  const prevVisibleRef = useRef(false);

  useEffect(() => {
    if (visible && !prevVisibleRef.current) {
      // Fresh appearance: pick new random celebration
      const msgIdx = Math.floor(Math.random() * PRINT_CELEBRATIONS.length);
      const iconIdx = Math.floor(Math.random() * CELEBRATION_ICONS.length);
      setMessage(PRINT_CELEBRATIONS[msgIdx]);
      setIcon(CELEBRATION_ICONS[iconIdx]);
    }
    prevVisibleRef.current = visible;
  }, [visible]);

  if (!visible || !message) return null;

  return (
    <div
      className="flex items-center justify-center gap-3 mt-4 pt-3"
      style={{
        animation: "anim-celebration-pop 0.5s ease-out",
        borderTop: "1px solid rgba(81, 207, 102, 0.15)",
      }}
    >
      <span
        className="select-none"
        style={{
          fontSize: "36px",
          filter: "drop-shadow(0 0 8px rgba(81, 207, 102, 0.4))",
        }}
      >
        {icon}
      </span>
      <span
        className="text-lg font-bold"
        style={{
          color: "#51cf66",
          textShadow: "0 0 12px rgba(81, 207, 102, 0.3)",
        }}
      >
        {message}
      </span>
    </div>
  );
}
