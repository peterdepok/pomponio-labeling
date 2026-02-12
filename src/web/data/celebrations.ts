/**
 * Celebration and encouragement content for gamified UI.
 * Pure data module, no React dependencies.
 * Extend by adding strings to any array.
 */

/** Shown during LABEL_PRINTED state, randomized per label. */
export const PRINT_CELEBRATIONS: string[] = [
  "Crushed it.",
  "Clean weight, clean label.",
  "Another one in the box.",
  "Machine mode.",
  "That label hit different.",
  "Locked and loaded.",
  "Nailed it.",
  "Smooth operator.",
  "Precision work.",
  "On a roll.",
  "Like clockwork.",
  "Chef's kiss.",
  "Dialed in perfectly.",
  "Money label.",
  "Textbook execution.",
];

/** Shown in speed popup when operator exceeds threshold PPM. */
export const SPEED_ENCOURAGEMENTS: string[] = [
  "You're on fire.",
  "Fast hands, clean labels.",
  "No wasted motion.",
  "Dialed in.",
  "Production beast.",
  "Speed demon.",
  "Unstoppable pace.",
  "Flying through it.",
  "Setting records.",
  "Keep that energy.",
  "Absolute unit.",
  "In the zone.",
];

/** Unicode icons paired with celebration and speed messages. */
export const CELEBRATION_ICONS: string[] = [
  "\u2714",   // heavy check mark
  "\uD83D\uDD25", // fire
  "\u26A1",   // lightning
  "\u2B50",   // star
  "\uD83D\uDC51", // crown
  "\uD83D\uDE80", // rocket
  "\uD83C\uDFC6", // trophy
  "\uD83C\uDFAF", // target
  "\uD83D\uDCAA", // muscle
  "\u2728",   // sparkles
];
