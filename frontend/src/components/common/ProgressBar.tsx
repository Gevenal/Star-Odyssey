import React from 'react';

interface ProgressBarProps {
  current: number;
  max: number;
  label?: string;
  showPercentage?: boolean;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'purple';
  criticalThreshold?: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  current,
  max,
  label,
  showPercentage = false,
  color = 'blue',
  criticalThreshold,
}) => {
  // TODO: Implement progress bar with color coding
  const percentage = Math.min((current / max) * 100, 100);
  const isCritical = criticalThreshold && current <= criticalThreshold;

  const colorClasses = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-600',
    purple: 'bg-purple-600',
  };

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between mb-1 text-sm">
          <span className="text-gray-300">{label}</span>
          {showPercentage && (
            <span className={isCritical ? 'text-red-400' : 'text-gray-400'}>
              {current}/{max}
            </span>
          )}
        </div>
      )}

      <div className="w-full bg-gray-700 rounded-full h-2.5">
        <div
          className={`h-2.5 rounded-full transition-all ${
            isCritical ? 'bg-red-600' : colorClasses[color]
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
