import React from 'react';
import clsx from 'clsx';
import { Settings, Save, LogOut, AlertTriangle } from 'lucide-react';
import { useGameStore } from '@/stores/gameStore';
import Button from '@/components/common/Button';

interface HeaderProps {
  onSettingsClick?: () => void;
  onSaveClick?: () => void;
  onExitClick?: () => void;
  className?: string;
}

export const Header: React.FC<HeaderProps> = ({
  onSettingsClick,
  onSaveClick,
  onExitClick,
  className,
}: HeaderProps) => {
  const { gameState } = useGameStore();
  const world = gameState?.world;
  const resources = world?.resources;

  // Format time display
  const formatTimeOfDay = (time: string): string => {
    const timeMap: Record<string, string> = {
      morning: '🌅 Morning',
      afternoon: '☀️ Afternoon',
      evening: '🌆 Evening',
      night: '🌙 Night',
    };
    return timeMap[time] || time;
  };

  // Check if there are critical resources
  const hasCriticalResource = resources && (
    (resources.oxygenLevel?.current ?? 0) <= (resources.oxygenLevel?.criticalThreshold ?? 0) ||
    (resources.powerLevel?.current ?? 0) <= (resources.powerLevel?.criticalThreshold ?? 0)
  );

  return (
    <header
      className={clsx(
        'h-16 bg-space-800 border-b border-space-600',
        'flex items-center justify-between px-6',
        'flex-shrink-0',
        className
      )}
    >
      {/* Left: Title and Game Info */}
      <div className="flex items-center gap-6">
        <h1 className="text-2xl font-display font-bold text-cyan-400 tracking-wider">
          ODYSSEY-7
        </h1>

        {gameState && (
          <>
            <div className="h-8 w-px bg-space-600" />
            
            <div className="flex items-center gap-4 text-sm">
              {/* Day Counter */}
              <div className="flex flex-col items-center">
                <span className="text-gray-500 text-xs uppercase">Day</span>
                <span className="text-white font-bold text-lg">{world?.day || 1}/7</span>
              </div>

              {/* Turn Counter */}
              <div className="flex flex-col items-center">
                <span className="text-gray-500 text-xs uppercase">Turn</span>
                <span className="text-gray-300 font-medium">{world?.turn || 1}</span>
              </div>

              {/* Time of Day */}
              <div className="flex flex-col items-center">
                <span className="text-gray-500 text-xs uppercase">Time</span>
                <span className="text-gray-300">{formatTimeOfDay(world?.timeOfDay || 'morning')}</span>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Center: Critical Warnings */}
      {hasCriticalResource && (
        <div className="flex items-center gap-2 px-4 py-2 bg-red-500/20 border border-red-500/50 rounded-lg animate-pulse">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <span className="text-red-400 font-medium text-sm">CRITICAL RESOURCES LOW</span>
        </div>
      )}

      {/* Right: Quick Stats and Actions */}
      <div className="flex items-center gap-6">
        {/* Quick Resource Display */}
        {resources && (
          <div className="flex items-center gap-4">
            <ResourceQuickStat
              label="O₂"
              value={resources.oxygenLevel?.current ?? 0}
              critical={resources.oxygenLevel?.criticalThreshold ?? 0}
            />
            <ResourceQuickStat
              label="PWR"
              value={resources.powerLevel?.current ?? 0}
              critical={resources.powerLevel?.criticalThreshold ?? 0}
            />
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {onSaveClick && (
            <Button variant="ghost" size="sm" onClick={onSaveClick}>
              <Save size={18} />
            </Button>
          )}
          {onSettingsClick && (
            <Button variant="ghost" size="sm" onClick={onSettingsClick}>
              <Settings size={18} />
            </Button>
          )}
          {onExitClick && (
            <Button variant="ghost" size="sm" onClick={onExitClick}>
              <LogOut size={18} />
            </Button>
          )}
        </div>
      </div>
    </header>
  );
};

// Quick resource display component
interface ResourceQuickStatProps {
  label: string;
  value: number;
  critical: number;
}

const ResourceQuickStat: React.FC<ResourceQuickStatProps> = ({ label, value, critical }: ResourceQuickStatProps) => {
  const isCritical = value <= critical;
  const isWarning = value <= critical * 1.5;

  return (
    <div className="flex items-center gap-2">
      <span className="text-gray-500 text-xs uppercase">{label}</span>
      <span
        className={clsx(
          'font-bold',
          isCritical && 'text-red-400 animate-pulse',
          isWarning && !isCritical && 'text-yellow-400',
          !isWarning && 'text-cyan-400'
        )}
      >
        {Math.round(value)}%
      </span>
    </div>
  );
};

export default Header;