 # Frontend Roadmap and Task Matrix
 
 This document defines the roadmap for building the web frontend that consumes
 backend APIs to deliver the full game experience and integrates Gemini for
 dynamic image generation.
 
 ## Roadmap
 
 ### Phase 0 - Stabilize API Integration
 - Align frontend API types with backend response shapes:
   - `POST /api/v1/game/start`
   - `GET /api/v1/game/actions/{session_id}`
   - `POST /api/v1/game/action`
   - `POST /api/v1/game/end-turn/{session_id}`
   - `GET /api/v1/game/state/{session_id}`
 - Add consistent error handling and user-friendly error states.
 - Add loading states for all async flows.
 - Ensure API base URL configuration via `VITE_API_URL`.
 
 ### Phase 1 - Core Gameplay UI
 - Home screen:
   - Start new game flow (player name entry).
   - Load game placeholder until backend save/load is ready.
 - Game screen layout:
   - Narration panel with streaming support.
   - Resource monitor with warnings and critical thresholds.
   - NPC list with status, location, and details modal.
   - Action input (freeform) and action list (predefined).
   - End Turn flow and turn summary handling.
 - Game state updates:
   - Apply server responses to update state and narration history.
   - Handle empty actions and fallbacks gracefully.
 
 ### Phase 1.5 - Gemini Image Generation (Dynamic Visuals)
 - Add a Gemini image generation service wrapper (backend or proxy):
   - Provide a stable frontend API for image requests.
   - Return image URL or base64 for display.
 - UI integrations:
   - Scene image panel that updates on major narration events.
   - NPC portrait placeholders with generated portraits.
 - Caching and rate limiting:
   - Avoid generating on every action.
   - Cache images by scene key or NPC id.
 - UX considerations:
   - Loading skeletons and fallback images.
   - Settings to disable generation.
 
 ### Phase 2 - Extended Experience (Future)
 - Video playback for key story events.
 - Background music and ambient sound controls.
 - Audio settings: volume sliders, mute, and preference persistence.
 - Expanded settings panel:
   - Text speed, theme, and accessibility options.
 - Performance improvements:
   - Lazy-load heavy panels and media assets.
   - Prefetch next scene assets on fast networks.
 
 ## Task Distribution Matrix
 
 The assignments below align with the current project structure under `frontend/src`.
 
 ### Team Member A - API Layer and Data Contracts
 - `src/api/`:
   - `client.ts` (base URL, interceptors, error mapping)
   - `gameApi.ts` (all gameplay endpoints)
 - `src/types/`:
   - `api.ts` (request/response contracts)
   - `game.ts` (state models, actions, responses)
 - Define types for Gemini image generation endpoints and payloads.
 - Add API error normalization and retry strategy for transient failures.
 
 ### Team Member B - UI Components and Layout
 - `src/components/layout/`:
   - `GameLayout.tsx`, `Header.tsx`, `Sidebar.tsx`
 - `src/components/game/`:
   - `NarrationPanel.tsx`
   - `ResourceMonitor.tsx`
   - `NPCPanel.tsx`, `NPCCard.tsx`
   - `ActionInput.tsx`, `ActionMenu.tsx`
 - `src/components/common/`:
   - `Button.tsx`, `Modal.tsx`, `LoadingSpinner.tsx`, `ProgressBar.tsx`
 - Visual design for Gemini-generated images panel.
 
 ### Team Member C - State Management and Gameplay Flow
 - `src/stores/`:
   - `gameStore.ts` (game session state)
   - `uiStore.ts` (modals, UI flags)
 - `src/hooks/`:
   - `useGameActions.ts` (submit actions, handle responses)
   - `useGameStream.ts` (SSE streaming)
 - Game state updates after start, action, and end-turn responses.
 - Error and loading state coordination across screens.
 
 ### Team Member D - Pages, Routing, and Media Integration
 - `src/pages/`:
   - `HomePage.tsx`, `GamePage.tsx`, `EndingPage.tsx`
 - Integration of Gemini image panel into `GamePage`.
 - Phase 2 media work:
   - Video playback component and hooks.
   - Background music player and settings UI.
 - UX polish: empty states, onboarding hints, and settings page.
 
 ## Notes
 - Keep API changes backward-compatible with the backend where possible.
 - Avoid coupling UI directly to backend schema beyond the API layer.
 - Prefer small, incremental updates with clear UI feedback on errors.
