/**
 * Barcode scanner gun SVG icon.
 * Used in ScannerScreen and AnimalsScreen scan prompts.
 * Simple monochrome silhouette with configurable size and color.
 */

interface ScanGunIconProps {
  /** Pixel dimension for the square viewBox (default 96). */
  size?: number;
  /** Fill color (default "#e8e8e8"). */
  color?: string;
}

export function ScanGunIcon({ size = 96, color = "#e8e8e8" }: ScanGunIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 96 96"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Scanner body (angled rectangle) */}
      <rect
        x="18"
        y="28"
        width="48"
        height="24"
        rx="4"
        fill={color}
        transform="rotate(-8 18 28)"
      />
      {/* Scanner nose / barrel */}
      <rect
        x="60"
        y="26"
        width="20"
        height="16"
        rx="3"
        fill={color}
        transform="rotate(-8 60 26)"
      />
      {/* Handle / grip */}
      <rect
        x="28"
        y="48"
        width="16"
        height="28"
        rx="4"
        fill={color}
        transform="rotate(8 28 48)"
      />
      {/* Trigger */}
      <rect
        x="44"
        y="50"
        width="10"
        height="6"
        rx="2"
        fill={color}
        opacity="0.7"
        transform="rotate(8 44 50)"
      />
      {/* Scan beam (dashed line emanating from barrel) */}
      <line
        x1="80"
        y1="30"
        x2="92"
        y2="28"
        stroke={color}
        strokeWidth="2"
        strokeDasharray="3 2"
        opacity="0.6"
      />
      <line
        x1="80"
        y1="34"
        x2="92"
        y2="34"
        stroke={color}
        strokeWidth="2"
        strokeDasharray="3 2"
        opacity="0.6"
      />
      <line
        x1="80"
        y1="38"
        x2="92"
        y2="40"
        stroke={color}
        strokeWidth="2"
        strokeDasharray="3 2"
        opacity="0.6"
      />
    </svg>
  );
}
