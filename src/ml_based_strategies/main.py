from pathlib import Path

from ml_based_strategies.viz.schema import load_style
from ml_based_strategies.viz.world_map import save_snapshot
from ml_based_strategies.world.loader import load_world

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WORLD = ROOT / "data" / "worlds"
DEFAULT_STYLE = ROOT / "data" / "viz" / "style.toml"
DEFAULT_OUT = ROOT / "out" / "world.html"


def main(world_path: Path = DEFAULT_WORLD, out_path: Path = DEFAULT_OUT, style_path: Path = DEFAULT_STYLE) -> Path:
    world = load_world(world_path)
    edges = sum(len(n) for n in world.adjacency_dict.values()) // 2
    print(
        f"World: {len(world.locations_dict)} locations, {edges} paths, {len(world.factions_dict)} factions, "
        f"{len(world.threats_dict)} threats"
    )
    out = save_snapshot(world, load_style(style_path), out_path)
    print(f"Snapshot: {out}")
    return out


if __name__ == "__main__":  # pragma: no cover
    main()
