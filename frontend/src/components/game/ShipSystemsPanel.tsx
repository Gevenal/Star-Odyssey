import React from 'react';

interface SystemStatus {
  name: string;
  status: 'operational' | 'damaged' | 'critical' | 'offline';
  efficiency?: number;
}

interface ShipSystemsPanelProps {
  systems: SystemStatus[];
}

export const ShipSystemsPanel: React.FC<ShipSystemsPanelProps> = ({ systems }) => {
  // TODO: Implement ship systems display
  // TODO: Add system icons
  // TODO: Add click to view details

  const statusColors = {
    operational: 'text-green-400',
    damaged: 'text-yellow-400',
    critical: 'text-red-400',
    offline: 'text-gray-600',
  };

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <h3 className="text-white font-bold mb-3">Ship Systems</h3>

      <div className="space-y-2">
        {systems.map((system, index) => (
          <div key={index} className="flex justify-between items-center">
            <span className="text-gray-300 text-sm">{system.name}</span>
            <span className={`text-xs font-semibold ${statusColors[system.status]}`}>
              {system.status.toUpperCase()}
              {system.efficiency && ` (${system.efficiency}%)`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
