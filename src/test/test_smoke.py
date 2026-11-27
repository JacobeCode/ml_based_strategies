import ml_based_strategies
from ml_based_strategies.main import main


def test_import():
    assert ml_based_strategies.__version__


def test_main_writes_snapshot(tmp_path, capsys):
    out = main(out_path=tmp_path / "world.html")
    assert out.exists()
    assert "9 locations" in capsys.readouterr().out
