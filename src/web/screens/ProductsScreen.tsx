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
      </div>

      {/* Last used product: prominent repeat button */}
      {lastUsedProduct && !isSearch && (
        <div className="flex-shrink-0 px-5 pt-3">
          <button
            onClick={() => onSelectProduct(lastUsedProduct)}
            className="game-btn w-full rounded-xl px-5 py-3 select-none relative overflow-hidden flex items-center gap-4"
            style={{
              background: "linear-gradient(145deg, #1a2e1a, #142814)",
              border: "2px solid rgba(81, 207, 102, 0.35)",
              boxShadow: "0 4px 0 0 #0a1a0a, 0 5px 16px rgba(81, 207, 102, 0.12), inset 0 1px 0 rgba(255,255,255,0.06)",
            }}
          >
            <div className="game-gloss" />
            <div
              className="game-btn-ledge"
              style={{
                height: "4px",
                background: "#0a1a0a",
                borderRadius: "0 0 12px 12px",
              }}
            />
            <span
              className="relative z-10 select-none"
              style={{ fontSize: "28px", filter: "drop-shadow(0 0 6px rgba(81, 207, 102, 0.4))" }}
            >
              &#x21bb;
            </span>
            <div className="relative z-10 flex-1 text-left">
              <div className="text-xs uppercase tracking-[0.15em]" style={{ color: "#51cf66" }}>
                Last Used
              </div>
              <div className="text-lg font-bold text-[#e8e8e8] leading-tight">
                {lastUsedProduct.name}
              </div>
            </div>
            <div
              className="relative z-10 rounded-lg px-4 py-2 font-bold text-sm uppercase tracking-wide select-none"
              style={{
                background: "linear-gradient(180deg, #51cf66, #40a855)",
                color: "#0a1a0a",
                boxShadow: "0 2px 0 0 #2d8a3e, 0 3px 8px rgba(81, 207, 102, 0.3)",
              }}
            >
              Select Again
            </div>
          </button>
        </div>
      )}

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
                <div className="grid grid-cols-3 gap-4">
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
          <div className="grid grid-cols-3 gap-5">
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
