"""Base model with camelCase support."""

from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelCaseModel(BaseModel):
    """Base model that converts snake_case to camelCase in JSON output."""
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )
