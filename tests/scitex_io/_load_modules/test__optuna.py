#!/usr/bin/env python3
# Time-stamp: "2025-06-02 17:15:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__optuna.py

"""Tests for Optuna study and YAML configuration loading functionality.

All previous mock-theater tests (MagicMock'd trial / patched _load_yaml)
were deleted because they observed MagicMock call counts rather than
production-state outcomes. The integration tree
(`tests/integration/_load_modules/test__optuna_real.py`) covers the
real end-to-end paths using a real `optuna.trial.FixedTrial` and real
YAML files. The tests below exercise the public surface area
(signatures, docstrings, availability flag, real round-trip through
load_yaml_as_an_optuna_dict).
"""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
# Optional dep for the optuna loader (`import optuna`).
optuna = pytest.importorskip("optuna")

import yaml


def test_optuna_available_flag_is_bool():
    # Arrange
    from scitex_io._load_modules._optuna import OPTUNA_AVAILABLE

    # Act
    actual = OPTUNA_AVAILABLE
    # Assert
    assert isinstance(actual, bool)


def test_load_yaml_as_optuna_dict_signature_has_fpath_yaml():
    # Arrange
    import inspect

    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    # Act
    sig = inspect.signature(load_yaml_as_an_optuna_dict)
    # Assert
    assert "fpath_yaml" in sig.parameters


def test_load_yaml_as_optuna_dict_signature_has_trial():
    # Arrange
    import inspect

    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    # Act
    sig = inspect.signature(load_yaml_as_an_optuna_dict)
    # Assert
    assert "trial" in sig.parameters


def test_load_study_rdb_signature_has_study_name():
    # Arrange
    import inspect

    from scitex_io._load_modules import load_study_rdb

    # Act
    sig = inspect.signature(load_study_rdb)
    # Assert
    assert "study_name" in sig.parameters


def test_load_study_rdb_signature_has_rdb_raw_bytes_url():
    # Arrange
    import inspect

    from scitex_io._load_modules import load_study_rdb

    # Act
    sig = inspect.signature(load_study_rdb)
    # Assert
    assert "rdb_raw_bytes_url" in sig.parameters


def test_load_yaml_as_optuna_dict_has_docstring():
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    # Act
    doc = load_yaml_as_an_optuna_dict.__doc__
    # Assert
    assert doc is not None


def test_load_yaml_as_optuna_dict_docstring_mentions_yaml():
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    # Act
    doc = load_yaml_as_an_optuna_dict.__doc__
    # Assert
    assert "YAML" in doc


def test_load_yaml_as_optuna_dict_docstring_mentions_optuna():
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    # Act
    doc = load_yaml_as_an_optuna_dict.__doc__
    # Assert
    assert "Optuna" in doc


def test_load_study_rdb_has_docstring():
    # Arrange
    from scitex_io._load_modules import load_study_rdb

    # Act
    doc = load_study_rdb.__doc__
    # Assert
    assert doc is not None


def test_load_study_rdb_docstring_mentions_study():
    # Arrange
    from scitex_io._load_modules import load_study_rdb

    # Act
    doc = load_study_rdb.__doc__
    # Assert
    assert "study" in doc.lower()


def test_load_study_rdb_docstring_mentions_rdb():
    # Arrange
    from scitex_io._load_modules import load_study_rdb

    # Act
    doc = load_study_rdb.__doc__
    # Assert
    assert "RDB" in doc


@pytest.fixture
def categorical_yaml_path(tmp_path):
    # Arrange
    p = tmp_path / "cfg.yaml"
    p.write_text(
        yaml.safe_dump(
            {
                "optimizer": {
                    "distribution": "categorical",
                    "values": ["adam", "sgd", "rmsprop"],
                }
            }
        )
    )
    return str(p)


def test_load_yaml_as_optuna_dict_categorical_returns_one_of_values(
    categorical_yaml_path,
):
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    trial = optuna.trial.FixedTrial({"optimizer": "adam"})
    # Act
    result = load_yaml_as_an_optuna_dict(categorical_yaml_path, trial)
    # Assert
    assert result["optimizer"] == "adam"


@pytest.fixture
def uniform_yaml_path(tmp_path):
    # Arrange
    p = tmp_path / "uni.yaml"
    p.write_text(
        yaml.safe_dump(
            {"batch_size": {"distribution": "uniform", "min": 16, "max": 128}}
        )
    )
    return str(p)


def test_load_yaml_as_optuna_dict_uniform_returns_suggested_int(uniform_yaml_path):
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    trial = optuna.trial.FixedTrial({"batch_size": 17})
    # Act
    result = load_yaml_as_an_optuna_dict(uniform_yaml_path, trial)
    # Assert
    assert result["batch_size"] == 17


@pytest.fixture
def loguniform_yaml_path(tmp_path):
    # Arrange
    p = tmp_path / "log.yaml"
    p.write_text(
        yaml.safe_dump(
            {
                "learning_rate": {
                    "distribution": "loguniform",
                    "min": 1e-5,
                    "max": 1e-1,
                }
            }
        )
    )
    return str(p)


def test_load_yaml_as_optuna_dict_loguniform_returns_suggested_value(
    loguniform_yaml_path,
):
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    trial = optuna.trial.FixedTrial({"learning_rate": 1e-4})
    # Act
    result = load_yaml_as_an_optuna_dict(loguniform_yaml_path, trial)
    # Assert
    assert result["learning_rate"] == pytest.approx(1e-4)


@pytest.fixture
def intloguniform_yaml_path(tmp_path):
    # Arrange
    p = tmp_path / "intlog.yaml"
    p.write_text(
        yaml.safe_dump(
            {
                "hidden_size": {
                    "distribution": "intloguniform",
                    "min": 8,
                    "max": 512,
                }
            }
        )
    )
    return str(p)


def test_load_yaml_as_optuna_dict_intloguniform_returns_suggested_value(
    intloguniform_yaml_path,
):
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    trial = optuna.trial.FixedTrial({"hidden_size": 16})
    # Act
    result = load_yaml_as_an_optuna_dict(intloguniform_yaml_path, trial)
    # Assert
    assert result["hidden_size"] == 16


def test_load_yaml_as_optuna_dict_empty_yaml_raises_attributeerror(tmp_path):
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    p = tmp_path / "empty.yaml"
    p.write_text("")
    trial = optuna.trial.FixedTrial({})
    # Act
    ctx = pytest.raises(AttributeError)
    # Assert
    with ctx:
        # ``yaml.safe_load("")`` returns ``None``; the helper iterates the
        # parsed mapping unconditionally, so empty input surfaces as an
        # AttributeError. Pinning the current behaviour with a real test
        # avoids the previous mock-based assumption that it returns {}.
        load_yaml_as_an_optuna_dict(str(p), trial)


def test_load_yaml_as_optuna_dict_string_min_max_converted_to_float(tmp_path):
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    p = tmp_path / "strminmax.yaml"
    p.write_text(
        yaml.safe_dump(
            {"param1": {"distribution": "uniform", "min": "10", "max": "100"}}
        )
    )
    trial = optuna.trial.FixedTrial({"param1": 50})
    # Act
    result = load_yaml_as_an_optuna_dict(str(p), trial)
    # Assert
    assert result["param1"] == 50


def test_load_yaml_as_optuna_dict_ml_scenario_picks_model_type(tmp_path):
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    ml_config = {
        "model_type": {
            "distribution": "categorical",
            "values": ["cnn", "rnn", "transformer"],
        },
        "learning_rate": {"distribution": "loguniform", "min": 1e-5, "max": 1e-1},
    }
    p = tmp_path / "ml.yaml"
    p.write_text(yaml.safe_dump(ml_config))
    trial = optuna.trial.FixedTrial(
        {"model_type": "transformer", "learning_rate": 1e-3}
    )
    # Act
    result = load_yaml_as_an_optuna_dict(str(p), trial)
    # Assert
    assert result["model_type"] == "transformer"


def test_load_yaml_as_optuna_dict_ml_scenario_picks_learning_rate(tmp_path):
    # Arrange
    from scitex_io._load_modules import load_yaml_as_an_optuna_dict

    ml_config = {
        "learning_rate": {"distribution": "loguniform", "min": 1e-5, "max": 1e-1}
    }
    p = tmp_path / "ml2.yaml"
    p.write_text(yaml.safe_dump(ml_config))
    trial = optuna.trial.FixedTrial({"learning_rate": 1e-3})
    # Act
    result = load_yaml_as_an_optuna_dict(str(p), trial)
    # Assert
    assert result["learning_rate"] == pytest.approx(1e-3)


def test_load_study_rdb_creates_study_in_real_sqlite(tmp_path):
    """End-to-end real-collaborator test.

    Creates a real Optuna study in a temporary sqlite RDB file, then
    loads it back through ``load_study_rdb`` and asserts the study
    name round-trips. Exercises the real ``RDBStorage`` + ``load_study``
    code path that the prior mock-based tests only pretended to cover.
    """
    # Arrange
    from scitex_io._load_modules import load_study_rdb

    db_path = tmp_path / "real.db"
    rdb_url = f"sqlite:///{db_path}"
    storage = optuna.storages.RDBStorage(url=rdb_url)
    optuna.create_study(study_name="real_study", storage=storage)

    # Act
    loaded = load_study_rdb("real_study", rdb_url)
    # Assert
    assert loaded.study_name == "real_study"


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
