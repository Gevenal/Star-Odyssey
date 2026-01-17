import { create } from 'zustand';
import { GameState, GameActionResponse } from '@/types/game';

interface NarrationEntry {
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
  addNarration: (type: NarrationEntry['type'], content: string) => void;
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
  setSession: (id) => set({ sessionId: id }),

  setGameState: (state) => set({ gameState: state }),

  updateGameState: (partial) =>
    set((state) => ({
      gameState: state.gameState ? { ...state.gameState, ...partial } : null,
    })),

  addNarration: (type, content) =>
    set((state) => ({
      narrationHistory: [
        ...state.narrationHistory,
        { type, content, timestamp: Date.now() },
      ],
    })),

  setLoading: (loading) => set({ isLoading: loading }),

  setStreaming: (streaming) => set({ isStreaming: streaming }),

  appendStreamContent: (content) =>
    set((state) => ({
      streamingContent: state.streamingContent + content,
    })),

  clearStreamContent: () => set({ streamingContent: '' }),

  setAvailableActions: (actions) => set({ availableActions: actions }),

  setError: (error) => set({ error }),

  reset: () =>
    set({
      sessionId: null,
      gameState: null,
      narrationHistory: [],
      isLoading: false,
      isStreaming: false,
      streamingContent: '',
      availableActions: [],
      error: null,
    }),
}));
