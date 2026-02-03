import type { WholesaleState, ChannelAllocation } from '../types';
import {
  calculateWholesaleOutputs,
  calculateBoxCapacity,
  calculateComboAdvantage,
  DEFAULT_BOX_TYPES,
} from '../utils/wholesaleCalculations';
import { formatCurrency, formatNumber } from '../utils/calculations';
import { InputSlider, MetricCard } from './shared';

interface WholesaleProgramProps {
  wholesale: WholesaleState;
  onWholesaleChange: (wholesale: WholesaleState) => void;
}

type CutCategory = 'ground' | 'premium' | 'ultraPremium';

export function WholesaleProgram({ wholesale, onWholesaleChange }: WholesaleProgramProps) {
  const outputs = calculateWholesaleOutputs(wholesale);
  const comboAdvantage = calculateComboAdvantage(outputs.scenarioProfit);

  const updateField = <K extends keyof WholesaleState>(key: K, value: WholesaleState[K]) => {
    onWholesaleChange({ ...wholesale, [key]: value });
  };

  const updatePrice = (category: CutCategory, channel: 'wholesale' | 'retail', value: number) => {
    onWholesaleChange({
      ...wholesale,
      prices: {
        ...wholesale.prices,
        [category]: {
          ...wholesale.prices[category],
          [channel]: value,
        },
      },
    });
  };

  const updateAllocation = (category: CutCategory, channel: keyof ChannelAllocation, value: number) => {
    const currentAllocation = wholesale.channelAllocation[category];
    const otherChannels = Object.keys(currentAllocation).filter(k => k !== channel) as (keyof ChannelAllocation)[];
    const currentOtherTotal = otherChannels.reduce((sum, k) => sum + currentAllocation[k], 0);

    // Normalize other channels to make total 100%
    const remaining = 100 - value;
    const scale = currentOtherTotal > 0 ? remaining / currentOtherTotal : 0;

    const newAllocation: ChannelAllocation = {
      ...currentAllocation,
      [channel]: value,
    };

    otherChannels.forEach(k => {
      newAllocation[k] = Math.round(currentAllocation[k] * scale);
    });

    // Fix rounding errors
    const total = Object.values(newAllocation).reduce((a, b) => a + b, 0);
    if (total !== 100) {
      const diff = 100 - total;
      const firstOther = otherChannels[0];
      newAllocation[firstOther] += diff;
    }

    onWholesaleChange({
      ...wholesale,
      channelAllocation: {
        ...wholesale.channelAllocation,
        [category]: newAllocation,
      },
    });
  };

  // Calculate box capacity
  const groundForCaldera = outputs.poundsPerCategory.ground * (wholesale.channelAllocation.ground.caldera / 100);
  const premiumForCaldera = outputs.poundsPerCategory.premium * (wholesale.channelAllocation.premium.caldera / 100);
  const ultraPremiumForCaldera = outputs.poundsPerCategory.ultraPremium * (wholesale.channelAllocation.ultraPremium.caldera / 100);
  const boxCapacity = calculateBoxCapacity(premiumForCaldera, ultraPremiumForCaldera, groundForCaldera, DEFAULT_BOX_TYPES);

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-full">
      {/* Input Controls Sidebar */}
      <div className="lg:w-96 flex-shrink-0 bg-[var(--color-secondary-bg)] rounded-lg p-4 overflow-y-auto max-h-[calc(100vh-180px)]">
        <h3 className="text-lg font-semibold mb-4 text-[var(--color-text-primary)]">Animal & Cost Parameters</h3>

        <InputSlider
          label="Animals per Month"
          value={wholesale.animalsPerMonth}
          min={1}
          max={20}
          step={1}
          format="number"
          onChange={(v) => updateField('animalsPerMonth', v)}
        />
        <InputSlider
          label="Live Weight (lbs)"
          value={wholesale.liveWeight}
          min={1000}
          max={1600}
          step={50}
          format="number"
          onChange={(v) => updateField('liveWeight', v)}
        />
        <InputSlider
          label="Cost per Pound (live)"
          value={wholesale.costPerPound}
          min={1.20}
          max={2.00}
          step={0.05}
          format="currency"
          onChange={(v) => updateField('costPerPound', v)}
        />
        <InputSlider
          label="Harvest Fee"
          value={wholesale.harvestFee}
          min={50}
          max={100}
          step={5}
          format="currency"
          onChange={(v) => updateField('harvestFee', v)}
        />
        <InputSlider
          label="Processing Cost"
          value={wholesale.processingCost}
          min={400}
          max={700}
          step={25}
          format="currency"
          onChange={(v) => updateField('processingCost', v)}
        />

        <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mt-6 mb-3">
          Pricing by Cut Category
        </h4>

        {/* Ground Pricing */}
        <div className="mb-4 p-3 bg-[var(--color-primary-bg)] rounded">
          <div className="text-sm font-medium text-[var(--color-text-primary)] mb-2">Ground Beef</div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-[var(--color-text-secondary)]">Wholesale</label>
              <input
                type="number"
                value={wholesale.prices.ground.wholesale}
                onChange={(e) => updatePrice('ground', 'wholesale', parseFloat(e.target.value) || 0)}
                step={0.25}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-[var(--color-text-secondary)]">Retail</label>
              <input
                type="number"
                value={wholesale.prices.ground.retail}
                onChange={(e) => updatePrice('ground', 'retail', parseFloat(e.target.value) || 0)}
                step={0.25}
                className="w-full text-sm"
              />
            </div>
          </div>
        </div>

        {/* Premium Pricing */}
        <div className="mb-4 p-3 bg-[var(--color-primary-bg)] rounded">
          <div className="text-sm font-medium text-[var(--color-text-primary)] mb-2">Premium Cuts</div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-[var(--color-text-secondary)]">Wholesale</label>
              <input
                type="number"
                value={wholesale.prices.premium.wholesale}
                onChange={(e) => updatePrice('premium', 'wholesale', parseFloat(e.target.value) || 0)}
                step={0.50}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-[var(--color-text-secondary)]">Retail</label>
              <input
                type="number"
                value={wholesale.prices.premium.retail}
                onChange={(e) => updatePrice('premium', 'retail', parseFloat(e.target.value) || 0)}
                step={1}
                className="w-full text-sm"
              />
            </div>
          </div>
        </div>

        {/* Ultra Premium Pricing */}
        <div className="mb-4 p-3 bg-[var(--color-primary-bg)] rounded">
          <div className="text-sm font-medium text-[var(--color-text-primary)] mb-2">Ultra Premium Cuts</div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-xs text-[var(--color-text-secondary)]">Wholesale</label>
              <input
                type="number"
                value={wholesale.prices.ultraPremium.wholesale}
                onChange={(e) => updatePrice('ultraPremium', 'wholesale', parseFloat(e.target.value) || 0)}
                step={0.50}
                className="w-full text-sm"
              />
            </div>
            <div>
              <label className="text-xs text-[var(--color-text-secondary)]">Retail</label>
              <input
                type="number"
                value={wholesale.prices.ultraPremium.retail}
                onChange={(e) => updatePrice('ultraPremium', 'retail', parseFloat(e.target.value) || 0)}
                step={1}
                className="w-full text-sm"
              />
            </div>
          </div>
        </div>

        <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mt-6 mb-3">
          Channel Allocation
        </h4>

        {/* Ground Allocation */}
        <ChannelAllocationControl
          label="Ground"
          allocation={wholesale.channelAllocation.ground}
          onChange={(channel, value) => updateAllocation('ground', channel, value)}
        />

        {/* Premium Allocation */}
        <ChannelAllocationControl
          label="Premium"
          allocation={wholesale.channelAllocation.premium}
          onChange={(channel, value) => updateAllocation('premium', channel, value)}
        />

        {/* Ultra Premium Allocation */}
        <ChannelAllocationControl
          label="Ultra Premium"
          allocation={wholesale.channelAllocation.ultraPremium}
          onChange={(channel, value) => updateAllocation('ultraPremium', channel, value)}
        />
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="Net Profit/Animal"
            value={formatCurrency(outputs.scenarioProfit.combo)}
            subtitle={`${formatNumber(comboAdvantage.multiplier, 1)}x vs all ground`}
            status="green"
          />
          <MetricCard
            label="Monthly Net Profit"
            value={formatCurrency(outputs.monthlyNetProfit)}
            subtitle={`${wholesale.animalsPerMonth} animals/mo`}
          />
          <MetricCard
            label="Annual Projection"
            value={formatCurrency(outputs.annualProjection)}
            subtitle="At current volume"
          />
          <MetricCard
            label="Cost Basis/Animal"
            value={formatCurrency(outputs.costBasis)}
            subtitle={`${outputs.yield.total} lbs saleable`}
          />
        </div>

        {/* Scenario Comparison */}
        <div className="bg-[var(--color-secondary-bg)] rounded-lg p-5 mb-6">
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
            Scenario Comparison: Net Profit per Animal
          </h4>
          <div className="space-y-3">
            <ScenarioBar
              label="All Ground"
              value={outputs.scenarioProfit.allGround}
              maxValue={outputs.scenarioProfit.combo}
              color="var(--color-text-secondary)"
            />
            <ScenarioBar
              label="All Wholesale"
              value={outputs.scenarioProfit.allWholesale}
              maxValue={outputs.scenarioProfit.combo}
              color="var(--color-warning)"
            />
            <ScenarioBar
              label="Combo Model"
              value={outputs.scenarioProfit.combo}
              maxValue={outputs.scenarioProfit.combo}
              color="var(--color-success)"
              highlight
            />
          </div>
          <div className="mt-4 p-3 bg-[var(--color-primary-bg)] rounded text-sm">
            <span className="text-[var(--color-success)] font-semibold">
              Combo model yields {formatCurrency(comboAdvantage.vsAllGround)} more per animal
            </span>
            <span className="text-[var(--color-text-secondary)]">
              {' '}than grinding everything ({formatNumber(comboAdvantage.multiplier, 1)}x improvement)
            </span>
          </div>
        </div>

        {/* Yield & Inventory */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Yield Breakdown */}
          <div className="bg-[var(--color-secondary-bg)] rounded-lg p-5">
            <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
              Monthly Yield by Category
            </h4>
            <div className="space-y-3">
              <YieldRow
                label="Ground"
                pounds={outputs.poundsPerCategory.ground}
                revenue={outputs.revenueByCategory.ground}
                color="var(--color-text-secondary)"
              />
              <YieldRow
                label="Premium"
                pounds={outputs.poundsPerCategory.premium}
                revenue={outputs.revenueByCategory.premium}
                color="var(--color-warning)"
              />
              <YieldRow
                label="Ultra Premium"
                pounds={outputs.poundsPerCategory.ultraPremium}
                revenue={outputs.revenueByCategory.ultraPremium}
                color="var(--color-success)"
              />
              <div className="border-t border-[var(--color-accent)] pt-2 mt-2">
                <div className="flex justify-between text-sm font-medium">
                  <span>Total</span>
                  <span>{formatNumber(outputs.poundsPerCategory.total, 0)} lbs / {formatCurrency(outputs.monthlyGrossRevenue)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Channel Revenue */}
          <div className="bg-[var(--color-secondary-bg)] rounded-lg p-5">
            <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
              Monthly Revenue by Channel
            </h4>
            <div className="space-y-3">
              <ChannelRow label="Wholesale" revenue={outputs.revenueByChannel.wholesale * wholesale.animalsPerMonth} />
              <ChannelRow label="Retail (Templeton)" revenue={outputs.revenueByChannel.retail * wholesale.animalsPerMonth} />
              <ChannelRow label="Online" revenue={outputs.revenueByChannel.online * wholesale.animalsPerMonth} />
              <ChannelRow label="Caldera Boxes" revenue={outputs.revenueByChannel.caldera * wholesale.animalsPerMonth} />
            </div>
          </div>
        </div>

        {/* Wholesale Operations */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="Wholesale Accounts Needed"
            value={outputs.wholesaleAccountsRequired.toString()}
            subtitle="At 500 lbs/week each"
            status={outputs.wholesaleAccountsRequired <= 2 ? 'green' : 'yellow'}
          />
          <MetricCard
            label="Premium for Caldera"
            value={`${outputs.premiumCutsForCaldera} lbs`}
            subtitle="Monthly inventory"
            status={outputs.premiumCutsForCaldera >= 50 ? 'green' : outputs.premiumCutsForCaldera >= 25 ? 'yellow' : 'red'}
          />
          <MetricCard
            label="Processing Utilization"
            value={`${Math.round((wholesale.animalsPerMonth / 20) * 100)}%`}
            subtitle="20 head capacity"
          />
          <MetricCard
            label="Combo Advantage"
            value={`+${formatCurrency(comboAdvantage.vsAllGround)}`}
            subtitle="Per animal vs all ground"
            status="green"
          />
        </div>

        {/* Box Capacity Calculator */}
        <div className="bg-[var(--color-secondary-bg)] rounded-lg p-5">
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-4">
            Box Production Capacity (Monthly)
          </h4>
          <p className="text-sm text-[var(--color-text-secondary)] mb-4">
            Given {formatNumber(premiumForCaldera, 0)} lbs premium, {formatNumber(ultraPremiumForCaldera, 0)} lbs ultra premium, and {formatNumber(groundForCaldera, 0)} lbs ground allocated to Caldera:
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {boxCapacity.map(({ boxType, capacity }) => (
              <div key={boxType.name} className="p-3 bg-[var(--color-primary-bg)] rounded">
                <div className="text-2xl font-bold text-[var(--color-text-primary)]">{capacity}</div>
                <div className="text-sm font-medium text-[var(--color-text-primary)]">{boxType.name}</div>
                <div className="text-xs text-[var(--color-text-secondary)]">{boxType.description}</div>
                <div className="text-xs text-[var(--color-success)] mt-1">{formatCurrency(boxType.price)} each</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Helper Components

interface ChannelAllocationControlProps {
  label: string;
  allocation: ChannelAllocation;
  onChange: (channel: keyof ChannelAllocation, value: number) => void;
}

function ChannelAllocationControl({ label, allocation, onChange }: ChannelAllocationControlProps) {
  const channels: { key: keyof ChannelAllocation; label: string }[] = [
    { key: 'wholesale', label: 'Wholesale' },
    { key: 'retail', label: 'Retail' },
    { key: 'online', label: 'Online' },
    { key: 'caldera', label: 'Caldera' },
  ];

  return (
    <div className="mb-4 p-3 bg-[var(--color-primary-bg)] rounded">
      <div className="text-sm font-medium text-[var(--color-text-primary)] mb-2">{label}</div>
      <div className="space-y-2">
        {channels.map(({ key, label: channelLabel }) => (
          <div key={key} className="flex items-center gap-2">
            <span className="text-xs text-[var(--color-text-secondary)] w-16">{channelLabel}</span>
            <input
              type="range"
              min={0}
              max={100}
              value={allocation[key]}
              onChange={(e) => onChange(key, parseInt(e.target.value))}
              className="flex-1"
            />
            <span className="text-xs text-[var(--color-text-primary)] w-10 text-right">{allocation[key]}%</span>
          </div>
        ))}
      </div>
      <div className="text-xs text-[var(--color-text-secondary)] mt-2 text-right">
        Total: {Object.values(allocation).reduce((a, b) => a + b, 0)}%
      </div>
    </div>
  );
}

interface ScenarioBarProps {
  label: string;
  value: number;
  maxValue: number;
  color: string;
  highlight?: boolean;
}

function ScenarioBar({ label, value, maxValue, color, highlight }: ScenarioBarProps) {
  const width = (value / maxValue) * 100;

  return (
    <div className={`${highlight ? 'p-2 bg-[var(--color-primary-bg)] rounded' : ''}`}>
      <div className="flex justify-between text-sm mb-1">
        <span className={`${highlight ? 'font-medium text-[var(--color-text-primary)]' : 'text-[var(--color-text-secondary)]'}`}>
          {label}
        </span>
        <span className={`font-medium ${highlight ? 'text-[var(--color-success)]' : ''}`}>
          {formatCurrency(value)}
        </span>
      </div>
      <div className="h-4 bg-[var(--color-accent)] rounded overflow-hidden">
        <div
          className="h-full rounded transition-all duration-300"
          style={{ width: `${width}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

interface YieldRowProps {
  label: string;
  pounds: number;
  revenue: number;
  color: string;
}

function YieldRow({ label, pounds, revenue, color }: YieldRowProps) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-3 h-3 rounded" style={{ backgroundColor: color }} />
      <span className="text-sm text-[var(--color-text-secondary)] flex-1">{label}</span>
      <span className="text-sm text-[var(--color-text-primary)]">{formatNumber(pounds, 0)} lbs</span>
      <span className="text-sm text-[var(--color-success)] w-20 text-right">{formatCurrency(revenue)}</span>
    </div>
  );
}

interface ChannelRowProps {
  label: string;
  revenue: number;
}

function ChannelRow({ label, revenue }: ChannelRowProps) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-[var(--color-text-secondary)]">{label}</span>
      <span className="text-[var(--color-text-primary)] font-medium">{formatCurrency(revenue)}</span>
    </div>
  );
}
