import React from 'react';
import { NPCState } from '@/types/game';

interface NPCCardProps {
  npc: NPCState;
  onClick?: () => void;
}

export const NPCCard: React.FC<NPCCardProps> = ({ npc, onClick }) => {
  // TODO: Add NPC portrait/avatar
  // TODO: Add status indicators (health, stress)
  // TODO: Add activity/location display

  return (
    <div
      onClick={onClick}
      className={`
        bg-gray-800 rounded-lg p-3 border-2
        ${npc.alive ? 'border-gray-700' : 'border-red-900'}
        ${onClick ? 'cursor-pointer hover:bg-gray-750' : ''}
      `}
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="text-white font-bold">{npc.name}</h4>
          <p className="text-gray-400 text-xs">{npc.role}</p>
        </div>
        {!npc.alive && (
          <span className="text-red-400 text-xs font-bold">DECEASED</span>
        )}
      </div>

      <div className="space-y-1 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-500">Health:</span>
          <span className={npc.health > 50 ? 'text-green-400' : 'text-red-400'}>
            {npc.health}%
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Stress:</span>
          <span className={npc.stressLevel < 50 ? 'text-green-400' : 'text-yellow-400'}>
            {npc.stressLevel}%
          </span>
        </div>
        <div className="text-gray-500">
          Location: <span className="text-gray-300">{npc.location}</span>
        </div>
      </div>
    </div>
  );
};
