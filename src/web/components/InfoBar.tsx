/**
 * Game HUD status bar: recessed badge cells with colored indicators.
 * 44px height. Looks like an inventory tray from a tablet game.
 */

interface InfoBarProps {
  animalName: string | null;
  boxNumber: number | null;
  packageCount: number;
  operatorName: string | null;
}

interface HudCellProps {
  label: string;
  value: string;
  color: string;
  active: boolean;
}

function HudCell({ label, value, color, active }: HudCellProps) {
  return (
    <div
      className="flex-1 flex items-center justify-center gap-2.5 h-[32px] mx-1 rounded-lg"
      style={{
        background: "#080e1a",
        boxShadow: "inset 0 2px 4px rgba(0,0,0,0.5), 0 1px 0 rgba(255,255,255,0.04)",
      }}
    >
      {/* Status pip */}
      <div
        className="w-2 h-2 rounded-full flex-shrink-0"
        style={{
          background: active ? color : "#2a2a4a",
          boxShadow: active ? `0 0 6px ${color}80` : "none",
        }}
      />
      <span
        className="text-[10px] uppercase tracking-[0.12em] font-semibold"
        style={{ color: "#606080" }}
      >
        {label}
      </span>
      <span
        className="text-sm font-bold"
        style={{
          color: active ? color : "#606080",
          textShadow: active ? `0 0 8px ${color}40` : "none",
        }}
      >
        {value}
      </span>
    </div>
  );
}

export function InfoBar({ animalName, boxNumber, packageCount, operatorName }: InfoBarProps) {
  return (
    <div
      className="h-11 flex items-center px-2 flex-shrink-0"
      style={{
        background: "linear-gradient(180deg, #0f1b30 0%, #0a0e1a 100%)",
        boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04), 0 -2px 0 #080e1a",
      }}
    >
      <HudCell
        label="Animal"
        value={animalName ?? "None"}
        color="#00d4ff"
        active={animalName !== null}
      />
      <HudCell
        label="Box"
        value={boxNumber !== null ? `#${boxNumber}` : "\u2014"}
        color="#51cf66"
        active={boxNumber !== null}
      />
      <HudCell
        label="Pkgs"
        value={String(packageCount)}
        color="#ffa500"
        active={packageCount > 0}
      />
      <HudCell
        label="Operator"
        value={operatorName ?? "None"}
        color="#b197fc"
        active={operatorName !== null}
      />
    </div>
  );
}
