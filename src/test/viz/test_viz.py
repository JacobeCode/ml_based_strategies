import pytest

from ml_based_strategies.main import DEFAULT_STYLE, DEFAULT_WORLD
from ml_based_strategies.viz.schema import load_style
from ml_based_strategies.viz.world_map import save_snapshot, world_figure
from ml_based_strategies.world.loader import load_world


def test_world_figure_has_every_location():
    w = load_world(DEFAULT_WORLD)
    style = load_style(DEFAULT_STYLE)
    fig = world_figure(w, style)
    node_traces_tup = fig.data[2:]
    assert sum(len(t.x) for t in node_traces_tup) == len(w.locations_dict)
    assert {t.name for t in node_traces_tup} == {"Gang", "Order", "Lancers", "Unclaimed"}
    unclaimed = next(t for t in node_traces_tup if t.name == "Unclaimed")
    assert unclaimed.marker.color == style.neutral
    # One cost-hover midpoint per undirected path.
    assert len(fig.data[1].x) == sum(len(n) for n in w.adjacency_dict.values()) // 2
    assert len(fig.data[1].text) == len(fig.data[1].x)


def test_save_snapshot_writes_html(tmp_path):
    out = save_snapshot(load_world(DEFAULT_WORLD), load_style(DEFAULT_STYLE), tmp_path / "sub" / "w.html")
    assert "plotly" in out.read_text()


def test_style_rejects_unknown_key(tmp_path):
    p = tmp_path / "s.toml"
    p.write_text('neutral = "#999"\nnuetral_size = 3\n')
    with pytest.raises(ValueError, match="Extra inputs"):
        load_style(p)
