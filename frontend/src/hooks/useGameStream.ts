import { useCallback, useEffect, useRef } from 'react';
import { gameApi } from '@/api/gameApi';
import { useGameStore } from '@/stores/gameStore';
import { PlayerAction, GameActionResponse } from '@/types/game';

interface UseGameStreamOptions {
  onComplete?: (response?: GameActionResponse) => void;
  onError?: (error: Error) => void;
}

/**
 * Hook for managing SSE streaming of game narration.
 * Uses POST /game/action/stream under the hood (fetch + ReadableStream).
 */
export const useGameStream = (options?: UseGameStreamOptions) => {
  const streamControllerRef = useRef<{ close: () => void } | null>(null);
  const streamedContentRef = useRef('');
  const { setStreaming, appendStreamContent, clearStreamContent, addNarration } = useGameStore();

  const startStream = useCallback(
    (
      action: PlayerAction,
      callbacks?: {
        onComplete?: (response?: GameActionResponse) => void;
        onError?: (error: Error) => void;
      }
    ) => {
      clearStreamContent();
      streamedContentRef.current = '';
      setStreaming(true);
      streamControllerRef.current = null;

      const controller = gameApi.submitActionStream(action, {
        onChunk: (chunk) => {
          streamedContentRef.current += chunk + ' ';
          appendStreamContent(chunk + ' ');
        },
        onComplete: (response) => {
          setStreaming(false);
          streamControllerRef.current = null;

          const streamed = streamedContentRef.current.trim();
          if (streamed) {
            addNarration('narrator', streamed);
            clearStreamContent();
          } else if (response?.narration) {
            addNarration('narrator', response.narration);
          }
          if (response?.oracleMessage) {
            addNarration('oracle', response.oracleMessage);
          }
          if (response?.npcReactions) {
            response.npcReactions.forEach((reaction) => {
              if (reaction.reactionText) {
                addNarration('event', `${reaction.npcId}: ${reaction.reactionText}`);
              }
            });
          }

          if (callbacks?.onComplete) {
            callbacks.onComplete(response);
          } else {
            options?.onComplete?.(response);
          }
        },
        onError: (error) => {
          setStreaming(false);
          clearStreamContent();
          streamControllerRef.current = null;
          if (callbacks?.onError) {
            callbacks.onError(error);
          } else {
            options?.onError?.(error);
          }
        },
      });

      streamControllerRef.current = controller;
    },
    [setStreaming, appendStreamContent, clearStreamContent, addNarration, options]
  );

  const stopStream = useCallback(() => {
    if (streamControllerRef.current) {
      streamControllerRef.current.close();
      streamControllerRef.current = null;
      setStreaming(false);
    }
  }, [setStreaming]);

  useEffect(() => {
    return () => {
      stopStream();
    };
  }, [stopStream]);

  return {
    startStream,
    stopStream,
  };
};
