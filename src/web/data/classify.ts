/**
 * Product classification matching Python src/ui/theme.py classify_product().
 * Maps products into 6 UI categories: Steaks, Roasts, Ground, Offal/Specialty, Bones, Sausage/Processed.
 */

export type ProductCategory =
  | "Steaks"
  | "Roasts"
  | "Ground"
  | "Offal/Specialty"
  | "Bones"
  | "Sausage/Processed";

export function classifyProduct(_sku: string, name: string): ProductCategory {
  const lower = name.toLowerCase();

  // Bones
  if (["bone", "marrow", "stock bone"].some(k => lower.includes(k))) {
    if (!lower.includes("steak") && !lower.includes("short rib") && !lower.includes("prime rib")) {
      return "Bones";
    }
  }

  // Ground and burger
  if (["ground", "burger", "patties", "patty"].some(k => lower.includes(k))) {
    return "Ground";
  }

  // Sausage and processed
  if (["sausage", "chorizo", "hot dog", "bacon", "jerky", "summer", "trim"].some(k => lower.includes(k))) {
    return "Sausage/Processed";
  }

  // Offal and specialty
  if (["liver", "heart", "kidney", "tongue", "cheek", "oxtail", "sweet bread", "tendon", "navel", "fat"].some(k => lower.includes(k))) {
    return "Offal/Specialty";
  }

  // Roasts
  if (["roast", "brisket", "prime rib", "tri-tip", "picanha roast"].some(k => lower.includes(k))) {
    return "Roasts";
  }

  // Everything else is a steak
  return "Steaks";
}
