/**
 * Theme constants for the Pomponio Ranch Labeling System.
 */

// Surface elevation system (darkest to lightest)
export const SURFACE = {
  0: "#0d0d1a",
  1: "#141428",
  2: "#1a1a2e",
  3: "#1e2240",
  4: "#252a4a",
} as const;

// Color palette
export const BG_PRIMARY = "#1a1a2e";
export const BG_SECONDARY = "#16213e";
export const BG_TERTIARY = "#0f3460";
export const BG_INPUT = "#202040";

export const TEXT_PRIMARY = "#e8e8e8";
export const TEXT_SECONDARY = "#a0a0b0";
export const TEXT_ACCENT = "#00d4ff";
export const TEXT_WARNING = "#ff6b6b";
export const TEXT_SUCCESS = "#51cf66";

export const BORDER_DEFAULT = "#2a2a4a";
export const BORDER_ACTIVE = "#00d4ff";

// Button colors
export const BTN_PRIMARY_BG = "#0f3460";
export const BTN_PRIMARY_HOVER = "#1a4a7a";
export const BTN_PRIMARY_TEXT = "#ffffff";

export const BTN_SUCCESS_BG = "#2d6a2d";
export const BTN_SUCCESS_HOVER = "#3d8a3d";
export const BTN_SUCCESS_TEXT = "#ffffff";

export const BTN_DANGER_BG = "#6a2d2d";
export const BTN_DANGER_HOVER = "#8a3d3d";
export const BTN_DANGER_TEXT = "#ffffff";

export const BTN_SECONDARY_BG = "#2a2a4a";
export const BTN_SECONDARY_HOVER = "#3a3a5a";
export const BTN_SECONDARY_TEXT = "#e8e8e8";

// Category colors for product grid
// fill/shadow are saturated game-button colors; bg/hover are dark card tints
export const CATEGORY_COLORS: Record<string, {
  bg: string; hover: string; accent: string;
  fill: string; fillLight: string; shadow: string;
}> = {
  "Steaks":            { bg: "#4a1a1a", hover: "#6a2a2a", accent: "#ff6b6b", fill: "#c0392b", fillLight: "#e74c3c", shadow: "#922b21" },
  "Roasts":            { bg: "#3a2a1a", hover: "#5a3a2a", accent: "#e8a850", fill: "#d68910", fillLight: "#f0b429", shadow: "#9a6700" },
  "Ground":            { bg: "#2a2a2a", hover: "#3a3a3a", accent: "#a0a0a0", fill: "#566573", fillLight: "#7f8c8d", shadow: "#2c3e50" },
  "Offal/Specialty":   { bg: "#1a2a3a", hover: "#2a3a4a", accent: "#6bb5ff", fill: "#2e86c1", fillLight: "#5dade2", shadow: "#1a5276" },
  "Bones":             { bg: "#2a2a1a", hover: "#3a3a2a", accent: "#d4c090", fill: "#b7950b", fillLight: "#d4ac0d", shadow: "#7d6608" },
  "Sausage/Processed": { bg: "#2a1a2a", hover: "#3a2a3a", accent: "#c090d4", fill: "#8e44ad", fillLight: "#af7ac5", shadow: "#6c3483" },
};

// Workflow state colors
export const STATE_COLORS: Record<string, string> = {
  idle: TEXT_SECONDARY,
  product_selected: "#00d4ff",
  weight_captured: "#ffa500",
  label_printed: "#51cf66",
};

// Workflow steps for progress bar (streamlined auto-flow)
export const WORKFLOW_STEPS: Array<{
  state: string;
  label: string;
  shortLabel: string;
  color: string;
  bgTint: string;
}> = [
  { state: "idle", label: "Select Product", shortLabel: "Product", color: "#a0a0b0", bgTint: "#a0a0b020" },
  { state: "product_selected", label: "Weighing", shortLabel: "Weigh", color: "#00d4ff", bgTint: "#00d4ff20" },
  { state: "weight_captured", label: "Printing", shortLabel: "Print", color: "#ffa500", bgTint: "#ffa50020" },
  { state: "label_printed", label: "Done", shortLabel: "Done", color: "#51cf66", bgTint: "#51cf6620" },
];

// Category display order
export const CATEGORY_ORDER = [
  "Steaks",
  "Roasts",
  "Ground",
  "Offal/Specialty",
  "Bones",
  "Sausage/Processed",
] as const;
