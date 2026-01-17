import React from 'react';
import { ProgressBar } from '@/components/common/ProgressBar';
import { ResourceLevels } from '@/types/game';

interface ResourceMonitorProps {
  resources: ResourceLevels;
}

export const ResourceMonitor: React.FC<ResourceMonitorProps> = ({ resources }) => {
  // TODO: Add warning indicators for critical resources
  // TODO: Add trend arrows (increasing/decreasing)
  // TODO: Add tooltips with decay rates

  const resourceConfig = [
    { key: 'oxygenLevel', label: 'Oxygen', color: 'blue' as const },
    { key: 'fuelReserves', label: 'Fuel', color: 'yellow' as const },
    { key: 'powerLevel', label: 'Power', color: 'green' as const },
    { key: 'medicalSupplies', label: 'Medical', color: 'red' as const },
    { key: 'foodWater', label: 'Food/Water', color: 'blue' as const },
    { key: 'repairMaterials', label: 'Repair Materials', color: 'purple' as const },
  ];

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <h3 className="text-white font-bold mb-3">Ship Resources</h3>

      <div className="space-y-3">
        {resourceConfig.map(({ key, label, color }) => {
          const resource = resources[key as keyof ResourceLevels];
          return (
            <ProgressBar
              key={key}
              label={label}
              current={resource.current}
              max={resource.max}
              color={color}
              criticalThreshold={resource.criticalThreshold}
              showPercentage
            />
          );
        })}
      </div>
    </div>
  );
};
