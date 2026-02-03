import type { UnitEconomicsInputs, ScenarioType, WeeklyActual } from '../types';
import {
  generateWeeklyProjections,
  calculateCashFlow,
  calculateRunningCac,
  formatCurrency,
} from '../utils/calculations';
import { SCENARIO_CONFIGS } from '../utils/constants';
import { MetricCard, LineChart, AreaChart } from './shared';

interface TestModelerProps {
  scenario: ScenarioType;
  unitEconomics: UnitEconomicsInputs;
  cashPosition: number;
  actuals: WeeklyActual[];
  onScenarioChange: (scenario: ScenarioType) => void;
  onActualsChange: (actuals: WeeklyActual[]) => void;
  onCashPositionChange: (cash: number) => void;
}

export function TestModeler({
  scenario,
  unitEconomics,
  cashPosition,
  actuals,
  onScenarioChange,
  onActualsChange,
  onCashPositionChange,
}: TestModelerProps) {
  const config = SCENARIO_CONFIGS[scenario];

  // Generate projections for all scenarios
  const conservativeProjections = generateWeeklyProjections(SCENARIO_CONFIGS.conservative);
  const baseProjections = generateWeeklyProjections(SCENARIO_CONFIGS.base);
  const aggressiveProjections = generateWeeklyProjections(SCENARIO_CONFIGS.aggressive);

  // Cash flow for selected scenario
  const cashFlow = calculateCashFlow(cashPosition, config, unitEconomics);

  // Calculate actuals metrics
  const totalActualSubs = actuals.reduce((sum, a) => sum + a.subscribers, 0);
  const totalActualSpend = actuals.reduce((sum, a) => sum + a.spend, 0);
  const runningCac = calculateRunningCac(actuals);

  // Week labels
  const weekLabels = Array.from({ length: 12 }, (_, i) => `W${i + 1}`);

  // Prepare subscriber chart data
  const subscriberChartData = [
    { label: 'Conservative', values: conservativeProjections, color: 'var(--color-text-secondary)' },
    { label: 'Base Case', values: baseProjections, color: 'var(--color-warning)' },
    { label: 'Aggressive', values: aggressiveProjections, color: 'var(--color-success)' },
  ];

  // Add actuals if present
  if (actuals.length > 0) {
    const actualValues = actuals.map((_, i) => {
      const cumulative = actuals.slice(0, i + 1).reduce((sum, a) => sum + a.subscribers, 0) + 1;
      return cumulative;
    });
    // Pad with nulls to match length (we will handle rendering)
    while (actualValues.length < 12) {
      actualValues.push(actualValues[actualValues.length - 1] || 1);
    }
    subscriberChartData.push({
      label: 'Actual',
      values: actualValues,
      color: 'var(--color-danger)',
    });
  }

  // Cash flow chart data
  const cashChartData = [
    { label: 'Cash Position', values: cashFlow.map(cf => cf.cash), color: 'var(--color-success)' },
  ];

  const handleActualChange = (week: number, field: keyof WeeklyActual, value: number) => {
    const newActuals = [...actuals];
    const existingIndex = newActuals.findIndex(a => a.week === week);

    if (existingIndex >= 0) {
      newActuals[existingIndex] = { ...newActuals[existingIndex], [field]: value };
    } else {
      newActuals.push({
        week,
        subscribers: field === 'subscribers' ? value : 0,
        spend: field === 'spend' ? value : 0,
        revenue: field === 'revenue' ? value : 0,
      });
      newActuals.sort((a, b) => a.week - b.week);
    }

    onActualsChange(newActuals);
  };

  const getActualValue = (week: number, field: keyof WeeklyActual): number => {
    const actual = actuals.find(a => a.week === week);
    return actual ? actual[field] : 0;
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 h-full">
      {/* Sidebar Controls */}
      <div className="lg:w-80 flex-shrink-0 bg-[var(--color-secondary-bg)] rounded-lg p-4 overflow-y-auto">
        <h3 className="text-lg font-semibold mb-4 text-[var(--color-text-primary)]">Scenario Configuration</h3>

        {/* Scenario Selector */}
        <div className="mb-6">
          <label className="text-sm text-[var(--color-text-secondary)] block mb-2">Select Scenario</label>
          <div className="flex gap-2">
            {(['conservative', 'base', 'aggressive'] as const).map(s => (
              <button
                key={s}
                onClick={() => onScenarioChange(s)}
                className={`flex-1 py-2 px-3 rounded text-sm capitalize transition-colors ${
                  scenario === s
                    ? 'bg-[var(--color-accent)] text-[var(--color-text-primary)]'
                    : 'bg-[var(--color-primary-bg)] text-[var(--color-text-secondary)] hover:bg-[var(--color-accent)]'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Scenario Details */}
        <div className="mb-6 p-3 bg-[var(--color-primary-bg)] rounded">
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
            {scenario.charAt(0).toUpperCase() + scenario.slice(1)} Parameters
          </h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-[var(--color-text-secondary)]">Creative/mo</span>
              <span>{formatCurrency(config.monthlyCreativeSpend)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-text-secondary)]">Ad Spend/mo</span>
              <span>{formatCurrency(config.monthlyAdSpend)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-text-secondary)]">Effective CAC</span>
              <span>{formatCurrency(config.effectiveCac)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-[var(--color-text-secondary)]">90 Day Target</span>
              <span>{config.totalSubs} subs</span>
            </div>
          </div>
        </div>

        {/* Starting Cash */}
        <div className="mb-6">
          <label className="text-sm text-[var(--color-text-secondary)] block mb-2">Starting Cash Position</label>
          <input
            type="number"
            value={cashPosition}
            onChange={e => onCashPositionChange(parseFloat(e.target.value) || 0)}
            className="w-full"
          />
        </div>

        {/* Actuals Entry */}
        <div>
          <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
            Enter Weekly Actuals
          </h4>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {Array.from({ length: 12 }, (_, i) => i + 1).map(week => (
              <div key={week} className="p-2 bg-[var(--color-primary-bg)] rounded">
                <div className="text-xs text-[var(--color-text-secondary)] mb-1">Week {week}</div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs text-[var(--color-text-secondary)]">New Subs</label>
                    <input
                      type="number"
                      value={getActualValue(week, 'subscribers') || ''}
                      onChange={e => handleActualChange(week, 'subscribers', parseInt(e.target.value) || 0)}
                      className="w-full text-sm"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-[var(--color-text-secondary)]">Spend</label>
                    <input
                      type="number"
                      value={getActualValue(week, 'spend') || ''}
                      onChange={e => handleActualChange(week, 'spend', parseFloat(e.target.value) || 0)}
                      className="w-full text-sm"
                      placeholder="0"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        {/* Summary Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard
            label="90 Day Target"
            value={`${config.totalSubs} subs`}
            subtitle={`${formatCurrency(config.monthlyCreativeSpend + config.monthlyAdSpend)}/mo spend`}
          />
          <MetricCard
            label="Total Investment"
            value={formatCurrency((config.monthlyCreativeSpend + config.monthlyAdSpend) * 3)}
            subtitle="Over 90 days"
          />
          <MetricCard
            label="Actual Subscribers"
            value={`${totalActualSubs + 1}`}
            subtitle={actuals.length > 0 ? `${actuals.length} weeks tracked` : 'No actuals entered'}
            status={totalActualSubs >= config.totalSubs * (actuals.length / 12) ? 'green' : 'yellow'}
          />
          <MetricCard
            label="Running CAC"
            value={runningCac > 0 ? formatCurrency(runningCac) : 'N/A'}
            subtitle={totalActualSpend > 0 ? `${formatCurrency(totalActualSpend)} spent` : 'Enter actuals'}
            status={runningCac === 0 ? 'neutral' : runningCac <= config.effectiveCac ? 'green' : runningCac <= config.effectiveCac * 1.5 ? 'yellow' : 'red'}
          />
        </div>

        {/* Charts */}
        <div className="space-y-6">
          {/* Subscriber Growth */}
          <div>
            <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
              Subscriber Growth Projections
            </h4>
            <LineChart
              data={subscriberChartData}
              xLabels={weekLabels}
              height={220}
              yFormat={v => Math.round(v).toString()}
            />
          </div>

          {/* Cash Position */}
          <div>
            <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
              Cash Position ({scenario} scenario)
            </h4>
            <AreaChart
              data={cashChartData}
              xLabels={weekLabels}
              height={200}
              yFormat={v => `$${(v / 1000).toFixed(0)}K`}
              showThreshold={{ value: 20000, label: 'Min threshold' }}
            />
          </div>

          {/* Weekly Breakdown Table */}
          <div>
            <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
              Weekly Cash Flow Projection
            </h4>
            <div className="bg-[var(--color-secondary-bg)] rounded-lg overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[var(--color-accent)]">
                    <th className="text-left p-3 text-[var(--color-text-secondary)]">Week</th>
                    <th className="text-right p-3 text-[var(--color-text-secondary)]">Spend</th>
                    <th className="text-right p-3 text-[var(--color-text-secondary)]">Revenue</th>
                    <th className="text-right p-3 text-[var(--color-text-secondary)]">Cash</th>
                  </tr>
                </thead>
                <tbody>
                  {cashFlow.map(cf => (
                    <tr key={cf.week} className="border-b border-[var(--color-accent)] border-opacity-30">
                      <td className="p-3">Week {cf.week}</td>
                      <td className="p-3 text-right text-[var(--color-danger)]">
                        {formatCurrency(cf.spend)}
                      </td>
                      <td className="p-3 text-right text-[var(--color-success)]">
                        {formatCurrency(cf.revenue)}
                      </td>
                      <td className={`p-3 text-right font-medium ${cf.cash < 20000 ? 'text-[var(--color-danger)]' : ''}`}>
                        {formatCurrency(cf.cash)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
