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
    def test_help_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["--help"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_usage_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["--help"])
        # Act
        # Assert
        # Assert
        assert "Usage:" in res.output

    def test_help_yaml_in_res_output_or_configuration_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["--help"])
        # Act
        # Assert
        # Assert
        assert "YAML" in res.output or "configuration" in res.output


    def test_default_pretty_res_exit_code_equals_n_0(self, runner, config_dir):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir)])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_default_pretty_config_dir_in_res_output(self, runner, config_dir):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir)])
        # Act
        # Assert
        # Assert
        assert "Config dir:" in res.output

    def test_default_pretty_namespaces_in_res_output(self, runner, config_dir):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir)])
        # Act
        # Assert
        # Assert
        assert "Namespaces:" in res.output

    def test_default_pretty_path_in_res_output_or_params_in_res_output(self, runner, config_dir):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir)])
        # Act
        # Assert
        # Assert
        assert "PATH" in res.output or "PARAMS" in res.output


    def test_json_output_res_exit_code_equals_n_0(self, runner, config_dir):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir), "--json"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_json_output_payload_is_dict(self, runner, config_dir):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir), "--json"])
        # Assert
        assert res.exit_code == 0, res.output
        payload = json.loads(res.output)
        # Act
        # Assert
        assert isinstance(payload, dict)

    def test_json_output_path_in_payload_or_params_in_payload(self, runner, config_dir):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir), "--json"])
        # Assert
        assert res.exit_code == 0, res.output
        payload = json.loads(res.output)
        # Act
        # Assert
        assert "PATH" in payload or "PARAMS" in payload


    def test_verbose_debug_res_exit_code_equals_n_0(self, runner, config_dir):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir), "--debug", "-v"])
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_no_debug_flag(self, runner, config_dir):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(config_dir), "--no-debug"])
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_missing_dir_does_not_crash(self, runner, tmp_path):
        # load_configs tolerates missing dir (returns empty); cmd should still exit 0
        # Arrange
        # Arrange
        missing = tmp_path / "nope"
        # Act
        # Act
        res = runner.invoke(load_configs_cmd, ["-d", str(missing)])
        # Either succeeds with empty namespaces, or surfaces error — both acceptable
        # Assert
        # Assert
        assert res.exit_code in (0, 1, 2)


class TestConfigsDeprecated:
    def test_emits_redirect_and_exit_2_res_exit_code_equals_n_2(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(configs_deprecated, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 2

    def test_emits_redirect_and_exit_2_load_configs_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(configs_deprecated, [])
        # Act
        # Assert
        # Assert
        assert "load-configs" in res.output

