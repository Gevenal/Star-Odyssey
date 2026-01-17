import { useCallback } from 'react';
import { gameApi } from '@/api/gameApi';
import { useGameStore } from '@/stores/gameStore';
import { PlayerAction } from '@/types/game';
import { useGameStream } from './useGameStream';

/**
 * Hook for submitting player actions
 */
export const useGameActions = () => {
  const { sessionId, setLoading, setError, addNarration, setGameState } = useGameStore();
  const { startStream } = useGameStream({
    onComplete: () => setLoading(false),
    onError: (error) => {
      setLoading(false);
      setError(error.message);
    },
  });

  /**
   * Submit action with streaming narration
   */
  const submitActionStreaming = useCallback(
    async (actionData: Omit<PlayerAction, 'sessionId'>) => {
      if (!sessionId) {
        setError('No active game session');
        return;
      }

      setLoading(true);
      setError(null);

      const action: PlayerAction = {
        ...actionData,
        sessionId,
      };

      // Add player action to history
      addNarration('player', actionData.actionText);

      // Start streaming
      startStream(action);
    },
    [sessionId, setLoading, setError, addNarration, startStream]
  );

  /**
   * Submit action without streaming (instant response)
   */
  const submitActionInstant = useCallback(
    async (actionData: Omit<PlayerAction, 'sessionId'>) => {
      if (!sessionId) {
        setError('No active game session');
        return;
      }

      setLoading(true);
      setError(null);

      const action: PlayerAction = {
        ...actionData,
        sessionId,
      };

      try {
        // Add player action to history
        addNarration('player', actionData.actionText);

        // Submit action
        const response = await gameApi.submitAction(action);

        // Add narration to history
        addNarration('narrator', response.narration);

        if (response.oracleMessage) {
          addNarration('oracle', response.oracleMessage);
        }

        // TODO: Update game state with response

        setLoading(false);
      } catch (error) {
        setLoading(false);
        setError(error instanceof Error ? error.message : 'Failed to submit action');
      }
    },
    [sessionId, setLoading, setError, addNarration]
  );

  /**
   * End current turn
   */
  const endTurn = useCallback(async () => {
    if (!sessionId) {
      setError('No active game session');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await gameApi.endTurn(sessionId);

      // Update game state
      setGameState(response.gameState);

      // Add turn summary
      addNarration('event', response.turnSummary);

      // Add events
      response.events.forEach((event) => {
        addNarration('event', event);
      });

      setLoading(false);
    } catch (error) {
      setLoading(false);
      setError(error instanceof Error ? error.message : 'Failed to end turn');
    }
  }, [sessionId, setLoading, setError, setGameState, addNarration]);

  return {
    submitActionStreaming,
    submitActionInstant,
    endTurn,
  };
};
