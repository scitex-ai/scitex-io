#!/usr/bin/env python3
"""Real tests for scitex_io._load_modules._optuna using a tiny live study."""

import pytest

optuna = pytest.importorskip("optuna")
import yaml

from scitex_io._load_modules._optuna import (
    OPTUNA_AVAILABLE,
    load_study_rdb,
    load_yaml_as_an_optuna_dict,
)


def test_optuna_available_flag():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert OPTUNA_AVAILABLE is True


def test_load_yaml_categorical(tmp_path):
    # Arrange
    # Arrange
    cfg = {"opt": {"distribution": "categorical", "values": ["adam", "sgd"]}}
    p = tmp_path / "h.yaml"
    p.write_text(yaml.safe_dump(cfg))

    def objective(trial):
        d = load_yaml_as_an_optuna_dict(str(p), trial)
        assert d["opt"] in ("adam", "sgd")
        return 1.0

    s = optuna.create_study()
    # Act
    # Act
    s.optimize(objective, n_trials=3)
    # Assert
    # Assert
    assert len(s.trials) == 3


def test_load_yaml_uniform_log_intlog(tmp_path):
    # Arrange
    # Arrange
    cfg = {
        "u": {"distribution": "uniform", "min": 1, "max": 10},
        "lu": {"distribution": "loguniform", "min": 1e-3, "max": 1.0},
        "ilu": {"distribution": "intloguniform", "min": 1, "max": 100},
    }
    p = tmp_path / "g.yaml"
    p.write_text(yaml.safe_dump(cfg))

    seen = {}

    def objective(trial):
        d = load_yaml_as_an_optuna_dict(str(p), trial)
        seen.update(d)
        return 0.0

    s = optuna.create_study()
    # suggest_loguniform is deprecated → suppress warning
    import warnings

    # Act
    # Act
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        s.optimize(objective, n_trials=2)
    # Assert
    # Assert
    assert {"u", "lu", "ilu"} <= set(seen.keys())


def test_load_study_rdb_loaded_study_name_equals_t(tmp_path, capsys):
    # Arrange
    # Arrange
    db_path = tmp_path / "x.db"
    url = f"sqlite:///{db_path}"
    s = optuna.create_study(study_name="t", storage=url)
    s.optimize(lambda t: t.suggest_float("x", -1, 1) ** 2, n_trials=3)
    # Act
    loaded = load_study_rdb("t", url)
    # Act
    # Assert
    # Assert
    assert loaded.study_name == "t"


def test_load_study_rdb_len_loaded_trials_is_3(tmp_path, capsys):
    # Arrange
    # Arrange
    db_path = tmp_path / "x.db"
    url = f"sqlite:///{db_path}"
    s = optuna.create_study(study_name="t", storage=url)
    s.optimize(lambda t: t.suggest_float("x", -1, 1) ** 2, n_trials=3)
    # Act
    loaded = load_study_rdb("t", url)
    # Act
    # Assert
    # Assert
    assert len(loaded.trials) == 3


def test_load_study_rdb_loaded_in_out(tmp_path, capsys):
    # Arrange
    # Arrange
    db_path = tmp_path / "x.db"
    url = f"sqlite:///{db_path}"
    s = optuna.create_study(study_name="t", storage=url)
    s.optimize(lambda t: t.suggest_float("x", -1, 1) ** 2, n_trials=3)
    # Act
    loaded = load_study_rdb("t", url)
    # Assert
    assert loaded.study_name == "t"
    assert len(loaded.trials) == 3
    out = capsys.readouterr().out
    # Act
    # Assert
    assert "Loaded" in out


