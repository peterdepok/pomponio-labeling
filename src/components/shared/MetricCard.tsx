interface MetricCardProps {
  label: string;
  value: string;
  subtitle?: string;
  status?: 'green' | 'yellow' | 'red' | 'neutral';
  size?: 'small' | 'medium' | 'large';
}

export function MetricCard({
  label,
  value,
  subtitle,
  status = 'neutral',
  size = 'medium',
}: MetricCardProps) {
  const statusColors = {
    green: 'border-[var(--color-success)]',
    yellow: 'border-[var(--color-warning)]',
    red: 'border-[var(--color-danger)]',
    neutral: 'border-[var(--color-accent)]',
  };

  const sizeClasses = {
    small: 'p-2',
    medium: 'p-4',
    large: 'p-6',
  };

  const valueSizes = {
    small: 'text-lg',
    medium: 'text-2xl',
    large: 'text-3xl',
  };

  return (
    <div
      className={`bg-[var(--color-secondary-bg)] rounded-lg border-l-4 ${statusColors[status]} ${sizeClasses[size]}`}
    >
      <div className="text-xs text-[var(--color-text-secondary)] uppercase tracking-wide mb-1">
        {label}
      </div>
      <div className={`${valueSizes[size]} font-semibold text-[var(--color-text-primary)]`}>
        {value}
      </div>
      {subtitle && (
        <div className="text-sm text-[var(--color-text-secondary)] mt-1">{subtitle}</div>
      )}
    </div>
  );
}
