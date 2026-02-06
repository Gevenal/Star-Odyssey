import { useCallback, useEffect, useRef } from 'react';
import { gameApi } from '@/api/gameApi';
import { useGameStore } from '@/stores/gameStore';
import { PlayerAction, GameActionResponse } from '@/types/game';

interface UseGameStreamOptions {
  onComplete?: (response?: GameActionResponse) => void;
  onError?: (error: Error) => void;
}

/**
 * Hook for managing SSE streaming of game narration
 */
export const useGameStream = (options?: UseGameStreamOptions) => {
  const eventSourceRef = useRef<EventSource | null>(null);
  const { setStreaming, appendStreamContent, clearStreamContent, addNarration } = useGameStore();

  const startStream = useCallback(
    (
      action: PlayerAction,
      callbacks?: {
        onComplete?: (response?: GameActionResponse) => void;
        onError?: (error: Error) => void;
      }
    ) => {
      // Clear previous stream content
      clearStreamContent();
      setStreaming(true);

      try {
        // Create EventSource connection
        const eventSource = gameApi.submitActionStream(action);
        eventSourceRef.current = eventSource;

        let completeResponse: GameActionResponse | undefined;

        // Handle incoming messages
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'narration') {
              // Backend sends {"type": "narration", "chunk": "..."}
              if (data.chunk) {
                appendStreamContent(data.chunk + ' ');
              }
            } else if (data.type === 'complete') {
              // Backend sends {"type": "complete", "response": {...}}
              setStreaming(false);
              completeResponse = data.response as GameActionResponse;

              // Add streamed content to history
              const { streamingContent } = useGameStore.getState();
              if (streamingContent.trim()) {
                addNarration('narrator', streamingContent.trim());
                clearStreamContent();
              } else if (completeResponse?.narration) {
                // If no streamed content, use narration from response
                addNarration('narrator', completeResponse.narration);
              }

              // Add Oracle message
              if (completeResponse?.oracleMessage) {
                addNarration('oracle', completeResponse.oracleMessage);
              }

              // Add NPC reactions
              if (completeResponse?.npcReactions) {
                completeResponse.npcReactions.forEach((reaction) => {
                  if (reaction.reactionText) {
                    addNarration('event', `${reaction.npcId}: ${reaction.reactionText}`);
                  }
                });
              }

              eventSource.close();
              eventSourceRef.current = null;

              // Call callbacks
              if (callbacks?.onComplete) {
                callbacks.onComplete(completeResponse);
              } else {
                options?.onComplete?.(completeResponse);
              }
            } else if (data.type === 'error') {
              setStreaming(false);
              clearStreamContent();
              eventSource.close();
              eventSourceRef.current = null;

              const error = new Error(data.message || 'Unknown error');
              if (callbacks?.onError) {
                callbacks.onError(error);
              } else {
                options?.onError?.(error);
              }
            }
          } catch (parseError) {
            console.error('Failed to parse SSE message:', parseError);
            // Continue processing, don't interrupt stream
          }
        };

        // Handle errors
        eventSource.onerror = (error) => {
          console.error('SSE Error:', error);
          setStreaming(false);
          clearStreamContent();
          if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
          }

          const streamError = new Error('Stream connection failed');
          if (callbacks?.onError) {
            callbacks.onError(streamError);
          } else {
            options?.onError?.(streamError);
          }
        };
      } catch (error) {
        setStreaming(false);
        clearStreamContent();
        const streamError = error instanceof Error ? error : new Error('Failed to start stream');
        if (callbacks?.onError) {
          callbacks.onError(streamError);
        } else {
          options?.onError?.(streamError);
        }
      }
    },
    [setStreaming, appendStreamContent, clearStreamContent, addNarration, options]
  );

  const stopStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setStreaming(false);
    }
  }, [setStreaming]);

  // Cleanup on unmount
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
