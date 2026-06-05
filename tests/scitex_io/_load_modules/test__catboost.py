#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__catboost.py

"""Real-collaborator tests for the CatBoost model loader.

Mock-based tests previously covered call-shape assertions on
``CatBoostClassifier`` / ``CatBoostRegressor``. Per STX-NM001..003 those
tests are deleted; the surviving tests train a real CatBoost model,
save it, and load it back through ``_load_catboost``.
"""

import os
import tempfile

import numpy as np
import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")


# ---------------------------------------------------------------------------
# Validation (no catboost dependency required)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "invalid_path",
    [
        "model.pkl",
        "model.joblib",
        "model.json",
        "model.txt",
        "model.h5",
        "model.pth",
        "model.onnx",
        "model.cbm.bak",
    ],
)
def test_load_catboost_rejects_non_cbm_extension(invalid_path):
    """Reject paths whose extension is not .cbm."""
    # Arrange
    pytest.importorskip("catboost")
    from scitex_io._load_modules._catboost import _load_catboost
    # Act
    ctx = pytest.raises(ValueError, match="File must have .cbm extension")
    # Assert
    with ctx:
        _load_catboost(invalid_path)


# ---------------------------------------------------------------------------
# Real catboost fixtures + tests
# ---------------------------------------------------------------------------


@pytest.fixture
def catboost_module():
    """Skip the test if real catboost is not installed."""
    return pytest.importorskip("catboost")


@pytest.fixture
def trained_classifier_path(tmp_path, catboost_module):
    """Train a small CatBoostClassifier and save it to disk."""
    np.random.seed(42)
    X = np.random.rand(100, 5)
    y = np.random.randint(0, 2, 100)
    model = catboost_module.CatBoostClassifier(
        iterations=10, verbose=False, random_seed=42
    )
    model.fit(X, y)
    out = tmp_path / "classifier.cbm"
    model.save_model(str(out))
    return out, X


@pytest.fixture
def trained_regressor_path(tmp_path, catboost_module):
    """Train a small CatBoostRegressor and save it to disk."""
    np.random.seed(42)
    X = np.random.rand(100, 5)
    y = np.random.rand(100) * 100
    model = catboost_module.CatBoostRegressor(
        iterations=10, verbose=False, random_seed=42
    )
    model.fit(X, y)
    out = tmp_path / "regressor.cbm"
    model.save_model(str(out))
    return out, X


@pytest.fixture
def trained_multiclass_path(tmp_path, catboost_module):
    """Train a 3-class CatBoostClassifier and save it to disk."""
    np.random.seed(42)
    X = np.random.rand(150, 4)
    y = np.random.randint(0, 3, 150)
    model = catboost_module.CatBoostClassifier(
        iterations=10, verbose=False, random_seed=42
    )
    model.fit(X, y)
    out = tmp_path / "multiclass.cbm"
    model.save_model(str(out))
    return out, X


def test_load_catboost_classifier_exposes_predict(trained_classifier_path):
    """Loaded classifier exposes a ``predict`` method."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, _ = trained_classifier_path
    # Act
    loaded = _load_catboost(str(path))
    # Assert
    assert hasattr(loaded, "predict")


def test_load_catboost_classifier_exposes_predict_proba(trained_classifier_path):
    """Loaded classifier exposes ``predict_proba``."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, _ = trained_classifier_path
    # Act
    loaded = _load_catboost(str(path))
    # Assert
    assert hasattr(loaded, "predict_proba")


def test_load_catboost_classifier_predicts_correct_row_count(trained_classifier_path):
    """``predict`` on N rows returns N predictions."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, X = trained_classifier_path
    loaded = _load_catboost(str(path))
    # Act
    predictions = loaded.predict(X[:5])
    # Assert
    assert len(predictions) == 5


def test_load_catboost_classifier_predicts_binary_labels(trained_classifier_path):
    """Binary classifier predictions are in ``{0, 1}``."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, X = trained_classifier_path
    loaded = _load_catboost(str(path))
    # Act
    predictions = loaded.predict(X[:5])
    # Assert
    assert all(int(pred) in (0, 1) for pred in predictions)


def test_load_catboost_classifier_probabilities_have_two_columns(
    trained_classifier_path,
):
    """``predict_proba`` returns one column per class for the binary case."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, X = trained_classifier_path
    loaded = _load_catboost(str(path))
    # Act
    probabilities = loaded.predict_proba(X[:5])
    # Assert
    assert probabilities.shape == (5, 2)


def test_load_catboost_classifier_probabilities_sum_to_one(trained_classifier_path):
    """Per-row probabilities sum to 1."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, X = trained_classifier_path
    loaded = _load_catboost(str(path))
    # Act
    probabilities = loaded.predict_proba(X[:5])
    # Assert
    assert np.allclose(probabilities.sum(axis=1), 1.0)


def test_load_catboost_classifier_feature_importance_has_one_entry_per_feature(
    trained_classifier_path,
):
    """Feature importance has one entry per training feature."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, _ = trained_classifier_path
    loaded = _load_catboost(str(path))
    # Act
    importance = loaded.get_feature_importance()
    # Assert
    assert len(importance) == 5


def test_load_catboost_classifier_feature_importance_is_non_negative(
    trained_classifier_path,
):
    """All feature-importance entries are non-negative."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, _ = trained_classifier_path
    loaded = _load_catboost(str(path))
    # Act
    importance = loaded.get_feature_importance()
    # Assert
    assert all(imp >= 0 for imp in importance)


def test_load_catboost_regressor_exposes_predict(trained_regressor_path):
    """Loaded regressor exposes a ``predict`` method."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, _ = trained_regressor_path
    # Act
    loaded = _load_catboost(str(path))
    # Assert
    assert hasattr(loaded, "predict")


def test_load_catboost_regressor_get_params_returns_dict(trained_regressor_path):
    """Loaded regressor returns its hyperparameters as a dict."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, _ = trained_regressor_path
    loaded = _load_catboost(str(path))
    # Act
    params = loaded.get_params()
    # Assert
    assert isinstance(params, dict)


def test_load_catboost_multiclass_predicts_correct_row_count(trained_multiclass_path):
    """Multiclass predictions have one entry per input row."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, X = trained_multiclass_path
    loaded = _load_catboost(str(path))
    # Act
    predictions = loaded.predict(X[:5])
    # Assert
    assert len(predictions) == 5


def test_load_catboost_multiclass_predictions_are_valid_classes(
    trained_multiclass_path,
):
    """All multiclass predictions are in ``{0, 1, 2}``."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, X = trained_multiclass_path
    loaded = _load_catboost(str(path))
    # Act
    predictions = loaded.predict(X[:5])
    # Assert
    assert all(int(pred) in (0, 1, 2) for pred in predictions)


def test_load_catboost_multiclass_probabilities_have_three_columns(
    trained_multiclass_path,
):
    """``predict_proba`` returns one column per class for the 3-class case."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, X = trained_multiclass_path
    loaded = _load_catboost(str(path))
    # Act
    probabilities = loaded.predict_proba(X[:5])
    # Assert
    assert probabilities.shape == (5, 3)


def test_load_catboost_multiclass_probabilities_sum_to_one(trained_multiclass_path):
    """Per-row 3-class probabilities sum to 1."""
    # Arrange
    from scitex_io._load_modules._catboost import _load_catboost
    path, X = trained_multiclass_path
    loaded = _load_catboost(str(path))
    # Act
    probabilities = loaded.predict_proba(X[:5])
    # Assert
    assert np.allclose(probabilities.sum(axis=1), 1.0)


def test_scitex_io_load_dispatches_cbm_to_catboost(trained_classifier_path):
    """Loading via the public ``scitex_io.load`` dispatcher works."""
    # Arrange
    import scitex_io
    path, X = trained_classifier_path
    # Act
    loaded = scitex_io.load(str(path))
    # Assert
    assert hasattr(loaded, "predict")


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
