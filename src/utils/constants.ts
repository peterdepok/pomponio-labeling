import type { UnitEconomicsInputs, ScenarioConfig, Milestone, WholesaleState } from '../types';

export const DEFAULT_UNIT_ECONOMICS: UnitEconomicsInputs = {
  boxPrice: 150,
  cogs: 65,
  shippingCost: 45,
  fulfillmentLabor: 12,
  cac: 100,
  monthlyChurn: 0.08,
  addOnRate: 0.20,
  addOnMargin: 0.60,
};

export const SCENARIO_CONFIGS: Record<string, ScenarioConfig> = {
  conservative: {
    monthlyCreativeSpend: 2000,
    monthlyAdSpend: 1500,
    effectiveCac: 150,
    week1to4Subs: 3,
    week5to8Subs: 5,
    week9to12Subs: 7,
    totalSubs: 15,
  },
  base: {
    monthlyCreativeSpend: 3000,
    monthlyAdSpend: 2500,
    effectiveCac: 100,
    week1to4Subs: 5,
    week5to8Subs: 8,
    week9to12Subs: 12,
    totalSubs: 25,
  },
  aggressive: {
    monthlyCreativeSpend: 3500,
    monthlyAdSpend: 4000,
    effectiveCac: 75,
    week1to4Subs: 8,
    week5to8Subs: 12,
    week9to12Subs: 18,
    totalSubs: 38,
  },
};

export const MILESTONES: Milestone[] = [
  {
    day: 30,
    targetSubs: 10,
    killTriggerSubs: 5,
    killTriggerCac: 175,
    decision: 'Continue or Pause for diagnosis',
  },
  {
    day: 60,
    targetSubs: 25,
    killTriggerSubs: 15,
    killTriggerCac: 150,
    decision: 'Continue, restructure, or terminate',
  },
  {
    day: 90,
    targetSubs: 50,
    killTriggerSubs: 30,
    killTriggerCac: 125,
    decision: 'Scale, maintain, or exit',
  },
];

export const DEFAULT_CASH_POSITION = 84000;
export const DEFAULT_FIXED_MONTHLY_COSTS = 5500; // Creative retainer + baseline ops

export const INFRASTRUCTURE_ASSETS = [
  {
    name: 'Processing Capacity',
    currentUtilization: 60,
    calderaContribution: 'Incremental volume',
    valueUnlocked: 'Marginal revenue',
  },
  {
    name: 'Sourcing Relationships',
    currentUtilization: 100,
    calderaContribution: 'Volume leverage',
    valueUnlocked: 'Cost reduction',
  },
  {
    name: 'Retail Traffic',
    currentUtilization: 75,
    calderaContribution: 'Content creation, cross sell',
    valueUnlocked: 'Brand amplification',
  },
  {
    name: 'Bone/Byproduct Stream',
    currentUtilization: 30,
    calderaContribution: 'Potential monetization',
    valueUnlocked: 'Cost offset ($1.5K-2K/mo)',
  },
];

export const DEFAULT_WHOLESALE: WholesaleState = {
  animalsPerMonth: 5,
  liveWeight: 1300,
  costPerPound: 1.60,
  harvestFee: 70,
  processingCost: 556,
  prices: {
    ground: { wholesale: 6.00, retail: 7.00 },
    premium: { wholesale: 9.00, retail: 19.00 },
    ultraPremium: { wholesale: 14.00, retail: 36.00 },
  },
  channelAllocation: {
    ground: { wholesale: 70, retail: 20, online: 10, caldera: 0 },
    premium: { wholesale: 20, retail: 40, online: 20, caldera: 20 },
    ultraPremium: { wholesale: 0, retail: 30, online: 30, caldera: 40 },
  },
};
