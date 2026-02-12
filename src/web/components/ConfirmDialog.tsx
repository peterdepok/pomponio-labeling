/**
 * Modal confirmation dialog with glass morphism and scale-in animation.
 * Red accent bar for destructive actions.
 */

import { TouchButton } from "./TouchButton.tsx";

interface ConfirmDialogProps {
  title: string;
  message: string;
  confirmText?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  title,
  message,
  confirmText = "Confirm",
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{
        backgroundColor: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(4px)",
        WebkitBackdropFilter: "blur(4px)",
      }}
    >
      <div
        className="max-w-md w-full mx-4 rounded-2xl overflow-hidden"
        style={{
          background: "linear-gradient(145deg, #1e2240, #141428)",
          boxShadow: "0 8px 40px rgba(0, 0, 0, 0.6), inset 0 1px 0 rgba(255,255,255,0.06)",
          animation: "dialog-scale-in 200ms ease-out",
        }}
      >
        {/* Red accent bar */}
        <div
          className="h-1"
          style={{
            background: "linear-gradient(90deg, #6a2d2d, #ff6b6b, #6a2d2d)",
          }}
        />

        <div className="p-8">
          <h2 className="text-2xl font-bold text-[#e8e8e8] mb-4">{title}</h2>
          <p className="text-[#a0a0b0] text-lg mb-8 whitespace-pre-line">{message}</p>
          <div className="flex gap-4">
            <TouchButton
              text="Cancel"
              style="secondary"
              onClick={onCancel}
              className="flex-1"
            />
            <TouchButton
              text={confirmText}
              style="danger"
              onClick={onConfirm}
              className="flex-1"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
