import { create } from 'zustand';
import { GameState, GameActionResponse, StateChange, NPCReaction } from '@/types/game';

const NARRATION_STORAGE_PREFIX = 'star_odyssey:narration:';

export function getNarrationStorageKey(sessionId: string): string {
  return NARRATION_STORAGE_PREFIX + sessionId;
}

export function getNarrationFromStorage(sessionId: string): NarrationEntry[] {
  try {
    const raw = localStorage.getItem(getNarrationStorageKey(sessionId));
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (e): e is NarrationEntry =>
        e != null &&
        typeof e === 'object' &&
        ['player', 'narrator', 'oracle', 'event'].includes((e as NarrationEntry).type) &&
        typeof (e as NarrationEntry).content === 'string' &&
        typeof (e as NarrationEntry).timestamp === 'number'
    );
  } catch {
    return [];
  }
}

export interface NarrationEntry {
  type: 'player' | 'narrator' | 'oracle' | 'event';
  content: string;
  timestamp: number;
}

interface GameStore {
  // State
  sessionId: string | null;
  gameState: GameState | null;
  narrationHistory: NarrationEntry[];
  isLoading: boolean;
  isStreaming: boolean;
  streamingContent: string;
  availableActions: string[];
  error: string | null;

  // Actions
  setSession: (id: string) => void;
  setGameState: (state: GameState) => void;
  updateGameState: (partial: Partial<GameState>) => void;
  applyActionResponse: (response: GameActionResponse) => void;
  addNarration: (type: NarrationEntry['type'], content: string) => void;
  setNarrationHistory: (entries: NarrationEntry[]) => void;
  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  appendStreamContent: (content: string) => void;
  clearStreamContent: () => void;
  setAvailableActions: (actions: string[]) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useGameStore = create<GameStore>((set) => ({
  // Initial state
  sessionId: null,
  gameState: null,
  narrationHistory: [],
  isLoading: false,
  isStreaming: false,
  streamingContent: '',
  availableActions: [],
  error: null,

  // Action implementations
  setSession: (id: string) => set({ sessionId: id }),

  setGameState: (state: GameState) => set({ gameState: state }),

  updateGameState: (partial: Partial<GameState>) =>
    set((state: GameStore) => ({
      gameState: state.gameState ? { ...state.gameState, ...partial } : null,
    })),

  /**
   * Apply action response and update game state
   * Handles state changes, resource changes, NPC reactions, etc.
   */
  applyActionResponse: (response: GameActionResponse) =>
    set((state: GameStore) => {
      if (!state.gameState) return state;

      const newState = { ...state.gameState };

      // Apply state changes
      response.stateChanges.forEach((change: StateChange) => {
        applyStateChange(newState, change);
      });

      // Apply resource changes
      response.resourceChanges.forEach((change: { resourceName: string; changeAmount: number; reason?: string }) => {
        applyResourceChange(newState, change);
      });

      // Apply NPC reactions
      response.npcReactions.forEach((reaction: NPCReaction) => {
        applyNPCReaction(newState, reaction);
      });

      // Update available actions
      const availableActions = response.availableActions || [];

      // Check if ending is triggered
      if (response.triggerEnding) {
        newState.phase = 'ending';
      }

      return {
        gameState: newState,
        availableActions,
      };
    }),

  addNarration: (type: NarrationEntry['type'], content: string) =>
    set((state: GameStore) => {
      const entries = [
        ...state.narrationHistory,
        { type, content, timestamp: Date.now() },
      ];
      if (state.sessionId) {
        try {
          localStorage.setItem(
            getNarrationStorageKey(state.sessionId),
            JSON.stringify(entries)
          );
        } catch {
          // ignore quota or other storage errors
        }
      }
      return { narrationHistory: entries };
    }),

  setNarrationHistory: (entries: NarrationEntry[]) =>
    set({ narrationHistory: entries }),

  setLoading: (loading: boolean) => set({ isLoading: loading }),

  setStreaming: (streaming: boolean) => set({ isStreaming: streaming }),

  appendStreamContent: (content: string) =>
    set((state: GameStore) => ({
      streamingContent: state.streamingContent + content,
    })),

  clearStreamContent: () => set({ streamingContent: '' }),

  setAvailableActions: (actions: string[]) => set({ availableActions: actions }),

  setError: (error: string | null) => set({ error }),

  reset: () =>
    set((state: GameStore) => {
      if (state.sessionId) {
        try {
          localStorage.removeItem(getNarrationStorageKey(state.sessionId));
        } catch {
          // ignore
        }
      }
      return {
        sessionId: null,
        gameState: null,
        narrationHistory: [],
        isLoading: false,
        isStreaming: false,
        streamingContent: '',
        availableActions: [],
        error: null,
      };
    }),
}));

/**
 * Apply a single state change to the game state
 */
function applyStateChange(state: GameState, change: StateChange): void {
  const { entityType, entityId, field, newValue } = change;

  switch (entityType) {
    case 'player':
      if (field in state.player) {
        (state.player as any)[field] = parseValue(newValue, (state.player as any)[field]);
      }
      break;

    case 'npc':
      if (entityId && state.npcs[entityId]) {
        const npc = state.npcs[entityId];
        if (field in npc) {
          (npc as any)[field] = parseValue(newValue, (npc as any)[field]);
        }
      }
      break;

    case 'world':
      if (field in state.world) {
        (state.world as any)[field] = parseValue(newValue, (state.world as any)[field]);
      }
      break;

    case 'location':
      // Location-related state changes can be handled here
      break;
  }
}

/**
 * Apply resource changes
 */
function applyResourceChange(state: GameState, change: { resourceName: string; changeAmount: number }): void {
  const { resourceName, changeAmount } = change;
  const resourceKey = resourceNameToKey(resourceName);

  if (resourceKey && state.world.resources[resourceKey]) {
    const resource = state.world.resources[resourceKey];
    resource.current = Math.max(
      resource.min,
      Math.min(resource.max, resource.current + changeAmount)
    );
  }
}

/**
 * Apply NPC reactions
 */
function applyNPCReaction(state: GameState, reaction: NPCReaction): void {
  const { npcId, newActivity, dispositionChange } = reaction;

  if (state.npcs[npcId]) {
    const npc = state.npcs[npcId];

    // Update activity
    if (newActivity) {
      npc.currentActivity = newActivity;
    }

    // Update relationship (if player relationship exists)
    if (state.player.name && npc.relationships[state.player.name]) {
      const relationship = npc.relationships[state.player.name];
      relationship.trustLevel = Math.max(0, Math.min(100, relationship.trustLevel + dispositionChange));
    }
  }
}

/**
 * Convert resource name to resource key
 */
function resourceNameToKey(resourceName: string): keyof GameState['world']['resources'] | null {
  const mapping: Record<string, keyof GameState['world']['resources']> = {
    oxygen: 'oxygenLevel',
    fuel: 'fuelReserves',
    power: 'powerLevel',
    medical: 'medicalSupplies',
    food: 'foodWater',
    repair: 'repairMaterials',
  };

  const lowerName = resourceName.toLowerCase();
  for (const [key, value] of Object.entries(mapping)) {
    if (lowerName.includes(key)) {
      return value;
    }
  }

  return null;
}

/**
 * Parse new value while maintaining type consistency
 */
function parseValue(newValue: string, oldValue: any): any {
  // Try to parse as number
  if (typeof oldValue === 'number') {
    const num = parseFloat(newValue);
    if (!isNaN(num)) return num;
  }

  // Try to parse as boolean
  if (typeof oldValue === 'boolean') {
    if (newValue.toLowerCase() === 'true') return true;
    if (newValue.toLowerCase() === 'false') return false;
  }

  // Try to parse as array
  if (Array.isArray(oldValue)) {
    try {
      const parsed = JSON.parse(newValue);
      if (Array.isArray(parsed)) return parsed;
    } catch {
      // If not JSON, try splitting by comma
      if (newValue.includes(',')) {
        return newValue.split(',').map((s) => s.trim());
      }
    }
  }

  // Try to parse as object
  if (typeof oldValue === 'object' && oldValue !== null && !Array.isArray(oldValue)) {
    try {
      const parsed = JSON.parse(newValue);
      if (typeof parsed === 'object' && !Array.isArray(parsed)) return parsed;
    } catch {
      // Parse failed, return original value
    }
  }

  // Default to returning string
  return newValue;
}
