#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._loading._load_configs.

`load_configs` normalises every filename stem + every nested string key
to UPPER_CASE on load, and the returned ``DotDict`` is case-insensitive
on string-key lookup. The tests below exercise:

  * Filename → UPPER stem
  * Nested key → UPPER attribute
  * Case-insensitive lookup of UPPER-stored nested string-mapping keys
  * Case-collision fail-loud (ValueError naming file + path + both keys)
  * DEBUG_*/debug_* promotion when IS_DEBUG is set
  * Each of the three IS_DEBUG triggers (kwarg, ``CI=True``, IS_DEBUG.yaml)
  * Empty / missing / error paths

No mocks: every test writes real YAML files into a tmp dir and points
``load_configs`` at it via the ``config_dir`` argument, exercising the
real ``glob`` + ``load`` collaborators.
"""

import os

import pytest
import yaml

from scitex_io import load_configs
from scitex_io._utils import DotDict


def _write_configs(config_dir, files):
    """Write ``{stem: mapping}`` to ``<config_dir>/<stem>.yaml`` files.

    Real on-disk YAML so the test exercises the production ``glob`` +
    ``load`` path rather than a mocked stand-in.
    """
    os.makedirs(config_dir, exist_ok=True)
    for stem, mapping in files.items():
        with open(os.path.join(config_dir, f"{stem}.yaml"), "w") as f:
            yaml.dump(mapping, f, default_flow_style=False, sort_keys=False)


@pytest.fixture
def config_dir(tmp_path):
    """Return a fresh ``<tmp>/config`` directory path (not yet created)."""
    return os.path.join(str(tmp_path), "config")


@pytest.fixture
def ci_env_true():
    """Set ``CI=True`` for the test, restoring the prior value after."""
    saved = os.environ.get("CI")
    os.environ["CI"] = "True"
    try:
        yield
    finally:
        if saved is None:
            os.environ.pop("CI", None)
        else:
            os.environ["CI"] = saved


@pytest.fixture
def ci_env_unset():
    """Ensure ``CI`` is unset for the test, restoring the prior value."""
    saved = os.environ.get("CI")
    os.environ.pop("CI", None)
    try:
        yield
    finally:
        if saved is not None:
            os.environ["CI"] = saved


class TestLoadConfigsBasic:
    """Top-level shape: filename → UPPER stem; keys → UPPER attribute."""

    def test_returns_dotdict_instance(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(config_dir, {"config1": {"param1": "value1"}})
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert isinstance(result, DotDict)

    def test_filename_stem_becomes_upper_top_level_key(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(config_dir, {"config1": {"param1": "value1"}})
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert result.CONFIG1.PARAM1 == "value1"

    def test_integer_value_preserved(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(config_dir, {"config1": {"param2": 123}})
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert result.CONFIG1.PARAM2 == 123

    def test_already_upper_keys_preserved(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(config_dir, {"MODEL": {"HIDDEN_DIM": 256, "DROPOUT": 0.3}})
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert result.MODEL.HIDDEN_DIM == 256

    def test_merges_multiple_files(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(
            config_dir,
            {"a": {"param1": "value1"}, "b": {"param2": "value2"}},
        )
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert result.A.PARAM1 == "value1" and result.B.PARAM2 == "value2"


class TestUpperNormalisation:
    """The UPPER_CASE walker + case-insensitive lookup."""

    def test_lowercase_top_key_becomes_upper(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(config_dir, {"preprocess": {"sample_rate": 1_000}})
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert result.PREPROCESS.SAMPLE_RATE == 1_000

    def test_nested_lowercase_key_becomes_upper(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(
            config_dir, {"preprocess": {"nested": {"field_a": "a", "field_b": 42}}}
        )
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert result.PREPROCESS.NESTED.FIELD_A == "a"


class TestCaseInsensitiveLookup:
    """The Issue #32 fix: lowercase lookup of UPPER-stored string keys."""

    def test_keys_returns_upper_canonical_form(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(
            config_dir,
            {"SEIZURE": {"STR2COLOR": {"seizure": "red", "unknown": "gray"}}},
        )
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert set(result.SEIZURE.STR2COLOR.keys()) == {"SEIZURE", "UNKNOWN"}

    def test_lowercase_getitem_resolves_upper_stored_key(
        self, config_dir, ci_env_unset
    ):
        # Arrange
        _write_configs(config_dir, {"SEIZURE": {"STR2COLOR": {"seizure": "red"}}})
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert result.SEIZURE.STR2COLOR["seizure"] == "red"

    def test_upper_getitem_resolves_upper_stored_key(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(config_dir, {"SEIZURE": {"STR2COLOR": {"seizure": "red"}}})
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert result.SEIZURE.STR2COLOR["SEIZURE"] == "red"

    def test_lowercase_contains_matches_upper_stored_key(
        self, config_dir, ci_env_unset
    ):
        # Arrange
        _write_configs(config_dir, {"SEIZURE": {"STR2COLOR": {"seizure": "red"}}})
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=config_dir)
        # Assert
        assert "seizure" in result.SEIZURE.STR2COLOR


class TestCaseCollisionFailLoud:
    """A case collision is a user config error — fail loud at load time."""

    def test_filename_collision_raises_valueerror(self, config_dir, ci_env_unset):
        # Arrange — two stems folding to the same UPPER top-level key.
        _write_configs(
            config_dir, {"MODEL": {"HIDDEN_DIM": 256}, "model": {"OTHER": 1}}
        )
        # Act
        ctx = pytest.raises(ValueError)
        # Assert
        with ctx:
            load_configs(IS_DEBUG=False, config_dir=config_dir)

    def test_filename_collision_message_names_config_directory(
        self, config_dir, ci_env_unset
    ):
        # Arrange
        _write_configs(
            config_dir, {"MODEL": {"HIDDEN_DIM": 256}, "model": {"OTHER": 1}}
        )
        # Act
        ctx = pytest.raises(ValueError, match=r"config directory")
        # Assert
        with ctx:
            load_configs(IS_DEBUG=False, config_dir=config_dir)

    def test_filename_collision_message_names_both_stems(
        self, config_dir, ci_env_unset
    ):
        # Arrange
        _write_configs(
            config_dir, {"MODEL": {"HIDDEN_DIM": 256}, "model": {"OTHER": 1}}
        )
        # Act — both offending stems must appear (order-agnostic).
        ctx = pytest.raises(ValueError, match=r"'MODEL'.*'model'|'model'.*'MODEL'")
        # Assert
        with ctx:
            load_configs(IS_DEBUG=False, config_dir=config_dir)

    def test_nested_key_collision_raises_valueerror(self, config_dir, ci_env_unset):
        # Arrange — two keys inside one mapping fold to the same UPPER.
        _write_configs(config_dir, {"m": {"HIDDEN_DIM": 256, "hidden_dim": 999}})
        # Act
        ctx = pytest.raises(ValueError)
        # Assert
        with ctx:
            load_configs(IS_DEBUG=False, config_dir=config_dir)

    def test_nested_key_collision_message_names_source_file(
        self, config_dir, ci_env_unset
    ):
        # Arrange
        _write_configs(config_dir, {"m": {"HIDDEN_DIM": 256, "hidden_dim": 999}})
        # Act
        ctx = pytest.raises(ValueError, match=r"file 'm'")
        # Assert
        with ctx:
            load_configs(IS_DEBUG=False, config_dir=config_dir)

    def test_nested_key_collision_message_names_mapping_path(
        self, config_dir, ci_env_unset
    ):
        # Arrange
        _write_configs(config_dir, {"m": {"HIDDEN_DIM": 256, "hidden_dim": 999}})
        # Act
        ctx = pytest.raises(ValueError, match=r"CONFIG\.M")
        # Assert
        with ctx:
            load_configs(IS_DEBUG=False, config_dir=config_dir)

    def test_nested_key_collision_message_names_both_keys(
        self, config_dir, ci_env_unset
    ):
        # Arrange
        _write_configs(config_dir, {"m": {"HIDDEN_DIM": 256, "hidden_dim": 999}})
        # Act — both literal keys must appear (order-agnostic).
        ctx = pytest.raises(
            ValueError,
            match=r"'HIDDEN_DIM'.*'hidden_dim'|'hidden_dim'.*'HIDDEN_DIM'",
        )
        # Assert
        with ctx:
            load_configs(IS_DEBUG=False, config_dir=config_dir)

    def test_deep_string_mapping_collision_message_names_full_path(
        self, config_dir, ci_env_unset
    ):
        # Arrange — the neurovista reproduction: a deeply nested string
        # mapping (STR2COLOR) with two keys folding to one UPPER.
        _write_configs(
            config_dir,
            {"SEIZURE": {"STR2COLOR": {"seizure": "red", "SEIZURE": "blue"}}},
        )
        # Act
        ctx = pytest.raises(ValueError, match=r"CONFIG\.SEIZURE\.STR2COLOR")
        # Assert
        with ctx:
            load_configs(IS_DEBUG=False, config_dir=config_dir)


class TestNonStringKeysUntouched:
    """Non-string keys are matched exactly, never case-folded."""

    def test_integer_key_resolves_exactly(self):
        # Arrange — DotDict directly: int keys must stay exact.
        d = DotDict({1: "one", 2: "two"})
        # Act
        value = d[1]
        # Assert
        assert value == "one"

    def test_integer_key_membership_exact(self):
        # Arrange
        d = DotDict({42: "answer"})
        # Act
        present = 42 in d
        # Assert
        assert present is True

    def test_no_collision_between_int_and_string_keys(self):
        # Arrange — an int key and a string key never collide.
        d = DotDict({1: "int-one", "ONE": "str-one"})
        # Act
        # Assert
        assert d[1] == "int-one"


class TestDotDictDirectLookup:
    """DotDict case-insensitive lookup, exercised without load_configs."""

    def test_lowercase_getitem_on_upper_storage(self):
        # Arrange
        d = DotDict({"SEIZURE": "red"})
        # Act
        value = d["seizure"]
        # Assert
        assert value == "red"

    def test_upper_getitem_on_lower_storage(self):
        # Arrange — DotDict itself does not force UPPER storage.
        d = DotDict({"seizure": "red"})
        # Act
        value = d["SEIZURE"]
        # Assert
        assert value == "red"

    def test_lowercase_attribute_access_on_upper_storage(self):
        # Arrange
        d = DotDict({"SEIZURE": "red"})
        # Act
        value = d.seizure
        # Assert
        assert value == "red"

    def test_upper_attribute_access_on_lower_storage(self):
        # Arrange
        d = DotDict({"seizure": "red"})
        # Act
        value = d.SEIZURE
        # Assert
        assert value == "red"

    def test_lowercase_contains_on_upper_storage(self):
        # Arrange
        d = DotDict({"SEIZURE": "red"})
        # Act
        present = "seizure" in d
        # Assert
        assert present is True

    def test_upper_contains_on_lower_storage(self):
        # Arrange
        d = DotDict({"seizure": "red"})
        # Act
        present = "SEIZURE" in d
        # Assert
        assert present is True

    def test_get_lowercase_resolves_upper_storage(self):
        # Arrange
        d = DotDict({"SEIZURE": "red"})
        # Act
        value = d.get("seizure")
        # Assert
        assert value == "red"

    def test_get_missing_returns_default(self):
        # Arrange
        d = DotDict({"SEIZURE": "red"})
        # Act
        value = d.get("absent", "fallback")
        # Assert
        assert value == "fallback"

    def test_keys_return_stored_form_not_folded(self):
        # Arrange
        d = DotDict({"SEIZURE": "red", "unknown": "gray"})
        # Act
        stored = set(d.keys())
        # Assert
        assert stored == {"SEIZURE", "unknown"}

    def test_missing_string_key_raises_keyerror_with_original(self):
        # Arrange
        d = DotDict({"SEIZURE": "red"})
        # Act
        ctx = pytest.raises(KeyError)
        # Assert
        with ctx:
            d["absent"]

    def test_nested_dotdict_lookup_is_case_insensitive(self):
        # Arrange — recursion: nested dicts wrap into DotDict.
        d = DotDict({"OUTER": {"inner_key": "v"}})
        # Act
        value = d["outer"]["INNER_KEY"]
        # Assert
        assert value == "v"


class TestDebugPromotion:
    """DEBUG_<KEY> overrides <KEY> when IS_DEBUG is on."""

    def test_debug_replaces_normal_value(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(
            config_dir,
            {"config1": {"param1": "normal_value", "DEBUG_param1": "debug_value"}},
        )
        # Act
        result = load_configs(IS_DEBUG=True, config_dir=config_dir)
        # Assert
        assert result.CONFIG1.PARAM1 == "debug_value"

    def test_lowercase_debug_prefix_promotes(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(config_dir, {"config1": {"debug_param2": "another_debug_value"}})
        # Act
        result = load_configs(IS_DEBUG=True, config_dir=config_dir)
        # Assert
        assert result.CONFIG1.PARAM2 == "another_debug_value"

    def test_debug_promotion_in_nested_dict(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(
            config_dir,
            {"config1": {"top_level": {"DEBUG_special_key": "debug_special_value"}}},
        )
        # Act
        result = load_configs(IS_DEBUG=True, config_dir=config_dir)
        # Assert
        assert result.CONFIG1.TOP_LEVEL.SPECIAL_KEY == "debug_special_value"

    def test_ci_env_triggers_debug(self, config_dir, ci_env_true):
        # Arrange
        _write_configs(
            config_dir, {"config1": {"param": "normal", "DEBUG_param": "debug"}}
        )
        # Act
        result = load_configs(IS_DEBUG=None, config_dir=config_dir)
        # Assert
        assert result.CONFIG1.PARAM == "debug"

    def test_is_debug_yaml_triggers_debug(self, config_dir, ci_env_unset):
        # Arrange
        _write_configs(
            config_dir,
            {
                "IS_DEBUG": {"IS_DEBUG": True},
                "config1": {"param": "normal", "DEBUG_param": "debug"},
            },
        )
        # Act
        result = load_configs(IS_DEBUG=None, config_dir=config_dir)
        # Assert
        assert result.CONFIG1.PARAM == "debug"

    def test_show_prints_debug_substitution(self, config_dir, ci_env_unset, capsys):
        # Arrange
        _write_configs(config_dir, {"config1": {"DEBUG_param": "debug_value"}})
        # Act
        load_configs(IS_DEBUG=True, show=True, config_dir=config_dir)
        # Assert
        assert "DEBUG_param -> param" in capsys.readouterr().out


class TestEdgeCases:
    def test_empty_file_returns_empty_dotdict(self, config_dir, ci_env_unset):
        # Arrange — an empty YAML file loads as None and is skipped.
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, "empty.yaml"), "w") as f:
            f.write("")
        # Act
        result = load_configs(config_dir=config_dir)
        # Assert
        assert isinstance(result, DotDict) and len(result) == 0

    def test_malformed_yaml_returns_empty_and_prints(
        self, config_dir, ci_env_unset, capsys
    ):
        # Arrange — invalid YAML triggers the generic resilience path.
        os.makedirs(config_dir, exist_ok=True)
        with open(os.path.join(config_dir, "broken.yaml"), "w") as f:
            f.write("key: [unclosed\n")
        # Act
        result = load_configs(config_dir=config_dir)
        # Assert
        assert isinstance(result, DotDict) and len(result) == 0


class TestRealFilesystemRoundTrip:
    """End-to-end with real YAML files written to a tmp config dir."""

    @pytest.fixture
    def populated_config_dir(self, config_dir):
        _write_configs(
            config_dir,
            {
                "config1": {
                    "param1": "value1",
                    "param2": 123,
                    "nested": {"key1": "val1", "DEBUG_key2": "debug_val2"},
                },
                "config2": {
                    "param3": "value3",
                    "DEBUG_param4": "debug_value4",
                    "debug_param5": "debug_value5",
                },
                "IS_DEBUG": {"IS_DEBUG": False},
            },
        )
        return config_dir

    def test_production_mode_loads_normal_value(
        self, populated_config_dir, ci_env_unset
    ):
        # Arrange
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=populated_config_dir)
        # Assert
        assert result.CONFIG1.PARAM1 == "value1"

    def test_production_mode_skips_debug_promotion(
        self, populated_config_dir, ci_env_unset
    ):
        # Arrange
        # Act
        result = load_configs(IS_DEBUG=False, config_dir=populated_config_dir)
        # Assert
        assert "PARAM4" not in result.CONFIG2

    def test_debug_mode_promotes_top_level(self, populated_config_dir, ci_env_unset):
        # Arrange
        # Act
        result = load_configs(IS_DEBUG=True, config_dir=populated_config_dir)
        # Assert
        assert result.CONFIG2.PARAM4 == "debug_value4"

    def test_debug_mode_promotes_nested(self, populated_config_dir, ci_env_unset):
        # Arrange
        # Act
        result = load_configs(IS_DEBUG=True, config_dir=populated_config_dir)
        # Assert
        assert result.CONFIG1.NESTED.KEY2 == "debug_val2"


if __name__ == "__main__":
    pytest.main([os.path.abspath(__file__)])
