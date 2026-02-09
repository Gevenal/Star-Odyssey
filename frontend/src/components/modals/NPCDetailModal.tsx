import React from 'react';
import { Modal } from '@/components/common/Modal';
import { NPCState } from '@/types/game';

interface NPCDetailModalProps {
  npc: NPCState | null;
  isOpen: boolean;
  onClose: () => void;
}

export const NPCDetailModal: React.FC<NPCDetailModalProps> = ({
  npc,
  isOpen,
  onClose,
}) => {
  if (!npc) return null;

  // TODO: Add full personality display
  // TODO: Add relationship graph
  // TODO: Add interaction history

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={npc.name} size="lg">
      <div className="space-y-4">
        <div>
          <h4 className="text-gray-400 text-sm uppercase mb-1">Role</h4>
          <p className="text-white">{npc.role}</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <h4 className="text-gray-400 text-sm uppercase mb-1">Health</h4>
            <p className="text-white">{npc.health}%</p>
          </div>
          <div>
            <h4 className="text-gray-400 text-sm uppercase mb-1">Stress</h4>
            <p className="text-white">{npc.stressLevel}%</p>
          </div>
        </div>

        <div>
          <h4 className="text-gray-400 text-sm uppercase mb-1">Current Activity</h4>
          <p className="text-white">{npc.currentActivity || 'None'}</p>
        </div>

        <div>
          <h4 className="text-gray-400 text-sm uppercase mb-2">Goals</h4>
          <ul className="list-disc list-inside text-white space-y-1">
            {npc.goals.map((goal, index) => (
              <li key={index}>{goal}</li>
            ))}
          </ul>
        </div>
      </div>
    </Modal>
  );
};
