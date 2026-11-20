import pytest

from ml_based_strategies.main import DEFAULT_WORLD
from ml_based_strategies.world.loader import load_world

FACTIONS = """
[[factions]]
id = "a"
name = "A"
color = "#000"
allowed_kinds = ["field"]

[[factions]]
id = "b"
name = "B"
color = "#fff"
allowed_kinds = ["field"]
allowed_ids = ["x"]

[[factions]]
id = "c"
name = "C"
color = "#888"
allowed_ids = ["y"]
"""
LOCATIONS = """
[[locations]]
id = "x"
name = "X"
kind = "base"
x = 0
y = 0
owner = "a"
protected = true

[[locations]]
id = "y"
name = "Y"
kind = "field"
x = 1
y = 1
"""
PATHS = """
[[paths]]
a = "x"
b = "y"
cost = 2
"""
THREAT = '\n[[threats]]\nid = "t"\nlocation = "{loc}"\nkind = "{kind}"\nlevel = {level}\n'
NEW_LOC = '\n[[locations]]\nid = "z"\nname = "Z"\nkind = "field"\nx = 0\ny = 0\n'


def _load(tmp_path, factions=FACTIONS, locations=LOCATIONS, paths=PATHS, threats=None):
    (tmp_path / "factions.toml").write_text(factions)
    (tmp_path / "locations.toml").write_text(locations)
    (tmp_path / "paths.toml").write_text(paths)
    if threats is not None:
        (tmp_path / "threats.toml").write_text(threats)
    return load_world(tmp_path)


def test_sample_world_loads():
    w = load_world(DEFAULT_WORLD)
    assert len(w.locations_dict) == 9
    assert w.neighbors("lab") == {"outpost": 3, "factory": 4, "core": 3}
    assert w.neighbors("factory")["lab"] == 4  # paths are undirected
    assert [t.id for t in w.threats_at("lab")] == ["lab_monsters"]
    assert w.threats_at("village") == []


def test_can_enter_masks_kind_and_protection(tmp_path):
    w = _load(tmp_path)  # no threats.toml: the file is optional
    assert w.threats_dict == {}
    assert w.can_enter("a", "y")
    assert not w.can_enter("a", "x")  # owner, but "base" kind not allowed
    assert not w.can_enter("b", "x")  # listed by id, but protected and not owner
    assert w.can_enter("c", "y")  # by id alone: "field" is not in its kinds


def test_missing_required_file_rejected(tmp_path):
    (tmp_path / "factions.toml").write_text(FACTIONS)
    with pytest.raises(FileNotFoundError, match="locations.toml"):
        load_world(tmp_path)


@pytest.mark.parametrize(
    "file, extra, match",
    [
        ("paths", '\n[[paths]]\na = "x"\nb = "nope"\ncost = 1\n', "unknown location"),
        ("paths", '\n[[paths]]\na = "x"\nb = "y"\ncost = 0\n', "greater than 0"),
        ("paths", '\n[[paths]]\na = "x"\nb = "y"\ncost = 1.5\n', "valid integer"),
        ("paths", '\n[[paths]]\na = "x"\nb = "x"\ncost = 1\n', "self-loop"),
        ("paths", "\n[[paths]]\n", "Field required"),
        ("locations", NEW_LOC + "protectd = true\n", "Extra inputs"),
        ("locations", NEW_LOC.replace('"z"', '"x"'), "duplicate location"),
        ("locations", NEW_LOC + 'owner = "ghost"\n', "unknown owner"),
        ("locations", NEW_LOC, "disconnected"),
        ("locations", NEW_LOC.replace('name = "Z"\n', ""), "Field required"),
        ("paths", THREAT.format(loc="y", kind="trap", level=1), r"paths\.toml: unexpected tables \['threats'\]"),
        ("factions", '\n[[factions]]\nid = "a"\nname = "A2"\ncolor = "#111"\n', "duplicate faction"),
        (
            "factions",
            '\n[[factions]]\nid = "d"\nname = "D"\ncolor = "#111"\nallowed_kinds = ["feild"]\n',
            r"unknown location kinds \['feild'\]",
        ),
        (
            "factions",
            '\n[[factions]]\nid = "d"\nname = "D"\ncolor = "#111"\nallowed_ids = ["nope"]\n',
            r"unknown location ids \['nope'\]",
        ),
        ("threats", THREAT.format(loc="nope", kind="anomaly", level=1), "unknown location 'nope'"),
        ("threats", THREAT.format(loc="y", kind="zombies", level=1), "anomaly"),
        ("threats", THREAT.format(loc="y", kind="trap", level=6), "less than or equal to 5"),
        (
            "threats",
            THREAT.format(loc="y", kind="monsters", level=1) + THREAT.format(loc="x", kind="trap", level=2),
            "duplicate threat",
        ),
    ],
)
def test_invalid_worlds_rejected(tmp_path, file, extra, match):
    files_dict = {"factions": FACTIONS, "locations": LOCATIONS, "paths": PATHS, "threats": ""}
    files_dict[file] += extra
    with pytest.raises(ValueError, match=match):
        _load(tmp_path, **files_dict)
