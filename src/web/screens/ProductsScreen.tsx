/**
 * Product grid with game-style 3D category tab pills, 3-column layout,
 * and a Search tab with on-screen QWERTY keyboard for kiosk use.
 */

import { useState, useMemo, useCallback } from "react";
import { getActiveProducts } from "../data/skus.ts";
import type { Product } from "../data/skus.ts";
import { classifyProduct } from "../data/classify.ts";
import type { ProductCategory } from "../data/classify.ts";
import { CATEGORY_ORDER, CATEGORY_COLORS } from "../data/theme.ts";
import { ProductButton } from "../components/ProductButton.tsx";
import { OnScreenKeyboard } from "../components/OnScreenKeyboard.tsx";

interface ProductsScreenProps {
  onSelectProduct: (product: Product) => void;
  activeCategory: string;
  onCategoryChange: (cat: string) => void;
  lastUsedProduct: Product | null;
}

type ActiveTab = ProductCategory | "Search";

export function ProductsScreen({
  onSelectProduct,
  activeCategory,
  onCategoryChange,
  lastUsedProduct,
}: ProductsScreenProps) {
  const [searchQuery, setSearchQuery] = useState("");

  const allProducts = useMemo(() => getActiveProducts(), []);

  const categorized = useMemo(() => {
    const grouped: Record<ProductCategory, Product[]> = {
      "Steaks": [],
      "Roasts": [],
      "Ground": [],
      "Offal/Specialty": [],
      "Bones": [],
      "Sausage/Processed": [],
    };
    for (const p of allProducts) {
      const cat = classifyProduct(p.sku, p.name);
      grouped[cat].push(p);
    }
    return grouped;
  }, [allProducts]);

  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase();
    return allProducts.filter(p => p.name.toLowerCase().includes(q));
  }, [allProducts, searchQuery]);

  const handleTabChange = useCallback((tab: ActiveTab) => {
    onCategoryChange(tab);
    if (tab !== "Search") {
      setSearchQuery("");
    }
  }, [onCategoryChange]);

  const handleKey = useCallback((char: string) => {
    setSearchQuery(prev => prev + char);
  }, []);

  const handleBackspace = useCallback(() => {
    setSearchQuery(prev => prev.slice(0, -1));
  }, []);

  const handleClear = useCallback(() => {
    setSearchQuery("");
  }, []);

  const isSearch = activeCategory === "Search";
  const currentProducts = isSearch ? [] : (categorized[activeCategory as ProductCategory] ?? []);

  return (
    <div className="flex flex-col h-full">
      {/* Category tabs: game-style 3D pill buttons */}
      <div className="flex gap-2 p-3 flex-shrink-0 overflow-x-auto" style={{ background: "#0a0a16" }}>
        {CATEGORY_ORDER.map(cat => {
          const colors = CATEGORY_COLORS[cat];
          const count = categorized[cat]?.length ?? 0;
          const isActive = cat === activeCategory;
          return (
            <button
              key={cat}
              onClick={() => handleTabChange(cat)}
              className="game-btn min-h-[48px] px-5 rounded-xl font-bold whitespace-nowrap select-none flex items-center gap-2 relative overflow-hidden"
              style={{
                background: isActive
                  ? `linear-gradient(180deg, ${colors.fillLight}, ${colors.fill})`
                  : "linear-gradient(180deg, #2a2a4a, #1e2240)",
                boxShadow: isActive
                  ? `0 4px 0 0 ${colors.shadow}, 0 5px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.2)`
                  : "0 3px 0 0 #141428, 0 4px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06)",
                color: isActive ? "#ffffff" : "#808090",
                fontSize: "14px",
                textShadow: isActive ? "0 1px 3px rgba(0,0,0,0.4)" : "none",
              }}
            >
              {isActive && <div className="game-gloss" />}
              <div
                className="game-btn-ledge"
                style={{
                  height: isActive ? "4px" : "3px",
                  background: isActive ? colors.shadow : "#141428",
                  borderRadius: "0 0 12px 12px",
                }}
              />
              <span className="relative z-10">{cat}</span>
              <span
                className="relative z-10 text-xs font-mono rounded-full px-1.5 py-0.5"
                style={{
                  background: isActive ? "rgba(255,255,255,0.2)" : "rgba(255,255,255,0.06)",
                  color: isActive ? "#ffffff" : "#606080",
                  fontSize: "11px",
                }}
              >
                {count}
              </span>
            </button>
          );
        })}

        {/* Search tab */}
        <button
          onClick={() => handleTabChange("Search")}
          className="game-btn min-h-[48px] px-5 rounded-xl font-bold whitespace-nowrap select-none flex items-center gap-2 relative overflow-hidden"
          style={{
            background: isSearch
              ? "linear-gradient(180deg, #e0e0e0, #b0b0b0)"
              : "linear-gradient(180deg, #2a2a4a, #1e2240)",
            boxShadow: isSearch
              ? "0 4px 0 0 #808080, 0 5px 12px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.4)"
              : "0 3px 0 0 #141428, 0 4px 8px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.06)",
            color: isSearch ? "#1a1a2e" : "#808090",
            fontSize: "14px",
          }}
        >
          {isSearch && <div className="game-gloss" />}
          <div
            className="game-btn-ledge"
            style={{
              height: isSearch ? "4px" : "3px",
              background: isSearch ? "#808080" : "#141428",
              borderRadius: "0 0 12px 12px",
            }}
          />
          <span className="relative z-10">Search</span>
        </button>

        {/* Last used: dominant repeat button, sized to match product grid buttons */}
        {lastUsedProduct && (
          <button
            onClick={() => onSelectProduct(lastUsedProduct)}
            className="game-btn ml-auto h-[96px] min-w-[280px] px-8 rounded-2xl font-extrabold select-none flex items-center gap-4 relative overflow-hidden"
            style={{
              background: "linear-gradient(180deg, #43a047, #2e7d32)",
              boxShadow: "0 6px 0 0 #1a3a1a, 0 8px 20px rgba(81, 207, 102, 0.3), inset 0 2px 0 rgba(255,255,255,0.25), inset 0 -2px 4px rgba(0,0,0,0.15)",
              border: "2px solid rgba(81, 207, 102, 0.5)",
              color: "#ffffff",
              textShadow: "0 2px 4px rgba(0,0,0,0.4), 0 0 12px rgba(26, 58, 26, 0.8)",
              borderRadius: "16px",
            }}
          >
            <div className="game-gloss" />
            <div
              className="absolute inset-0 pointer-events-none rounded-2xl"
              style={{ boxShadow: "inset 0 0 20px rgba(255,255,255,0.08)" }}
            />
            <div
              className="game-btn-ledge"
              style={{
                height: "6px",
                background: "#1a3a1a",
                borderRadius: "0 0 16px 16px",
              }}
            />
            <span className="relative z-10" style={{ fontSize: "32px" }}>&#x21bb;</span>
            <div className="relative z-10 flex flex-col items-start">
              <span className="text-xs uppercase tracking-widest" style={{ color: "rgba(255,255,255,0.6)", fontSize: "10px" }}>Last Used</span>
              <span className="truncate max-w-[200px]" style={{ fontSize: "clamp(18px, 1.9vw, 24px)" }}>{lastUsedProduct.name}</span>
            </div>
          </button>
        )}
      </div>

      {/* Content: either category grid or search interface */}
      {isSearch ? (
        <div className="flex-1 flex flex-col min-h-0 p-4 gap-3">
          {/* Search input display */}
          <div
            className="flex items-center h-[56px] px-5 rounded-xl flex-shrink-0"
            style={{
              background: "#080e1a",
              boxShadow: "inset 0 2px 6px rgba(0,0,0,0.6), 0 1px 0 rgba(255,255,255,0.05)",
            }}
          >
            <span
              className="text-xl font-bold tracking-wide flex-1"
              style={{ color: searchQuery ? "#e8e8e8" : "#404060" }}
            >
              {searchQuery || "Type to search..."}
            </span>
            {searchQuery && (
              <span className="text-sm font-mono" style={{ color: "#606080" }}>
                {searchResults.length} result{searchResults.length !== 1 ? "s" : ""}
              </span>
            )}
          </div>

          {/* Results grid (scrollable) */}
          {searchQuery.trim() && (
            <div className="flex-1 overflow-y-auto min-h-0">
              {searchResults.length > 0 ? (
                <div className="grid grid-cols-4 gap-4">
                  {searchResults.map(product => {
                    const cat = classifyProduct(product.sku, product.name);
                    return (
                      <ProductButton
                        key={product.sku}
                        name={product.name}
                        sku={product.sku}
                        category={cat}
                        onClick={() => onSelectProduct(product)}
                      />
                    );
                  })}
                </div>
              ) : (
                <div className="text-center text-[#606080] py-8 text-lg">
                  No products match "{searchQuery}"
                </div>
              )}
            </div>
          )}

          {/* On-screen keyboard (pinned to bottom) */}
          <div className="flex-shrink-0 mt-auto">
            <OnScreenKeyboard
              onKey={handleKey}
              onBackspace={handleBackspace}
              onClear={handleClear}
            />
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-5">
          <div className="grid grid-cols-4 gap-5">
            {currentProducts.map(product => (
              <ProductButton
                key={product.sku}
                name={product.name}
                sku={product.sku}
                category={activeCategory as ProductCategory}
                onClick={() => onSelectProduct(product)}
              />
            ))}
          </div>
          {currentProducts.length === 0 && (
            <div className="text-center text-[#606080] py-12 text-lg">
              No products in this category.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
