import React, { useEffect, useState } from "react";
import { GameLayout } from "@/components/layout/GameLayout";
import { NarrationPanel } from "@/components/game/NarrationPanel";
import { ActionInput } from "@/components/game/ActionInput";
import { ResourceMonitor } from "@/components/game/ResourceMonitor";
import { NPCPanel } from "@/components/game/NPCPanel";
import { useGameStore } from "@/stores/gameStore";
import { useGameActions } from "@/hooks/useGameActions";
import { gameApi } from "@/api/gameApi";
import { ActionDefinition } from "@/types/api";
import { useNavigate } from "react-router-dom";

interface GamePageProps {
  onExit?: () => void;
}

export const GamePage: React.FC<GamePageProps> = ({ onExit }) => {
  const { gameState, isLoading, sessionId, error, setError } = useGameStore();
  const { submitActionStreaming, endTurn } = useGameActions();
  const [availableActions, setAvailableActions] = useState<ActionDefinition[]>(
    [],
  );
  const [loadingActions, setLoadingActions] = useState(false);
  const navigate = useNavigate();

  // Fetch currently available actions (filtered by RulesEngine)
  const fetchAvailableActions = async () => {
    if (!sessionId) return;
    setLoadingActions(true);
    try {
      const actions = await gameApi.getAvailableActions(sessionId);
      setAvailableActions(actions);
    } catch (err) {
      console.error("Failed to fetch actions:", err);
    } finally {
      setLoadingActions(false);
    }
  };

  // Fetch available actions when game starts and state changes
  useEffect(() => {
    fetchAvailableActions();
  }, [sessionId, gameState?.world?.turn]);

  // Handle predefined action selection
  const handleActionSelect = (action: ActionDefinition) => {
    // Clear previous errors
    setError(null);
    submitActionStreaming({
      actionType: action.category,
      actionId: action.actionId,
      actionText: action.description,
    });
  };

  // Handle freeform action input
  const handleFreeformAction = (actionText: string) => {
    setError(null);
    submitActionStreaming({
      actionType: 'freeform',
      actionId: 'freeform',
      actionText,
    });
  };

  // Handle end turn
  const handleEndTurn = async () => {
    setError(null);
    await endTurn();
    // Refresh available actions
    fetchAvailableActions();
  };

  if (!gameState) {
    return (
      <div className="min-h-screen bg-space-900 flex items-center justify-center text-white">
        Loading...
      </div>
    );
  }

  // Group actions by category
  const actionsByCategory = availableActions.reduce(
    (acc, action) => {
      const cat = action.category || "Other";
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(action);
      return acc;
    },
    {} as Record<string, ActionDefinition[]>,
  );

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
        {/* Error Banner */}
        {error && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-3 flex items-center justify-between">
            <span className="text-red-400 text-sm">{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-300 text-sm"
            >
              ✕
            </button>
          </div>
        )}

        {/* Narration */}
        <div className="flex-1 overflow-hidden">
          <NarrationPanel />
        </div>

        {/* Action Input (Freeform) */}
        <div className="bg-gray-900 rounded-lg p-4">
          <ActionInput
            onSubmit={handleFreeformAction}
            disabled={isLoading}
            placeholder="Type your action..."
          />
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
            <div className="text-gray-400 text-center py-4">
              Loading actions...
            </div>
          ) : availableActions.length === 0 ? (
            <div className="text-gray-400 text-center py-4">
              No actions available
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(actionsByCategory).map(([category, actions]) => (
                <div key={category}>
                  <h4 className="text-gray-400 text-xs uppercase mb-2">
                    {category}
                  </h4>
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
