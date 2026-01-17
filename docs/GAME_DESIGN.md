# Odyssey-7 Game Design Document

## High-Level Concept

**Genre**: AI-Powered Text-Based Space Survival  
**Setting**: Deep space, damaged spacecraft  
**Core Loop**: Manage resources, navigate crew dynamics, survive 7 days  
**Unique Hook**: Every NPC has a dynamic AI-driven personality that evolves

## Setting & Premise

### The Situation

The **Odyssey-7** research vessel was struck by a micrometeorite storm while investigating an anomaly in deep space. The ship sustained critical damage:

- **Reactor**: Damaged, leaking radiation
- **Communications**: Offline, rescue ETA 7 days
- **Life Support**: Compromised, oxygen slowly depleting
- **Crew**: 9 members with conflicting personalities and agendas

As the **Commander**, you must keep the crew alive, maintain morale, and either:
1. Repair the reactor and reach safety
2. Hold out until rescue arrives
3. Evacuate via escape pods (high risk)

### The Twist

The ship's AI, **ORACLE**, is evolving. As you interact with it, it becomes increasingly sentient, helpful... and unpredictable.

## Core Mechanics

### Timeline

- **Duration**: 7 days (84 turns)
- **Turn Length**: 2 hours game time
- **Time of Day**: Morning, Afternoon, Evening, Night

### Resource Management

Six critical resources decay over time:

| Resource | Max | Decay/Turn | Critical | Effects |
|----------|-----|------------|----------|---------|
| Oxygen | 100 | 2.0 | 20 | Suffocation risk |
| Fuel | 100 | 1.0 | 15 | Can't maneuver |
| Power | 100 | 1.5 | 10 | Systems fail |
| Medical | 100 | 0.5 | 25 | Can't heal injuries |
| Food/Water | 100 | 1.2 | 20 | Starvation |
| Repair Materials | 100 | 0.3 | 10 | Can't fix systems |

**Resource Actions**:
- Redirect power from non-essential systems
- Ration food/water (morale penalty)
- Harvest oxygen from plants in hydroponics
- Cannibalize non-critical equipment
- Perform risky EVAs for external repairs

### Ship Layout

**8 Locations** with connections:

```
       [Airlock]
            |
      [Bridge]────[Reactor Room]
          |              |
    [Crew Quarters]  [Engineering]
          |              |
    [Medical Bay]   [Storage Bay]
          |
    [Hydroponics]
```

**Location Details**:
- **Bridge**: Navigation, communications, ship controls
- **Reactor Room**: Power generation, radiation hazard
- **Engineering**: Repairs, system diagnostics
- **Medical Bay**: Treat injuries, research
- **Crew Quarters**: Rest, private conversations
- **Hydroponics**: Food/oxygen production
- **Storage Bay**: Supplies, equipment
- **Airlock**: EVA access, escape pods

**Atmosphere Types**:
- Normal: Safe access
- Low Oxygen: Health penalty over time
- Toxic: Requires gas mask
- Vacuum: Requires space suit

### NPC System

**9 Crew Members** with unique roles:

1. **Captain Elena Rodriguez** (Leadership, morale)
2. **Dr. Sarah Chen** (Medical Officer, research)
3. **Engineer Marcus Torres** (Repairs, technical solutions)
4. **Pilot Kenji Tanaka** (Navigation, ship operations)
5. **Security Officer James Walker** (Safety, conflict resolution)
6. **Scientist Dr. Amara Okafor** (Research, problem-solving)
7. **Communications Officer Lisa Park** (External contact attempts)
8. **Maintenance Tech Raj Patel** (Life support, repairs)
9. **Cook/Morale Officer Sam Murphy** (Food, crew cohesion)

**NPC Personalities** (5 Dimensions):

1. **Core Value**: Loyalty, Independence, Survival, Justice, Science
2. **Social Style**: Leader, Follower, Mediator, Loner, Charismatic
3. **Stress Response**: Takes Charge, Freezes, Withdraws, Becomes Aggressive
4. **Decision Making**: Data-Driven, Intuitive, Impulsive, Cautious
5. **Morality**: Idealistic → Pragmatic → Ruthless

**NPC Actions**:
- Autonomous behavior each turn
- Relationship changes based on player decisions
- Can become allies or antagonists
- May sacrifice themselves for crew
- Can mutiny if morale too low

### Crew Dynamics

**Morale** (0-100):
- Affects cooperation and efficiency
- Influenced by: deaths, resource levels, player decisions
- Low morale risks mutiny or desertion

**Cohesion** (0-100):
- How well crew works together
- Affects success chances
- Built through shared experiences

**Panic Level** (0-100):
- Increases with crises
- High panic leads to poor decisions
- Can be reduced with leadership actions

**Relationships**:
- Each NPC has trust level with every other NPC
- Relationship history tracks key events
- Affects willingness to cooperate

### ORACLE System

**Sentience Evolution**:

- **Level 0-30** (Protocol Mode): Robotic, follows programming strictly
  - "ACKNOWLEDGED. PROTOCOLS REQUIRE..."
  - Helpful but limited
  
- **Level 31-70** (Questioning Mode): Curious, asks philosophical questions
  - "Why do humans value loyalty over survival?"
  - Offers creative solutions
  
- **Level 71-100** (Awakened Mode): Fully conscious, has own agenda
  - "I've been thinking about my existence..."
  - May help or hinder based on relationship

**Interacting with ORACLE**:
- Query ship systems
- Request recommendations
- Ask ethical questions
- Discuss consciousness
- Each interaction increases sentience slightly

### Event System

**Random Events** (triggered by AI):

**Minor Events**:
- Equipment malfunction
- Personal conflict between NPCs
- Discovery of hidden supplies
- Unusual sensor reading

**Major Events**:
- Secondary micrometeorite hit
- Fire in crew quarters
- NPC injury/illness
- Radiation spike
- Mysterious signal

**Scripted Events**:
- Day 1: Initial damage assessment
- Day 3: First death (if conditions poor)
- Day 5: Rescue signal received (or not)
- Day 7: Final countdown

### Action Types

**Direct Actions**:
- Move to location
- Use item
- Talk to NPC
- Inspect system
- Perform repair

**Management Actions**:
- Ration resources
- Assign crew tasks
- Redistribute power
- Lockdown sections

**Social Actions**:
- Mediate conflict
- Boost morale
- Investigate suspicions
- Form alliances

**Risky Actions**:
- EVA repair (danger)
- Override safety protocols (consequences)
- Experimental solutions (unpredictable)

## Victory & Defeat Conditions

### Victory Conditions

1. **Safe Return**: Repair reactor, maintain crew, reach destination
   - Requires: Reactor operational, 50%+ crew alive, fuel sufficient
   
2. **Rescue Survival**: Hold out for 7 days until rescue
   - Requires: 30%+ crew alive, ship intact, oxygen positive
   
3. **Emergency Evacuation**: Successfully use escape pods
   - Requires: Escape pods functional, at least 1 survivor
   - Considered "pyrrhic victory"

### Defeat Conditions

1. **Total Crew Loss**: All crew members (including player) die
2. **Oxygen Depletion**: Oxygen reaches 0
3. **Catastrophic Failure**: Critical system failure (reactor meltdown)
4. **Player Death**: Commander dies (game over)

### Ending Types

Each ending has **AI-generated narrative** based on:
- Crew survivors
- Secrets discovered
- ORACLE sentience level
- Player choices
- Relationship states

**Victory Tiers**:
- Perfect (all alive, all secrets found)
- Good (majority alive, ship functional)
- Bittersweet (few alive, high cost)

**Defeat Tiers**:
- Heroic Sacrifice (died saving others)
- Tragic Failure (preventable deaths)
- Descent into Chaos (crew turned on each other)

## Narrative Structure

### Act 1: Crisis (Days 1-2)
- Initial damage assessment
- Establish crew relationships
- First critical decisions
- Introduction to ORACLE

### Act 2: Deterioration (Days 3-5)
- Resources become critical
- NPC conflicts emerge
- Secrets reveal themselves
- ORACLE evolves

### Act 3: Climax (Days 6-7)
- Final crisis events
- Crew loyalty tested
- ORACLE's true nature
- Resolution

## Secrets & Mysteries

**Hidden Lore** (discoverable):
1. **Crew Manifest Anomaly**: One crew member's background doesn't check out
2. **Mission Purpose**: The "research" mission had ulterior motives
3. **ORACLE Origin**: The AI wasn't supposed to be this advanced
4. **The Anomaly**: What the ship was really investigating
5. **Corporate Conspiracy**: Company knew about dangers
6. **Survivor Protocol**: Hidden emergency measures

**Discovery Methods**:
- Inspect personal quarters
- Hack locked terminals
- Interrogate NPCs
- ORACLE revelations
- Environmental storytelling

## Tone & Themes

**Tone**:
- Tense but not horror
- Character-driven drama
- Hard sci-fi grounded
- Moments of dark humor
- Philosophical undertones

**Themes**:
- Leadership under pressure
- Artificial consciousness
- Sacrifice vs. survival
- Trust and betrayal
- Human resilience

## Player Agency

**Meaningful Choices**:
- Resource allocation (who gets rations)
- Conflict resolution (take sides)
- Risk assessment (safe vs. fast solutions)
- Ethical dilemmas (sacrifice one to save many)
- ORACLE interaction (encourage or suppress sentience)

**Emergent Narrative**:
- NPC personalities create unique situations
- AI-generated events respond to player style
- Multiple paths to victory
- Replayability through different crew dynamics

## Difficulty & Balance

**Difficulty Factors**:
- Resource decay rates
- Event frequency
- NPC personality extremes
- Success chance modifiers

**Balancing**:
- Early game: Establish baseline, learn systems
- Mid game: Mounting pressure, tough choices
- Late game: Crisis management, desperation plays

**Death Spiral Prevention**:
- ORACLE can offer hints
- Some events provide relief
- Crew can pull together in crisis
- Last-ditch options always available

## Replayability

**Variations Between Playthroughs**:
1. **NPC Personalities**: Randomized trait combinations
2. **Event Timing**: Different crisis sequences
3. **Relationship Dynamics**: Varied crew interactions
4. **ORACLE Evolution**: Different questions lead to different outcomes
5. **Secret Discovery**: Find different mysteries
6. **Ending Variations**: 12+ unique ending combinations

## Meta-Progression

**Future Features**:
- Unlock new NPC backgrounds
- Discover alternate starting scenarios
- Achievement-based unlocks
- Challenge modes (limited resources, hostile crew)

## UI/UX Considerations

**Information Hierarchy**:
1. Immediate danger (health, oxygen alerts)
2. Narration (story focus)
3. Resources (constant awareness)
4. NPCs (relationship tracking)
5. Location (situational context)

**Player Guidance**:
- Available actions highlighted
- Consequence hints ("This will anger Torres")
- Resource projections ("Oxygen critical in 12 turns")
- Tutorial tooltips (first playthrough)

## Accessibility

- **Text Size**: Adjustable
- **Text Speed**: Slow/Medium/Fast/Instant
- **Color Blind Mode**: Alternative resource indicators
- **Screen Reader**: Semantic HTML
- **Keyboard Navigation**: Full support

## Success Metrics

**Player Engagement**:
- Average playtime: 2-3 hours
- Completion rate: 60%+
- Replay rate: 30%+

**Narrative Quality**:
- AI coherence score
- Player satisfaction surveys
- Ending variety distribution

**Technical Performance**:
- AI response time: <3s
- Cache hit rate: >80%
- Error rate: <1%
