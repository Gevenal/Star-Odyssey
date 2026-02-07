import React from 'react';
import { clsx } from 'clsx';
import { Heart, Brain, MapPin, Activity, Skull } from 'lucide-react';
import { NPCState } from '@/types/game';
import ProgressBar from '@/components/common/ProgressBar';

interface NPCCardProps {
  npc: NPCState;
  isSelected?: boolean;
  compact?: boolean;
  onClick?: (npc: NPCState) => void;
  className?: string;
}

export const NPCCard: React.FC<NPCCardProps> = ({
  npc,
  isSelected = false,
  compact = false,
  onClick,
  className,
}) => {
  const { name, role, location, alive, health, stressLevel, currentActivity } = npc;

  // Get status color
  const getStatusColor = (): string => {
    if (!alive) return 'border-red-500/50 bg-red-500/10';
    if (health < 30 || stressLevel > 80) return 'border-yellow-500/50';
    if (isSelected) return 'border-cyan-500';
    return 'border-space-600';
  };

  // Get role icon background color
  const getRoleColor = (): string => {
    const roleColors: Record<string, string> = {
      Captain: 'bg-yellow-500/20 text-yellow-400',
      Engineer: 'bg-orange-500/20 text-orange-400',
      Doctor: 'bg-red-500/20 text-red-400',
      Scientist: 'bg-purple-500/20 text-purple-400',
      Security: 'bg-blue-500/20 text-blue-400',
      default: 'bg-gray-500/20 text-gray-400',
    };
    return roleColors[role] || roleColors.default;
  };

  // Format location display
  const formatLocation = (loc: string): string => {
    return loc
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  if (compact) {
    return (
      <button
        onClick={() => onClick?.(npc)}
        className={clsx(
          'w-full flex items-center gap-3 p-2 rounded-lg border transition-all',
          'hover:bg-space-700/50',
          getStatusColor(),
          !alive && 'opacity-60',
          className
        )}
      >
        {/* Avatar */}
        <div
          className={clsx(
            'w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold',
            alive ? getRoleColor() : 'bg-red-500/20 text-red-400'
          )}
        >
          {alive ? name.charAt(0) : <Skull size={14} />}
        </div>

        {/* Info */}
        <div className="flex-1 text-left min-w-0">
          <div className="text-sm text-white font-medium truncate">{name}</div>
          <div className="text-xs text-gray-500">{role}</div>
        </div>

        {/* Quick Health Indicator */}
        {alive && (
          <div
            className={clsx(
              'w-2 h-2 rounded-full',
              health > 70 ? 'bg-green-400' : health > 30 ? 'bg-yellow-400' : 'bg-red-400'
            )}
          />
        )}
      </button>
    );
  }

  return (
    <button
      onClick={() => onClick?.(npc)}
      className={clsx(
        'w-full text-left p-4 rounded-lg border transition-all',
        'hover:bg-space-700/50',
        getStatusColor(),
        !alive && 'opacity-60',
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start gap-3 mb-3">
        {/* Avatar */}
        <div
          className={clsx(
            'w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold flex-shrink-0',
            alive ? getRoleColor() : 'bg-red-500/20 text-red-400'
          )}
        >
          {alive ? name.charAt(0) : <Skull size={20} />}
        </div>

        {/* Name and Role */}
        <div className="flex-1 min-w-0">
          <h4 className="text-white font-medium truncate">{name}</h4>
          <p className="text-gray-500 text-sm">{role}</p>
          
          {/* Status Badge */}
          {!alive && (
            <span className="inline-block mt-1 px-2 py-0.5 bg-red-500/20 text-red-400 text-xs rounded">
              DECEASED
            </span>
          )}
        </div>
      </div>

      {alive && (
        <>
          {/* Stats */}
          <div className="space-y-2 mb-3">
            {/* Health */}
            <div className="flex items-center gap-2">
              <Heart size={12} className="text-red-400 flex-shrink-0" />
              <ProgressBar
                value={health}
                max={100}
                size="sm"
                color="red"
                criticalThreshold={30}
                warningThreshold={50}
              />
              <span className="text-xs text-gray-400 w-8">{health}%</span>
            </div>

            {/* Stress */}
            <div className="flex items-center gap-2">
              <Brain size={12} className="text-purple-400 flex-shrink-0" />
              <ProgressBar
                value={stressLevel}
                max={100}
                size="sm"
                color="purple"
              />
              <span className="text-xs text-gray-400 w-8">{stressLevel}%</span>
            </div>
          </div>

          {/* Location */}
          <div className="flex items-center gap-2 text-xs text-gray-400">
            <MapPin size={12} />
            <span className="truncate">{formatLocation(location)}</span>
          </div>

          {/* Current Activity */}
          {currentActivity && (
            <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
              <Activity size={12} />
              <span className="truncate italic">{currentActivity}</span>
            </div>
          )}
        </>
      )}
    </button>
  );
};

export default NPCCard;