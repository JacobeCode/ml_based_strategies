"""Viz style file schema (pydantic edge): display-only settings, kept out of the world file."""

import tomllib
from pathlib import Path

from ml_based_strategies.domain.spec_model import SpecModel


class Style(SpecModel):
    neutral: str  # marker color for unowned locations


def load_style(path: str | Path) -> Style:
    """Load and validate a style file. Raises pydantic.ValidationError (a ValueError) on bad data."""
    with open(path, "rb") as f:
        return Style.model_validate(tomllib.load(f))
