import React, { useEffect, useState } from 'react';
import { GameLayout } from '@/components/layout/GameLayout';
import { NarrationPanel } from '@/components/game/NarrationPanel';
import { ActionInput } from '@/components/game/ActionInput';
import { ResourceMonitor } from '@/components/game/ResourceMonitor';
import { NPCPanel } from '@/components/game/NPCPanel';
import { useGameStore } from '@/stores/gameStore';
import { useGameActions } from '@/hooks/useGameActions';
import { gameApi } from '@/api/gameApi';
import { ActionDefinition } from '@/types/api';

interface GamePageProps {
  onExit?: () => void;
}

export const GamePage: React.FC<GamePageProps> = ({ onExit }) => {
  const { gameState, isLoading, sessionId, addNarration, setGameState } = useGameStore();
  const { submitActionStreaming } = useGameActions();
  const [availableActions, setAvailableActions] = useState<ActionDefinition[]>([]);
  const [loadingActions, setLoadingActions] = useState(false);

  // 获取当前可用的 actions（基于 RulesEngine 过滤）
  const fetchAvailableActions = async () => {
    if (!sessionId) return;
    setLoadingActions(true);
    try {
      const actions = await gameApi.getAvailableActions(sessionId);
      setAvailableActions(actions);
    } catch (err) {
      console.error('Failed to fetch actions:', err);
    } finally {
      setLoadingActions(false);
    }
  };

  // 游戏开始时和状态变化时获取可用 actions
  useEffect(() => {
    fetchAvailableActions();
  }, [sessionId, gameState?.world?.turn]);

  // 处理选择预定义的 action
  const handleActionSelect = (action: ActionDefinition) => {
    submitActionStreaming({
      actionType: action.category,
      actionId: action.actionId,
      actionText: action.description,
    });
  };

  // 结束回合
  const handleEndTurn = async () => {
    if (!sessionId) return;
    try {
      const response = await gameApi.endTurn(sessionId);
      addNarration('narrator', response.turnSummary || 'Time passes...');
      if (response.events && response.events.length > 0) {
        response.events.forEach((event: string) => addNarration('event', event));
      }
      // 刷新游戏状态
      const newState = await gameApi.getGameState(sessionId);
      setGameState(newState);
      // 刷新可用 actions
      fetchAvailableActions();
    } catch (err) {
      console.error('Failed to end turn:', err);
    }
  };

  if (!gameState) {
    return <div className="min-h-screen bg-space-900 flex items-center justify-center text-white">Loading...</div>;
  }

  // 按类别分组 actions
  const actionsByCategory = availableActions.reduce((acc, action) => {
    const cat = action.category || 'Other';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(action);
    return acc;
  }, {} as Record<string, ActionDefinition[]>);

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
        <div className="flex-1 overflow-hidden">
          <NarrationPanel />
        </div>

        {/* Available Actions */}
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-bold">Available Actions</h3>
            <button
              onClick={handleEndTurn}
              disabled={isLoading}
              className="px-4 py-2 bg-yellow-600 hover:bg-yellow-500 disabled:bg-gray-600 text-white rounded font-bold transition-colors"
            >
              ⏭️ End Turn
            </button>
          </div>
          
          {loadingActions ? (
            <div className="text-gray-400 text-center py-4">Loading actions...</div>
          ) : availableActions.length === 0 ? (
            <div className="text-gray-400 text-center py-4">No actions available</div>
          ) : (
            <div className="space-y-3">
              {Object.entries(actionsByCategory).map(([category, actions]) => (
                <div key={category}>
                  <h4 className="text-gray-400 text-xs uppercase mb-2">{category}</h4>
                  <div className="grid grid-cols-2 gap-2">
                    {actions.map((action) => (
                      <button
                        key={action.actionId}
                        onClick={() => handleActionSelect(action)}
                        disabled={isLoading}
                        className="px-3 py-2 bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 text-gray-200 rounded text-sm transition-colors text-left"
                        title={action.description}
                      >
                        {action.displayName}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </GameLayout>
  );
};
