import React from 'react';

interface Location {
  id: string;
  name: string;
  accessible: boolean;
  npcsPresent: number;
}

interface LocationMapProps {
  currentLocation: string;
  locations: Location[];
  onLocationClick?: (locationId: string) => void;
}

export const LocationMap: React.FC<LocationMapProps> = ({
  currentLocation,
  locations,
  onLocationClick,
}) => {
  // TODO: Implement ship layout visualization
  // TODO: Add connection lines between locations
  // TODO: Add NPC markers on locations

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <h3 className="text-white font-bold mb-3">Ship Layout</h3>

      <div className="space-y-2">
        {locations.map((location) => (
          <div
            key={location.id}
            onClick={() => location.accessible && onLocationClick?.(location.id)}
            className={`
              px-3 py-2 rounded border
              ${location.id === currentLocation ? 'border-blue-500 bg-blue-900' : 'border-gray-700'}
              ${location.accessible ? 'cursor-pointer hover:bg-gray-800' : 'opacity-50'}
            `}
          >
            <div className="flex justify-between items-center">
              <span className="text-white text-sm">{location.name}</span>
              {location.npcsPresent > 0 && (
                <span className="text-gray-400 text-xs">
                  {location.npcsPresent} crew
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
