/**
 * Animated "printer with wings" overlay.
 * Plays during the WEIGHT_CAPTURED -> LABEL_PRINTED transition.
 * Pure CSS animation, no external libraries.
 */

interface PrintAnimationProps {
  visible: boolean;
}

export function PrintAnimation({ visible }: PrintAnimationProps) {
  if (!visible) return null;

  return (
    <div
      className="absolute inset-0 flex items-center justify-center pointer-events-none"
      style={{ zIndex: 40 }}
    >
      <div
        style={{
          animation: "anim-printer-fly 1.2s ease-out forwards",
        }}
      >
        {/* Wing container with printer icon */}
        <div className="relative flex items-center justify-center">
          {/* Left wing */}
          <span
            className="text-4xl select-none"
            style={{
              animation: "anim-wing-flap 0.3s ease-in-out infinite",
              transformOrigin: "right center",
              display: "inline-block",
              marginRight: "-4px",
              opacity: 0.7,
            }}
          >
            {"\uD83E\uDEB6"}
          </span>

          {/* Printer body */}
          <span
            className="text-6xl select-none"
            style={{
              filter: "drop-shadow(0 0 12px rgba(0, 212, 255, 0.5))",
            }}
          >
            {"\uD83D\uDDA8\uFE0F"}
          </span>

          {/* Right wing */}
          <span
            className="text-4xl select-none"
            style={{
              animation: "anim-wing-flap 0.3s ease-in-out infinite",
              animationDelay: "0.15s",
              transformOrigin: "left center",
              display: "inline-block",
              marginLeft: "-4px",
              opacity: 0.7,
              transform: "scaleX(-1)",
            }}
          >
            {"\uD83E\uDEB6"}
          </span>
        </div>
      </div>
    </div>
  );
}
