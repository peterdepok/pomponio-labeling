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
