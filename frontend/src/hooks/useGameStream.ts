import { useCallback, useEffect, useRef } from 'react';
import { gameApi } from '@/api/gameApi';
import { useGameStore } from '@/stores/gameStore';
import { PlayerAction } from '@/types/game';

interface UseGameStreamOptions {
  onComplete?: () => void;
  onError?: (error: Error) => void;
}

/**
 * Hook for managing SSE streaming of game narration
 */
export const useGameStream = (options?: UseGameStreamOptions) => {
  const eventSourceRef = useRef<EventSource | null>(null);
  const { setStreaming, appendStreamContent, clearStreamContent, addNarration } = useGameStore();

  const startStream = useCallback((action: PlayerAction) => {
    // TODO: Implement SSE streaming

    // Clear previous stream content
    clearStreamContent();
    setStreaming(true);

    try {
      // Create EventSource connection
      const eventSource = gameApi.submitActionStream(action);
      eventSourceRef.current = eventSource;

      // Handle incoming messages
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'narration_chunk') {
          appendStreamContent(data.content);
        } else if (data.type === 'complete') {
          // Stream complete
          setStreaming(false);
          addNarration('narrator', data.fullNarration);
          eventSource.close();
          options?.onComplete?.();
        }
      };

      // Handle errors
      eventSource.onerror = (error) => {
        console.error('SSE Error:', error);
        setStreaming(false);
        eventSource.close();
        options?.onError?.(new Error('Stream connection failed'));
      };
    } catch (error) {
      setStreaming(false);
      options?.onError?.(error as Error);
    }
  }, [setStreaming, appendStreamContent, clearStreamContent, addNarration, options]);

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
