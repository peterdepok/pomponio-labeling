/**
 * Hero weight readout with radial gradient background and glowing border.
 * 72px weight number for high visibility at distance.
 */

interface WeightDisplayProps {
  weight: number;
  stable: boolean;
  locked: boolean;
}

export function WeightDisplay({ weight, stable, locked }: WeightDisplayProps) {
  const color = locked ? "#51cf66" : stable ? "#ffa500" : "#a0a0b0";
  const statusText = locked ? "LOCKED" : stable ? "STABLE" : weight > 0 ? "READING..." : "NO WEIGHT";

  const bgGradient = locked
    ? "radial-gradient(ellipse at 50% 40%, #1a3a1a 0%, #0d0d1a 70%)"
    : stable
      ? "radial-gradient(ellipse at 50% 40%, #2a2a1a 0%, #0d0d1a 70%)"
      : "radial-gradient(ellipse at 50% 40%, #1a1a2e 0%, #0d0d1a 70%)";

  return (
    <div
      className="flex flex-col items-center gap-2 p-5 rounded-xl"
      style={{
        background: bgGradient,
        border: `2px solid ${color}40`,
        boxShadow: `0 0 20px ${color}20, inset 0 1px 0 rgba(255,255,255,0.04)`,
      }}
    >
      <div
        className="text-xs font-bold uppercase tracking-[0.25em]"
        style={{ color }}
      >
        {statusText}
      </div>
      <div className="flex items-baseline gap-2">
        <span
          className="text-[56px] leading-none font-bold font-mono tabular-nums"
          style={{
            color,
            textShadow: `0 0 30px ${color}30`,
          }}
        >
          {weight.toFixed(2)}
        </span>
        <span
          className="text-2xl font-semibold"
          style={{ color: `${color}99` }}
        >
          lb
        </span>
      </div>
    </div>
  );
}
