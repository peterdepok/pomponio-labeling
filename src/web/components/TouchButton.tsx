/**
 * Game-style workflow button with 3D ledge, glossy highlight, and bounce.
 * Three sizes: lg (80px, primary workflow), md (64px, default), sm (48px, cancel/inline).
 * Shares the .game-btn CSS system with ProductButton and category tabs.
 */

import { useRef, useCallback } from "react";

interface TouchButtonProps {
  text: string;
  style?: "primary" | "success" | "danger" | "secondary";
  size?: "lg" | "md" | "sm";
  onClick?: () => void;
  disabled?: boolean;
  width?: string;
  className?: string;
}

const SIZE_MAP = {
  lg: { height: 80, text: "text-xl", ledge: 6 },
  md: { height: 64, text: "text-lg", ledge: 5 },
  sm: { height: 48, text: "text-base", ledge: 4 },
} as const;

const STYLES = {
  primary: {
    fill: "#1565c0",
    fillLight: "#1e88e5",
    shadow: "#0d47a1",
  },
  success: {
    fill: "#2e7d32",
    fillLight: "#43a047",
    shadow: "#1b5e20",
  },
  danger: {
    fill: "#c62828",
    fillLight: "#e53935",
    shadow: "#8e0000",
  },
  secondary: {
    fill: "#37474f",
    fillLight: "#546e7a",
    shadow: "#263238",
  },
} as const;

export function TouchButton({
  text,
  style = "primary",
  size = "md",
  onClick,
  disabled = false,
  width,
  className = "",
}: TouchButtonProps) {
  const s = STYLES[style];
  const sz = SIZE_MAP[size];
  const btnRef = useRef<HTMLButtonElement>(null);

  const handleClick = useCallback(() => {
    if (disabled || !onClick) return;
    const btn = btnRef.current;
    if (btn) {
      btn.classList.remove("game-btn-bounce");
      void btn.offsetWidth;
      btn.classList.add("game-btn-bounce");
    }
    onClick();
  }, [onClick, disabled]);

  return (
    <button
      ref={btnRef}
      onClick={handleClick}
      disabled={disabled}
      className={`
        game-btn relative overflow-hidden rounded-xl font-bold text-white
        flex items-center justify-center select-none
        ${sz.text}
        ${disabled ? "opacity-40 grayscale !cursor-not-allowed" : ""}
        ${className}
      `}
      style={{
        width: width || undefined,
        minHeight: `${sz.height}px`,
        background: disabled
          ? "linear-gradient(180deg, #2a2a3a, #1e1e2e)"
          : `linear-gradient(180deg, ${s.fillLight} 0%, ${s.fill} 100%)`,
        boxShadow: disabled
          ? "0 3px 0 0 #141428, inset 0 1px 0 rgba(255,255,255,0.04)"
          : `0 ${sz.ledge}px 0 0 ${s.shadow}, 0 ${sz.ledge + 2}px 12px rgba(0,0,0,0.3), inset 0 2px 0 rgba(255,255,255,0.2), inset 0 -2px 4px rgba(0,0,0,0.15)`,
        textShadow: disabled ? "none" : "0 2px 4px rgba(0,0,0,0.3)",
      }}
    >
      {/* Glossy highlight */}
      {!disabled && <div className="game-gloss" />}

      {/* 3D ledge */}
      <div
        className="game-btn-ledge"
        style={{
          height: disabled ? "3px" : `${sz.ledge}px`,
          background: disabled ? "#141428" : s.shadow,
          borderRadius: `0 0 12px 12px`,
        }}
      />

      <span className="relative z-10">{text}</span>
    </button>
  );
}
