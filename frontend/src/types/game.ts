// Enums
export type GamePhase = 'intro' | 'playing' | 'ending';
export type TurnPhase = 'world_update' | 'event_generation' | 'npc_actions' | 'player_turn' | 'consequence_resolution' | 'end_check';
export type Atmosphere = 'normal' | 'toxic' | 'vacuum' | 'low_oxygen';
export type Mood = 'tense' | 'peaceful' | 'mysterious' | 'urgent' | 'desperate' | 'hopeful';
export type ConfidenceLevel = 'high' | 'medium' | 'speculative';

// Resources
export interface ResourceLevel {
  current: number;
  max: number;
  min: number;
  criticalThreshold: number;
  decayRate: number;
}

export interface ResourceLevels {
  oxygenLevel: ResourceLevel;
  fuelReserves: ResourceLevel;
  powerLevel: ResourceLevel;
  medicalSupplies: ResourceLevel;
  foodWater: ResourceLevel;
  repairMaterials: ResourceLevel;
}

// NPCs
export interface PersonalityTraits {
  coreValue: string;
  socialStyle: string;
  stressResponse: string;
  decisionMaking: string;
  morality: string;
  quirks: string[];
}

export interface NPCRelationship {
  targetNpcId: string;
  trustLevel: number;
  relationshipHistory: string[];
}

export interface NPCState {
  id: string;
  name: string;
  role: string;
  location: string;
  alive: boolean;
  health: number;
  stressLevel: number;
  personality: PersonalityTraits;
  relationships: Record<string, NPCRelationship>;
  goals: string[];
  currentActivity?: string;
}

// Game State
export interface PlayerState {
  name: string;
  health: number;
  stress: number;
  radiationExposure: number;
  location: string;
  inventory: string[];
  reputation: Record<string, number>;
  discoveredSecrets: string[];
  flags: Record<string, boolean>;
}

export interface WorldState {
  day: number;
  turn: number;
  timeOfDay: string;
  resources: ResourceLevels;
  crewMorale: number;
  crewCohesion: number;
  panicLevel: number;
  globalFlags: Record<string, boolean>;
  eventsOccurred: string[];
  activeThreats: string[];
}

export interface GameState {
  sessionId: string;
  phase: GamePhase;
  currentTurnPhase: TurnPhase;
  player: PlayerState;
  npcs: Record<string, NPCState>;
  world: WorldState;
  turnCount: number;
  oracleSentienceLevel: number;
  /** Recent turn history (backend may omit or truncate) */
  history?: Record<string, unknown>[];
  /** Set when game has ended */
  endingTriggered?: string | null;
}

// Actions & Responses
export interface PlayerAction {
  sessionId: string;
  actionType: string;
  actionId: string;
  actionText: string;
  targetLocation?: string;
  targetNpc?: string;
  targetItem?: string;
}

export interface StateChange {
  entityType: 'player' | 'npc' | 'world' | 'location';
  entityId?: string;
  field: string;
  oldValue?: string;
  newValue: string;
  reason: string;
}

export interface NPCReaction {
  npcId: string;
  reactionText: string;
  dispositionChange: number;
  newActivity?: string;
}

export interface GameActionResponse {
  success: boolean;
  narration: string;
  resourceChanges: Array<{ resourceName: string; changeAmount: number; reason: string }>;
  stateChanges: StateChange[];
  npcReactions: NPCReaction[];
  availableActions: string[];
  mood: Mood;
  triggerEnding: boolean;
  endingId?: string;
  oracleMessage?: string;
  confidenceLevel: ConfidenceLevel;
}
