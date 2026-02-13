/**
 * Game-style top navigation with embossed header panel and 3D tab buttons.
 * 64px height. Brand nameplate on left, four chunky tab buttons.
 */

export type TabId = "Label" | "Products" | "Boxes" | "Animals" | "Scanner" | "Settings";

interface TabNavProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  onExit?: () => void;
}

const TABS: TabId[] = ["Animals", "Products", "Label", "Boxes", "Scanner", "Settings"];

const TAB_COLORS: Record<TabId, { fill: string; fillLight: string; shadow: string }> = {
  Label:    { fill: "#1565c0", fillLight: "#1e88e5", shadow: "#0d47a1" },
  Products: { fill: "#c0392b", fillLight: "#e74c3c", shadow: "#922b21" },
  Boxes:    { fill: "#2e7d32", fillLight: "#43a047", shadow: "#1b5e20" },
  Animals:  { fill: "#6a1b9a", fillLight: "#8e24aa", shadow: "#4a148c" },
  Scanner:  { fill: "#e65100", fillLight: "#ff6d00", shadow: "#bf360c" },
  Settings: { fill: "#546e7a", fillLight: "#78909c", shadow: "#37474f" },
};

export function TabNav({ activeTab, onTabChange, onExit }: TabNavProps) {
  return (
    <nav
      className="h-[64px] flex items-center gap-2 px-3 flex-shrink-0 relative"
      style={{
        background: "linear-gradient(180deg, #1a2744 0%, #0f1b30 100%)",
        boxShadow: "0 4px 0 0 #080e1a, 0 6px 20px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.08)",
      }}
    >
      {/* Brand nameplate: recessed badge */}
      <div
        className="flex items-center justify-center flex-shrink-0 rounded-lg px-4 h-[44px]"
        style={{
          background: "#080e1a",
          boxShadow: "inset 0 2px 6px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.05)",
          minWidth: "160px",
        }}
      >
        <div className="text-center select-none">
          <div
            className="text-[12px] font-extrabold tracking-[0.3em] leading-tight"
            style={{
              color: "#e8e8e8",
              textShadow: "0 1px 3px rgba(0,0,0,0.5)",
            }}
          >
            POMPONIO
          </div>
          <div
            className="text-[10px] font-bold tracking-[0.4em] leading-tight mt-0.5"
            style={{
              color: "#00d4ff",
              textShadow: "0 0 8px rgba(0,212,255,0.4)",
            }}
          >
            RANCH
          </div>
        </div>
      </div>

      {/* Tab buttons: game-style 3D pills */}
      <div className="flex-1 flex gap-2 justify-center">
        {TABS.map(tab => {
          const isActive = tab === activeTab;
          const colors = TAB_COLORS[tab];
          return (
            <button
              key={tab}
              onClick={() => onTabChange(tab)}
              className="game-btn h-[44px] px-6 rounded-lg font-extrabold select-none relative overflow-hidden"
              style={{
                minWidth: "100px",
                fontSize: "16px",
                background: isActive
                  ? `linear-gradient(180deg, ${colors.fillLight}, ${colors.fill})`
                  : "linear-gradient(180deg, #2a2a4a, #1e2240)",
                boxShadow: isActive
                  ? `0 4px 0 0 ${colors.shadow}, 0 5px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.2)`
                  : "0 3px 0 0 #0a0e1a, 0 4px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06)",
                color: isActive ? "#ffffff" : "#c0c0d0",
                textShadow: isActive ? "0 1px 3px rgba(0,0,0,0.4)" : "none",
              }}
            >
              {isActive && <div className="game-gloss" />}
              <div
                className="game-btn-ledge"
                style={{
                  height: isActive ? "4px" : "3px",
                  background: isActive ? colors.shadow : "#0a0e1a",
                  borderRadius: "0 0 8px 8px",
                }}
              />
              <span className="relative z-10">{tab}</span>
            </button>
          );
        })}
      </div>

      {/* Exit button: danger styled, far right */}
      {onExit && (
        <button
          onClick={onExit}
          className="game-btn h-[44px] px-5 rounded-lg font-extrabold select-none relative overflow-hidden flex-shrink-0"
          style={{
            minWidth: "80px",
            fontSize: "16px",
            background: "linear-gradient(180deg, #e53935, #c62828)",
            boxShadow: "0 4px 0 0 #8e0000, 0 5px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.2)",
            color: "#ffffff",
            textShadow: "0 1px 3px rgba(0,0,0,0.4)",
          }}
        >
          <div className="game-gloss" />
          <div
            className="game-btn-ledge"
            style={{
              height: "4px",
              background: "#8e0000",
              borderRadius: "0 0 8px 8px",
            }}
          />
          <span className="relative z-10">Exit</span>
        </button>
      )}
    </nav>
  );
}
