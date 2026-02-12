/**
 * Compact horizontal 6-step workflow progress bar for 1280x1024 kiosk.
 * Shows circles with connecting lines; only the active step has a text label.
 */

import { WorkflowState } from "../hooks/useWorkflow.ts";
import { WORKFLOW_STEPS } from "../data/theme.ts";

interface StatusIndicatorProps {
  state: WorkflowState;
}

export function StatusIndicator({ state }: StatusIndicatorProps) {
  const currentIdx = WORKFLOW_STEPS.findIndex(s => s.state === state);
  const activeStep = WORKFLOW_STEPS[currentIdx];

  return (
    <div className="flex items-center gap-0 px-4 py-2 rounded-lg card-elevated">
      {WORKFLOW_STEPS.map((step, idx) => {
        const isCompleted = idx < currentIdx;
        const isActive = idx === currentIdx;
        const isUpcoming = idx > currentIdx;

        const circleSize = isActive ? 28 : 24;
        const color = step.color;

        return (
          <div key={step.state} className="flex items-center flex-1 last:flex-none">
            <div className="flex items-center justify-center" style={{ minWidth: 36 }}>
              <div
                className={`rounded-full flex items-center justify-center font-bold text-xs ${
                  isActive ? "animate-[glow-pulse_2s_ease-in-out_infinite]" : ""
                }`}
                style={{
                  width: circleSize,
                  height: circleSize,
                  backgroundColor: isCompleted || isActive ? color : "transparent",
                  border: `2px solid ${isUpcoming ? "#2a2a4a" : color}`,
                  color: isCompleted || isActive ? "#0d0d1a" : "#606080",
                  "--glow-color": color,
                  boxShadow: isActive ? `0 0 12px ${color}40` : undefined,
                } as React.CSSProperties}
              >
                {isCompleted ? "\u2713" : idx + 1}
              </div>
            </div>

            {/* Connecting line (not after last step) */}
            {idx < WORKFLOW_STEPS.length - 1 && (
              <div
                className="flex-1 h-[2px] mx-1"
                style={{
                  backgroundColor: isCompleted ? color : "#2a2a4a",
                }}
              />
            )}
          </div>
        );
      })}

      {/* Active step label */}
      {activeStep && (
        <div
          className="ml-4 pl-4 border-l border-[#2a2a4a] text-sm font-semibold whitespace-nowrap"
          style={{ color: activeStep.color }}
        >
          {activeStep.label}
        </div>
      )}
    </div>
  );
}
