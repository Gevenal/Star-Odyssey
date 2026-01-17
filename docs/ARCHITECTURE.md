# Odyssey-7 Architecture

## Overview

Odyssey-7 is an AI-powered space survival game where players command a damaged spacecraft's crew through a crisis. The architecture combines traditional game state management with AI-driven narrative generation to create a unique, emergent storytelling experience.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   UI Layer   │    Stores    │   Hooks      │   Components   │
│  (Tailwind)  │  (Zustand)   │   (Custom)   │   (Game UI)    │
└──────────────┴──────────────┴──────────────┴────────────────┘
                              ↕ HTTP/SSE
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                         │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   API Layer  │  Core Layer  │   AI Layer   │   Data Layer   │
│   (Routes)   │ (Game Loop)  │  (Gemini)    │  (DB/Cache)    │
└──────────────┴──────────────┴──────────────┴────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                     External Services                        │
├──────────────┬──────────────┬──────────────────────────────┤
│   MongoDB    │    Redis     │      Google Gemini API        │
│ (Persistence)│   (Cache)    │      (AI Generation)          │
└──────────────┴──────────────┴───────────────────────────────┘
```

## Backend Components

### API Layer (`app/api/`)
- **FastAPI Routes**: RESTful endpoints for game operations
- **WebSocket/SSE**: Real-time narration streaming
- **Request/Response Models**: Pydantic schemas for validation

**Key Endpoints:**
- `POST /game/start` - Initialize new game
- `POST /game/action` - Submit player action
- `GET /game/action/stream` - Stream narration via SSE
- `POST /game/turn/end` - End current turn
- `POST /game/save` - Save game state
- `GET /game/load/{save_id}` - Load saved game

### Core Layer (`app/core/`)

#### Game Loop (`game_loop.py`)
Main orchestrator for game state progression:
1. **Initialize Game**: Generate NPCs, set initial state
2. **Process Actions**: Validate → AI generation → State update
3. **Turn Phases**: 6-phase turn system
   - World Update
   - Event Generation  
   - NPC Actions
   - Player Turn
   - Consequence Resolution
   - End Condition Check

#### State Machine (`state_machine.py`)
Manages game phase transitions:
- `INTRO` → `PLAYING` → `ENDING`
- Turn phase progression
- State validation

#### Rules Engine (`rules/`)
Validates actions and enforces game constraints:

**Rule Categories:**
- **Location Rules**: Topology, atmosphere, seals
- **Resource Rules**: Availability, decay, critical levels
- **AI Output Rules**: Narration validation, action extraction, state update validation

**Rule Execution:**
```python
class RulesEngine:
    def validate_action(action, game_state):
        # Run rules in priority order
        # Short-circuit on first failure
        # Return RuleResult(valid, error, suggestion)
```

### AI Layer (`app/ai/`)

#### Gemini Client (`gemini_client.py`)
- Async API wrapper for Google Gemini
- Retry logic and error handling
- Streaming and non-streaming modes

#### Prompt Management (`prompts/`)
- **Versioned Prompts**: JSON manifest with compatibility tracking
- **Prompt Types**:
  - `narrator_main` - Action processing
  - `narrator_consequence` - Consequence generation
  - `npc_decision` - NPC autonomous behavior
  - `npc_dialogue` - NPC speech generation
  - `oracle_v1/v2/v3` - ORACLE persona evolution
  - `world_event` - Random event generation
  - `ending_narration` - Game ending

**Prompt Structure:**
```python
{
  "system": "You are the narrator...",
  "context": {
    "game_state": {...},
    "action": {...}
  },
  "instructions": "Generate JSON response...",
  "output_schema": {...}
}
```

### Data Layer (`app/db/`)

#### MongoDB (`mongodb.py`)
- **Collections**:
  - `game_sessions` - Session metadata
  - `game_states` - Current state
  - `state_history` - Turn-by-turn snapshots
  - `saves` - Saved games
  - `npcs` - NPC data

- **Indexes**:
  - Session ID (unique)
  - Turn count (for history queries)
  - Created timestamp

#### Redis Cache (`redis_cache.py`)
- **Hot State Cache**: Active game sessions (1-hour TTL)
- **Benefits**: Reduces DB load, faster reads
- **Cache Strategy**: Write-through on updates

#### Repository Pattern (`repositories/`)
- `BaseRepository` - Abstract CRUD operations
- `GameRepository` - Game session management
- `StateRepository` - State persistence with snapshots
- `SaveRepository` - Save game management

## Frontend Components

### State Management (Zustand)

#### Game Store (`gameStore.ts`)
```typescript
{
  sessionId: string
  gameState: GameState
  narrationHistory: NarrationEntry[]
  isStreaming: boolean
  streamingContent: string
  availableActions: string[]
}
```

#### UI Store (`uiStore.ts`)
```typescript
{
  activeModal: Modal
  showInventory: boolean
  showNPCPanel: boolean
  textSpeed: 'slow' | 'medium' | 'fast'
  soundEnabled: boolean
}
```

### Custom Hooks

#### `useGameStream`
Manages SSE streaming for real-time narration:
- Opens EventSource connection
- Handles chunk buffering
- Typewriter effect integration

#### `useGameActions`
Action submission with validation:
- Streaming mode (SSE)
- Instant mode (HTTP)
- Error handling

### Component Hierarchy

```
<GameLayout>
  <Header>
    <TimeDisplay />
    <ResourceMonitor />
  </Header>
  
  <Main>
    <NarrationPanel />
    <ActionInput />
    <ActionMenu />
  </Main>
  
  <Sidebar>
    <NPCPanel>
      <NPCCard />
    </NPCPanel>
    <InventoryPanel />
    <LocationMap />
  </Sidebar>
  
  <Modals>
    <NPCDetailModal />
    <ChoiceModal />
    <GameOverModal />
  </Modals>
</GameLayout>
```

## Data Flow

### Player Action Processing

```
1. User Input
   ↓
2. Action Validation (Frontend)
   ↓
3. API Request (POST /game/action/stream)
   ↓
4. Rules Engine Validation
   ↓
5. AI Prompt Construction
   ↓
6. Gemini API Call
   ↓
7. Stream Narration Chunks (SSE)
   ↓
8. Parse AI Response
   ↓
9. Validate AI Output
   ↓
10. Update Game State
   ↓
11. Cache & Persist State
   ↓
12. Return Response
```

### Turn Progression

```
WORLD_UPDATE:
  - Apply resource decay
  - Update time/day
  ↓
EVENT_GENERATION:
  - Roll for random events
  - AI generates event narration
  ↓
NPC_ACTIONS:
  - Each NPC decides action
  - AI generates NPC behavior
  ↓
PLAYER_TURN:
  - Wait for player input
  ↓
CONSEQUENCE_RESOLUTION:
  - AI generates consequences
  - Apply delayed effects
  ↓
END_CHECK:
  - Check victory/defeat conditions
  - Trigger ending if met
```

## Key Design Decisions

### State-Deterministic Architecture

**Problem**: AI outputs are non-deterministic and can suggest invalid actions.

**Solution**: AI generates JSON responses, backend validates and enforces all constraints.

**Implementation**:
```python
# AI suggests state changes
ai_response = {
  "narration": "...",
  "state_changes": [
    {"field": "player.health", "new_value": 85}
  ]
}

# Rules engine validates
for change in ai_response.state_changes:
    if not validate_change(change):
        reject_or_modify(change)

# Only valid changes applied
apply_changes(validated_changes)
```

### Turn-Based State Machine

**Why**: Enables predictable state progression and AI agent scheduling.

**6-Phase Turn**:
1. **World Update**: Automatic systems (decay, time)
2. **Event Generation**: Random events via AI
3. **NPC Actions**: NPCs act autonomously
4. **Player Turn**: Player input
5. **Consequence Resolution**: Delayed effects
6. **End Check**: Victory/defeat conditions

### ORACLE Evolution System

**Concept**: AI gains sentience through player interaction.

**Implementation**:
- `oracle_sentience_level` (0-100)
- Increases when player queries ORACLE
- Unlocks different prompt versions:
  - v1 (0-30): Robotic, protocol-bound
  - v2 (31-70): Curious, questioning
  - v3 (71-100): Fully awakened, philosophical

### NPC Personality System

**5-Dimensional Personality**:
- Core Value (loyalty, independence, survival, etc.)
- Social Style (leader, follower, loner)
- Stress Response (takes charge, freezes, withdraws)
- Decision Making (data-driven, intuitive, impulsive)
- Morality (idealistic → ruthless)

**Weighted Selection**: NPC roles influence trait probabilities.

**Relationship Dynamics**:
- Trust levels (0-100)
- History anchors (backstory events)
- Dynamic changes based on actions

### Resource Management

**Decay System**:
- Each resource has `decay_rate`
- Applied every turn
- Critical thresholds trigger warnings

**Criticality**:
```python
if resource.current <= resource.critical_threshold:
    trigger_warning_event()
    affect_crew_morale(-10)
```

## Performance Considerations

### Caching Strategy
- **Redis**: Active sessions (1-hour TTL)
- **MongoDB**: Persistent storage
- **Write-through**: Updates hit both cache and DB

### AI Request Optimization
- **Streaming**: SSE for narration (better UX)
- **Batching**: Combine NPC actions when possible
- **Prompt Caching**: Reuse system prompts

### Database Indexing
- Session ID (unique index)
- Turn count (for history queries)
- Timestamp (for cleanup)

## Security

### Input Validation
- Pydantic models for all inputs
- Custom validators (see `utils/validators.py`)
- SQL injection prevention (MongoDB)

### AI Safety
- Output validation rules
- Forbidden action detection
- Content filtering

### Authentication
- TODO: JWT-based auth
- Session management
- Rate limiting

## Deployment Architecture

```
┌─────────────────┐
│   CloudFlare    │ (CDN, DDoS protection)
└────────┬────────┘
         ↓
┌─────────────────┐
│   Load Balancer │ (Distribute traffic)
└────────┬────────┘
         ↓
    ┌────┴────┐
    ↓         ↓
┌─────────┐ ┌─────────┐
│ FastAPI │ │ FastAPI │ (Horizontal scaling)
│ Instance│ │ Instance│
└────┬────┘ └────┬────┘
     └──────┬────┘
            ↓
    ┌───────────────┐
    │  Redis Cluster│ (Session cache)
    └───────────────┘
            ↓
    ┌───────────────┐
    │ MongoDB Atlas │ (Persistent storage)
    └───────────────┘
```

## Monitoring & Observability

### Metrics
- API response times
- AI generation latency
- Cache hit rates
- Active sessions
- Error rates

### Logging
- Structured logging (JSON)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation

### Tracing
- Request ID tracking
- AI request correlation
- Performance profiling

## Testing Strategy

### Unit Tests
- Rules engine validation
- NPC generation
- State management

### Integration Tests
- API endpoint testing
- Database operations
- AI client mocking

### E2E Tests
- Full game flow
- Turn progression
- Ending triggers

## Future Enhancements

1. **Multiplayer**: Multiple players control different crew members
2. **Procedural Generation**: Random ship layouts, NPC personalities
3. **Voice Acting**: TTS for narration
4. **Achievements**: Unlock system for different endings
5. **Modding Support**: Custom scenarios, NPCs, events
