/**
 * Full-screen modal with on-screen keyboard for kiosk text entry.
 * Wraps OnScreenKeyboard in a dialog overlay with a text display,
 * confirm/cancel buttons, and optional number/symbol rows.
 */

import { useState, useEffect, useCallback } from "react";
import { OnScreenKeyboard } from "./OnScreenKeyboard.tsx";
import { TouchButton } from "./TouchButton.tsx";

interface KeyboardModalProps {
  isOpen: boolean;
  title: string;
  initialValue: string;
  placeholder?: string;
  onConfirm: (value: string) => void;
  onCancel: () => void;
  showNumbers?: boolean;
  showSymbols?: boolean;
}

export function KeyboardModal({
  isOpen,
  title,
  initialValue,
  placeholder = "",
  onConfirm,
  onCancel,
  showNumbers = false,
  showSymbols = false,
}: KeyboardModalProps) {
  const [value, setValue] = useState(initialValue);

  // Reset value when modal opens with new initial value
  useEffect(() => {
    if (isOpen) {
      setValue(initialValue);
    }
  }, [isOpen, initialValue]);

  // Signal to barcode scanner that a keyboard modal is open. The scanner
  // hook checks for this attribute to avoid capturing keystrokes meant
  // for the on-screen keyboard (which fires synthetic key events).
  useEffect(() => {
    if (isOpen) {
      document.body.setAttribute("data-keyboard-modal-open", "true");
    } else {
      document.body.removeAttribute("data-keyboard-modal-open");
    }
    return () => {
      document.body.removeAttribute("data-keyboard-modal-open");
    };
  }, [isOpen]);

  const handleKey = useCallback((char: string) => {
    setValue(prev => prev + char);
  }, []);

  const handleBackspace = useCallback(() => {
    setValue(prev => prev.slice(0, -1));
  }, []);

  const handleClear = useCallback(() => {
    setValue("");
  }, []);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 flex flex-col items-center justify-center z-50"
      style={{
        backgroundColor: "rgba(0, 0, 0, 0.85)",
        backdropFilter: "blur(4px)",
        WebkitBackdropFilter: "blur(4px)",
      }}
    >
      <div
        className="w-full max-w-4xl mx-4 rounded-2xl overflow-hidden flex flex-col"
        style={{
          background: "linear-gradient(145deg, #1e2240, #141428)",
          boxShadow: "0 8px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255,255,255,0.06)",
          animation: "dialog-scale-in 200ms ease-out",
        }}
      >
        {/* Cyan accent bar */}
        <div
          className="h-1"
          style={{
            background: "linear-gradient(90deg, #0f3460, #00d4ff, #0f3460)",
          }}
        />

        <div className="p-6">
          {/* Title */}
          <h2 className="text-xl font-bold text-[#e8e8e8] mb-3">{title}</h2>

          {/* Text display bar */}
          <div
            className="flex items-center h-[56px] px-5 rounded-xl mb-4"
            style={{
              background: "#080e1a",
              boxShadow: "inset 0 2px 6px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.05)",
            }}
          >
            <span
              className="text-xl font-bold tracking-wide flex-1 truncate"
              style={{ color: value ? "#e8e8e8" : "#404060" }}
            >
              {value || placeholder}
            </span>
          </div>

          {/* Keyboard */}
          <OnScreenKeyboard
            onKey={handleKey}
            onBackspace={handleBackspace}
            onClear={handleClear}
            showNumbers={showNumbers}
            showSymbols={showSymbols}
          />

          {/* Confirm / Cancel */}
          <div className="flex gap-4 mt-4">
            <TouchButton
              text="Cancel"
              style="secondary"
              onClick={onCancel}
              className="flex-1"
            />
            <TouchButton
              text="Done"
              style="primary"
              onClick={() => onConfirm(value)}
              className="flex-1"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
