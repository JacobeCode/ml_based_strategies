"""
Reads a world directory of TOML files, validates it, and builds the runtime World.
"""

import tomllib
from pathlib import Path

from ml_based_strategies.world.graph import World
from ml_based_strategies.world.schema import WorldSpec, build_adjacency


def load_world(world_dir: str | Path) -> World:
    """
    Load and validate a world directory: one `<key>.toml` per WorldSpec field, holding only that key.
    A field with a default makes its file optional. Raises ValueError (incl. pydantic.ValidationError) on bad data.
    """
    # check data_dict consistency
    data_dict: dict = {}
    for key, field in WorldSpec.model_fields.items():
        path = Path(world_dir) / f"{key}.toml"
        try:
            with open(path, "rb") as f:
                part_dict = tomllib.load(f)
        except FileNotFoundError:
            if field.is_required():
                raise
            continue

        # unexpected set mixup in files
        if unexpected_set := part_dict.keys() - {key}:
            raise ValueError(f"{path}: unexpected tables {sorted(unexpected_set)}; expected only {key!r}")
        data_dict |= part_dict

    # validate and build runtime World
    spec = WorldSpec.model_validate(data_dict)
    return World(
        locations_dict={loc.id: loc for loc in spec.locations},
        factions_dict={f.id: f for f in spec.factions},
        adjacency_dict=build_adjacency([loc.id for loc in spec.locations], spec.paths),
        threats_dict={t.id: t for t in spec.threats},
    )
