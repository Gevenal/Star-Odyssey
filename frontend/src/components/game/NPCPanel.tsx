import React, { useState, useMemo } from 'react';
import { clsx } from 'clsx';
import { Users, Filter } from 'lucide-react';
import { NPCState } from '@/types/game';
import NPCCard from './NPCCard';
import Modal from '@/components/common/Modal';
import Button from '@/components/common/Button';

interface NPCPanelProps {
  npcs: Record<string, NPCState>;
  onNPCClick?: (npc: NPCState) => void;
  compact?: boolean;
  className?: string;
}

type FilterOption = 'all' | 'alive' | 'here' | 'critical';

export const NPCPanel: React.FC<NPCPanelProps> = ({
  npcs,
  onNPCClick,
  compact = true,
  className,
}) => {
  const [filter, setFilter] = useState<FilterOption>('alive');
  const [selectedNPC, setSelectedNPC] = useState<NPCState | null>(null);

  // Convert to array and sort
  const npcList = useMemo(() => {
    const list = Object.values(npcs);
    
    // Filter based on filter option
    const filtered = list.filter((npc) => {
      switch (filter) {
        case 'alive':
          return npc.alive;
        case 'critical':
          return npc.alive && (npc.health < 30 || npc.stressLevel > 80);
        // 'here' requires player location, simplified handling here
        case 'here':
        case 'all':
        default:
          return true;
      }
    });

    // Sort: alive first, then by health status
    return filtered.sort((a, b) => {
      if (a.alive !== b.alive) return a.alive ? -1 : 1;
      return b.health - a.health;
    });
  }, [npcs, filter]);

  const handleNPCClick = (npc: NPCState) => {
    setSelectedNPC(npc);
    onNPCClick?.(npc);
  };

  // Statistics
  const stats = useMemo(() => {
    const list = Object.values(npcs);
    return {
      total: list.length,
      alive: list.filter((n) => n.alive).length,
      critical: list.filter((n) => n.alive && (n.health < 30 || n.stressLevel > 80)).length,
    };
  }, [npcs]);

  return (
    <>
      <div className={clsx('bg-space-800 rounded-lg', className)}>
        {/* Header */}
        <div className="px-4 py-3 border-b border-space-600">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users size={16} className="text-cyan-400" />
              <h3 className="text-cyan-400 font-bold text-sm uppercase tracking-wider">
                Crew Status
              </h3>
            </div>
            <span className="text-xs text-gray-500">
              {stats.alive}/{stats.total} alive
            </span>
          </div>

          {/* Filter Buttons */}
          <div className="flex gap-1 mt-2">
            {[
              { value: 'alive', label: 'Alive' },
              { value: 'critical', label: 'Critical' },
              { value: 'all', label: 'All' },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setFilter(opt.value as FilterOption)}
                className={clsx(
                  'px-2 py-1 text-xs rounded transition-colors',
                  filter === opt.value
                    ? 'bg-cyan-500/20 text-cyan-400'
                    : 'text-gray-500 hover:text-gray-300'
                )}
              >
                {opt.label}
                {opt.value === 'critical' && stats.critical > 0 && (
                  <span className="ml-1 text-red-400">({stats.critical})</span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* NPC List */}
        <div className="p-2 space-y-2 max-h-[400px] overflow-y-auto">
          {npcList.length === 0 ? (
            <div className="text-center text-gray-500 py-4 text-sm">
              No crew members match this filter
            </div>
          ) : (
            npcList.map((npc) => (
              <NPCCard
                key={npc.id}
                npc={npc}
                compact={compact}
                onClick={handleNPCClick}
              />
            ))
          )}
        </div>
      </div>

      {/* NPC Detail Modal */}
      <NPCDetailModal
        npc={selectedNPC}
        isOpen={selectedNPC !== null}
        onClose={() => setSelectedNPC(null)}
      />
    </>
  );
};

// NPC detail modal
interface NPCDetailModalProps {
  npc: NPCState | null;
  isOpen: boolean;
  onClose: () => void;
}

const NPCDetailModal: React.FC<NPCDetailModalProps> = ({ npc, isOpen, onClose }) => {
  if (!npc) return null;

  const { personality, goals, relationships } = npc;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={npc.name}
      size="lg"
    >
      <div className="space-y-6">
        {/* Basic Info */}
        <div className="flex items-start gap-4">
          <div className="w-16 h-16 rounded-full bg-cyan-500/20 flex items-center justify-center text-2xl font-bold text-cyan-400">
            {npc.name.charAt(0)}
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">{npc.name}</h3>
            <p className="text-gray-400">{npc.role}</p>
            <p className="text-sm text-gray-500 mt-1">
              Currently at: {npc.location.replace(/_/g, ' ')}
            </p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-xs text-gray-500 uppercase">Health</span>
            <div className="text-lg font-bold text-white">{npc.health}%</div>
          </div>
          <div>
            <span className="text-xs text-gray-500 uppercase">Stress</span>
            <div className="text-lg font-bold text-white">{npc.stressLevel}%</div>
          </div>
        </div>

        {/* Personality */}
        {personality && (
          <div>
            <h4 className="text-sm font-bold text-cyan-400 uppercase mb-2">Personality</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div><span className="text-gray-500">Core Value:</span> <span className="text-gray-300">{personality.coreValue}</span></div>
              <div><span className="text-gray-500">Social Style:</span> <span className="text-gray-300">{personality.socialStyle}</span></div>
              <div><span className="text-gray-500">Under Stress:</span> <span className="text-gray-300">{personality.stressResponse}</span></div>
              <div><span className="text-gray-500">Decisions:</span> <span className="text-gray-300">{personality.decisionMaking}</span></div>
            </div>
          </div>
        )}

        {/* Goals */}
        {goals && goals.length > 0 && (
          <div>
            <h4 className="text-sm font-bold text-cyan-400 uppercase mb-2">Known Goals</h4>
            <ul className="space-y-1">
              {goals.map((goal, i) => (
                <li key={i} className="text-sm text-gray-300 flex items-start gap-2">
                  <span className="text-cyan-400">•</span>
                  {goal}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Relationships */}
        {relationships && Object.keys(relationships).length > 0 && (
          <div>
            <h4 className="text-sm font-bold text-cyan-400 uppercase mb-2">Relationships</h4>
            <div className="space-y-2">
              {Object.entries(relationships).map(([targetId, rel]) => (
                <div key={targetId} className="flex items-center justify-between text-sm">
                  <span className="text-gray-300">{targetId.replace(/_/g, ' ')}</span>
                  <span className={clsx(
                    rel.trustLevel > 60 ? 'text-green-400' :
                    rel.trustLevel > 40 ? 'text-gray-400' : 'text-red-400'
                  )}>
                    Trust: {rel.trustLevel}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default NPCPanel;