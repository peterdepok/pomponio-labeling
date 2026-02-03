import type {
  UnitEconomicsInputs,
  UnitEconomicsOutputs,
  ScenarioConfig,
  WeeklyActual,
  MilestoneStatus,
  CalderaState
} from '../types';
import { MILESTONES } from './constants';

/**
 * Calculate contribution margin per box
 * Formula: Box Price - COGS - Shipping - Fulfillment Labor
 */
export function calculateContributionMargin(inputs: UnitEconomicsInputs): number {
  return inputs.boxPrice - inputs.cogs - inputs.shippingCost - inputs.fulfillmentLabor;
}

/**
 * Calculate contribution margin as percentage of box price
 */
export function calculateContributionMarginPercent(inputs: UnitEconomicsInputs): number {
  const margin = calculateContributionMargin(inputs);
  return inputs.boxPrice > 0 ? margin / inputs.boxPrice : 0;
}

/**
 * Calculate average customer lifespan in months
 * Formula: 1 / Monthly Churn Rate
 */
export function calculateAvgCustomerLifespan(monthlyChurn: number): number {
  return monthlyChurn > 0 ? 1 / monthlyChurn : 0;
}

/**
 * Calculate customer lifetime value
 * Formula: (Contribution Margin * Customer Lifespan) + Add-on Revenue
 * Add-on Revenue = Contribution Margin * Add-on Rate * Add-on Margin * Lifespan
 */
export function calculateLTV(inputs: UnitEconomicsInputs): number {
  const margin = calculateContributionMargin(inputs);
  const lifespan = calculateAvgCustomerLifespan(inputs.monthlyChurn);
  const baseValue = margin * lifespan;
  const addOnValue = inputs.boxPrice * inputs.addOnRate * inputs.addOnMargin * lifespan;
  return baseValue + addOnValue;
}

/**
 * Calculate LTV to CAC ratio
 */
export function calculateLtvCacRatio(inputs: UnitEconomicsInputs): number {
  const ltv = calculateLTV(inputs);
  return inputs.cac > 0 ? ltv / inputs.cac : 0;
}

/**
 * Calculate payback period in months
 * Formula: CAC / Monthly Contribution Margin
 */
export function calculatePaybackPeriod(inputs: UnitEconomicsInputs): number {
  const margin = calculateContributionMargin(inputs);
  return margin > 0 ? inputs.cac / margin : Infinity;
}

/**
 * Calculate break-even number of subscribers
 * Formula: Fixed Monthly Costs / Contribution Margin
 */
export function calculateBreakEvenSubscribers(
  inputs: UnitEconomicsInputs,
  fixedMonthlyCosts: number
): number {
  const margin = calculateContributionMargin(inputs);
  return margin > 0 ? Math.ceil(fixedMonthlyCosts / margin) : Infinity;
}

/**
 * Calculate all unit economics outputs
 */
export function calculateUnitEconomics(
  inputs: UnitEconomicsInputs,
  fixedMonthlyCosts: number
): UnitEconomicsOutputs {
  return {
    contributionMargin: calculateContributionMargin(inputs),
    contributionMarginPercent: calculateContributionMarginPercent(inputs),
    avgCustomerLifespan: calculateAvgCustomerLifespan(inputs.monthlyChurn),
    ltv: calculateLTV(inputs),
    ltvCacRatio: calculateLtvCacRatio(inputs),
    paybackPeriod: calculatePaybackPeriod(inputs),
    breakEvenSubscribers: calculateBreakEvenSubscribers(inputs, fixedMonthlyCosts),
  };
}

/**
 * Get LTV/CAC ratio status color
 */
export function getLtvCacStatus(ratio: number): 'red' | 'yellow' | 'green' {
  if (ratio < 2) return 'red';
  if (ratio < 3) return 'yellow';
  return 'green';
}

/**
 * Generate weekly subscriber projections for a scenario
 */
export function generateWeeklyProjections(config: ScenarioConfig): number[] {
  const weeks: number[] = [];
  const weeklyRates = [
    config.week1to4Subs / 4,
    config.week1to4Subs / 4,
    config.week1to4Subs / 4,
    config.week1to4Subs / 4,
    config.week5to8Subs / 4,
    config.week5to8Subs / 4,
    config.week5to8Subs / 4,
    config.week5to8Subs / 4,
    config.week9to12Subs / 4,
    config.week9to12Subs / 4,
    config.week9to12Subs / 4,
    config.week9to12Subs / 4,
  ];

  let cumulative = 1; // Start with 1 existing subscriber
  for (let i = 0; i < 12; i++) {
    cumulative += weeklyRates[i];
    weeks.push(Math.round(cumulative));
  }
  return weeks;
}

/**
 * Calculate weekly cash position over 90 days
 */
export function calculateCashFlow(
  startingCash: number,
  config: ScenarioConfig,
  unitEconomics: UnitEconomicsInputs
): { week: number; cash: number; spend: number; revenue: number }[] {
  const weeklyCreative = config.monthlyCreativeSpend / 4.33;
  const weeklyAd = config.monthlyAdSpend / 4.33;
  const weeklySpend = weeklyCreative + weeklyAd;

  const projections = generateWeeklyProjections(config);
  const margin = calculateContributionMargin(unitEconomics);

  const cashFlow: { week: number; cash: number; spend: number; revenue: number }[] = [];
  let cash = startingCash;

  for (let week = 1; week <= 12; week++) {
    // Revenue delayed by 1 week for payment processing
    const revenue = week > 1 ? projections[week - 2] * margin : margin; // 1 existing sub
    cash = cash - weeklySpend + revenue;

    cashFlow.push({
      week,
      cash: Math.round(cash),
      spend: Math.round(weeklySpend),
      revenue: Math.round(revenue),
    });
  }

  return cashFlow;
}

/**
 * Calculate running CAC based on actuals
 */
export function calculateRunningCac(actuals: WeeklyActual[]): number {
  const totalSpend = actuals.reduce((sum, a) => sum + a.spend, 0);
  const totalSubs = actuals.reduce((sum, a) => sum + a.subscribers, 0);
  return totalSubs > 0 ? totalSpend / totalSubs : 0;
}

/**
 * Evaluate milestone status based on actuals
 */
export function evaluateMilestoneStatus(
  actuals: WeeklyActual[],
  unitEconomics: UnitEconomicsInputs
): MilestoneStatus[] {
  return MILESTONES.map(milestone => {
    const weekIndex = milestone.day / 7;
    const relevantActuals = actuals.slice(0, weekIndex);

    if (relevantActuals.length < weekIndex) {
      return {
        day: milestone.day,
        status: 'pending' as const,
        actualSubs: null,
        actualCac: null,
      };
    }

    const actualSubs = relevantActuals.reduce((sum, a) => sum + a.subscribers, 0) + 1;
    const actualCac = calculateRunningCac(relevantActuals);

    let status: 'green' | 'yellow' | 'red';

    if (actualSubs < milestone.killTriggerSubs || actualCac > milestone.killTriggerCac) {
      status = 'red';
    } else if (actualSubs >= milestone.targetSubs && actualCac <= unitEconomics.cac) {
      status = 'green';
    } else {
      status = 'yellow';
    }

    return {
      day: milestone.day,
      status,
      actualSubs,
      actualCac: actualCac || null,
    };
  });
}

/**
 * Generate recommendation based on milestone statuses
 */
export function generateRecommendation(statuses: MilestoneStatus[]): string {
  const hasRed = statuses.some(s => s.status === 'red');
  const hasYellow = statuses.some(s => s.status === 'yellow');
  const allGreen = statuses.every(s => s.status === 'green' || s.status === 'pending');
  const allPending = statuses.every(s => s.status === 'pending');

  if (allPending) {
    return 'No actuals entered. Input weekly results to track progress against milestones.';
  }

  if (hasRed) {
    return 'PAUSE AND DIAGNOSE: At least one milestone has triggered kill criteria. Review channel strategy, creative performance, and targeting before additional spend.';
  }

  if (hasYellow) {
    return 'CONTINUE WITH ENHANCED MONITORING: Performance is within acceptable range but not meeting targets. Increase measurement frequency and prepare contingency plans.';
  }

  if (allGreen) {
    return 'SCALE INVESTMENT: All indicators green. Consider increasing marketing budget to accelerate subscriber acquisition while maintaining CAC efficiency.';
  }

  return 'Continue monitoring progress against milestones.';
}

/**
 * Calculate opportunity cost of inaction per month
 */
export function calculateOpportunityCost(processingUtilization: number): {
  wastedCapacity: number;
  inventoryCost: number;
  totalMonthly: number;
} {
  // Rough estimates based on S&S context
  const monthlyProcessingCapacity = 50000; // lbs
  const unusedCapacity = monthlyProcessingCapacity * (1 - processingUtilization / 100);
  const wastedCapacity = unusedCapacity * 0.50; // $0.50/lb opportunity cost
  const inventoryCost = 2000; // Fixed carrying cost estimate

  return {
    wastedCapacity: Math.round(wastedCapacity),
    inventoryCost,
    totalMonthly: Math.round(wastedCapacity + inventoryCost),
  };
}

/**
 * Encode state to URL parameters
 */
export function encodeStateToUrl(state: CalderaState): string {
  const params = new URLSearchParams();
  params.set('s', JSON.stringify(state));
  return params.toString();
}

/**
 * Decode state from URL parameters
 */
export function decodeStateFromUrl(search: string): Partial<CalderaState> | null {
  try {
    const params = new URLSearchParams(search);
    const stateStr = params.get('s');
    if (stateStr) {
      return JSON.parse(stateStr);
    }
  } catch {
    console.error('Failed to decode state from URL');
  }
  return null;
}

/**
 * Format currency
 */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

/**
 * Format percentage
 */
export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

/**
 * Format number with commas
 */
export function formatNumber(value: number, decimals: number = 1): string {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}
