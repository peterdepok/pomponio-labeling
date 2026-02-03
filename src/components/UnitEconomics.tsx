import type { UnitEconomicsInputs, WholesaleState } from '../types';
import {
  calculateUnitEconomics,
  getLtvCacStatus,
  formatCurrency,
  formatPercent,
  formatNumber,
  calculateLTV,
} from '../utils/calculations';
import { calculateWholesaleOutputs } from '../utils/wholesaleCalculations';
import { InputSlider, MetricCard, WaterfallChart, Gauge, TornadoChart } from './shared';

interface UnitEconomicsProps {
  inputs: UnitEconomicsInputs;
  fixedMonthlyCosts: number;
  wholesale: WholesaleState;
  onInputChange: (key: keyof UnitEconomicsInputs, value: number) => void;
}

export function UnitEconomics({ inputs, fixedMonthlyCosts, wholesale, onInputChange }: UnitEconomicsProps) {
  const outputs = calculateUnitEconomics(inputs, fixedMonthlyCosts);
  const ltvCacStatus = getLtvCacStatus(outputs.ltvCacRatio);
  const wholesaleOutputs = calculateWholesaleOutputs(wholesale);

  // Calculate box capacity from wholesale inventory
  const avgPremiumPerBox = 3; // lbs of premium + ultra premium per standard box
  const boxCapacity = Math.floor(wholesaleOutputs.premiumCutsForCaldera / avgPremiumPerBox);

  // Waterfall data for margin breakdown
  const waterfallItems = [
    { label: 'Price', value: inputs.boxPrice },
    { label: 'COGS', value: -inputs.cogs },
    { label: 'Ship', value: -inputs.shippingCost },
    { label: 'Labor', value: -inputs.fulfillmentLabor },
    { label: 'Margin', value: outputs.contributionMargin, isTotal: true },
  ];

  // Sensitivity analysis for tornado chart
  const baseLtv = calculateLTV(inputs);
  const sensitivityItems = [
    {
      label: 'Churn Rate',
      lowValue: calculateLTV({ ...inputs, monthlyChurn: inputs.monthlyChurn * 0.7 }),
      highValue: calculateLTV({ ...inputs, monthlyChurn: inputs.monthlyChurn * 1.3 }),
      baseValue: baseLtv,
    },
    {
      label: 'Box Price',
      lowValue: calculateLTV({ ...inputs, boxPrice: inputs.boxPrice * 0.9 }),
      highValue: calculateLTV({ ...inputs, boxPrice: inputs.boxPrice * 1.1 }),
      baseValue: baseLtv,
    },
    {
      label: 'COGS',
      lowValue: calculateLTV({ ...inputs, cogs: inputs.cogs * 1.15 }),
      highValue: calculateLTV({ ...inputs, cogs: inputs.cogs * 0.85 }),
      baseValue: baseLtv,
    },
    {
      label: 'Shipping',
      lowValue: calculateLTV({ ...inputs, shippingCost: inputs.shippingCost * 1.2 }),
      highValue: calculateLTV({ ...inputs, shippingCost: inputs.shippingCost * 0.8 }),
      baseValue: baseLtv,
    },
    {
      label: 'Add-on Rate',
      lowValue: calculateLTV({ ...inputs, addOnRate: inputs.addOnRate * 0.5 }),
      highValue: calculateLTV({ ...inputs, addOnRate: inputs.addOnRate * 1.5 }),
      baseValue: baseLtv,
    },
  ];

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-full">
      {/* Input Controls Sidebar */}
      <div className="lg:w-80 flex-shrink-0 bg-[var(--color-secondary-bg)] rounded-lg p-4 overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4 text-[var(--color-text-primary)]">Input Parameters</h3>

        <div className="space-y-1">
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mt-4 mb-2">
            Revenue
          </h4>
          <InputSlider
            label="Box Price (Monthly)"
            value={inputs.boxPrice}
            min={100}
            max={250}
            step={10}
            format="currency"
            onChange={(v) => onInputChange('boxPrice', v)}
          />

          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mt-4 mb-2">
            Costs
          </h4>
          <InputSlider
            label="COGS per Box"
            value={inputs.cogs}
            min={40}
            max={100}
            step={5}
            format="currency"
            onChange={(v) => onInputChange('cogs', v)}
          />
          <InputSlider
            label="Shipping Cost"
            value={inputs.shippingCost}
            min={25}
            max={60}
            step={5}
            format="currency"
            onChange={(v) => onInputChange('shippingCost', v)}
          />
          <InputSlider
            label="Fulfillment Labor"
            value={inputs.fulfillmentLabor}
            min={8}
            max={20}
            step={2}
            format="currency"
            onChange={(v) => onInputChange('fulfillmentLabor', v)}
          />

          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mt-4 mb-2">
            Acquisition
          </h4>
          <InputSlider
            label="Customer Acquisition Cost"
            value={inputs.cac}
            min={50}
            max={200}
            step={10}
            format="currency"
            onChange={(v) => onInputChange('cac', v)}
          />
          <InputSlider
            label="Monthly Churn Rate"
            value={inputs.monthlyChurn}
            min={0.03}
            max={0.15}
            step={0.01}
            format="percent"
            onChange={(v) => onInputChange('monthlyChurn', v)}
          />

          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mt-4 mb-2">
            Add-ons
          </h4>
          <InputSlider
            label="Add-on Attachment Rate"
            value={inputs.addOnRate}
            min={0}
            max={0.50}
            step={0.05}
            format="percent"
            onChange={(v) => onInputChange('addOnRate', v)}
          />
          <InputSlider
            label="Add-on Margin"
            value={inputs.addOnMargin}
            min={0.40}
            max={0.80}
            step={0.05}
            format="percent"
            onChange={(v) => onInputChange('addOnMargin', v)}
          />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="Contribution Margin"
            value={formatCurrency(outputs.contributionMargin)}
            subtitle={`${formatPercent(outputs.contributionMarginPercent)} of price`}
            status={outputs.contributionMarginPercent > 0.18 ? 'green' : outputs.contributionMarginPercent > 0.10 ? 'yellow' : 'red'}
          />
          <MetricCard
            label="Customer LTV"
            value={formatCurrency(outputs.ltv)}
            subtitle={`${formatNumber(outputs.avgCustomerLifespan)} mo lifespan`}
          />
          <MetricCard
            label="LTV:CAC Ratio"
            value={`${formatNumber(outputs.ltvCacRatio)}x`}
            subtitle={ltvCacStatus === 'green' ? 'Healthy' : ltvCacStatus === 'yellow' ? 'Marginal' : 'Unhealthy'}
            status={ltvCacStatus}
          />
          <MetricCard
            label="Payback Period"
            value={`${formatNumber(outputs.paybackPeriod)} mo`}
            subtitle={`Break-even: ${outputs.breakEvenSubscribers} subs`}
            status={outputs.paybackPeriod < 6 ? 'green' : outputs.paybackPeriod < 12 ? 'yellow' : 'red'}
          />
        </div>

        {/* Wholesale Integration Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <MetricCard
            label="Premium Cuts Available"
            value={`${wholesaleOutputs.premiumCutsForCaldera} lbs`}
            subtitle="From wholesale program"
            status={wholesaleOutputs.premiumCutsForCaldera >= 50 ? 'green' : wholesaleOutputs.premiumCutsForCaldera >= 25 ? 'yellow' : 'red'}
          />
          <MetricCard
            label="Box Capacity"
            value={`${boxCapacity} boxes`}
            subtitle="Monthly from inventory"
            status={boxCapacity >= 15 ? 'green' : boxCapacity >= 8 ? 'yellow' : 'red'}
          />
          <MetricCard
            label="Inventory Constraint"
            value={boxCapacity >= outputs.breakEvenSubscribers ? 'Unconstrained' : 'Constrained'}
            subtitle={boxCapacity >= outputs.breakEvenSubscribers ? 'Can meet demand' : 'Increase wholesale volume'}
            status={boxCapacity >= outputs.breakEvenSubscribers ? 'green' : 'red'}
          />
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          {/* Margin Waterfall */}
          <div>
            <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
              Margin Waterfall
            </h4>
            <WaterfallChart items={waterfallItems} height={180} />
          </div>

          {/* LTV/CAC Gauge */}
          <div>
            <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
              LTV/CAC Health
            </h4>
            <Gauge
              value={outputs.ltvCacRatio}
              min={0}
              max={5}
              thresholds={[
                { value: 0, color: 'var(--color-danger)' },
                { value: 2, color: 'var(--color-warning)' },
                { value: 3, color: 'var(--color-success)' },
              ]}
              label="LTV:CAC Ratio"
              size={180}
            />
          </div>
        </div>

        {/* Sensitivity Analysis */}
        <div>
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
            LTV Sensitivity Analysis
          </h4>
          <p className="text-xs text-[var(--color-text-secondary)] mb-2">
            Impact of +/-30% change in each variable on customer lifetime value
          </p>
          <TornadoChart items={sensitivityItems} height={220} />
        </div>
      </div>
    </div>
  );
}
