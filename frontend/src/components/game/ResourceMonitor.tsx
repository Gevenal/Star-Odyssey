import React from 'react';
import { clsx } from 'clsx';
import {
  Wind,       // Oxygen
  Zap,        // Power
  Fuel,       // Fuel
  Heart,      // Medical
  Utensils,   // Food
  Wrench,     // Repair
  AlertTriangle,
} from 'lucide-react';
import { ResourceLevels, ResourceLevel } from '@/types/game';
import ProgressBar from '@/components/common/ProgressBar';

interface ResourceMonitorProps {
  resources: ResourceLevels;
  compact?: boolean;
  showDecayRate?: boolean;
  className?: string;
}

interface ResourceConfig {
  key: keyof ResourceLevels;
  label: string;
  icon: React.ReactNode;
  color: 'cyan' | 'green' | 'yellow' | 'red' | 'purple';
}

const RESOURCE_CONFIG: ResourceConfig[] = [
  { key: 'oxygenLevel', label: 'Oxygen', icon: <Wind size={16} />, color: 'cyan' },
  { key: 'powerLevel', label: 'Power', icon: <Zap size={16} />, color: 'yellow' },
  { key: 'fuelReserves', label: 'Fuel', icon: <Fuel size={16} />, color: 'purple' },
  { key: 'medicalSupplies', label: 'Medical', icon: <Heart size={16} />, color: 'red' },
  { key: 'foodWater', label: 'Food & Water', icon: <Utensils size={16} />, color: 'green' },
  { key: 'repairMaterials', label: 'Repair Parts', icon: <Wrench size={16} />, color: 'cyan' },
];

export const ResourceMonitor: React.FC<ResourceMonitorProps> = ({
  resources,
  compact = false,
  showDecayRate = false,
  className,
}) => {
  return (
    <div className={clsx('bg-space-800 rounded-lg', className)}>
      <div className="px-4 py-3 border-b border-space-600">
        <h3 className="text-cyan-400 font-bold text-sm uppercase tracking-wider">
          Ship Resources
        </h3>
      </div>

      <div className={clsx('p-4', compact ? 'space-y-2' : 'space-y-4')}>
        {RESOURCE_CONFIG.map((config) => {
          const resource = resources[config.key];
          if (!resource) return null;

          return (
            <ResourceItem
              key={config.key}
              config={config}
              resource={resource}
              compact={compact}
              showDecayRate={showDecayRate}
            />
          );
        })}
      </div>
    </div>
  );
};

// 单个资源项
interface ResourceItemProps {
  config: ResourceConfig;
  resource: ResourceLevel;
  compact: boolean;
  showDecayRate: boolean;
}

const ResourceItem: React.FC<ResourceItemProps> = ({
  config,
  resource,
  compact,
  showDecayRate,
}) => {
  const { current, max, criticalThreshold, decayRate } = resource;
  const percentage = (current / max) * 100;
  const isCritical = current <= criticalThreshold;
  const isWarning = current <= criticalThreshold * 1.5;

  return (
    <div className={clsx(compact ? 'space-y-1' : 'space-y-2')}>
      {/* Label Row */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={clsx(
              'flex-shrink-0',
              isCritical ? 'text-red-400' : isWarning ? 'text-yellow-400' : 'text-gray-400'
            )}
          >
            {config.icon}
          </span>
          <span className={clsx('text-sm', isCritical ? 'text-red-400' : 'text-gray-300')}>
            {config.label}
          </span>
          {isCritical && (
            <AlertTriangle size={14} className="text-red-400 animate-pulse" />
          )}
        </div>

        <div className="flex items-center gap-2">
          <span
            className={clsx(
              'text-sm font-medium',
              isCritical ? 'text-red-400' : isWarning ? 'text-yellow-400' : 'text-white'
            )}
          >
            {Math.round(current)}%
          </span>
          {showDecayRate && decayRate !== 0 && (
            <span
              className={clsx(
                'text-xs',
                decayRate < 0 ? 'text-red-400' : 'text-green-400'
              )}
            >
              ({decayRate > 0 ? '+' : ''}{decayRate}/turn)
            </span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <ProgressBar
        value={current}
        max={max}
        color={config.color}
        size={compact ? 'sm' : 'md'}
        criticalThreshold={criticalThreshold}
        warningThreshold={criticalThreshold * 1.5}
        animated={isCritical}
      />
    </div>
  );
};

export default ResourceMonitor;