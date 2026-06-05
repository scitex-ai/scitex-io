#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2025-06-02 14:55:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__matlab.py

"""Tests for MATLAB file loading functionality (real-file based, no mocks).

Tests cover:
- Basic MATLAB file loading with scipy.io
- Complex MATLAB data structures
- Different MATLAB file versions
- Various MATLAB data types and conversions
- Large file handling
- Error conditions and edge cases
- Integration with scientific computing workflows
"""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
# scipy is required by the MATLAB loader (`from scipy.io import loadmat`).
pytest.importorskip("scipy")

import numpy as np
import scipy.io as sio


def _save_mat(data, format_version="5", suffix=".mat"):
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        sio.savemat(f.name, data, format=format_version)
        return f.name


@pytest.fixture
def basic_mat_path():
    # Arrange
    data = {
        "double_array": np.random.rand(10, 20),
        "integer_scalar": 42,
        "float_scalar": 3.14159,
        "complex_array": np.array([1 + 2j, 3 + 4j, 5 + 6j]),
    }
    path = _save_mat(data)
    try:
        yield path, data
    finally:
        os.unlink(path)


def test_basic_matlab_loading_contains_double_array(basic_mat_path):
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    path, _data = basic_mat_path
    # Act
    loaded_data = _load_matlab(path)
    # Assert
    assert "double_array" in loaded_data


def test_basic_matlab_loading_round_trips_double_array(basic_mat_path):
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    path, data = basic_mat_path
    # Act
    loaded_data = _load_matlab(path)
    # Assert
    assert np.allclose(loaded_data["double_array"], data["double_array"])


def test_basic_matlab_loading_round_trips_integer_scalar(basic_mat_path):
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    path, _data = basic_mat_path
    # Act
    loaded_data = _load_matlab(path)
    # Assert
    assert loaded_data["integer_scalar"].item() == 42


def test_basic_matlab_loading_round_trips_float_scalar(basic_mat_path):
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    path, _data = basic_mat_path
    # Act
    loaded_data = _load_matlab(path)
    # Assert
    assert abs(loaded_data["float_scalar"].item() - 3.14159) < 1e-10


@pytest.mark.parametrize(
    "invalid_path",
    ["file.txt", "file.hdf5", "file.csv", "file.json", "file.mat.bak", "file.matlab", "file"],
)
def test_extension_validation_raises_valueerror_for_non_mat(invalid_path):
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    # Act
    ctx = pytest.raises(ValueError, match="File must have .mat extension")
    # Assert
    with ctx:
        _load_matlab(invalid_path)


def test_scipy_loadmat_returns_test_array_key():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    data = {
        "test_array": np.random.rand(5, 5),
        "metadata": np.array(["experiment_1"], dtype="U20"),
    }
    path = _save_mat(data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert "test_array" in loaded_data
    finally:
        os.unlink(path)


def test_scipy_loadmat_kwargs_forwarding_returns_array_key():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    data = {"test_array": np.random.rand(5, 5)}
    path = _save_mat(data)
    try:
        # Act
        loaded = _load_matlab(path, squeeze_me=True, struct_as_record=False)
        # Assert
        assert "test_array" in loaded
    finally:
        os.unlink(path)


def test_struct_loading_preserves_experiment_key():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    nested_data = {
        "experiment": {"name": "test_experiment", "data": np.random.rand(5, 5)},
        "results": {"accuracy": 0.95},
    }
    path = _save_mat(nested_data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert "experiment" in loaded_data
    finally:
        os.unlink(path)


def test_struct_loading_preserves_results_key():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    nested_data = {
        "experiment": {"name": "test_experiment"},
        "results": {"accuracy": 0.95},
    }
    path = _save_mat(nested_data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert "results" in loaded_data
    finally:
        os.unlink(path)


def test_large_file_handling_round_trips_matrix_shape():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    data = {"large_matrix": np.random.rand(200, 200)}
    path = _save_mat(data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert loaded_data["large_matrix"].shape == (200, 200)
    finally:
        os.unlink(path)


def test_large_file_handling_round_trips_matrix_values():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    data = {"large_matrix": np.random.rand(200, 200)}
    path = _save_mat(data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert np.array_equal(
            loaded_data["large_matrix"][:5, :5], data["large_matrix"][:5, :5]
        )
    finally:
        os.unlink(path)


@pytest.mark.parametrize("version", ["4", "5"])
def test_different_matlab_versions_round_trip(version):
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    test_data = {"version_test": np.array([1, 2, 3, 4, 5])}
    path = _save_mat(test_data, format_version=version)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert np.array_equal(
            loaded_data["version_test"].flatten(), test_data["version_test"]
        )
    finally:
        os.unlink(path)


def test_error_handling_nonexistent_file_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    # Act
    ctx = pytest.raises(ValueError)
    # Assert
    with ctx:
        _load_matlab("nonexistent_file.mat")


def test_error_handling_nonexistent_file_message_contains_filename():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    # Act
    try:
        _load_matlab("nonexistent_file.mat")
        error_message = ""
    except ValueError as exc:
        error_message = str(exc)
    # Assert
    assert "Error loading file nonexistent_file.mat" in error_message


def test_corrupted_file_raises_valueerror_with_loading_message():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    with tempfile.NamedTemporaryFile(suffix=".mat", delete=False) as f:
        f.write(b"This is not a valid MATLAB file content")
        temp_path = f.name
    try:
        # Act
        try:
            _load_matlab(temp_path)
            error_message = ""
        except ValueError as exc:
            error_message = str(exc)
        # Assert
        assert "Error loading file" in error_message
    finally:
        os.unlink(temp_path)


def test_scientific_data_round_trips_experimental_key():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    scientific_data = {
        "experimental_data": {
            "time_series": np.random.rand(100, 8),
            "sampling_rate": 1000.0,
        },
        "analysis_results": {"power_spectrum": np.random.rand(64, 8)},
    }
    path = _save_mat(scientific_data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert "experimental_data" in loaded_data
    finally:
        os.unlink(path)


def test_scientific_data_round_trips_analysis_key():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    scientific_data = {
        "experimental_data": {"time_series": np.random.rand(100, 8)},
        "analysis_results": {"power_spectrum": np.random.rand(64, 8)},
    }
    path = _save_mat(scientific_data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert "analysis_results" in loaded_data
    finally:
        os.unlink(path)


def test_edge_cases_preserves_empty_array_key():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    edge_case_data = {"empty_array": np.array([]), "single_value": np.array([42])}
    path = _save_mat(edge_case_data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert "empty_array" in loaded_data
    finally:
        os.unlink(path)


def test_edge_cases_round_trips_single_value():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    edge_case_data = {"single_value": np.array([42])}
    path = _save_mat(edge_case_data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        # Assert
        assert loaded_data["single_value"].flatten()[0] == 42
    finally:
        os.unlink(path)


def test_edge_cases_nan_value_preserved():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    data = {"nan_values": np.array([np.nan, 1.0, np.inf, -np.inf])}
    path = _save_mat(data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        nan_array = loaded_data["nan_values"].flatten()
        # Assert
        assert np.isnan(nan_array[0])
    finally:
        os.unlink(path)


def test_edge_cases_inf_value_preserved():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    data = {"nan_values": np.array([np.nan, 1.0, np.inf, -np.inf])}
    path = _save_mat(data)
    try:
        # Act
        loaded_data = _load_matlab(path)
        nan_array = loaded_data["nan_values"].flatten()
        # Assert
        assert np.isinf(nan_array[2])
    finally:
        os.unlink(path)


def test_integration_with_main_load_function_contains_test_key():
    # Arrange
    import scitex_io  # noqa: F401 — established by importorskip at module top

    test_data = {"integration_test": np.array([1, 2, 3, 4, 5])}
    path = _save_mat(test_data)
    try:
        # Act
        loaded_data = scitex_io.load(path)
        # Assert
        assert "integration_test" in loaded_data
    finally:
        os.unlink(path)


def test_memory_efficiency_repeated_load_returns_consistent_shape():
    # Arrange
    from scitex_io._load_modules._matlab import _load_matlab

    data = {"repeated_test": np.random.rand(50, 50)}
    path = _save_mat(data)
    try:
        # Act
        loaded_data = None
        for _ in range(5):
            loaded_data = _load_matlab(path)
        # Assert
        assert loaded_data["repeated_test"].shape == (50, 50)
    finally:
        os.unlink(path)


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
