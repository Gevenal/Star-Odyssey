import apiClient, { apiRequest } from './client';
import {
  GameStartResponse,
  ActionDefinition,
  AvailableActionsResponse,
  TurnEndResponse,
  EndingResponse,
  SaveGameResponse,
  LoadGameResponse,
} from '@/types/api';
import { GameState, GameActionResponse, PlayerAction } from '@/types/game';

const BASE_URL = apiClient.defaults.baseURL ?? 'http://localhost:8000/api/v1';

/** Request body for backend (snake_case) */
function toActionBody(action: PlayerAction): Record<string, unknown> {
  return {
    session_id: action.sessionId,
    action_type: action.actionType,
    action_id: action.actionId,
    action_text: action.actionText,
    ...(action.targetLocation != null && { target_location: action.targetLocation }),
    ...(action.targetNpc != null && { target_npc: action.targetNpc }),
    ...(action.targetItem != null && { target_item: action.targetItem }),
  };
}

export const gameApi = {
  /**
   * Start a new game session.
   * Uses retry for transient failures.
   */
  startGame: (playerName: string): Promise<GameStartResponse> =>
    apiRequest<GameStartResponse>({
      method: 'POST',
      url: '/game/start',
      data: { player_name: playerName },
    }),

  /**
   * Submit a player action (non-streaming).
   */
  submitAction: (action: PlayerAction): Promise<GameActionResponse> =>
    apiRequest<GameActionResponse>({
      method: 'POST',
      url: '/game/action',
      data: toActionBody(action),
    }),

  /**
   * Submit a player action with SSE streaming (POST + stream).
   * Backend expects POST /game/action/stream with JSON body; EventSource is GET-only, so we use fetch.
   * Returns a controller with close() to abort the stream.
   */
  submitActionStream: (
    action: PlayerAction,
    callbacks: {
      onChunk?: (chunk: string) => void;
      onComplete?: (response: GameActionResponse) => void;
      onError?: (error: Error) => void;
    }
  ): { close: () => void } => {
    const ac = new AbortController();
    const body = JSON.stringify(toActionBody(action));

    (async () => {
      try {
        const res = await fetch(`${BASE_URL}/game/action/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body,
          signal: ac.signal,
        });

        if (!res.ok) {
          const text = await res.text();
          let message = res.statusText;
          try {
            const j = JSON.parse(text) as { detail?: string; message?: string };
            message = (j.detail ?? j.message ?? text) || message;
          } catch {
            message = text || message;
          }
          callbacks.onError?.(new Error(message));
          return;
        }

        const reader = res.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) {
          callbacks.onError?.(new Error('No response body'));
          return;
        }

        let buffer = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() ?? '';
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const raw = line.slice(6).trim();
              if (!raw) continue;
              try {
                const data = JSON.parse(raw) as {
                  type: string;
                  chunk?: string;
                  response?: GameActionResponse;
                  code?: number;
                  message?: string;
                };
                if (data.type === 'narration' && data.chunk) {
                  callbacks.onChunk?.(data.chunk);
                } else if (data.type === 'complete' && data.response) {
                  callbacks.onComplete?.(data.response);
                  return;
                } else if (data.type === 'error') {
                  callbacks.onError?.(new Error(data.message ?? 'Stream error'));
                  return;
                }
              } catch {
                // skip malformed line
              }
            }
          }
        }
      } catch (e) {
        if ((e as Error).name === 'AbortError') return;
        callbacks.onError?.(e instanceof Error ? e : new Error(String(e)));
      }
    })();

    return {
      close: () => ac.abort(),
    };
  },

  /**
   * Get current game state.
   */
  getGameState: (sessionId: string): Promise<GameState> =>
    apiRequest<GameState>({
      method: 'GET',
      url: `/game/state/${sessionId}`,
    }),

  /**
   * Get available actions for the current state.
   */
  getAvailableActions: async (sessionId: string): Promise<ActionDefinition[]> => {
    const data = await apiRequest<AvailableActionsResponse>({
      method: 'GET',
      url: `/game/actions/${sessionId}`,
    });
    return data.actions ?? [];
  },

  /**
   * End the current turn.
   */
  endTurn: (sessionId: string): Promise<TurnEndResponse> =>
    apiRequest<TurnEndResponse>({
      method: 'POST',
      url: `/game/end-turn/${sessionId}`,
    }),

  /**
   * Get ending narration and summary.
   */
  getEnding: (sessionId: string): Promise<EndingResponse> =>
    apiRequest<EndingResponse>({
      method: 'GET',
      url: `/game/ending/${sessionId}`,
    }),

  /**
   * Save current game.
   */
  saveGame: (sessionId: string): Promise<SaveGameResponse> =>
    apiRequest<SaveGameResponse>({
      method: 'POST',
      url: `/game/save/${sessionId}`,
    }),

  /**
   * Load a saved game by save ID.
   */
  loadGame: async (saveId: string): Promise<GameState> => {
    const data = await apiRequest<LoadGameResponse>({
      method: 'GET',
      url: `/game/load/${saveId}`,
    });
    return data.gameState;
  },
};
