import React from 'react';
import { GameLayout } from '@/components/layout/GameLayout';
import { NarrationPanel } from '@/components/game/NarrationPanel';
import { ActionInput } from '@/components/game/ActionInput';
import { ResourceMonitor } from '@/components/game/ResourceMonitor';
import { NPCPanel } from '@/components/game/NPCPanel';
import { useGameStore } from '@/stores/gameStore';
import { useGameActions } from '@/hooks/useGameActions';

export const GamePage: React.FC = () => {
  const { gameState, isLoading } = useGameStore();
  const { submitActionStreaming } = useGameActions();

  // TODO: Implement game page layout
  // TODO: Add modal management
  // TODO: Add event notifications

  const handleActionSubmit = (actionText: string) => {
    submitActionStreaming({
      actionType: 'freeform',
      actionId: 'custom',
      actionText,
    });
  };

  if (!gameState) {
    return <div>Loading...</div>;
  }

  return (
    <GameLayout
      sidebar={
        <div className="space-y-4">
          <ResourceMonitor resources={gameState.world.resources} />
          <NPCPanel npcs={gameState.npcs} />
        </div>
      }
    >
      <div className="h-full flex flex-col gap-4">
        {/* Narration */}
        <div className="flex-1">
          <NarrationPanel />
        </div>

        {/* Action input */}
        <div>
          <ActionInput
            onSubmit={handleActionSubmit}
            disabled={isLoading}
          />
        </div>
      </div>
    </GameLayout>
  );
};
