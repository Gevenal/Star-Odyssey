# Odyssey-7 API Documentation

## Base URL

```
Production: https://api.odyssey7.com/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

Currently, no authentication is required. Future versions will use JWT tokens.

## Common Headers

```http
Content-Type: application/json
Accept: application/json
```

## Endpoints

### Game Management

#### Start New Game

```http
POST /game/start
```

**Request Body:**
```json
{
  "player_name": "Commander Smith"
}
```

**Response:**
```json
{
  "session_id": "uuid-here",
  "game_state": { ... },
  "initial_narration": "The ship shudders as the damage reports flood in..."
}
```

---

#### Submit Player Action

```http
POST /game/action
```

**Request Body:**
```json
{
  "session_id": "uuid",
  "action_type": "freeform" | "predefined",
  "action_id": "custom" | "move_to_engineering",
  "action_text": "I inspect the reactor controls",
  "target_location": "Reactor Room" (optional),
  "target_npc": "npc_id" (optional),
  "target_item": "repair_kit" (optional)
}
```

**Response:**
```json
{
  "success": true,
  "narration": "You approach the reactor controls...",
  "resource_changes": [
    {
      "resource_name": "power_level",
      "change_amount": -5,
      "reason": "Diagnostic scan"
    }
  ],
  "state_changes": [
    {
      "entity_type": "player",
      "field": "location",
      "new_value": "Reactor Room"
    }
  ],
  "npc_reactions": [
    {
      "npc_id": "engineer_torres",
      "reaction_text": "Torres nods approvingly",
      "disposition_change": 5
    }
  ],
  "available_actions": [...],
  "mood": "tense",
  "trigger_ending": false,
  "oracle_message": null,
  "confidence_level": "high"
}
```

---

#### Submit Action (Streaming)

```http
GET /game/action/stream
```

**Query Parameters:**
- `session_id` - Session UUID
- `action_type` - Action type
- `action_id` - Action ID
- `action_text` - Action description
- `target_location` (optional)
- `target_npc` (optional)
- `target_item` (optional)

**Response:** Server-Sent Events (SSE)

```
event: narration_chunk
data: {"content": "You approach "}

event: narration_chunk  
data: {"content": "the reactor "}

event: narration_chunk
data: {"content": "controls..."}

event: complete
data: {
  "full_narration": "You approach the reactor controls...",
  "resource_changes": [...],
  "state_changes": [...],
  ...
}
```

---

#### Get Game State

```http
GET /game/state/{session_id}
```

**Response:**
```json
{
  "session_id": "uuid",
  "phase": "playing",
  "current_turn_phase": "player_turn",
  "player": { ... },
  "npcs": { ... },
  "world": { ... },
  "turn_count": 42,
  "oracle_sentience_level": 67
}
```

---

#### Get Available Actions

```http
GET /game/actions/{session_id}
```

**Response:**
```json
[
  {
    "action_id": "move_to_engineering",
    "action_type": "movement",
    "display_name": "Go to Engineering",
    "description": "Move to the Engineering section",
    "category": "Navigation",
    "requires_target": false
  },
  {
    "action_id": "talk_to_npc",
    "action_type": "social",
    "display_name": "Talk to Crew Member",
    "description": "Initiate conversation",
    "category": "Social",
    "requires_target": true,
    "target_type": "npc"
  }
]
```

---

#### End Turn

```http
POST /game/turn/end/{session_id}
```

**Response:**
```json
{
  "game_state": { ... },
  "turn_summary": "Resources continued to decay. Dr. Chen made progress on the radiation research.",
  "events": [
    "A small power fluctuation was detected in Sector 3",
    "ORACLE reported unusual sensor readings"
  ]
}
```

---

### Save/Load

#### Save Game

```http
POST /game/save/{session_id}
```

**Request Body (optional):**
```json
{
  "save_name": "Before reactor repair"
}
```

**Response:**
```json
{
  "save_id": "save-uuid",
  "saved_at": "2024-01-17T10:30:00Z"
}
```

---

#### Load Game

```http
GET /game/load/{save_id}
```

**Response:**
```json
{
  "game_state": { ... }
}
```

---

#### List Saves

```http
GET /game/saves?player_name=Commander
```

**Response:**
```json
{
  "saves": [
    {
      "save_id": "uuid",
      "session_id": "uuid",
      "player_name": "Commander",
      "save_name": "Before reactor repair",
      "day": 3,
      "turn": 42,
      "created_at": "2024-01-17T10:30:00Z"
    }
  ]
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message",
  "error_code": "INVALID_ACTION" (optional)
}
```

**Common HTTP Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

**Error Codes:**
- `INVALID_ACTION` - Action validation failed
- `SESSION_NOT_FOUND` - Session doesn't exist
- `GAME_OVER` - Game has ended
- `AI_ERROR` - AI generation failed
- `INVALID_STATE` - Game state invalid

## Rate Limiting

- **Actions**: 60 per minute
- **Saves**: 10 per minute
- **State Queries**: 120 per minute

## WebSocket (Future)

Future version will support WebSocket for real-time updates:

```javascript
const ws = new WebSocket('wss://api.odyssey7.com/ws/{session_id}');

ws.on('npc_action', (data) => {
  // NPC performed autonomous action
});

ws.on('event_triggered', (data) => {
  // Random event occurred
});
```

## SDK Example (TypeScript)

```typescript
import { GameClient } from 'odyssey7-sdk';

const client = new GameClient({
  baseURL: 'http://localhost:8000/api/v1'
});

// Start game
const { sessionId, gameState } = await client.startGame('Commander');

// Submit action with streaming
const stream = client.submitActionStream({
  sessionId,
  actionType: 'freeform',
  actionId: 'custom',
  actionText: 'I check the oxygen systems'
});

stream.on('chunk', (chunk) => {
  console.log(chunk.content);
});

stream.on('complete', (response) => {
  console.log('Action complete:', response);
});
```
