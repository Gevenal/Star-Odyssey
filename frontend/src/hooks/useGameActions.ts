import { useCallback } from 'react';
import { gameApi } from '@/api/gameApi';
import { useGameStore } from '@/stores/gameStore';
import { PlayerAction } from '@/types/game';
import { useGameStream } from './useGameStream';
import { useNavigate } from 'react-router-dom';

/**
 * Hook for submitting player actions
 */
export const useGameActions = () => {
  const navigate = useNavigate();
  const {
    sessionId,
    setLoading,
    setError,
    addNarration,
    setGameState,
    applyActionResponse,
    setAvailableActions,
  } = useGameStore();
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

      // Handle empty actions
      if (!actionData.actionText?.trim() && !actionData.actionId) {
        setError('Please provide an action');
        return;
      }

      setLoading(true);
      setError(null);

      const action: PlayerAction = {
        ...actionData,
        sessionId,
      };

      // Add player action to history
      if (actionData.actionText) {
        addNarration('player', actionData.actionText);
      }

      // Start streaming with enhanced callback
      startStream(action, {
        onComplete: async (response) => {
          // Apply response to game state
          if (response) {
            applyActionResponse(response);

            // Update available actions
            if (response.availableActions) {
              setAvailableActions(response.availableActions);
            }

            // Check if ending is triggered
            if (response.triggerEnding && response.endingId) {
              navigate(`/ending/${sessionId}`);
              return;
            }

            // Refresh game state to ensure synchronization
            try {
              const updatedState = await gameApi.getGameState(sessionId);
              setGameState(updatedState);
            } catch (stateError) {
              console.warn('Failed to refresh game state:', stateError);
              // Don't block flow, state already updated via applyActionResponse
            }
          }

          setLoading(false);
        },
        onError: (error) => {
          setLoading(false);
          setError(error.message);
          addNarration('event', `Error: ${error.message}`);
        },
      });
    },
    [
      sessionId,
      setLoading,
      setError,
      addNarration,
      startStream,
      applyActionResponse,
      setAvailableActions,
      setGameState,
      navigate,
    ]
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

      // Handle empty actions
      if (!actionData.actionText?.trim() && !actionData.actionId) {
        setError('Please provide an action');
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
        if (actionData.actionText) {
          addNarration('player', actionData.actionText);
        }

        // Submit action
        const response = await gameApi.submitAction(action);

        // Handle empty response or failed actions
        if (!response.success) {
          addNarration('narrator', response.narration || 'Action could not be completed.');
          setLoading(false);
          return;
        }

        // Add narration to history
        addNarration('narrator', response.narration);

        if (response.oracleMessage) {
          addNarration('oracle', response.oracleMessage);
        }

        // Apply response to game state
        applyActionResponse(response);

        // Update available actions
        if (response.availableActions) {
          setAvailableActions(response.availableActions);
        }

        // Check if ending is triggered
        if (response.triggerEnding && response.endingId) {
          navigate(`/ending/${sessionId}`);
          return;
        }

        // Refresh game state to ensure synchronization
        try {
          const updatedState = await gameApi.getGameState(sessionId);
          setGameState(updatedState);
        } catch (stateError) {
          console.warn('Failed to refresh game state:', stateError);
          // Don't block flow, state already updated via applyActionResponse
        }

        setLoading(false);
      } catch (error) {
        setLoading(false);
        const errorMessage =
          error instanceof Error ? error.message : 'Failed to submit action';
        setError(errorMessage);
        addNarration('event', `Error: ${errorMessage}`);
      }
    },
    [
      sessionId,
      setLoading,
      setError,
      addNarration,
      applyActionResponse,
      setAvailableActions,
      setGameState,
      navigate,
    ]
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
      if (response.turnSummary) {
        addNarration('event', response.turnSummary);
      }

      // Add events
      if (response.events && response.events.length > 0) {
        response.events.forEach((event) => {
          addNarration('event', event);
        });
      } else {
        // If no events, add default message
        addNarration('event', 'Time passes...');
      }

      // Check if game is over
      if (
        response.gameState?.phase === 'ending' ||
        response.gameState?.world?.game_meta?.game_phase === 'ending'
      ) {
        navigate(`/ending/${sessionId}`);
        return;
      }

      setLoading(false);
    } catch (error) {
      setLoading(false);
      const errorMessage =
        error instanceof Error ? error.message : 'Failed to end turn';
      setError(errorMessage);
      addNarration('event', `Error ending turn: ${errorMessage}`);
    }
  }, [sessionId, setLoading, setError, setGameState, addNarration, navigate]);

  return {
    submitActionStreaming,
    submitActionInstant,
    endTurn,
  };
};
