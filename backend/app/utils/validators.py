"""Custom Pydantic validators."""
from typing import Any


def validate_percentage(value: Any) -> float:
    """Validate value is between 0 and 100."""
    if not isinstance(value, (int, float)):
        raise ValueError("Value must be a number")

    if not 0 <= value <= 100:
        raise ValueError(f"Value must be between 0 and 100, got {value}")

    return float(value)


def validate_positive(value: Any) -> float:
    """Validate value is positive."""
    if not isinstance(value, (int, float)):
        raise ValueError("Value must be a number")

    if value < 0:
        raise ValueError(f"Value must be positive, got {value}")

    return float(value)


def sanitize_player_input(text: str, max_length: int = 500) -> str:
    """Sanitize player input text."""
    if not isinstance(text, str):
        raise ValueError("Input must be a string")

    text = text.strip()

    if len(text) == 0:
        raise ValueError("Input cannot be empty")

    if len(text) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length} characters")

    text = "".join(char for char in text if char.isprintable() or char in "\n\t")

    return text
