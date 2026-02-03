import { formatCurrency } from '../../utils/calculations';

interface WaterfallItem {
  label: string;
  value: number;
  isTotal?: boolean;
}

interface WaterfallChartProps {
  items: WaterfallItem[];
  height?: number;
}

export function WaterfallChart({ items, height = 200 }: WaterfallChartProps) {
  const maxValue = Math.max(...items.map(i => Math.abs(i.value)));
  const barWidth = 100 / items.length;

  return (
    <div className="bg-[var(--color-secondary-bg)] rounded-lg p-4">
      <svg width="100%" height={height} viewBox={`0 0 100 ${height}`} preserveAspectRatio="none">
        {items.map((item, index) => {
          const barHeight = (Math.abs(item.value) / maxValue) * (height - 40);
          const x = index * barWidth + barWidth * 0.1;
          const y = height - 30 - barHeight;
          const width = barWidth * 0.8;
          const isPositive = item.value >= 0;
          const fill = item.isTotal
            ? 'var(--color-accent)'
            : isPositive
            ? 'var(--color-success)'
            : 'var(--color-danger)';

          return (
            <g key={item.label}>
              <rect x={`${x}%`} y={y} width={`${width}%`} height={barHeight} fill={fill} rx="2" />
              <text
                x={`${x + width / 2}%`}
                y={height - 10}
                textAnchor="middle"
                fill="var(--color-text-secondary)"
                fontSize="6"
              >
                {item.label}
              </text>
              <text
                x={`${x + width / 2}%`}
                y={y - 5}
                textAnchor="middle"
                fill="var(--color-text-primary)"
                fontSize="6"
              >
                {formatCurrency(item.value)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

interface GaugeProps {
  value: number;
  min: number;
  max: number;
  thresholds: { value: number; color: string }[];
  label: string;
  size?: number;
}

export function Gauge({ value, min, max, thresholds, label, size = 150 }: GaugeProps) {
  const range = max - min;
  const normalizedValue = Math.max(min, Math.min(max, value));
  const angle = ((normalizedValue - min) / range) * 180 - 90;

  const getColor = () => {
    for (let i = thresholds.length - 1; i >= 0; i--) {
      if (value >= thresholds[i].value) {
        return thresholds[i].color;
      }
    }
    return thresholds[0].color;
  };

  return (
    <div className="bg-[var(--color-secondary-bg)] rounded-lg p-4 flex flex-col items-center">
      <svg width={size} height={size / 2 + 20} viewBox="0 0 100 60">
        {/* Background arc */}
        <path
          d="M 10 50 A 40 40 0 0 1 90 50"
          fill="none"
          stroke="var(--color-accent)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        {/* Colored segments */}
        {thresholds.map((threshold, index) => {
          const startAngle = index === 0 ? -90 : ((thresholds[index - 1].value - min) / range) * 180 - 90;
          const endAngle = ((threshold.value - min) / range) * 180 - 90;
          const startRad = (startAngle * Math.PI) / 180;
          const endRad = (endAngle * Math.PI) / 180;
          const x1 = 50 + 40 * Math.cos(startRad);
          const y1 = 50 + 40 * Math.sin(startRad);
          const x2 = 50 + 40 * Math.cos(endRad);
          const y2 = 50 + 40 * Math.sin(endRad);
          const largeArc = endAngle - startAngle > 90 ? 1 : 0;

          return (
            <path
              key={threshold.value}
              d={`M ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2}`}
              fill="none"
              stroke={threshold.color}
              strokeWidth="8"
              strokeLinecap="round"
              opacity="0.3"
            />
          );
        })}
        {/* Needle */}
        <g transform={`rotate(${angle}, 50, 50)`}>
          <line x1="50" y1="50" x2="50" y2="15" stroke={getColor()} strokeWidth="2" />
          <circle cx="50" cy="50" r="4" fill={getColor()} />
        </g>
        {/* Value */}
        <text x="50" y="55" textAnchor="middle" fill="var(--color-text-primary)" fontSize="10" fontWeight="bold">
          {value.toFixed(1)}x
        </text>
      </svg>
      <div className="text-sm text-[var(--color-text-secondary)] mt-2">{label}</div>
    </div>
  );
}

interface LineChartData {
  label: string;
  values: number[];
  color: string;
}

interface LineChartProps {
  data: LineChartData[];
  xLabels: string[];
  height?: number;
  yFormat?: (v: number) => string;
}

export function LineChart({ data, xLabels, height = 200, yFormat = (v) => v.toString() }: LineChartProps) {
  const allValues = data.flatMap(d => d.values);
  const maxValue = Math.max(...allValues);
  const minValue = Math.min(0, ...allValues);
  const range = maxValue - minValue || 1;

  const padding = { top: 20, right: 20, bottom: 30, left: 50 };
  const chartWidth = 100 - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const getY = (value: number) => {
    return padding.top + chartHeight - ((value - minValue) / range) * chartHeight;
  };

  const getX = (index: number) => {
    return padding.left + (index / (xLabels.length - 1)) * chartWidth;
  };

  return (
    <div className="bg-[var(--color-secondary-bg)] rounded-lg p-4">
      <svg width="100%" height={height} viewBox={`0 0 100 ${height}`} preserveAspectRatio="xMidYMid meet">
        {/* Y axis labels */}
        {[0, 0.25, 0.5, 0.75, 1].map(pct => {
          const value = minValue + range * pct;
          const y = getY(value);
          return (
            <g key={pct}>
              <line
                x1={padding.left}
                y1={y}
                x2={100 - padding.right}
                y2={y}
                stroke="var(--color-accent)"
                strokeWidth="0.5"
                strokeDasharray="2,2"
              />
              <text x={padding.left - 5} y={y + 2} textAnchor="end" fill="var(--color-text-secondary)" fontSize="5">
                {yFormat(value)}
              </text>
            </g>
          );
        })}
        {/* X axis labels */}
        {xLabels.map((label, index) => (
          <text
            key={label}
            x={getX(index)}
            y={height - 10}
            textAnchor="middle"
            fill="var(--color-text-secondary)"
            fontSize="5"
          >
            {label}
          </text>
        ))}
        {/* Data lines */}
        {data.map(series => {
          const points = series.values.map((v, i) => `${getX(i)},${getY(v)}`).join(' ');
          return (
            <g key={series.label}>
              <polyline points={points} fill="none" stroke={series.color} strokeWidth="1.5" />
              {series.values.map((v, i) => (
                <circle key={i} cx={getX(i)} cy={getY(v)} r="2" fill={series.color} />
              ))}
            </g>
          );
        })}
      </svg>
      {/* Legend */}
      <div className="flex gap-4 mt-2 justify-center">
        {data.map(series => (
          <div key={series.label} className="flex items-center gap-1">
            <div className="w-3 h-3 rounded" style={{ backgroundColor: series.color }} />
            <span className="text-xs text-[var(--color-text-secondary)]">{series.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

interface AreaChartProps {
  data: { label: string; values: number[]; color: string }[];
  xLabels: string[];
  height?: number;
  yFormat?: (v: number) => string;
  showThreshold?: { value: number; label: string };
}

export function AreaChart({ data, xLabels, height = 200, yFormat = (v) => v.toString(), showThreshold }: AreaChartProps) {
  const allValues = data.flatMap(d => d.values);
  if (showThreshold) allValues.push(showThreshold.value);
  const maxValue = Math.max(...allValues);
  const minValue = Math.min(0, ...allValues);
  const range = maxValue - minValue || 1;

  const padding = { top: 20, right: 20, bottom: 30, left: 50 };
  const chartWidth = 100 - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const getY = (value: number) => {
    return padding.top + chartHeight - ((value - minValue) / range) * chartHeight;
  };

  const getX = (index: number) => {
    return padding.left + (index / (xLabels.length - 1 || 1)) * chartWidth;
  };

  return (
    <div className="bg-[var(--color-secondary-bg)] rounded-lg p-4">
      <svg width="100%" height={height} viewBox={`0 0 100 ${height}`} preserveAspectRatio="xMidYMid meet">
        {/* Threshold line */}
        {showThreshold && (
          <g>
            <line
              x1={padding.left}
              y1={getY(showThreshold.value)}
              x2={100 - padding.right}
              y2={getY(showThreshold.value)}
              stroke="var(--color-danger)"
              strokeWidth="1"
              strokeDasharray="4,2"
            />
            <text
              x={100 - padding.right + 2}
              y={getY(showThreshold.value) + 2}
              fill="var(--color-danger)"
              fontSize="4"
            >
              {showThreshold.label}
            </text>
          </g>
        )}
        {/* Y axis labels */}
        {[0, 0.5, 1].map(pct => {
          const value = minValue + range * pct;
          const y = getY(value);
          return (
            <text key={pct} x={padding.left - 5} y={y + 2} textAnchor="end" fill="var(--color-text-secondary)" fontSize="5">
              {yFormat(value)}
            </text>
          );
        })}
        {/* X axis labels */}
        {xLabels.map((label, index) => (
          <text
            key={label}
            x={getX(index)}
            y={height - 10}
            textAnchor="middle"
            fill="var(--color-text-secondary)"
            fontSize="5"
          >
            {label}
          </text>
        ))}
        {/* Area fills */}
        {data.map(series => {
          const points = series.values.map((v, i) => `${getX(i)},${getY(v)}`);
          const areaPath = `M ${getX(0)},${getY(0)} ${points.join(' ')} L ${getX(series.values.length - 1)},${getY(0)} Z`;
          return (
            <g key={series.label}>
              <path d={areaPath} fill={series.color} fillOpacity="0.3" />
              <polyline points={points.join(' ')} fill="none" stroke={series.color} strokeWidth="1.5" />
            </g>
          );
        })}
      </svg>
    </div>
  );
}

interface TornadoItem {
  label: string;
  lowValue: number;
  highValue: number;
  baseValue: number;
}

interface TornadoChartProps {
  items: TornadoItem[];
  height?: number;
}

export function TornadoChart({ items, height = 250 }: TornadoChartProps) {
  const maxSwing = Math.max(...items.map(i => Math.max(Math.abs(i.lowValue - i.baseValue), Math.abs(i.highValue - i.baseValue))));
  const barHeight = (height - 40) / items.length;

  return (
    <div className="bg-[var(--color-secondary-bg)] rounded-lg p-4">
      <svg width="100%" height={height} viewBox={`0 0 100 ${height}`} preserveAspectRatio="xMidYMid meet">
        {/* Center line */}
        <line x1="50" y1="20" x2="50" y2={height - 20} stroke="var(--color-text-secondary)" strokeWidth="0.5" />

        {items.map((item, index) => {
          const y = 20 + index * barHeight;
          const lowDelta = item.lowValue - item.baseValue;
          const highDelta = item.highValue - item.baseValue;

          const lowX = 50 + (lowDelta / maxSwing) * 45;
          const highX = 50 + (highDelta / maxSwing) * 45;

          const minX = Math.min(lowX, highX);
          const maxX = Math.max(lowX, highX);

          return (
            <g key={item.label}>
              <rect
                x={minX}
                y={y + 2}
                width={maxX - minX}
                height={barHeight - 4}
                fill="var(--color-accent)"
                rx="2"
              />
              <text x="5" y={y + barHeight / 2 + 2} fill="var(--color-text-secondary)" fontSize="5">
                {item.label}
              </text>
              <text x={minX - 2} y={y + barHeight / 2 + 2} textAnchor="end" fill="var(--color-text-primary)" fontSize="4">
                ${item.lowValue.toFixed(0)}
              </text>
              <text x={maxX + 2} y={y + barHeight / 2 + 2} textAnchor="start" fill="var(--color-text-primary)" fontSize="4">
                ${item.highValue.toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Base value label */}
        <text x="50" y={height - 5} textAnchor="middle" fill="var(--color-text-secondary)" fontSize="5">
          Base LTV: ${items[0]?.baseValue.toFixed(0)}
        </text>
      </svg>
    </div>
  );
}
