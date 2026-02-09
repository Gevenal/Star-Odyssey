import { create } from 'zustand';

interface Modal {
  type: 'npc-detail' | 'choice' | 'game-over' | 'save-load' | null;
  data?: any;
}

interface UIStore {
  // State
  activeModal: Modal;
  showInventory: boolean;
  showNPCPanel: boolean;
  showShipSystems: boolean;
  showOracleTerminal: boolean;
  sidebarCollapsed: boolean;
  textSpeed: 'slow' | 'medium' | 'fast' | 'instant';
  soundEnabled: boolean;
  musicVolume: number;
  sfxVolume: number;

  // Actions
  openModal: (type: Modal['type'], data?: any) => void;
  closeModal: () => void;
  toggleInventory: () => void;
  toggleNPCPanel: () => void;
  toggleShipSystems: () => void;
  toggleOracleTerminal: () => void;
  toggleSidebar: () => void;
  setTextSpeed: (speed: 'slow' | 'medium' | 'fast' | 'instant') => void;
  setSoundEnabled: (enabled: boolean) => void;
  setMusicVolume: (volume: number) => void;
  setSfxVolume: (volume: number) => void;
}

export const useUIStore = create<UIStore>((set) => ({
  // Initial state
  activeModal: { type: null },
  showInventory: false,
  showNPCPanel: true,
  showShipSystems: true,
  showOracleTerminal: false,
  sidebarCollapsed: false,
  textSpeed: 'medium',
  soundEnabled: true,
  musicVolume: 0.7,
  sfxVolume: 0.8,

  // Action implementations
  openModal: (type, data) => set({ activeModal: { type, data } }),

  closeModal: () => set({ activeModal: { type: null } }),

  toggleInventory: () => set((state: UIStore) => ({ showInventory: !state.showInventory })),

  toggleNPCPanel: () => set((state: UIStore) => ({ showNPCPanel: !state.showNPCPanel })),

  toggleShipSystems: () => set((state: UIStore) => ({ showShipSystems: !state.showShipSystems })),

  toggleOracleTerminal: () => set((state: UIStore) => ({ showOracleTerminal: !state.showOracleTerminal })),

  toggleSidebar: () => set((state: UIStore) => ({ sidebarCollapsed: !state.sidebarCollapsed })),

  setTextSpeed: (speed: 'slow' | 'medium' | 'fast' | 'instant') => set({ textSpeed: speed }),

  setSoundEnabled: (enabled: boolean | boolean | boolean) => set({ soundEnabled: enabled }),

  setMusicVolume: (volume: number | number | number) => set({ musicVolume: volume }),

  setSfxVolume: (volume: number | number | number) => set({ sfxVolume: volume }),
}));
