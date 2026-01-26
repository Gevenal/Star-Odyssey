import apiClient from './client';
import {
  GameStartRequest,
  GameStartResponse,
  ActionDefinition,
  TurnEndResponse,
  SaveGameResponse,
  LoadGameResponse,
} from '@/types/api';
import { GameState, GameActionResponse, PlayerAction } from '@/types/game';

export const gameApi = {
  /**
   * Start a new game session
   */
  startGame: async (playerName: string): Promise<GameStartResponse> => {
    const response = await apiClient.post<GameStartResponse>('/game/start', {
      player_name: playerName,
    });
    return response.data;
  },

  /**
   * Submit a player action (non-streaming)
   */
  submitAction: async (action: PlayerAction): Promise<GameActionResponse> => {
    const response = await apiClient.post<GameActionResponse>('/game/action', {
      session_id: action.sessionId,
      action_type: action.actionType,
      action_id: action.actionId,
      action_text: action.actionText,
      target_location: action.targetLocation,
      target_npc: action.targetNpc,
      target_item: action.targetItem,
    });
    return response.data;
  },

  /**
   * Submit a player action with SSE streaming
   */
  submitActionStream: (action: PlayerAction): EventSource => {
    // TODO: Implement SSE connection
    const params = new URLSearchParams({
      sessionId: action.sessionId,
      actionType: action.actionType,
      actionId: action.actionId,
      actionText: action.actionText,
    });

    if (action.targetLocation) params.append('targetLocation', action.targetLocation);
    if (action.targetNpc) params.append('targetNpc', action.targetNpc);
    if (action.targetItem) params.append('targetItem', action.targetItem);

    const url = `${apiClient.defaults.baseURL}/game/action/stream?${params.toString()}`;
    return new EventSource(url);
  },

  /**
   * Get current game state
   */
  getGameState: async (sessionId: string): Promise<GameState> => {
    // TODO: Implement API call
    const response = await apiClient.get<GameState>(`/game/state/${sessionId}`);
    return response.data;
  },

  /**
   * Get available actions for current state
   */
  getAvailableActions: async (sessionId: string): Promise<ActionDefinition[]> => {
    // TODO: Implement API call
    const response = await apiClient.get<ActionDefinition[]>(`/game/actions/${sessionId}`);
    return response.data;
  },

  /**
   * End the current turn
   */
  endTurn: async (sessionId: string): Promise<TurnEndResponse> => {
    const response = await apiClient.post<TurnEndResponse>(`/game/end-turn/${sessionId}`);
    return response.data;
  },

  /**
   * Save current game
   */
  saveGame: async (sessionId: string): Promise<SaveGameResponse> => {
    // TODO: Implement API call
    const response = await apiClient.post<SaveGameResponse>(`/game/save/${sessionId}`);
    return response.data;
  },

  /**
   * Load a saved game
   */
  loadGame: async (saveId: string): Promise<GameState> => {
    // TODO: Implement API call
    const response = await apiClient.get<LoadGameResponse>(`/game/load/${saveId}`);
    return response.data.gameState;
  },
};
