import { useState, useEffect } from 'react';
import { calculateOpportunityCost, formatCurrency } from '../utils/calculations';
import { INFRASTRUCTURE_ASSETS } from '../utils/constants';
import { MetricCard } from './shared';

export function VerticalIntegration() {
  const [processingUtilization, setProcessingUtilization] = useState(60);
  const [monthsInactive, setMonthsInactive] = useState(2);
  const [runningCost, setRunningCost] = useState(0);

  const opportunityCost = calculateOpportunityCost(processingUtilization);

  // Running counter effect
  useEffect(() => {
    const totalCost = opportunityCost.totalMonthly * monthsInactive;
    const interval = setInterval(() => {
      setRunningCost(prev => {
        const increment = opportunityCost.totalMonthly / 30 / 24 / 60; // Cost per minute
        const newValue = prev + increment;
        return newValue > totalCost ? totalCost : newValue;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [opportunityCost.totalMonthly, monthsInactive]);

  // Reset counter when utilization changes
  useEffect(() => {
    setRunningCost(opportunityCost.totalMonthly * monthsInactive * 0.9);
  }, [processingUtilization, monthsInactive, opportunityCost.totalMonthly]);

  return (
    <div className="h-full overflow-y-auto">
      {/* Strategic Context Header */}
      <div className="bg-[var(--color-secondary-bg)] rounded-lg p-6 mb-6">
        <h3 className="text-lg font-semibold mb-3 text-[var(--color-text-primary)]">Strategic Context</h3>
        <p className="text-[var(--color-text-secondary)] leading-relaxed">
          Caldera is not a standalone venture seeking product market fit. It is a channel that monetizes
          existing Sinton & Sons infrastructure: processing capacity, sourcing relationships, retail traffic,
          and brand equity. The marginal economics favor action; processing and inventory costs are sunk.
          Every month without subscribers is wasted capacity.
        </p>
      </div>

      {/* Opportunity Cost Counter */}
      <div className="bg-gradient-to-r from-[var(--color-danger)] to-[var(--color-warning)] bg-opacity-20 rounded-lg p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-[var(--color-text-primary)]">Cost of Inaction</h3>
            <p className="text-sm text-[var(--color-text-secondary)]">
              Accumulated opportunity cost since December launch
            </p>
          </div>
          <div className="text-right">
            <div className="text-4xl font-bold text-[var(--color-danger)]">
              {formatCurrency(runningCost)}
            </div>
            <div className="text-sm text-[var(--color-text-secondary)]">
              {formatCurrency(opportunityCost.totalMonthly)}/month wasted
            </div>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4">
          <div>
            <label className="text-sm text-[var(--color-text-secondary)] block mb-1">
              Processing Utilization
            </label>
            <input
              type="range"
              min="30"
              max="90"
              value={processingUtilization}
              onChange={e => setProcessingUtilization(parseInt(e.target.value))}
              className="w-full"
            />
            <div className="text-sm text-[var(--color-text-primary)]">{processingUtilization}%</div>
          </div>
          <div>
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
      </div>

      {/* Cost Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <MetricCard
          label="Wasted Processing Capacity"
          value={formatCurrency(opportunityCost.wastedCapacity)}
          subtitle="Per month"
          status="red"
        />
        <MetricCard
          label="Inventory Carrying Cost"
          value={formatCurrency(opportunityCost.inventoryCost)}
          subtitle="Per month"
          status="yellow"
        />
        <MetricCard
          label="Total Monthly Opportunity Cost"
          value={formatCurrency(opportunityCost.totalMonthly)}
          subtitle="Recoverable with Caldera"
          status="red"
        />
      </div>

      {/* Infrastructure Assets Table */}
      <h3 className="text-lg font-semibold mb-4 text-[var(--color-text-primary)]">Infrastructure Assets</h3>
      <div className="bg-[var(--color-secondary-bg)] rounded-lg overflow-hidden mb-8">
        <table className="w-full">
          <thead>
            <tr className="bg-[var(--color-primary-bg)]">
              <th className="text-left p-4 text-sm text-[var(--color-text-secondary)] font-medium">Asset</th>
              <th className="text-left p-4 text-sm text-[var(--color-text-secondary)] font-medium">Current Utilization</th>
              <th className="text-left p-4 text-sm text-[var(--color-text-secondary)] font-medium">Caldera Contribution</th>
              <th className="text-left p-4 text-sm text-[var(--color-text-secondary)] font-medium">Value Unlocked</th>
            </tr>
          </thead>
          <tbody>
            {INFRASTRUCTURE_ASSETS.map((asset, index) => (
              <tr key={asset.name} className={index % 2 === 0 ? '' : 'bg-[var(--color-primary-bg)] bg-opacity-50'}>
                <td className="p-4 text-[var(--color-text-primary)] font-medium">{asset.name}</td>
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <div className="w-24 h-2 bg-[var(--color-accent)] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[var(--color-success)]"
                        style={{ width: `${asset.currentUtilization}%` }}
                      />
                    </div>
                    <span className="text-sm text-[var(--color-text-secondary)]">
                      {asset.currentUtilization}%
                    </span>
                  </div>
                </td>
                <td className="p-4 text-[var(--color-text-secondary)]">{asset.calderaContribution}</td>
                <td className="p-4 text-[var(--color-success)]">{asset.valueUnlocked}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Reframing Box */}
      <div className="bg-[var(--color-secondary-bg)] rounded-lg p-6 border-l-4 border-[var(--color-success)]">
        <h4 className="text-lg font-semibold mb-3 text-[var(--color-text-primary)]">Investment Reframe</h4>
        <div className="space-y-4 text-[var(--color-text-secondary)]">
          <p>
            <strong className="text-[var(--color-text-primary)]">Traditional View:</strong> $5,000/month marketing spend is venture risk on an unproven DTC brand.
          </p>
          <p>
            <strong className="text-[var(--color-text-primary)]">Integrated View:</strong> $5,000/month is channel activation cost for existing infrastructure
            already generating {formatCurrency(opportunityCost.totalMonthly)}/month in opportunity cost through underutilization.
          </p>
          <p>
            <strong className="text-[var(--color-text-primary)]">Net Position:</strong> At current utilization levels, marketing investment is partially
            offset by capacity utilization gains. Break even on opportunity cost alone requires approximately
            {Math.ceil(opportunityCost.totalMonthly / 28)} subscribers per month.
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
            Volume leverage through Caldera improves purchasing power across all S&S operations.
          </p>
        </div>

        <div className="bg-[var(--color-secondary-bg)] rounded-lg p-5">
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-3">
            Byproduct Monetization Opportunity
          </h4>
          <div className="text-2xl font-bold text-[var(--color-warning)] mb-2">
            $1,500 - $2,000/mo
          </div>
          <p className="text-sm text-[var(--color-text-secondary)]">
            Current bone/byproduct disposal cost that could become revenue stream through
            bone broth, pet treats, or rendering partnerships enabled by Caldera volume.
          </p>
        </div>
      </div>
    </div>
  );
}
