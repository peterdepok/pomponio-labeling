export interface UnitEconomicsInputs {
  boxPrice: number;
  cogs: number;
  shippingCost: number;
  fulfillmentLabor: number;
  cac: number;
  monthlyChurn: number;
  addOnRate: number;
  addOnMargin: number;
}

export interface UnitEconomicsOutputs {
  contributionMargin: number;
  contributionMarginPercent: number;
  avgCustomerLifespan: number;
  ltv: number;
  ltvCacRatio: number;
  paybackPeriod: number;
  breakEvenSubscribers: number;
}

export type ScenarioType = 'conservative' | 'base' | 'aggressive';

export interface ScenarioConfig {
  monthlyCreativeSpend: number;
  monthlyAdSpend: number;
  effectiveCac: number;
  week1to4Subs: number;
  week5to8Subs: number;
  week9to12Subs: number;
  totalSubs: number;
}

export interface WeeklyActual {
  week: number;
  subscribers: number;
  spend: number;
  revenue: number;
}

export interface Milestone {
  day: number;
  targetSubs: number;
  killTriggerSubs: number;
  killTriggerCac: number;
  decision: string;
}

export interface MilestoneStatus {
  day: number;
  status: 'green' | 'yellow' | 'red' | 'pending';
  actualSubs: number | null;
  actualCac: number | null;
}

export interface InfrastructureAsset {
  name: string;
  currentUtilization: number;
  calderaContribution: string;
  valueUnlocked: string;
}

export interface CalderaState {
  unitEconomics: UnitEconomicsInputs;
  scenario: ScenarioType;
  actuals: WeeklyActual[];
  cashPosition: number;
  fixedMonthlyCosts: number;
  wholesale: WholesaleState;
}

export interface SliderConfig {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  format: 'currency' | 'percent' | 'number';
  onChange: (value: number) => void;
}

// Wholesale Program Types
export interface WholesalePrices {
  ground: { wholesale: number; retail: number };
  premium: { wholesale: number; retail: number };
  ultraPremium: { wholesale: number; retail: number };
}

export interface ChannelAllocation {
  wholesale: number;
  retail: number;
  online: number;
  caldera: number;
}

export interface WholesaleChannelAllocations {
  ground: ChannelAllocation;
  premium: ChannelAllocation;
  ultraPremium: ChannelAllocation;
}

export interface WholesaleState {
  animalsPerMonth: number;
  liveWeight: number;
  costPerPound: number;
  harvestFee: number;
  processingCost: number;
  prices: WholesalePrices;
  channelAllocation: WholesaleChannelAllocations;
}

export interface AnimalYield {
  ground: number;
  premium: number;
  ultraPremium: number;
  total: number;
}

export interface ScenarioProfit {
  allGround: number;
  allWholesale: number;
  combo: number;
}

export interface ChannelRevenue {
  wholesale: number;
  retail: number;
  online: number;
  caldera: number;
}

export interface WholesaleOutputs {
  costBasis: number;
  yield: AnimalYield;
  scenarioProfit: ScenarioProfit;
  monthlyGrossRevenue: number;
  monthlyNetProfit: number;
  annualProjection: number;
  poundsPerCategory: AnimalYield;
  wholesaleAccountsRequired: number;
  premiumCutsForCaldera: number;
  revenueByChannel: ChannelRevenue;
  revenueByCategory: {
    ground: number;
    premium: number;
    ultraPremium: number;
  };
}

export interface WholesaleMilestone {
  id: string;
  name: string;
  target: string;
  status: 'green' | 'yellow' | 'red' | 'pending';
  description: string;
}

export interface BoxType {
  name: string;
  description: string;
  premiumLbs: number;
  ultraPremiumLbs: number;
  groundLbs: number;
  price: number;
}
