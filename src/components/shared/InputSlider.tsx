import { formatCurrency, formatPercent } from '../../utils/calculations';

interface InputSliderProps {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  format: 'currency' | 'percent' | 'number';
  onChange: (value: number) => void;
}

export function InputSlider({
  label,
  value,
  min,
  max,
  step,
  format,
  onChange,
}: InputSliderProps) {
  const formatValue = (v: number): string => {
    switch (format) {
      case 'currency':
        return formatCurrency(v);
      case 'percent':
        return formatPercent(v);
      default:
        return v.toString();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let newValue = parseFloat(e.target.value);
    if (format === 'percent') {
      newValue = newValue / 100;
    }
    if (!isNaN(newValue)) {
      onChange(Math.max(min, Math.min(max, newValue)));
    }
  };

  const inputValue = format === 'percent' ? value * 100 : value;

  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-1">
        <label className="text-sm text-[var(--color-text-secondary)]">{label}</label>
        <input
          type="number"
          value={format === 'percent' ? (value * 100).toFixed(0) : value}
          onChange={handleInputChange}
          className="w-20 text-right text-sm"
          step={format === 'percent' ? step * 100 : step}
        />
      </div>
      <input
        type="range"
        min={format === 'percent' ? min * 100 : min}
        max={format === 'percent' ? max * 100 : max}
        step={format === 'percent' ? step * 100 : step}
        value={inputValue}
        onChange={handleInputChange}
        className="w-full"
      />
      <div className="flex justify-between text-xs text-[var(--color-text-secondary)] mt-1">
        <span>{formatValue(min)}</span>
        <span>{formatValue(max)}</span>
      </div>
    </div>
  );
}
