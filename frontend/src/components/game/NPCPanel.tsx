import React from 'react';
import { NPCCard } from './NPCCard';
import { NPCState } from '@/types/game';
import { useUIStore } from '@/stores/uiStore';

interface NPCPanelProps {
  npcs: Record<string, NPCState>;
}

export const NPCPanel: React.FC<NPCPanelProps> = ({ npcs }) => {
  const { openModal } = useUIStore();

  const handleNPCClick = (npc: NPCState) => {
    openModal('npc-detail', npc);
  };

  // TODO: Add filtering (alive/dead, by location)
  // TODO: Add sorting options

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <h3 className="text-white font-bold mb-3">Crew Members</h3>

      <div className="space-y-3">
        {Object.values(npcs).map((npc) => (
          <NPCCard
            key={npc.id}
            npc={npc}
            onClick={() => handleNPCClick(npc)}
          />
        ))}
      </div>
    </div>
  );
};
