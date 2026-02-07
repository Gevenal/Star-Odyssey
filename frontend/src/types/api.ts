import { GameState, PlayerAction } from './game';

// ---------------------------------------------------------------------------
// Normalized API Error (for consistent handling across the app)
// ---------------------------------------------------------------------------

export interface ApiErrorDetail {
  message: string;
  status?: number;
  code?: string;
  detail?: string;
  retryable?: boolean;
}

export class ApiError extends Error {
  readonly status?: number;
  readonly code?: string;
  readonly detail?: string;
  readonly retryable: boolean;
  readonly originalError?: unknown;

  constructor(detail: ApiErrorDetail, originalError?: unknown) {
    super(detail.message);
    this.name = 'ApiError';
    this.status = detail.status;
    this.code = detail.code;
    this.detail = detail.detail;
    this.retryable = detail.retryable ?? false;
    this.originalError = originalError;
    Object.setPrototypeOf(this, ApiError.prototype);
  }

  static fromAxios(error: unknown): ApiError {
    const ax = error as { response?: { status: number; data?: { detail?: string; message?: string } }; code?: string; message?: string };
    const status = ax.response?.status;
    const message =
      ax.response?.data?.detail ??
      ax.response?.data?.message ??
      ax.message ??
      'An unexpected error occurred';
    const retryable =
      status != null && status >= 500 ||
      ax.code === 'ECONNABORTED' ||
      ax.code === 'ERR_NETWORK';

    return new ApiError(
      {
        message: normalizeMessage(message, status, ax.code),
        status,
        code: ax.code,
        detail: typeof ax.response?.data?.detail === 'string' ? ax.response.data.detail : undefined,
        retryable,
      },
      error
    );
  }
}

function normalizeMessage(message: string, status?: number, code?: string): string {
  if (status === 404) return 'Resource not found. Please check your session ID.';
  if (status === 400) return `Invalid request: ${message}`;
  if (status === 409) return 'Game session has ended or is invalid.';
  if (status != null && status >= 500) return 'Server error. Please try again later.';
  if (code === 'ECONNABORTED') return 'Request timeout. Please check your connection.';
  if (code === 'ERR_NETWORK') return 'Network error. Please check your connection.';
  return message;
}

// ---------------------------------------------------------------------------
// API Request types
// ---------------------------------------------------------------------------

export interface GameStartRequest {
  playerName: string;
}

export interface ActionSubmitRequest extends PlayerAction {}

// ---------------------------------------------------------------------------
// API Response types (aligned with backend camelCase / aliases)
// ---------------------------------------------------------------------------

export interface GameStartResponse {
  sessionId: string;
  gameState: GameState;
  initialNarration: string;
  availableActions?: string[];
  oracleMessage?: string;
}

export interface ActionRequirement {
  location?: string;
  items?: string[];
  timeCost?: number;
  minResourceLevels?: Record<string, number>;
  npcPresent?: string;
  minHealth?: number;
  maxStress?: number;
  requiredFlags?: Record<string, boolean>;
}

/** Action definition returned by GET /game/actions; used by ActionMenu and others */
export interface ActionDefinition {
  actionId: string;
  displayName: string;
  description: string;
  category: string;
  /** Time cost in turns; ActionMenu may read this at top level */
  timeCost?: number;
  requirements?: ActionRequirement;
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
  eventsOccurred: string[];
  npcActionsTaken: string[];
  stateSummary: Record<string, unknown>;
  narration: string;
  criticalAlerts: string[];
  turnNumber: number;
}

export interface EndingStatistics {
  daysSurvived: number;
  crewSurvived: number;
  secretsDiscovered: number;
  playerAlive: boolean;
  crewMorale: number;
  oracleSentience: number;
}

export interface EndingResponse {
  endingType: string;
  title: string;
  narration: string;
  survivorFates: Record<string, string>;
  epilogue: string;
  statistics: EndingStatistics;
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

// ---------------------------------------------------------------------------
// Gemini image generation (Phase 1.5 – types for future backend/proxy API)
// ---------------------------------------------------------------------------

export interface GeminiImageGenerateRequest {
  /** Scene key or NPC id to generate for */
  key: string;
  /** 'scene' | 'npc_portrait' */
  type: 'scene' | 'npc_portrait';
  /** Optional prompt override; backend may use key + type to build prompt */
  prompt?: string;
  /** Optional: skip cache and force regenerate */
  forceRefresh?: boolean;
}

export interface GeminiImageGenerateResponse {
  /** Image URL (if served by backend) or base64 data URL */
  imageUrl: string;
  /** Cache key used (e.g. scene key or npc id) */
  cacheKey: string;
  /** Whether this was from cache */
  fromCache: boolean;
}
