interface TrafficLightProps {
  status: 'green' | 'yellow' | 'red' | 'pending';
  size?: 'small' | 'medium' | 'large';
}

export function TrafficLight({ status, size = 'medium' }: TrafficLightProps) {
  const sizeClasses = {
    small: 'w-3 h-3',
    medium: 'w-4 h-4',
    large: 'w-6 h-6',
  };

  const statusColors = {
    green: 'bg-[var(--color-success)]',
    yellow: 'bg-[var(--color-warning)]',
    red: 'bg-[var(--color-danger)]',
    pending: 'bg-[var(--color-text-secondary)]',
  };

  const glowColors = {
    green: 'shadow-[0_0_8px_var(--color-success)]',
    yellow: 'shadow-[0_0_8px_var(--color-warning)]',
    red: 'shadow-[0_0_8px_var(--color-danger)]',
    pending: '',
  };

  return (
    <div
      className={`${sizeClasses[size]} rounded-full ${statusColors[status]} ${glowColors[status]}`}
    />
  );
}
