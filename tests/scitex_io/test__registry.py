#!/usr/bin/env python3
"""Tests for the format registry system."""

import pytest

from scitex_io import _builtin_handlers  # noqa: F401 — registers builtin formats
from scitex_io import _registry
from scitex_io._registry import (
    _normalize_ext,
    get_loader,
    get_saver,
    list_formats,
    register_saver,
    unregister_saver,
)


@pytest.fixture(autouse=True)
def _restore_registry():
    """Snapshot the user-registry and restore it after each test.

    Tests that call ``register_saver`` (a user override) without an
    explicit ``unregister_saver`` leak state into sibling tests — e.g.
    a leaked ``.json`` override makes a later "is original" assertion
    capture the leak as the baseline. Restoring the four user dicts
    after every test guarantees isolation regardless of cleanup hygiene
    inside individual tests.
    """
    # Arrange
    saved = {
        "savers": dict(_registry._user_savers),
        "loaders": dict(_registry._user_loaders),
    }
    # Act
    yield
    # Assert
    _registry._user_savers.clear()
    _registry._user_savers.update(saved["savers"])
    _registry._user_loaders.clear()
    _registry._user_loaders.update(saved["loaders"])


class TestNormalizeExt:
    def test_adds_dot_normalize_ext_csv_csv(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert _normalize_ext("csv") == ".csv"

    def test_keeps_dot_normalize_ext_csv_csv(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert _normalize_ext(".csv") == ".csv"

    def test_lowercase_normalize_ext_csv_csv(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert _normalize_ext(".CSV") == ".csv"


class TestRegistry:
    def test_builtin_formats_loaded_len_fmts_save_builtin_20(self):
        # Arrange
        # Arrange
        # Act
        fmts = list_formats()
        # Act
        # Assert
        # Assert
        assert len(fmts["save"]["builtin"]) > 20

    def test_builtin_formats_loaded_len_fmts_load_builtin_20(self):
        # Arrange
        # Arrange
        # Act
        fmts = list_formats()
        # Act
        # Assert
        # Assert
        assert len(fmts["load"]["builtin"]) > 20

    def test_get_builtin_saver(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert callable(get_saver(".json"))

    def test_get_builtin_loader(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert callable(get_loader(".json"))

    def test_unknown_ext_returns_none_get_saver_unknown_xyz_is_none(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert get_saver(".unknown_xyz") is None

    def test_unknown_ext_returns_none_get_loader_unknown_xyz_is_none(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert get_loader(".unknown_xyz") is None

    def test_user_override_get_saver_test_ov_is_my_saver(self):
        # Arrange
        # Arrange
        def my_saver(obj, path, **kw):
            pass

        # Act
        register_saver(".test_ov", my_saver)
        # Act
        # Assert
        # Assert
        assert get_saver(".test_ov") is my_saver

    def test_user_override_get_saver_test_ov_is_none(self):
        # Arrange
        # Arrange
        def my_saver(obj, path, **kw):
            pass

        # Act
        register_saver(".test_ov", my_saver)
        # Assert
        assert get_saver(".test_ov") is my_saver
        unregister_saver(".test_ov")
        # Act
        # Assert
        assert get_saver(".test_ov") is None

    def test_decorator_pattern_get_saver_test_deco_is_save_deco(self):
        @register_saver(".test_deco")
        # Arrange
        # Act
        # Arrange
        # Act
        def save_deco(obj, path, **kw):
            pass

        # Assert
        # Assert
        assert get_saver(".test_deco") is save_deco
        unregister_saver(".test_deco")

    def test_user_overrides_builtin_get_saver_json_is_custom_json(self):
        # Arrange
        # Arrange
        original = get_saver(".json")

        def custom_json(obj, path, **kw):
            pass

        # Act
        register_saver(".json", custom_json)
        # Act
        # Assert
        # Assert
        assert get_saver(".json") is custom_json

    def test_user_overrides_builtin_get_saver_json_is_original(self):
        # Arrange
        # Arrange
        original = get_saver(".json")

        def custom_json(obj, path, **kw):
            pass

        # Act
        register_saver(".json", custom_json)
        # Assert
        assert get_saver(".json") is custom_json
        unregister_saver(".json")
        # Act
        # Assert
        assert get_saver(".json") is original
