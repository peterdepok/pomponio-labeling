import type { UnitEconomicsInputs, WeeklyActual } from '../types';
import {
  evaluateMilestoneStatus,
  generateRecommendation,
  formatCurrency,
} from '../utils/calculations';
import { MILESTONES } from '../utils/constants';
import { TrafficLight, MetricCard } from './shared';

interface DecisionFrameworkProps {
  actuals: WeeklyActual[];
  unitEconomics: UnitEconomicsInputs;
}

export function DecisionFramework({ actuals, unitEconomics }: DecisionFrameworkProps) {
  const milestoneStatuses = evaluateMilestoneStatus(actuals, unitEconomics);
  const recommendation = generateRecommendation(milestoneStatuses);

  const totalSubs = actuals.reduce((sum, a) => sum + a.subscribers, 0) + 1;
  const totalSpend = actuals.reduce((sum, a) => sum + a.spend, 0);
  const runningCac = totalSubs > 1 ? totalSpend / (totalSubs - 1) : 0;

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'green':
        return 'On Track';
      case 'yellow':
        return 'Monitor';
      case 'red':
        return 'Kill Trigger';
      default:
        return 'Pending';
    }
  };

  return (
    <div className="h-full overflow-y-auto">
      {/* Current Status Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricCard
          label="Current Subscribers"
          value={totalSubs.toString()}
          subtitle={actuals.length > 0 ? `Week ${actuals.length}` : 'No data'}
        />
        <MetricCard
          label="Total Spend"
          value={formatCurrency(totalSpend)}
          subtitle={actuals.length > 0 ? `${actuals.length} weeks` : 'No spend tracked'}
        />
        <MetricCard
          label="Running CAC"
          value={runningCac > 0 ? formatCurrency(runningCac) : 'N/A'}
          subtitle={runningCac > 0 ? `Target: ${formatCurrency(unitEconomics.cac)}` : 'Enter actuals'}
          status={runningCac === 0 ? 'neutral' : runningCac <= unitEconomics.cac ? 'green' : runningCac <= unitEconomics.cac * 1.5 ? 'yellow' : 'red'}
        />
        <MetricCard
          label="Weeks Tracked"
          value={`${actuals.length}/12`}
          subtitle={`${Math.round((actuals.length / 12) * 100)}% complete`}
        />
      </div>

      {/* Milestone Cards */}
      <h3 className="text-lg font-semibold mb-4 text-[var(--color-text-primary)]">Milestone Checkpoints</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {MILESTONES.map((milestone, index) => {
          const status = milestoneStatuses[index];
          const borderColor = {
            green: 'border-[var(--color-success)]',
            yellow: 'border-[var(--color-warning)]',
            red: 'border-[var(--color-danger)]',
            pending: 'border-[var(--color-accent)]',
          }[status.status];

          return (
            <div
              key={milestone.day}
              className={`bg-[var(--color-secondary-bg)] rounded-lg p-5 border-t-4 ${borderColor}`}
            >
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-xl font-bold text-[var(--color-text-primary)]">
                  Day {milestone.day}
                </h4>
                <div className="flex items-center gap-2">
                  <TrafficLight status={status.status} size="large" />
                  <span className="text-sm text-[var(--color-text-secondary)]">
                    {getStatusLabel(status.status)}
                  </span>
                </div>
              </div>

              <div className="space-y-3">
                {/* Targets */}
                <div className="p-3 bg-[var(--color-primary-bg)] rounded">
                  <div className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
                    Targets
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[var(--color-text-secondary)]">Subscribers</span>
                    <span className="text-[var(--color-success)]">{milestone.targetSubs}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[var(--color-text-secondary)]">Max CAC</span>
                    <span className="text-[var(--color-success)]">{formatCurrency(unitEconomics.cac)}</span>
                  </div>
                </div>

                {/* Kill Triggers */}
                <div className="p-3 bg-[var(--color-primary-bg)] rounded">
                  <div className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
                    Kill Triggers
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[var(--color-text-secondary)]">Below subs</span>
                    <span className="text-[var(--color-danger)]">&lt; {milestone.killTriggerSubs}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-[var(--color-text-secondary)]">CAC above</span>
                    <span className="text-[var(--color-danger)]">&gt; {formatCurrency(milestone.killTriggerCac)}</span>
                  </div>
                </div>

                {/* Actuals (if available) */}
                {status.status !== 'pending' && (
                  <div className="p-3 bg-[var(--color-primary-bg)] rounded">
                    <div className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wide mb-2">
                      Actuals
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[var(--color-text-secondary)]">Subscribers</span>
                      <span className={status.actualSubs !== null && status.actualSubs >= milestone.targetSubs ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'}>
                        {status.actualSubs ?? 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-[var(--color-text-secondary)]">CAC</span>
                      <span className={status.actualCac !== null && status.actualCac <= milestone.killTriggerCac ? 'text-[var(--color-success)]' : 'text-[var(--color-warning)]'}>
                        {status.actualCac ? formatCurrency(status.actualCac) : 'N/A'}
                      </span>
                    </div>
                  </div>
                )}

                {/* Decision */}
                <div className="text-xs text-[var(--color-text-secondary)] italic mt-2">
                  Decision: {milestone.decision}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recommendation Engine */}
      <div className="bg-[var(--color-secondary-bg)] rounded-lg p-6">
        <h3 className="text-lg font-semibold mb-3 text-[var(--color-text-primary)]">Recommendation</h3>
        <div className={`p-4 rounded border-l-4 ${
          recommendation.includes('SCALE') ? 'border-[var(--color-success)] bg-[var(--color-success)]' :
          recommendation.includes('PAUSE') ? 'border-[var(--color-danger)] bg-[var(--color-danger)]' :
          recommendation.includes('CONTINUE') ? 'border-[var(--color-warning)] bg-[var(--color-warning)]' :
          'border-[var(--color-accent)] bg-[var(--color-accent)]'
        } bg-opacity-10`}>
          <p className="text-[var(--color-text-primary)]">{recommendation}</p>
        </div>
      </div>

      {/* Decision Logic Reference */}
      <div className="mt-8 p-4 bg-[var(--color-secondary-bg)] rounded-lg">
        <h4 className="text-sm font-medium text-[var(--color-text-secondary)] uppercase tracking-wide mb-3">
          Decision Logic Reference
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-start gap-2">
            <TrafficLight status="green" size="small" />
            <div>
              <span className="text-[var(--color-text-primary)] font-medium">Green</span>
              <p className="text-[var(--color-text-secondary)]">On track or exceeding target. Continue or scale.</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <TrafficLight status="yellow" size="small" />
            <div>
              <span className="text-[var(--color-text-primary)] font-medium">Yellow</span>
              <p className="text-[var(--color-text-secondary)]">Within 20% of target. Enhanced monitoring required.</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <TrafficLight status="red" size="small" />
            <div>
              <span className="text-[var(--color-text-primary)] font-medium">Red</span>
              <p className="text-[var(--color-text-secondary)]">Below kill threshold. Pause and diagnose or terminate.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
