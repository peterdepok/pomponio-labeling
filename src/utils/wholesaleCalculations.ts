import type {
  WholesaleState,
  WholesaleOutputs,
  AnimalYield,
  ScenarioProfit,
  ChannelRevenue,
  BoxType,
} from '../types';

// Yield ratios from PRD
const HOT_WEIGHT_RATIO = 0.60;
const SALEABLE_RATIO = 0.56;
const GROUND_RATIO = 0.76;
const PREMIUM_RATIO = 0.10;
const ULTRA_PREMIUM_RATIO = 0.14;

// Typical restaurant weekly volume for account sizing
const RESTAURANT_WEEKLY_VOLUME = 500;

/**
 * Calculate yield breakdown from live weight
 */
export function calculateYield(liveWeight: number): AnimalYield {
  const hotWeight = liveWeight * HOT_WEIGHT_RATIO;
  const saleableWeight = hotWeight * SALEABLE_RATIO;

  return {
    ground: Math.round(saleableWeight * GROUND_RATIO),
    premium: Math.round(saleableWeight * PREMIUM_RATIO),
    ultraPremium: Math.round(saleableWeight * ULTRA_PREMIUM_RATIO),
    total: Math.round(saleableWeight),
  };
}

/**
 * Calculate total cost basis per animal
 */
export function calculateCostBasis(state: WholesaleState): number {
  const liveCost = state.liveWeight * state.costPerPound;
  return liveCost + state.harvestFee + state.processingCost;
}

/**
 * Calculate profit for All Ground scenario
 * Grind entire animal, sell at ground wholesale price
 */
export function calculateAllGroundProfit(state: WholesaleState): number {
  const yieldData = calculateYield(state.liveWeight);
  const revenue = yieldData.total * state.prices.ground.wholesale;
  const cost = calculateCostBasis(state);
  return Math.round(revenue - cost);
}

/**
 * Calculate profit for All Wholesale scenario
 * Sell all cuts at wholesale prices
 */
export function calculateAllWholesaleProfit(state: WholesaleState): number {
  const yieldData = calculateYield(state.liveWeight);

  const groundRevenue = yieldData.ground * state.prices.ground.wholesale;
  const premiumRevenue = yieldData.premium * state.prices.premium.wholesale;
  const ultraPremiumRevenue = yieldData.ultraPremium * state.prices.ultraPremium.wholesale;

  const totalRevenue = groundRevenue + premiumRevenue + ultraPremiumRevenue;
  const cost = calculateCostBasis(state);

  return Math.round(totalRevenue - cost);
}

/**
 * Calculate revenue for a cut category based on channel allocation
 */
function calculateCategoryRevenue(
  pounds: number,
  wholesalePrice: number,
  retailPrice: number,
  allocation: { wholesale: number; retail: number; online: number; caldera: number }
): { total: number; byChannel: ChannelRevenue } {
  // Online and Caldera use retail pricing
  const wholesaleRev = pounds * (allocation.wholesale / 100) * wholesalePrice;
  const retailRev = pounds * (allocation.retail / 100) * retailPrice;
  const onlineRev = pounds * (allocation.online / 100) * retailPrice;
  const calderaRev = pounds * (allocation.caldera / 100) * retailPrice;

  return {
    total: wholesaleRev + retailRev + onlineRev + calderaRev,
    byChannel: {
      wholesale: wholesaleRev,
      retail: retailRev,
      online: onlineRev,
      caldera: calderaRev,
    },
  };
}

/**
 * Calculate profit for Combo scenario based on channel allocation
 */
export function calculateComboProfit(state: WholesaleState): number {
  const yieldData = calculateYield(state.liveWeight);

  const groundRev = calculateCategoryRevenue(
    yieldData.ground,
    state.prices.ground.wholesale,
    state.prices.ground.retail,
    state.channelAllocation.ground
  );

  const premiumRev = calculateCategoryRevenue(
    yieldData.premium,
    state.prices.premium.wholesale,
    state.prices.premium.retail,
    state.channelAllocation.premium
  );

  const ultraPremiumRev = calculateCategoryRevenue(
    yieldData.ultraPremium,
    state.prices.ultraPremium.wholesale,
    state.prices.ultraPremium.retail,
    state.channelAllocation.ultraPremium
  );

  const totalRevenue = groundRev.total + premiumRev.total + ultraPremiumRev.total;
  const cost = calculateCostBasis(state);

  return Math.round(totalRevenue - cost);
}

/**
 * Calculate all scenario profits
 */
export function calculateScenarioProfits(state: WholesaleState): ScenarioProfit {
  return {
    allGround: calculateAllGroundProfit(state),
    allWholesale: calculateAllWholesaleProfit(state),
    combo: calculateComboProfit(state),
  };
}

/**
 * Calculate complete wholesale outputs
 */
export function calculateWholesaleOutputs(state: WholesaleState): WholesaleOutputs {
  const yieldData = calculateYield(state.liveWeight);
  const costBasis = calculateCostBasis(state);
  const scenarioProfit = calculateScenarioProfits(state);

  // Calculate revenue by channel for combo model
  const groundRev = calculateCategoryRevenue(
    yieldData.ground,
    state.prices.ground.wholesale,
    state.prices.ground.retail,
    state.channelAllocation.ground
  );
  const premiumRev = calculateCategoryRevenue(
    yieldData.premium,
    state.prices.premium.wholesale,
    state.prices.premium.retail,
    state.channelAllocation.premium
  );
  const ultraPremiumRev = calculateCategoryRevenue(
    yieldData.ultraPremium,
    state.prices.ultraPremium.wholesale,
    state.prices.ultraPremium.retail,
    state.channelAllocation.ultraPremium
  );

  const revenueByChannel: ChannelRevenue = {
    wholesale: groundRev.byChannel.wholesale + premiumRev.byChannel.wholesale + ultraPremiumRev.byChannel.wholesale,
    retail: groundRev.byChannel.retail + premiumRev.byChannel.retail + ultraPremiumRev.byChannel.retail,
    online: groundRev.byChannel.online + premiumRev.byChannel.online + ultraPremiumRev.byChannel.online,
    caldera: groundRev.byChannel.caldera + premiumRev.byChannel.caldera + ultraPremiumRev.byChannel.caldera,
  };

  const monthlyGrossRevenue = (groundRev.total + premiumRev.total + ultraPremiumRev.total) * state.animalsPerMonth;
  const monthlyNetProfit = scenarioProfit.combo * state.animalsPerMonth;

  // Pounds per category per month
  const poundsPerCategory: AnimalYield = {
    ground: yieldData.ground * state.animalsPerMonth,
    premium: yieldData.premium * state.animalsPerMonth,
    ultraPremium: yieldData.ultraPremium * state.animalsPerMonth,
    total: yieldData.total * state.animalsPerMonth,
  };

  // Wholesale accounts needed (based on ground going to wholesale)
  const groundToWholesale = poundsPerCategory.ground * (state.channelAllocation.ground.wholesale / 100);
  const monthlyWholesaleNeed = groundToWholesale;
  const weeklyWholesaleNeed = monthlyWholesaleNeed / 4.33;
  const wholesaleAccountsRequired = Math.ceil(weeklyWholesaleNeed / RESTAURANT_WEEKLY_VOLUME);

  // Premium cuts available for Caldera
  const premiumForCaldera = poundsPerCategory.premium * (state.channelAllocation.premium.caldera / 100);
  const ultraPremiumForCaldera = poundsPerCategory.ultraPremium * (state.channelAllocation.ultraPremium.caldera / 100);
  const premiumCutsForCaldera = Math.round(premiumForCaldera + ultraPremiumForCaldera);

  return {
    costBasis,
    yield: yieldData,
    scenarioProfit,
    monthlyGrossRevenue: Math.round(monthlyGrossRevenue),
    monthlyNetProfit: Math.round(monthlyNetProfit),
    annualProjection: Math.round(monthlyNetProfit * 12),
    poundsPerCategory,
    wholesaleAccountsRequired,
    premiumCutsForCaldera,
    revenueByChannel,
    revenueByCategory: {
      ground: Math.round(groundRev.total * state.animalsPerMonth),
      premium: Math.round(premiumRev.total * state.animalsPerMonth),
      ultraPremium: Math.round(ultraPremiumRev.total * state.animalsPerMonth),
    },
  };
}

/**
 * Calculate box capacity given inventory
 */
export function calculateBoxCapacity(
  premiumLbs: number,
  ultraPremiumLbs: number,
  groundLbs: number,
  boxTypes: BoxType[]
): { boxType: BoxType; capacity: number }[] {
  return boxTypes.map(box => {
    // Calculate how many of this box type we can make
    const premiumConstraint = box.premiumLbs > 0 ? Math.floor(premiumLbs / box.premiumLbs) : Infinity;
    const ultraPremiumConstraint = box.ultraPremiumLbs > 0 ? Math.floor(ultraPremiumLbs / box.ultraPremiumLbs) : Infinity;
    const groundConstraint = box.groundLbs > 0 ? Math.floor(groundLbs / box.groundLbs) : Infinity;

    const capacity = Math.min(premiumConstraint, ultraPremiumConstraint, groundConstraint);

    return {
      boxType: box,
      capacity: capacity === Infinity ? 999 : capacity,
    };
  });
}

/**
 * Default box types
 */
export const DEFAULT_BOX_TYPES: BoxType[] = [
  {
    name: 'Standard Mixed',
    description: 'Ground, premium, ultra premium mix',
    premiumLbs: 1,
    ultraPremiumLbs: 2,
    groundLbs: 5,
    price: 150,
  },
  {
    name: 'Premium Selection',
    description: 'Premium and ultra premium only',
    premiumLbs: 4,
    ultraPremiumLbs: 4,
    groundLbs: 0,
    price: 225,
  },
  {
    name: 'Steak Box',
    description: 'Ultra premium cuts only',
    premiumLbs: 0,
    ultraPremiumLbs: 6,
    groundLbs: 0,
    price: 275,
  },
  {
    name: 'Ground Beef Box',
    description: 'All ground beef',
    premiumLbs: 0,
    ultraPremiumLbs: 0,
    groundLbs: 10,
    price: 95,
  },
];

/**
 * Calculate processing utilization
 */
export function calculateProcessingUtilization(animalsPerMonth: number, capacity: number = 20): number {
  return Math.round((animalsPerMonth / capacity) * 100);
}

/**
 * Calculate combo model advantage multiplier
 */
export function calculateComboAdvantage(scenarioProfit: ScenarioProfit): {
  vsAllGround: number;
  vsAllWholesale: number;
  multiplier: number;
} {
  return {
    vsAllGround: scenarioProfit.combo - scenarioProfit.allGround,
    vsAllWholesale: scenarioProfit.combo - scenarioProfit.allWholesale,
    multiplier: scenarioProfit.allGround > 0 ? scenarioProfit.combo / scenarioProfit.allGround : 0,
  };
}
