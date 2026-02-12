/**
 * Game-style product button: chunky 3D ledge, glossy highlight, bouncy press,
 * radial tap flash on click. Inspired by Candy Crush / Fall Guys.
 */

import { useRef, useCallback } from "react";
import { CATEGORY_COLORS } from "../data/theme.ts";
import type { ProductCategory } from "../data/classify.ts";


interface ProductButtonProps {
  name: string;
  sku: string;
  category: ProductCategory;
  onClick: () => void;
}

export function ProductButton({ name, sku, category, onClick }: ProductButtonProps) {
  const colors = CATEGORY_COLORS[category] ?? CATEGORY_COLORS["Steaks"];
  const btnRef = useRef<HTMLButtonElement>(null);

  const handleClick = useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    const btn = btnRef.current;
    if (!btn) return;

    // Bounce
    btn.classList.remove("game-btn-bounce");
    void btn.offsetWidth;
    btn.classList.add("game-btn-bounce");

    // Tap flash at click position
    const rect = btn.getBoundingClientRect();
    const flash = document.createElement("div");
    flash.className = "tap-flash";
    flash.style.left = `${e.clientX - rect.left - 30}px`;
    flash.style.top = `${e.clientY - rect.top - 30}px`;
    btn.appendChild(flash);
    setTimeout(() => flash.remove(), 400);

    onClick();
  }, [onClick]);

  return (
    <button
      ref={btnRef}
      onClick={handleClick}
      className="game-btn h-[96px] w-full rounded-2xl overflow-hidden flex flex-col items-center justify-center text-center px-4 relative"
      style={{
        background: `linear-gradient(180deg, ${colors.fillLight} 0%, ${colors.fill} 100%)`,
        boxShadow: `
          0 6px 0 0 ${colors.shadow},
          0 8px 16px rgba(0,0,0,0.4),
          inset 0 2px 0 rgba(255,255,255,0.25),
          inset 0 -2px 4px rgba(0,0,0,0.15)
        `,
        borderRadius: "16px",
      }}
    >
      {/* Glossy highlight */}
      <div className="game-gloss" />

      {/* Inner glow */}
      <div
        className="absolute inset-0 pointer-events-none rounded-2xl"
        style={{ boxShadow: "inset 0 0 20px rgba(255,255,255,0.08)" }}
      />

      {/* Product name */}
      <span
        className="relative z-10 font-extrabold leading-tight line-clamp-2"
        style={{
          fontSize: "clamp(18px, 1.9vw, 28px)",
          color: "#ffffff",
          textShadow: `0 2px 4px rgba(0,0,0,0.4), 0 0 12px ${colors.shadow}80`,
          letterSpacing: "0.01em",
        }}
      >
        {name}
      </span>

      {/* SKU */}
      <span
        className="relative z-10 font-mono mt-0.5"
        style={{
          fontSize: "10px",
          color: "rgba(255,255,255,0.5)",
          textShadow: "0 1px 2px rgba(0,0,0,0.3)",
        }}
      >
        {sku}
      </span>

      {/* 3D ledge */}
      <div
        className="game-btn-ledge"
        style={{
          height: "6px",
          background: colors.shadow,
          borderRadius: "0 0 16px 16px",
        }}
      />
    </button>
  );
}
