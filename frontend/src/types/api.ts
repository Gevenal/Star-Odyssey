import { GameState, GameActionResponse, PlayerAction } from './game';

// API Request types
export interface GameStartRequest {
  playerName: string;
}

export interface ActionSubmitRequest extends PlayerAction {}

// API Response types
export interface GameStartResponse {
  sessionId: string;
  gameState: GameState;
  initialNarration: string;
  availableActions?: string[];
  oracleMessage?: string;
}

export interface ActionDefinition {
  actionId: string;
  displayName: string;
  description: string;
  category: string;
  requirements?: {
    location?: string;
    items?: string[];
    timeCost?: number;
  };
  possibleOutcomes?: string[];
  cooldown?: number;
  oneTime?: boolean;
}

export interface AvailableActionsResponse {
  actions: ActionDefinition[];
  contextHints: string[];
  urgentActions: string[];
}

export interface TurnEndResponse {
  gameState: GameState;
  turnSummary: string;
  events: string[];
}

export interface SaveGameResponse {
  saveId: string;
  savedAt: string;
}

export interface LoadGameResponse {
  gameState: GameState;
}

export interface ErrorResponse {
  detail: string;
  errorCode?: string;
}
