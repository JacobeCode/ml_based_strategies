import ml_based_strategies
from ml_based_strategies.main import main


def test_import():
    assert ml_based_strategies.__version__


def test_main_greets(capsys):
    main()
    assert ml_based_strategies in capsys.readouterr().out
    