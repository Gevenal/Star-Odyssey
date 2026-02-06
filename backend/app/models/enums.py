"""Enumerations for game states and categories."""

from enum import Enum


class GamePhase(str, Enum):
    """Overall game phase."""

    INTRO = "intro"
    PLAYING = "playing"
    ENDING = "ending"


class TurnPhase(str, Enum):
    """Turn execution phase."""

    WORLD_UPDATE = "world_update"
    EVENT_GENERATION = "event_generation"
    NPC_ACTIONS = "npc_actions"
    PLAYER_TURN = "player_turn"
    CONSEQUENCE_RESOLUTION = "consequence_resolution"
    END_CHECK = "end_check"


class ActionCategory(str, Enum):
    """Category of player action."""

    CRISIS_RESPONSE = "crisis_response"
    RESOURCE_MANAGEMENT = "resource_management"
    SOCIAL_INTERACTION = "social_interaction"
    INVESTIGATION = "investigation"
    CRITICAL_DECISION = "critical_decision"
    REST_RECOVERY = "rest_recovery"
    FREEFORM = "freeform"


class Atmosphere(str, Enum):
    """Location atmosphere status."""

    NORMAL = "normal"
    TOXIC = "toxic"
    VACUUM = "vacuum"
    LOW_OXYGEN = "low_oxygen"


class NPCDisposition(str, Enum):
    """NPC disposition toward player."""

    HOSTILE = "hostile"
    UNFRIENDLY = "unfriendly"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    LOYAL = "loyal"


class Mood(str, Enum):
    """Current narrative mood."""

    TENSE = "tense"
    PEACEFUL = "peaceful"
    MYSTERIOUS = "mysterious"
    URGENT = "urgent"
    DESPERATE = "desperate"
    HOPEFUL = "hopeful"
