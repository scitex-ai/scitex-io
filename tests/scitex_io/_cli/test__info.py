"""Tests for scitex_io._cli._info: show-info and deprecated info."""

import json

import pytest
from click.testing import CliRunner

from scitex_io._cli._info import info_deprecated, show_info


@pytest.fixture
def runner():
    return CliRunner()


class TestShowInfo:
    def test_default_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_default_format_registry_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, [])
        # Act
        # Assert
        # Assert
        assert "Format Registry" in res.output

    def test_default_save_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, [])
        # Act
        # Assert
        # Assert
        assert "Save:" in res.output

    def test_default_load_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, [])
        # Act
        # Assert
        # Assert
        assert "Load:" in res.output


    def test_help_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["--help"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_usage_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["--help"])
        # Act
        # Assert
        # Assert
        assert "Usage:" in res.output

    def test_help_registered_i_o_formats_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["--help"])
        # Act
        # Assert
        # Assert
        assert "registered I/O formats" in res.output


    def test_verbose_v_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["-v"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_verbose_v_built_in_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["-v"])
        # Act
        # Assert
        # Assert
        assert "Built-in:" in res.output


    def test_verbose_vv_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["-vv"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_verbose_vv_built_in_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["-vv"])
        # Act
        # Assert
        # Assert
        assert "Built-in:" in res.output


    def test_json_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["--json"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_json_save_in_payload_and_load_in_payload(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["--json"])
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert "save" in payload and "load" in payload

    def test_json_builtin_in_payload_save(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["--json"])
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert "builtin" in payload["save"]

    def test_json_isinstance_payload_save_builtin_list(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_info, ["--json"])
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert isinstance(payload["save"]["builtin"], list)



class TestInfoDeprecated:
    def test_exit_2_with_message_res_exit_code_equals_n_2(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(info_deprecated, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 2

    def test_exit_2_with_message_show_info_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(info_deprecated, [])
        # Act
        # Assert
        # Assert
        assert "show-info" in res.output


    def test_ignores_unknown_options(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(info_deprecated, ["--bogus", "arg"])
        # Assert
        # Assert
        assert res.exit_code == 2
