"""Turn phase state machine."""
from enum import Enum


class TurnPhase(str, Enum):
    """Turn phase enumeration."""

    PLAYER_INPUT = "player_input"
    VALIDATE_ACTION = "validate_action"
    AI_NARRATION = "ai_narration"
    APPLY_EFFECTS = "apply_effects"
    NPC_ACTIONS = "npc_actions"
    WORLD_EVENTS = "world_events"
    CHECK_ENDINGS = "check_endings"
    TURN_COMPLETE = "turn_complete"


class TurnStateMachine:
    """Manages turn phase transitions and validation."""

    def __init__(self):
        """Initialize state machine with PLAYER_INPUT phase."""
        self.current_phase = TurnPhase.PLAYER_INPUT

    def transition(self, next_phase: TurnPhase) -> bool:
        """
        Transition to next phase if valid.

        Args:
            next_phase: Phase to transition to

        Returns:
            bool: True if transition was valid
        """
        raise NotImplementedError

    def can_transition_to(self, next_phase: TurnPhase) -> bool:
        """
        Check if transition to phase is valid.

        Args:
            next_phase: Phase to check

        Returns:
            bool: True if transition is valid
        """
        raise NotImplementedError

    def reset(self):
        """Reset to PLAYER_INPUT phase."""
        self.current_phase = TurnPhase.PLAYER_INPUT

    def get_next_phase(self) -> TurnPhase:
        """
        Get the next phase in sequence.

        Returns:
            TurnPhase: Next expected phase
        """
        raise NotImplementedError
