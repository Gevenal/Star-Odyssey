import React from 'react';
import { clsx } from 'clsx';

export type ProgressBarColor = 'cyan' | 'green' | 'yellow' | 'red' | 'purple';

interface ProgressBarProps {
  value: number;
  max?: number;
  min?: number;
  color?: ProgressBarColor;
  showLabel?: boolean;
  labelFormat?: 'percent' | 'value' | 'both';
  size?: 'sm' | 'md' | 'lg';
  animated?: boolean;
  criticalThreshold?: number;
  warningThreshold?: number;
  className?: string;
}

const colorStyles: Record<ProgressBarColor, string> = {
  cyan: 'bg-cyan-500',
  green: 'bg-green-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
  purple: 'bg-purple-500',
};

const sizeStyles: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  min = 0,
  color = 'cyan',
  showLabel = false,
  labelFormat = 'percent',
  size = 'md',
  animated = false,
  criticalThreshold,
  warningThreshold,
  className,
}) => {
  // 计算百分比
  const range = max - min;
  const normalizedValue = Math.max(min, Math.min(max, value));
  const percentage = range > 0 ? ((normalizedValue - min) / range) * 100 : 0;

  // 根据阈值自动确定颜色
  const getAutoColor = (): ProgressBarColor => {
    if (criticalThreshold !== undefined && normalizedValue <= criticalThreshold) {
      return 'red';
    }
    if (warningThreshold !== undefined && normalizedValue <= warningThreshold) {
      return 'yellow';
    }
    return color;
  };

  const finalColor = criticalThreshold !== undefined || warningThreshold !== undefined 
    ? getAutoColor() 
    : color;

  // 格式化标签
  const formatLabel = (): string => {
    switch (labelFormat) {
      case 'value':
        return `${normalizedValue}/${max}`;
      case 'both':
        return `${normalizedValue}/${max} (${percentage.toFixed(0)}%)`;
      case 'percent':
      default:
        return `${percentage.toFixed(0)}%`;
    }
  };

  return (
    <div className={clsx('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between mb-1 text-xs text-gray-400">
          <span>{formatLabel()}</span>
        </div>
      )}
      <div className={clsx('w-full bg-space-700 rounded-full overflow-hidden', sizeStyles[size])}>
        <div
          className={clsx(
            'h-full rounded-full transition-all duration-300 ease-out',
            colorStyles[finalColor],
            animated && 'animate-pulse'
          )}
          style={{ width: `${percentage}%` }}
          role="progressbar"
          aria-valuenow={normalizedValue}
          aria-valuemin={min}
          aria-valuemax={max}
        />
      </div>
    </div>
  );
};

export default ProgressBar;