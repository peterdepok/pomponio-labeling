/**
 * Blocking startup modal: requires operator identification before using the app.
 * Shows recent operators as quick-select buttons (MRU list of up to 5 names
 * persisted in localStorage). Falls back to on-screen keyboard for new names.
 */

import { useState, useEffect, useRef } from "react";
import { KeyboardModal } from "./KeyboardModal.tsx";
import { TouchButton } from "./TouchButton.tsx";
import { saveSettingsToServer } from "../hooks/useSettings.ts";

const RECENT_KEY = "pomponio_recentOperators";
const MAX_RECENT = 5;

function readRecent(): string[] {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed.filter((n: unknown) => typeof n === "string" && n.length > 0) : [];
  } catch {
    return [];
  }
}

function writeRecent(names: string[]): void {
  localStorage.setItem(RECENT_KEY, JSON.stringify(names.slice(0, MAX_RECENT)));
}

/** Push a name to the front of the MRU list (deduplicating, case-insensitive). */
export function touchRecentOperator(name: string): void {
  const trimmed = name.trim();
  if (!trimmed) return;
  const current = readRecent();
  const filtered = current.filter(n => n.toLowerCase() !== trimmed.toLowerCase());
  writeRecent([trimmed, ...filtered]);
}

interface OperatorGateModalProps {
  isOpen: boolean;
  onConfirm: (name: string) => void;
}

export function OperatorGateModal({ isOpen, onConfirm }: OperatorGateModalProps) {
  const [recentNames, setRecentNames] = useState<string[]>([]);
  const [showKeyboard, setShowKeyboard] = useState(false);

  // Emergency bypass: triple-tap the title within 2 seconds to enter as
  // "Emergency" without requiring the on-screen keyboard. This allows
  // operators to bypass a broken keyboard or corrupted localStorage.
  const bypassTapRef = useRef({ count: 0, lastTap: 0 });

  const handleTitleTap = () => {
    const now = Date.now();
    const bp = bypassTapRef.current;
    if (now - bp.lastTap > 2000) {
      bp.count = 1;
    } else {
      bp.count += 1;
    }
    bp.lastTap = now;
    if (bp.count >= 5) {
      bp.count = 0;
      onConfirm("Emergency");
    }
  };

  // Refresh recent list whenever the modal opens
  useEffect(() => {
    if (isOpen) {
      setRecentNames(readRecent());
      setShowKeyboard(false);
      bypassTapRef.current = { count: 0, lastTap: 0 };
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSelect = (name: string) => {
    touchRecentOperator(name);
    saveSettingsToServer();
    onConfirm(name);
  };

  const handleKeyboardConfirm = (value: string) => {
    const trimmed = value.trim();
    if (!trimmed) return;
    touchRecentOperator(trimmed);
    saveSettingsToServer();
    setShowKeyboard(false);
    onConfirm(trimmed);
  };

  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-[100]"
      style={{
        backgroundColor: "rgba(0, 0, 0, 0.85)",
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
      }}
    >
      <div
        className="max-w-md w-full mx-4 rounded-2xl overflow-hidden"
        style={{
          background: "linear-gradient(145deg, #1e2240, #141428)",
          boxShadow: "0 8px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255,255,255,0.06)",
        }}
      >
        {/* Cyan accent bar */}
        <div
          className="h-1"
          style={{
            background: "linear-gradient(90deg, #0f3460, #00d4ff, #0f3460)",
          }}
        />

        <div className="p-8">
          <h2
            className="text-2xl font-bold text-[#e8e8e8] mb-2 select-none"
            onClick={handleTitleTap}
          >
            Operator Identification
          </h2>
          <p className="text-sm text-[#606080] mb-6">Select your name or type a new one to begin.</p>

          {/* Recent operator buttons */}
          {recentNames.length > 0 && (
            <div className="space-y-3 mb-6">
              {recentNames.map(name => (
                <button
                  key={name}
                  onClick={() => handleSelect(name)}
                  className="w-full h-14 rounded-xl text-lg font-semibold text-[#e8e8e8] transition-transform active:scale-[0.97]"
                  style={{
                    background: "linear-gradient(145deg, #1a2040, #161630)",
                    border: "1px solid #2a2a4a",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04)",
                  }}
                >
                  {name}
                </button>
              ))}
            </div>
          )}

          {/* Divider */}
          {recentNames.length > 0 && (
            <div className="flex items-center gap-3 mb-6">
              <div className="flex-1 h-px bg-[#2a2a4a]" />
              <span className="text-xs text-[#606080] uppercase tracking-widest">or</span>
              <div className="flex-1 h-px bg-[#2a2a4a]" />
            </div>
          )}

          {/* New name button */}
          <TouchButton
            text="Enter New Name"
            style="primary"
            onClick={() => setShowKeyboard(true)}
            className="w-full"
          />
        </div>
      </div>

      {/* Keyboard modal rendered inside the z-[100] container so it paints above the overlay */}
      <KeyboardModal
        isOpen={showKeyboard}
        title="Operator Name"
        initialValue=""
        placeholder="Enter your name..."
        onConfirm={handleKeyboardConfirm}
        onCancel={() => setShowKeyboard(false)}
      />
    </div>
  );
}
