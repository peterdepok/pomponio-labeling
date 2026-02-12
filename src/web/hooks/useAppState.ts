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
  const [toast, setToast] = useState<string | null>(null);

  // --- Persist state to localStorage on every change ---

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.animals, JSON.stringify(animals));
  }, [animals]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.boxes, JSON.stringify(boxes));
  }, [boxes]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.packages, JSON.stringify(packages));
  }, [packages]);

  useEffect(() => {
    if (currentAnimalId !== null) {
      localStorage.setItem(STORAGE_KEYS.currentAnimalId, String(currentAnimalId));
    } else {
      localStorage.removeItem(STORAGE_KEYS.currentAnimalId);
    }
  }, [currentAnimalId]);

  useEffect(() => {
    if (currentBoxId !== null) {
      localStorage.setItem(STORAGE_KEYS.currentBoxId, String(currentBoxId));
    } else {
      localStorage.removeItem(STORAGE_KEYS.currentBoxId);
    }
  }, [currentBoxId]);

  const showToast = useCallback((msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3000);
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

  const createBox = useCallback((animalId: number): number => {
    const existingBoxes = boxes.filter(b => b.animalId === animalId);
    const id = nextBoxId++;
    const box: Box = {
      id,
      animalId,
      boxNumber: existingBoxes.length + 1,
      closed: false,
    };
    setBoxes(prev => [...prev, box]);
    return id;
  }, [boxes]);

  const closeBox = useCallback((boxId: number) => {
    setBoxes(prev =>
      prev.map(b => (b.id === boxId ? { ...b, closed: true } : b))
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
      const openBoxes = boxes.filter(b => b.animalId === animalId && !b.closed);
      if (openBoxes.length === 0) {
        const newBoxId = nextBoxId++;
        const existingBoxes = boxes.filter(b => b.animalId === animalId);
        setBoxes(prev => [...prev, {
          id: newBoxId,
          animalId,
          boxNumber: existingBoxes.length + 1,
          closed: false,
        }]);
        setCurrentBoxId(newBoxId);
      } else {
        setCurrentBoxId(openBoxes[0].id);
      }
    } else {
      setCurrentBoxId(null);
    }
  }, [boxes]);

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
    clearAllData,
  };
}
