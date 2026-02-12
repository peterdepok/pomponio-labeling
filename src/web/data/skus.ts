/**
 * Pomponio Ranch beef SKU database.
 * 71 active beef SKUs from data/pomponio_skus.csv.
 */

export interface Product {
  id: number;
  sku: string;
  name: string;
  category: string;
  unit: string;
  active: boolean;
}

export const PRODUCTS: Product[] = [
  { id: 1, sku: "00100", name: "Ribeye Steak Bone-In 1.5in Thick", category: "Beef", unit: "lb", active: true },
  { id: 2, sku: "00101", name: "New York Steak Boneless 1.25in Thick", category: "Beef", unit: "lb", active: true },
  { id: 3, sku: "00103", name: "Filet Mignon 8oz", category: "Beef", unit: "lb", active: true },
  { id: 4, sku: "00104", name: "Beef Filet Tips", category: "Beef", unit: "lb", active: true },
  { id: 5, sku: "00105", name: "Top Sirloin Steak 1.25in Thick", category: "Beef", unit: "lb", active: true },
  { id: 6, sku: "00108", name: "Tri-Tip", category: "Beef", unit: "lb", active: true },
  { id: 7, sku: "00109", name: "Flank Steak", category: "Beef", unit: "lb", active: true },
  { id: 8, sku: "00110", name: "Outside Skirt Steak", category: "Beef", unit: "lb", active: true },
  { id: 9, sku: "00111", name: "Hanger Steak", category: "Beef", unit: "lb", active: true },
  { id: 10, sku: "00112", name: "Bavette Steaks (Flap)", category: "Beef", unit: "lb", active: true },
  { id: 11, sku: "00113", name: "Chuck Petite Filet Steak", category: "Beef", unit: "lb", active: true },
  { id: 12, sku: "00114", name: "Brisket Flat", category: "Beef", unit: "lb", active: true },
  { id: 13, sku: "00115", name: "Brisket Primal", category: "Beef", unit: "lb", active: true },
  { id: 14, sku: "00116", name: "Beef Tenderloin", category: "Beef", unit: "lb", active: true },
  { id: 15, sku: "00117", name: "English Short Ribs", category: "Beef", unit: "lb", active: true },
  { id: 16, sku: "00118", name: "Korean Style Short Ribs", category: "Beef", unit: "pack", active: true },
  { id: 17, sku: "00120", name: "Chuck Roast", category: "Beef", unit: "lb", active: true },
  { id: 18, sku: "00121", name: "Eye of Round Roast", category: "Beef", unit: "lb", active: true },
  { id: 19, sku: "00122", name: "Burger Patties 70/30", category: "Beef", unit: "pack", active: true },
  { id: 20, sku: "00123", name: "Ground Beef 70/30", category: "Beef", unit: "lb", active: true },
  { id: 21, sku: "00124", name: "Stew Meat", category: "Beef", unit: "lb", active: true },
  { id: 22, sku: "00125", name: "Flat Iron Steak", category: "Beef", unit: "lb", active: true },
  { id: 23, sku: "00126", name: "Brisket Point", category: "Beef", unit: "lb", active: true },
  { id: 24, sku: "00132", name: "Inside Skirt Steak", category: "Beef", unit: "lb", active: true },
  { id: 25, sku: "00140", name: "Beef Shank 2in", category: "Beef", unit: "lb", active: true },
  { id: 26, sku: "00141", name: "Marrow Bones", category: "Beef", unit: "lb", active: true },
  { id: 27, sku: "00142", name: "Beef Stock Bones", category: "Beef", unit: "lb", active: true },
  { id: 28, sku: "00143", name: "Beef Cheeks", category: "Beef", unit: "lb", active: true },
  { id: 29, sku: "00144", name: "Beef Sweet Breads", category: "Beef", unit: "lb", active: true },
  { id: 30, sku: "00145", name: "Oxtail", category: "Beef", unit: "lb", active: true },
  { id: 31, sku: "00146", name: "Whole Beef Tongue", category: "Beef", unit: "lb", active: true },
  { id: 32, sku: "00147", name: "Beef Liver", category: "Beef", unit: "lb", active: true },
  { id: 33, sku: "00148", name: "Heart", category: "Beef", unit: "lb", active: true },
  { id: 34, sku: "00149", name: "Beef Kidney", category: "Beef", unit: "lb", active: true },
  { id: 35, sku: "00154", name: "Prime Rib Roast 3 Bone", category: "Beef", unit: "lb", active: true },
  { id: 36, sku: "00155", name: "Prime Rib Roast 4 Bone", category: "Beef", unit: "lb", active: true },
  { id: 37, sku: "00156", name: "Prime Rib Roast 7 Bone", category: "Beef", unit: "lb", active: true },
  { id: 38, sku: "00160", name: "Carne Asada Seasoned", category: "Beef", unit: "pack", active: true },
  { id: 39, sku: "00161", name: "Denver Steak (Boneless Short Rib)", category: "Beef", unit: "lb", active: true },
  { id: 40, sku: "00162", name: "Arrachera (Flap)", category: "Beef", unit: "lb", active: true },
  { id: 41, sku: "00164", name: "Picanha Steak", category: "Beef", unit: "lb", active: true },
  { id: 42, sku: "00165", name: "Beef Kabob (Sirloin)", category: "Beef", unit: "lb", active: true },
  { id: 43, sku: "00166", name: "Tomahawk", category: "Beef", unit: "lb", active: true },
  { id: 44, sku: "00167", name: "Oyster Steak", category: "Beef", unit: "lb", active: true },
  { id: 45, sku: "00168", name: "Velvet Steak", category: "Beef", unit: "lb", active: true },
  { id: 46, sku: "00169", name: "Cross Rib Roast", category: "Beef", unit: "lb", active: true },
  { id: 47, sku: "00170", name: "Chuck Eye Steak", category: "Beef", unit: "lb", active: true },
  { id: 48, sku: "00171", name: "T-Bone Steak", category: "Beef", unit: "lb", active: true },
  { id: 49, sku: "00172", name: "Porterhouse", category: "Beef", unit: "lb", active: true },
  { id: 50, sku: "00173", name: "Sirloin Tip Roast", category: "Beef", unit: "lb", active: true },
  { id: 51, sku: "00174", name: "Teres Major", category: "Beef", unit: "lb", active: true },
  { id: 52, sku: "00180", name: "Dino Rib", category: "Beef", unit: "lb", active: true },
  { id: 53, sku: "00181", name: "Meat for Jerky", category: "Beef", unit: "lb", active: true },
  { id: 54, sku: "00182", name: "PCM-Beef Trim", category: "Beef", unit: "lb", active: true },
  { id: 55, sku: "00183", name: "Liver Primal", category: "Beef", unit: "lb", active: true },
  { id: 56, sku: "00184", name: "Sirloin Tip Steak", category: "Beef", unit: "lb", active: true },
  { id: 57, sku: "00185", name: "Brisket Burger Patties", category: "Beef", unit: "pack", active: true },
  { id: 58, sku: "00186", name: "Picanha Roast", category: "Beef", unit: "lb", active: true },
  { id: 59, sku: "00187", name: "Beef Tendon", category: "Beef", unit: "lb", active: true },
  { id: 60, sku: "00188", name: "Beef Chorizo Sausage", category: "Beef", unit: "pack", active: true },
  { id: 61, sku: "00190", name: "Beef Burger Patties Quarter Pound", category: "Beef", unit: "pack", active: true },
  { id: 62, sku: "00191", name: "Beef Stir Fry", category: "Beef", unit: "lb", active: true },
  { id: 63, sku: "00192", name: "Burger Patties Chuck and Brisket", category: "Beef", unit: "pack", active: true },
  { id: 64, sku: "00193", name: "Navel", category: "Beef", unit: "lb", active: true },
  { id: 65, sku: "00194", name: "Steak Bites", category: "Beef", unit: "lb", active: true },
  { id: 66, sku: "00195", name: "Beef Stock Bones Bulk", category: "Beef", unit: "lb", active: true },
  { id: 67, sku: "00196", name: "Fajita Seasoned", category: "Beef", unit: "lb", active: true },
  { id: 68, sku: "00197", name: "Beef Hot Dogs", category: "Beef", unit: "pack", active: true },
  { id: 69, sku: "00198", name: "Beef Bacon", category: "Beef", unit: "pack", active: true },
  { id: 70, sku: "00199", name: "Beef Bacon Ends", category: "Beef", unit: "pack", active: true },
  { id: 71, sku: "00176", name: "Beef Summer Sausage", category: "Beef", unit: "pack", active: true },
];

export function getProductBySku(sku: string): Product | undefined {
  return PRODUCTS.find(p => p.sku === sku);
}

export function getActiveProducts(): Product[] {
  return PRODUCTS.filter(p => p.active);
}
