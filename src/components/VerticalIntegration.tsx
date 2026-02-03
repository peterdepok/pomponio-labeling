import { useState, useEffect } from 'react';
import type { WholesaleState } from '../types';
import { formatCurrency, formatNumber } from '../utils/calculations';
import {
  calculateWholesaleOutputs,
  calculateComboAdvantage,
  calculateProcessingUtilization,
} from '../utils/wholesaleCalculations';
import { MetricCard } from './shared';

interface VerticalIntegrationProps {
  wholesale: WholesaleState;
}

export function VerticalIntegration({ wholesale }: VerticalIntegrationProps) {
  const [monthsInactive, setMonthsInactive] = useState(2);
  const [runningCost, setRunningCost] = useState(0);

  const wholesaleOutputs = calculateWholesaleOutputs(wholesale);
  const comboAdvantage = calculateComboAdvantage(wholesaleOutputs.scenarioProfit);
  const processingUtilization = calculateProcessingUtilization(wholesale.animalsPerMonth);

  // Calculate opportunity cost based on actual wholesale data
  const monthlyOpportunityCost = Math.round(
    (wholesaleOutputs.scenarioProfit.combo - wholesaleOutputs.scenarioProfit.allGround) *
    (20 - wholesale.animalsPerMonth) * 0.5 // Unused capacity value
  );

  // Running counter effect
  useEffect(() => {
    const totalCost = monthlyOpportunityCost * monthsInactive;
    const interval = setInterval(() => {
      setRunningCost(prev => {
        const increment = monthlyOpportunityCost / 30 / 24 / 60;
        const newValue = prev + increment;
        return newValue > totalCost ? totalCost : newValue;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [monthlyOpportunityCost, monthsInactive]);

  useEffect(() => {
    setRunningCost(monthlyOpportunityCost * monthsInactive * 0.9);
  }, [wholesale.animalsPerMonth, monthsInactive, monthlyOpportunityCost]);

  // Calculate ground going to wholesale
  const groundToWholesale = wholesaleOutputs.poundsPerCategory.ground * (wholesale.channelAllocation.ground.wholesale / 100);

  return (
    <div className="h-full overflow-y-auto">
      {/* Strategic Context Header */}
      <div className="bg-[var(--color-secondary-bg)] rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold mb-3 text-[var(--color-text-primary)]">Strategic Context</h3>
        <p className="text-[var(--color-text-secondary)] leading-relaxed">
          The wholesale program is not a separate initiative. It is the volume engine that makes Caldera
          subscription economics viable. By moving ground beef through wholesale accounts, Sinton & Sons
          can stock premium cuts for retail and subscription channels at full margin. The combo model yields{' '}
          <span className="text-[var(--color-success)] font-semibold">{formatCurrency(wholesaleOutputs.scenarioProfit.combo)}</span>{' '}
          net per animal versus {formatCurrency(wholesaleOutputs.scenarioProfit.allGround)} for all ground.
          This <span className="text-[var(--color-success)] font-semibold">{formatNumber(comboAdvantage.multiplier, 1)}x</span> improvement
          is the foundation of the multi-channel strategy.
        </p>
      </div>

      {/* Live Wholesale Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        <MetricCard
          label="Processing Utilization"
          value={`${processingUtilization}%`}
          subtitle={`${wholesale.animalsPerMonth}/20 capacity`}
          status={processingUtilization >= 50 ? 'green' : processingUtilization >= 25 ? 'yellow' : 'red'}
        />
        <MetricCard
          label="Ground Wholesale Revenue"
          value={formatCurrency(wholesaleOutputs.revenueByChannel.wholesale * wholesale.animalsPerMonth)}
          subtitle="Monthly"
        />
        <MetricCard
          label="Premium Cut Inventory"
          value={`${wholesaleOutputs.premiumCutsForCaldera} lbs`}
          subtitle="For retail/subscription"
          status={wholesaleOutputs.premiumCutsForCaldera >= 50 ? 'green' : wholesaleOutputs.premiumCutsForCaldera >= 25 ? 'yellow' : 'red'}
        />
        <MetricCard
          label="Combo Model Advantage"
          value={`+${formatCurrency(comboAdvantage.vsAllGround)}`}
          subtitle={`${formatNumber(comboAdvantage.multiplier, 1)}x multiplier`}
          status="green"
        />
        <MetricCard
          label="Wholesale Accounts"
          value={wholesaleOutputs.wholesaleAccountsRequired.toString()}
          subtitle="Required at 500 lbs/wk"
          status={wholesaleOutputs.wholesaleAccountsRequired <= 2 ? 'green' : 'yellow'}
        />
      </div>

      {/* Opportunity Cost Counter */}
      <div className="bg-gradient-to-r from-[var(--color-danger)] to-[var(--color-warning)] bg-opacity-20 rounded-lg p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">Cost of Inaction</h3>
            <p className="text-sm text-[var(--color-text-secondary)]">
              Value lost from unused processing capacity since December launch
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-[var(--color-danger)]">
              {formatCurrency(runningCost)}
            </div>
            <div className="text-sm text-[var(--color-text-secondary)]">
              {formatCurrency(monthlyOpportunityCost)}/month at current volume
            </div>
          </div>
        </div>

        <div className="mt-4">
          <label className="text-sm text-[var(--color-text-secondary)] block mb-1">
            Months Since Launch
          </label>
          <input
            type="number"
            min="1"
            max="12"
            value={monthsInactive}
            onChange={e => setMonthsInactive(parseInt(e.target.value) || 1)}
            className="w-24"
          />
        </div>
      </div>

      {/* Wholesale Program Status */}
      <h3 className="text-lg font-semibold mb-4 text-[var(--color-text-primary)]">Wholesale Program Status</h3>
      <div className="bg-[var(--color-secondary-bg)] rounded-lg overflow-hidden mb-8">
        <table className="w-full">
          <thead>
            <tr className="bg-[var(--color-primary-bg)]">
              <th className="text-left p-4 text-sm text-[var(--color-text-secondary)] font-medium">Metric</th>
              <th className="text-left p-4 text-sm text-[var(--color-text-secondary)] font-medium">Current Value</th>
              <th className="text-left p-4 text-sm text-[var(--color-text-secondary)] font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td className="p-4 text-[var(--color-text-primary)] font-medium">Animals Processed/Month</td>
              <td className="p-4 text-[var(--color-text-primary)]">{wholesale.animalsPerMonth}</td>
              <td className="p-4">
                <StatusIndicator status={wholesale.animalsPerMonth >= 5 ? 'green' : wholesale.animalsPerMonth >= 3 ? 'yellow' : 'red'} />
              </td>
            </tr>
            <tr className="bg-[var(--color-primary-bg)] bg-opacity-50">
              <td className="p-4 text-[var(--color-text-primary)] font-medium">Ground to Wholesale</td>
              <td className="p-4 text-[var(--color-text-primary)]">{formatNumber(groundToWholesale, 0)} lbs/mo</td>
              <td className="p-4">
                <StatusIndicator status={groundToWholesale >= 2000 ? 'green' : groundToWholesale >= 1000 ? 'yellow' : 'red'} />
              </td>
            </tr>
            <tr>
              <td className="p-4 text-[var(--color-text-primary)] font-medium">Premium Inventory Available</td>
              <td className="p-4 text-[var(--color-text-primary)]">{wholesaleOutputs.premiumCutsForCaldera} lbs/mo</td>
              <td className="p-4">
                <StatusIndicator status={wholesaleOutputs.premiumCutsForCaldera >= 50 ? 'green' : wholesaleOutputs.premiumCutsForCaldera >= 25 ? 'yellow' : 'red'} />
              </td>
            </tr>
            <tr className="bg-[var(--color-primary-bg)] bg-opacity-50">
              <td className="p-4 text-[var(--color-text-primary)] font-medium">Net Profit/Animal</td>
              <td className="p-4 text-[var(--color-text-primary)]">{formatCurrency(wholesaleOutputs.scenarioProfit.combo)}</td>
              <td className="p-4">
                <StatusIndicator status={wholesaleOutputs.scenarioProfit.combo >= 1500 ? 'green' : wholesaleOutputs.scenarioProfit.combo >= 1000 ? 'yellow' : 'red'} />
              </td>
            </tr>
            <tr>
              <td className="p-4 text-[var(--color-text-primary)] font-medium">Monthly Net Profit</td>
              <td className="p-4 text-[var(--color-text-primary)]">{formatCurrency(wholesaleOutputs.monthlyNetProfit)}</td>
              <td className="p-4">
                <StatusIndicator status={wholesaleOutputs.monthlyNetProfit >= 10000 ? 'green' : wholesaleOutputs.monthlyNetProfit >= 5000 ? 'yellow' : 'red'} />
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Synergy View */}
      <h3 className="text-lg font-semibold mb-4 text-[var(--color-text-primary)]">Wholesale Enables Subscription</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Without Wholesale */}
        <div className="bg-[var(--color-secondary-bg)] rounded-lg p-5 border-l-4 border-[var(--color-danger)]">
          <h4 className="text-sm font-medium text-[var(--color-danger)] uppercase tracking-wide mb-3">
            Without Wholesale Program
          </h4>
          <ul className="space-y-2 text-sm text-[var(--color-text-secondary)]">
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-danger)]">✕</span>
              Limited premium inventory, must sell entire animal through one channel
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-danger)]">✕</span>
              Ground beef sits unsold or gets deeply discounted
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-danger)]">✕</span>
              Risk of stockouts on popular cuts for subscription boxes
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-danger)]">✕</span>
              Net profit per animal: {formatCurrency(wholesaleOutputs.scenarioProfit.allGround)}
            </li>
          </ul>
        </div>

        {/* With Wholesale */}
        <div className="bg-[var(--color-secondary-bg)] rounded-lg p-5 border-l-4 border-[var(--color-success)]">
          <h4 className="text-sm font-medium text-[var(--color-success)] uppercase tracking-wide mb-3">
            With Wholesale Program
          </h4>
          <ul className="space-y-2 text-sm text-[var(--color-text-secondary)]">
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-success)]">✓</span>
              Ground beef monetized through wholesale accounts at consistent volume
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-success)]">✓</span>
              Premium cuts available for retail and subscription at full margin
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-success)]">✓</span>
              Flexible box composition, can offer premium everything boxes
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[var(--color-success)]">✓</span>
              Net profit per animal: {formatCurrency(wholesaleOutputs.scenarioProfit.combo)}
            </li>
          </ul>
        </div>
      </div>

      {/* Investment Reframe */}
      <div className="bg-[var(--color-secondary-bg)] rounded-lg p-6 border-l-4 border-[var(--color-success)]">
        <h4 className="text-lg font-semibold mb-3 text-[var(--color-text-primary)]">Investment Reframe</h4>
        <div className="space-y-4 text-[var(--color-text-secondary)]">
          <p>
            <strong className="text-[var(--color-text-primary)]">Traditional View:</strong> $5,000/month marketing spend is venture risk on an unproven DTC brand.
          </p>
          <p>
            <strong className="text-[var(--color-text-primary)]">Integrated View:</strong> $5,000/month is channel activation cost for existing infrastructure.
            The wholesale program generates {formatCurrency(wholesaleOutputs.monthlyNetProfit)}/month in net profit while
            providing {wholesaleOutputs.premiumCutsForCaldera} lbs of premium cuts for Caldera boxes.
          </p>
          <p>
            <strong className="text-[var(--color-text-primary)]">Net Position:</strong> Marketing spend is funded by wholesale revenue.
            Each wholesale account secured reduces Caldera's effective customer acquisition cost by making premium inventory available
            at marginal cost rather than standalone unit economics.
          </p>
        </div>
      </div>

      {/* Sourcing Relationships */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[var(--color-secondary-bg)] rounded-lg p-5">
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-3">
            Active Sourcing Relationships
          </h4>
          <ul className="space-y-2">
            <li className="flex items-center gap-2 text-[var(--color-text-primary)]">
              <span className="w-2 h-2 rounded-full bg-[var(--color-success)]" />
              Avenales Ranch
            </li>
            <li className="flex items-center gap-2 text-[var(--color-text-primary)]">
              <span className="w-2 h-2 rounded-full bg-[var(--color-success)]" />
              Big Bluff Ranch
            </li>
          </ul>
          <p className="text-sm text-[var(--color-text-secondary)] mt-3">
            Volume leverage through wholesale improves purchasing power across all S&S operations.
          </p>
        </div>

        <div className="bg-[var(--color-secondary-bg)] rounded-lg p-5">
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-3">
            Wholesale Reference: Carmen Ranch
          </h4>
          <div className="text-lg font-bold text-[var(--color-text-primary)] mb-2">
            35 head/week
          </div>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Corey Carmen processes 35 head/week with majority going to wholesale ground accounts
            in Portland, Seattle, and Eugene markets. Premium cuts sold direct to consumer via
            shares and steak boxes. This model validates the combo approach at scale.
          </p>
        </div>
      </div>
    </div>
  );
}

function StatusIndicator({ status }: { status: 'green' | 'yellow' | 'red' }) {
  const colors = {
    green: 'bg-[var(--color-success)]',
    yellow: 'bg-[var(--color-warning)]',
    red: 'bg-[var(--color-danger)]',
  };

  const labels = {
    green: 'On Track',
    yellow: 'Monitor',
    red: 'Action Needed',
  };

  return (
    <div className="flex items-center gap-2">
      <div className={`w-3 h-3 rounded-full ${colors[status]}`} />
      <span className="text-sm text-[var(--color-text-secondary)]">{labels[status]}</span>
    </div>
  );
}
