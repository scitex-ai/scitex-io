"""Tests for scitex_io.utils package __init__ re-exports."""

import pytest

try:
    from zarr.codecs import GzipCodec  # noqa: F401  -- zarr v3 marker
except Exception:  # noqa: BLE001
    pytest.skip(
        "zarr v3 required (zarr.codecs.GzipCodec missing)",
        allow_module_level=True,
    )

import scitex_io.utils as utils


def test_public_names_importable_hasattr_utils_migrate_h5_to_zarr():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert hasattr(utils, "migrate_h5_to_zarr")


def test_public_names_importable_hasattr_utils_migrate_h5_to_zarr_batch():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert hasattr(utils, "migrate_h5_to_zarr_batch")


def test_public_names_importable_callable_utils_migrate_h5_to_zarr():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert callable(utils.migrate_h5_to_zarr)


def test_public_names_importable_callable_utils_migrate_h5_to_zarr_batch():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert callable(utils.migrate_h5_to_zarr_batch)




def test___all___migrate_h5_to_zarr_in_utils_all():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert "migrate_h5_to_zarr" in utils.__all__


def test___all___migrate_h5_to_zarr_batch_in_utils_all():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert "migrate_h5_to_zarr_batch" in utils.__all__


