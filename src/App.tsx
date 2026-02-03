import { useState, useEffect, useCallback } from 'react';
import type { UnitEconomicsInputs, ScenarioType, WeeklyActual, CalderaState, WholesaleState } from './types';
import { DEFAULT_UNIT_ECONOMICS, DEFAULT_CASH_POSITION, DEFAULT_FIXED_MONTHLY_COSTS, DEFAULT_WHOLESALE } from './utils/constants';
import { encodeStateToUrl, decodeStateFromUrl } from './utils/calculations';
import { UnitEconomics, WholesaleProgram, TestModeler, DecisionFramework, VerticalIntegration } from './components';

type TabType = 'economics' | 'wholesale' | 'modeler' | 'framework' | 'integration';

const TABS: { id: TabType; label: string }[] = [
  { id: 'economics', label: 'Unit Economics' },
  { id: 'wholesale', label: 'Wholesale Program' },
  { id: 'modeler', label: '90 Day Test' },
  { id: 'framework', label: 'Decision Framework' },
  { id: 'integration', label: 'Vertical Integration' },
];

function App() {
  const [activeTab, setActiveTab] = useState<TabType>('economics');
  const [unitEconomics, setUnitEconomics] = useState<UnitEconomicsInputs>(DEFAULT_UNIT_ECONOMICS);
  const [wholesale, setWholesale] = useState<WholesaleState>(DEFAULT_WHOLESALE);
  const [scenario, setScenario] = useState<ScenarioType>('base');
  const [actuals, setActuals] = useState<WeeklyActual[]>([]);
  const [cashPosition, setCashPosition] = useState(DEFAULT_CASH_POSITION);
  const [fixedMonthlyCosts] = useState(DEFAULT_FIXED_MONTHLY_COSTS);

  // Load state from URL on mount
  useEffect(() => {
    const savedState = decodeStateFromUrl(window.location.search);
    if (savedState) {
      if (savedState.unitEconomics) setUnitEconomics(savedState.unitEconomics);
      if (savedState.wholesale) setWholesale(savedState.wholesale);
      if (savedState.scenario) setScenario(savedState.scenario);
      if (savedState.actuals) setActuals(savedState.actuals);
      if (savedState.cashPosition) setCashPosition(savedState.cashPosition);
    }
  }, []);

  // Update URL when state changes (debounced)
  const updateUrl = useCallback(() => {
    const state: CalderaState = {
      unitEconomics,
      wholesale,
      scenario,
      actuals,
      cashPosition,
      fixedMonthlyCosts,
    };
    const encoded = encodeStateToUrl(state);
    window.history.replaceState(null, '', `?${encoded}`);
  }, [unitEconomics, wholesale, scenario, actuals, cashPosition, fixedMonthlyCosts]);

  useEffect(() => {
    const timeout = setTimeout(updateUrl, 500);
    return () => clearTimeout(timeout);
  }, [updateUrl]);

  const handleUnitEconomicsChange = (key: keyof UnitEconomicsInputs, value: number) => {
    setUnitEconomics(prev => ({ ...prev, [key]: value }));
  };

  const handleCopyShareLink = () => {
    navigator.clipboard.writeText(window.location.href);
    alert('Link copied to clipboard');
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="h-16 bg-[var(--color-secondary-bg)] border-b border-[var(--color-accent)] flex items-center justify-between px-6 flex-shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-[var(--color-text-primary)]">Caldera Decision Engine</h1>
          <span className="text-sm text-[var(--color-text-secondary)]">Sinton & Sons</span>
        </div>

        <div className="flex items-center gap-4">
          {/* Tab Navigation */}
          <nav className="hidden lg:flex gap-1">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-2 rounded text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'bg-[var(--color-accent)] text-[var(--color-text-primary)]'
                    : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-accent)] hover:bg-opacity-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>

          {/* Share Button */}
          <button
            onClick={handleCopyShareLink}
            className="px-3 py-1.5 text-sm bg-[var(--color-accent)] text-[var(--color-text-primary)] rounded hover:bg-opacity-80 transition-colors"
          >
            Share
          </button>
        </div>
      </header>

      {/* Mobile Tab Navigation */}
      <div className="lg:hidden bg-[var(--color-secondary-bg)] border-b border-[var(--color-accent)] p-2 flex gap-1 overflow-x-auto">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-2 rounded text-sm whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? 'bg-[var(--color-accent)] text-[var(--color-text-primary)]'
                : 'text-[var(--color-text-secondary)]'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Main Content */}
      <main className="flex-1 p-6 overflow-hidden">
        {activeTab === 'economics' && (
          <UnitEconomics
            inputs={unitEconomics}
            fixedMonthlyCosts={fixedMonthlyCosts}
            wholesale={wholesale}
            onInputChange={handleUnitEconomicsChange}
          />
        )}
        {activeTab === 'wholesale' && (
          <WholesaleProgram
            wholesale={wholesale}
            onWholesaleChange={setWholesale}
          />
        )}
        {activeTab === 'modeler' && (
          <TestModeler
            scenario={scenario}
            unitEconomics={unitEconomics}
            cashPosition={cashPosition}
            actuals={actuals}
            onScenarioChange={setScenario}
            onActualsChange={setActuals}
            onCashPositionChange={setCashPosition}
          />
        )}
        {activeTab === 'framework' && (
          <DecisionFramework
            actuals={actuals}
            unitEconomics={unitEconomics}
            wholesale={wholesale}
          />
        )}
        {activeTab === 'integration' && (
          <VerticalIntegration wholesale={wholesale} />
        )}
      </main>

      {/* Footer */}
      <footer className="h-10 bg-[var(--color-secondary-bg)] border-t border-[var(--color-accent)] flex items-center justify-between px-6 text-xs text-[var(--color-text-secondary)] flex-shrink-0">
        <span>Caldera Decision Engine v1.1</span>
        <span>Westco / Sinton & Sons</span>
      </footer>
    </div>
  );
}

export default App;
