/**
 * Production on-screen QWERTY keyboard for kiosk use.
 * Oversized keys for gloved-hand operation on 1280x1024 touchscreen.
 * Game-style 3D buttons. No external dependencies.
 *
 * Optional rows: numbers (0-9) and symbols (@, ., -, etc.)
 * controlled via props for context-specific keyboards.
 */

interface OnScreenKeyboardProps {
  onKey: (char: string) => void;
  onBackspace: () => void;
  onClear: () => void;
  showNumbers?: boolean;
  showSymbols?: boolean;
}

const NUMBER_ROW = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"];
const SYMBOL_ROW = ["@", ".", "-", "_", "/", ":"];

const LETTER_ROWS = [
  ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P"],
  ["A", "S", "D", "F", "G", "H", "J", "K", "L"],
  ["Z", "X", "C", "V", "B", "N", "M"],
];

const KEY_STYLE = {
  background: "linear-gradient(180deg, #2a2a4a, #1e2240)",
  boxShadow: "0 4px 0 0 #141428, 0 5px 10px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08)",
  color: "#e0e0e0",
} as const;

const ACTION_STYLE = {
  background: "linear-gradient(180deg, #3a2a2a, #2e1e1e)",
  boxShadow: "0 4px 0 0 #1a0e0e, 0 5px 10px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08)",
  color: "#ff8080",
} as const;

const CLEAR_STYLE = {
  background: "linear-gradient(180deg, #2a3a2a, #1e2e1e)",
  boxShadow: "0 4px 0 0 #0e1a0e, 0 5px 10px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08)",
  color: "#80ff80",
} as const;

const SYMBOL_STYLE = {
  background: "linear-gradient(180deg, #2a2a3a, #1e1e30)",
  boxShadow: "0 4px 0 0 #141428, 0 5px 10px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.08)",
  color: "#a0c0ff",
} as const;

const KEY_HEIGHT = "72px";
const LEDGE_HEIGHT = "4px";

export function OnScreenKeyboard({
  onKey,
  onBackspace,
  onClear,
  showNumbers = false,
  showSymbols = false,
}: OnScreenKeyboardProps) {
  return (
    <div className="flex flex-col gap-3 select-none w-full">
      {/* Number row (optional) */}
      {showNumbers && (
        <div className="flex gap-2 justify-center">
          {NUMBER_ROW.map(char => (
            <button
              key={char}
              onClick={() => onKey(char)}
              className="game-btn rounded-xl font-bold relative overflow-hidden flex-1"
              style={{
                ...KEY_STYLE,
                height: KEY_HEIGHT,
                fontSize: "22px",
                letterSpacing: "0.05em",
                maxWidth: "120px",
              }}
            >
              <div
                className="game-btn-ledge"
                style={{ height: LEDGE_HEIGHT, background: "#141428", borderRadius: "0 0 12px 12px" }}
              />
              <span className="relative z-10">{char}</span>
            </button>
          ))}
        </div>
      )}

      {/* Letter rows */}
      {LETTER_ROWS.map((row, ri) => (
        <div key={ri} className="flex gap-2 justify-center">
          {row.map(char => (
            <button
              key={char}
              onClick={() => onKey(char)}
              className="game-btn rounded-xl font-bold relative overflow-hidden flex-1"
              style={{
                ...KEY_STYLE,
                height: KEY_HEIGHT,
                fontSize: "22px",
                letterSpacing: "0.05em",
                maxWidth: "120px",
              }}
            >
              <div
                className="game-btn-ledge"
                style={{ height: LEDGE_HEIGHT, background: "#141428", borderRadius: "0 0 12px 12px" }}
              />
              <span className="relative z-10">{char}</span>
            </button>
          ))}
        </div>
      ))}

      {/* Symbol row (optional) */}
      {showSymbols && (
        <div className="flex gap-2 justify-center">
          {SYMBOL_ROW.map(char => (
            <button
              key={char}
              onClick={() => onKey(char)}
              className="game-btn rounded-xl font-bold relative overflow-hidden"
              style={{
                ...SYMBOL_STYLE,
                height: KEY_HEIGHT,
                fontSize: "22px",
                width: "100px",
              }}
            >
              <div
                className="game-btn-ledge"
                style={{ height: LEDGE_HEIGHT, background: "#141428", borderRadius: "0 0 12px 12px" }}
              />
              <span className="relative z-10">{char}</span>
            </button>
          ))}
        </div>
      )}

      {/* Bottom row: Backspace, Space, Clear */}
      <div className="flex gap-2 justify-center">
        <button
          onClick={onBackspace}
          className="game-btn rounded-xl font-bold relative overflow-hidden"
          style={{
            ...ACTION_STYLE,
            width: "180px",
            height: KEY_HEIGHT,
            fontSize: "18px",
            letterSpacing: "0.08em",
          }}
        >
          <div
            className="game-btn-ledge"
            style={{ height: LEDGE_HEIGHT, background: "#1a0e0e", borderRadius: "0 0 12px 12px" }}
          />
          <span className="relative z-10">BACK</span>
        </button>

        <button
          onClick={() => onKey(" ")}
          className="game-btn rounded-xl font-bold relative overflow-hidden flex-1"
          style={{
            ...KEY_STYLE,
            height: KEY_HEIGHT,
            fontSize: "18px",
            letterSpacing: "0.08em",
            maxWidth: "480px",
          }}
        >
          <div
            className="game-btn-ledge"
            style={{ height: LEDGE_HEIGHT, background: "#141428", borderRadius: "0 0 12px 12px" }}
          />
          <span className="relative z-10">SPACE</span>
        </button>

        <button
          onClick={onClear}
          className="game-btn rounded-xl font-bold relative overflow-hidden"
          style={{
            ...CLEAR_STYLE,
            width: "180px",
            height: KEY_HEIGHT,
            fontSize: "18px",
            letterSpacing: "0.08em",
          }}
        >
          <div
            className="game-btn-ledge"
            style={{ height: LEDGE_HEIGHT, background: "#0e1a0e", borderRadius: "0 0 12px 12px" }}
          />
          <span className="relative z-10">CLEAR</span>
        </button>
      </div>
    </div>
  );
}
