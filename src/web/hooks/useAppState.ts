/**
 * Top-level application state: animals, boxes, packages.
 * Persisted to localStorage under pomponio_ prefix.
 * Hydrates on first mount; writes reactively via useEffect.
 */

import { useState, useCallback, useEffect, useRef } from "react";

export interface Animal {
  id: number;
  name: string;
  startedAt: string;
  closedAt: string | null;
}

export interface Box {
  id: number;
  animalId: number;
  boxNumber: number;
  closed: boolean;
}

export interface Package {
  id: number;
  productId: number;
  productName: string;
  sku: string;
  animalId: number;
  boxId: number;
  weightLb: number;
  barcode: string;
  verified: boolean;
  voided?: boolean;
  voidedAt?: string;
  voidReason?: string;
}

let nextAnimalId = 1;
let nextBoxId = 1;
let nextPackageId = 1;

// --- localStorage persistence ---

const STORAGE_KEYS = {
  animals: "pomponio_animals",
  boxes: "pomponio_boxes",
  packages: "pomponio_packages",
  currentAnimalId: "pomponio_currentAnimalId",
  currentBoxId: "pomponio_currentBoxId",
} as const;

interface HydratedState {
  animals: Animal[];
  boxes: Box[];
  packages: Package[];
  currentAnimalId: number | null;
  currentBoxId: number | null;
}

function hydrateState(): HydratedState {
  try {
    const animals: Animal[] = JSON.parse(localStorage.getItem(STORAGE_KEYS.animals) || "[]");
    const boxes: Box[] = JSON.parse(localStorage.getItem(STORAGE_KEYS.boxes) || "[]");
    const packages: Package[] = JSON.parse(localStorage.getItem(STORAGE_KEYS.packages) || "[]");
    const rawAnimalId = localStorage.getItem(STORAGE_KEYS.currentAnimalId);
    const rawBoxId = localStorage.getItem(STORAGE_KEYS.currentBoxId);
    const currentAnimalId = rawAnimalId !== null ? Number(rawAnimalId) : null;
    const currentBoxId = rawBoxId !== null ? Number(rawBoxId) : null;

    // Initialize ID counters past any existing IDs to prevent collisions
    nextAnimalId = animals.length > 0 ? Math.max(...animals.map(a => a.id)) + 1 : 1;
    nextBoxId = boxes.length > 0 ? Math.max(...boxes.map(b => b.id)) + 1 : 1;
    nextPackageId = packages.length > 0 ? Math.max(...packages.map(p => p.id)) + 1 : 1;

    return { animals, boxes, packages, currentAnimalId, currentBoxId };
  } catch {
    return { animals: [], boxes: [], packages: [], currentAnimalId: null, currentBoxId: null };
  }
}

export function useAppState() {
  // Hydrate once on first render
  const hydratedRef = useRef<HydratedState | null>(null);
  if (hydratedRef.current === null) {
    hydratedRef.current = hydrateState();
  }
  const hydrated = hydratedRef.current;

  const [animals, setAnimals] = useState<Animal[]>(hydrated.animals);
  const [boxes, setBoxes] = useState<Box[]>(hydrated.boxes);
  const [packages, setPackages] = useState<Package[]>(hydrated.packages);
  const [currentAnimalId, setCurrentAnimalId] = useState<number | null>(hydrated.currentAnimalId);
  const [currentBoxId, setCurrentBoxId] = useState<number | null>(hydrated.currentBoxId);
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  // Storage health: set to true if any localStorage write fails (quota exceeded).
  // Exposed to the UI so a persistent warning banner can be displayed.
  const [storageWarning, setStorageWarning] = useState(false);

  // One-time restore from disk backup: if localStorage was empty on mount
  // (no animals), attempt to recover from the Flask backup endpoint.
  const restoredRef = useRef(false);
  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;

    // Only attempt restore if localStorage was empty
    if (hydrated.animals.length > 0) return;

    (async () => {
      try {
        const res = await fetch("/api/backup/restore");
        if (!res.ok) return;
        const json = await res.json();
        if (!json.ok || !json.data) return;

        const data = json.data;
        const restoredAnimals: Animal[] = data.animals ?? [];
        const restoredBoxes: Box[] = data.boxes ?? [];
        const restoredPackages: Package[] = data.packages ?? [];

        if (restoredAnimals.length === 0) return;

        // Restore ID counters past any existing IDs
        nextAnimalId = restoredAnimals.length > 0 ? Math.max(...restoredAnimals.map((a: Animal) => a.id)) + 1 : 1;
        nextBoxId = restoredBoxes.length > 0 ? Math.max(...restoredBoxes.map((b: Box) => b.id)) + 1 : 1;
        nextPackageId = restoredPackages.length > 0 ? Math.max(...restoredPackages.map((p: Package) => p.id)) + 1 : 1;

        setAnimals(restoredAnimals);
        setBoxes(restoredBoxes);
        setPackages(restoredPackages);
        setCurrentAnimalId(data.currentAnimalId ?? null);
        setCurrentBoxId(data.currentBoxId ?? null);

        // Show restoration toast (setToast is already defined in scope)
        setToast({ msg: `Restored from backup: ${restoredAnimals.length} animals, ${restoredPackages.length} packages`, type: "success" });
        setTimeout(() => setToast(null), 5000);

        console.log("[Backup] Restored from disk backup:", {
          animals: restoredAnimals.length,
          boxes: restoredBoxes.length,
          packages: restoredPackages.length,
        });
      } catch {
        // Restore is best-effort; if Flask is not running, silently skip
      }
    })();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // --- Persist state to localStorage on every change ---
  // Wrapped in try/catch to survive quota exceeded errors on kiosk browsers.

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.animals, JSON.stringify(animals));
      if (storageWarning) setStorageWarning(false);
    } catch {
      console.warn("localStorage write failed for animals");
      setStorageWarning(true);
    }
  }, [animals]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.boxes, JSON.stringify(boxes));
    } catch {
      console.warn("localStorage write failed for boxes");
      setStorageWarning(true);
    }
  }, [boxes]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEYS.packages, JSON.stringify(packages));
    } catch {
      console.warn("localStorage write failed for packages");
      setStorageWarning(true);
    }
  }, [packages]);

  useEffect(() => {
    try {
      if (currentAnimalId !== null) {
        localStorage.setItem(STORAGE_KEYS.currentAnimalId, String(currentAnimalId));
      } else {
        localStorage.removeItem(STORAGE_KEYS.currentAnimalId);
      }
    } catch {
      console.warn("localStorage write failed for currentAnimalId");
      setStorageWarning(true);
    }
  }, [currentAnimalId]);

  useEffect(() => {
    try {
      if (currentBoxId !== null) {
        localStorage.setItem(STORAGE_KEYS.currentBoxId, String(currentBoxId));
      } else {
        localStorage.removeItem(STORAGE_KEYS.currentBoxId);
      }
    } catch {
      console.warn("localStorage write failed for currentBoxId");
      setStorageWarning(true);
    }
  }, [currentBoxId]);

  const toastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((msg: string, type: "success" | "error" = "success") => {
    // Clear any pending toast dismissal to prevent stale timeouts
    if (toastTimerRef.current !== null) {
      clearTimeout(toastTimerRef.current);
    }
    setToast({ msg, type });
    const duration = type === "error" ? 6000 : 3000;
    toastTimerRef.current = setTimeout(() => {
      setToast(null);
      toastTimerRef.current = null;
    }, duration);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (toastTimerRef.current !== null) {
        clearTimeout(toastTimerRef.current);
      }
    };
  }, []);

  const createAnimal = useCallback((name: string): number => {
    const id = nextAnimalId++;
    const animal: Animal = {
      id,
      name,
      startedAt: new Date().toLocaleString(),
      closedAt: null,
    };
    setAnimals(prev => [...prev, animal]);
    return id;
  }, []);

  const closeAnimal = useCallback((animalId: number) => {
    setAnimals(prev =>
      prev.map(a =>
        a.id === animalId ? { ...a, closedAt: new Date().toLocaleString() } : a
      )
    );
    if (currentAnimalId === animalId) {
      setCurrentAnimalId(null);
      setCurrentBoxId(null);
    }
  }, [currentAnimalId]);

  const getOpenAnimals = useCallback((): Animal[] => {
    return animals.filter(a => a.closedAt === null);
  }, [animals]);

  // Track the created box ID via ref so we can return it synchronously
  const createdBoxIdRef = useRef<number>(0);

  const createBox = useCallback((animalId: number): number => {
    const id = nextBoxId++;
    createdBoxIdRef.current = id;
    setBoxes(prev => {
      const existingBoxes = prev.filter(b => b.animalId === animalId);
      return [...prev, {
        id,
        animalId,
        boxNumber: existingBoxes.length + 1,
        closed: false,
      }];
    });
    return id;
  }, []);

  const closeBox = useCallback((boxId: number) => {
    setBoxes(prev =>
      prev.map(b => (b.id === boxId ? { ...b, closed: true } : b))
    );
    // Prune voided packages from the closed box. Once a box is closed,
    // voided entries serve no UI purpose and would otherwise accumulate
    // in state indefinitely, degrading performance over long sessions.
    setPackages(prev =>
      prev.filter(p => !(p.boxId === boxId && p.voided))
    );
  }, []);

  const reopenBox = useCallback((boxId: number) => {
    setBoxes(prev =>
      prev.map(b => (b.id === boxId ? { ...b, closed: false } : b))
    );
  }, []);

  const getOpenBoxes = useCallback((animalId: number): Box[] => {
    return boxes.filter(b => b.animalId === animalId && !b.closed);
  }, [boxes]);

  const getBoxesForAnimal = useCallback((animalId: number): Box[] => {
    return boxes.filter(b => b.animalId === animalId);
  }, [boxes]);

  const createPackage = useCallback((pkg: Omit<Package, "id" | "verified" | "voided" | "voidedAt" | "voidReason">): number => {
    const id = nextPackageId++;
    setPackages(prev => [...prev, { ...pkg, id, verified: true }]);
    return id;
  }, []);

  const voidPackage = useCallback((packageId: number, reason: string) => {
    setPackages(prev =>
      prev.map(p =>
        p.id === packageId
          ? { ...p, voided: true, voidedAt: new Date().toISOString(), voidReason: reason }
          : p
      )
    );
  }, []);

  const getPackagesForAnimal = useCallback((animalId: number): Package[] => {
    return packages.filter(p => p.animalId === animalId && !p.voided);
  }, [packages]);

  const getPackagesForBox = useCallback((boxId: number): Package[] => {
    return packages.filter(p => p.boxId === boxId && !p.voided);
  }, [packages]);

  const getAllPackagesForBox = useCallback((boxId: number): Package[] => {
    return packages.filter(p => p.boxId === boxId);
  }, [packages]);

  const getManifestData = useCallback((animalId: number) => {
    const animalPackages = packages.filter(p => p.animalId === animalId && !p.voided);
    const grouped: Record<string, { sku: string; productName: string; quantity: number; weights: number[]; totalWeight: number }> = {};

    for (const pkg of animalPackages) {
      if (!grouped[pkg.sku]) {
        grouped[pkg.sku] = {
          sku: pkg.sku,
          productName: pkg.productName,
          quantity: 0,
          weights: [],
          totalWeight: 0,
        };
      }
      grouped[pkg.sku].quantity += 1;
      grouped[pkg.sku].weights.push(pkg.weightLb);
      grouped[pkg.sku].totalWeight += pkg.weightLb;
    }

    return Object.values(grouped);
  }, [packages]);

  const selectAnimal = useCallback((animalId: number | null) => {
    setCurrentAnimalId(animalId);
    if (animalId !== null) {
      // Use functional update to read the latest boxes state,
      // avoiding stale closure over the `boxes` array.
      setBoxes(prevBoxes => {
        const openBoxes = prevBoxes.filter(b => b.animalId === animalId && !b.closed);
        if (openBoxes.length === 0) {
          const newBoxId = nextBoxId++;
          const existingBoxes = prevBoxes.filter(b => b.animalId === animalId);
          setCurrentBoxId(newBoxId);
          return [...prevBoxes, {
            id: newBoxId,
            animalId,
            boxNumber: existingBoxes.length + 1,
            closed: false,
          }];
        } else {
          setCurrentBoxId(openBoxes[0].id);
          return prevBoxes; // no mutation
        }
      });
    } else {
      setCurrentBoxId(null);
    }
  }, []);

  /** Remove a closed animal and its boxes/packages from state and localStorage.
   *  Call after the animal's manifest CSV has been saved to disk. */
  const purgeAnimal = useCallback((animalId: number) => {
    setAnimals(prev => prev.filter(a => a.id !== animalId));
    setBoxes(prev => prev.filter(b => b.animalId !== animalId));
    setPackages(prev => prev.filter(p => p.animalId !== animalId));
    if (currentAnimalId === animalId) {
      setCurrentAnimalId(null);
      setCurrentBoxId(null);
    }
  }, [currentAnimalId]);

  const clearAllData = useCallback(() => {
    setAnimals([]);
    setBoxes([]);
    setPackages([]);
    setCurrentAnimalId(null);
    setCurrentBoxId(null);
    // Clear persisted state
    Object.values(STORAGE_KEYS).forEach(key => localStorage.removeItem(key));
    // Reset counters
    nextAnimalId = 1;
    nextBoxId = 1;
    nextPackageId = 1;
  }, []);

  return {
    animals,
    boxes,
    packages,
    currentAnimalId,
    currentBoxId,
    toast,
    showToast,
    storageWarning,
    createAnimal,
    closeAnimal,
    getOpenAnimals,
    createBox,
    closeBox,
    reopenBox,
    getOpenBoxes,
    getBoxesForAnimal,
    createPackage,
    getPackagesForAnimal,
    getPackagesForBox,
    getAllPackagesForBox,
    getManifestData,
    voidPackage,
    selectAnimal,
    setCurrentBoxId,
    purgeAnimal,
    clearAllData,
  };
}
