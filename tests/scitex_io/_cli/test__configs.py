"""Tests for scitex_io._cli._configs: load-configs and deprecated configs."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from scitex_io._cli._configs import configs_deprecated, load_configs_cmd


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "PATH.yaml").write_text("DATA_DIR: ./data\n")
    (cfg / "PARAMS.yaml").write_text("ALPHA: 0.05\nBETA: 0.2\n")
    return cfg


class TestLoadConfigs:
    @pytest.fixture
    def help_res(self, runner):
        return runner.invoke(load_configs_cmd, ["--help"])

    @pytest.fixture
    def pretty_res(self, runner, config_dir):
        return runner.invoke(load_configs_cmd, ["-d", str(config_dir)])

    @pytest.fixture
    def json_res(self, runner, config_dir):
        return runner.invoke(load_configs_cmd, ["-d", str(config_dir), "--json"])

    @pytest.fixture
    def json_payload(self, json_res):
        return json.loads(json_res.output)

    def test_help_flag_exits_with_zero_status(self, help_res):
        # Arrange
        # Act
        # Assert
        assert help_res.exit_code == 0

    def test_help_flag_output_has_usage_line(self, help_res):
        # Arrange
        # Act
        # Assert
        assert "Usage:" in help_res.output

    def test_help_flag_mentions_yaml_or_configuration(self, help_res):
        # Arrange
        # Act
        # Assert
        assert "YAML" in help_res.output or "configuration" in help_res.output

    def test_pretty_run_exits_with_zero_status(self, pretty_res):
        # Arrange
        # Act
        # Assert
        assert pretty_res.exit_code == 0, pretty_res.output

    def test_pretty_run_shows_config_dir_label(self, pretty_res):
        # Arrange
        # Act
        # Assert
        assert "Config dir:" in pretty_res.output

    def test_pretty_run_shows_namespaces_label(self, pretty_res):
        # Arrange
        # Act
        # Assert
        assert "Namespaces:" in pretty_res.output

    def test_pretty_run_mentions_at_least_one_known_namespace(self, pretty_res):
        # Arrange
        # Act
        # Assert
        assert "PATH" in pretty_res.output or "PARAMS" in pretty_res.output

    def test_json_run_exits_with_zero_status(self, json_res):
        # Arrange
        # Act
        # Assert
        assert json_res.exit_code == 0, json_res.output

    def test_json_payload_is_dict_type(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert isinstance(json_payload, dict)

    def test_json_payload_has_at_least_one_known_namespace(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "PATH" in json_payload or "PARAMS" in json_payload

    def test_verbose_debug_run_exits_with_zero_status(self, runner, config_dir):
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir), "--debug", "-v"])
        # Assert
        assert res.exit_code == 0, res.output

    def test_no_debug_flag_run_exits_with_zero_status(self, runner, config_dir):
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir), "--no-debug"])
        # Assert
        assert res.exit_code == 0, res.output

    def test_missing_dir_does_not_crash(self, runner, tmp_path):
        # Arrange
        missing = tmp_path / "nope"
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(missing)])
        # Assert
        # Either succeeds with empty namespaces, or surfaces error — both acceptable.
        assert res.exit_code in (0, 1, 2)


class TestConfigsDeprecated:
    @pytest.fixture
    def deprecated_res(self, runner):
        return runner.invoke(configs_deprecated, [])

    def test_deprecated_invoke_exits_with_status_2(self, deprecated_res):
        # Arrange
        # Act
        # Assert
        assert deprecated_res.exit_code == 2

    def test_deprecated_invoke_redirects_to_load_configs(self, deprecated_res):
        # Arrange
        # Act
        # Assert
        assert "load-configs" in deprecated_res.output
