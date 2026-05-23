"""Tests for scitex_io._cli._info: show-info and deprecated info."""

import json

import pytest
from click.testing import CliRunner

from scitex_io._cli._info import info_deprecated, show_info


@pytest.fixture
def runner():
    return CliRunner()


class TestShowInfo:
    @pytest.fixture
    def default_res(self, runner):
        return runner.invoke(show_info, [])

    @pytest.fixture
    def help_res(self, runner):
        return runner.invoke(show_info, ["--help"])

    @pytest.fixture
    def verbose_v_res(self, runner):
        return runner.invoke(show_info, ["-v"])

    @pytest.fixture
    def verbose_vv_res(self, runner):
        return runner.invoke(show_info, ["-vv"])

    @pytest.fixture
    def json_res(self, runner):
        return runner.invoke(show_info, ["--json"])

    @pytest.fixture
    def json_payload(self, json_res):
        return json.loads(json_res.output)

    def test_default_run_exits_with_zero_status(self, default_res):
        # Arrange
        # Act
        # Assert
        assert default_res.exit_code == 0, default_res.output

    def test_default_run_shows_format_registry_header(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "Format Registry" in default_res.output

    def test_default_run_shows_save_section(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "Save:" in default_res.output

    def test_default_run_shows_load_section(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "Load:" in default_res.output

    def test_help_flag_exits_with_zero_status(self, help_res):
        # Arrange
        # Act
        # Assert
        assert help_res.exit_code == 0

    def test_help_output_contains_usage_line(self, help_res):
        # Arrange
        # Act
        # Assert
        assert "Usage:" in help_res.output

    def test_help_output_describes_io_formats(self, help_res):
        # Arrange
        # Act
        # Assert
        assert "registered I/O formats" in help_res.output

    def test_verbose_v_exits_with_zero_status(self, verbose_v_res):
        # Arrange
        # Act
        # Assert
        assert verbose_v_res.exit_code == 0

    def test_verbose_v_shows_builtin_section(self, verbose_v_res):
        # Arrange
        # Act
        # Assert
        assert "Built-in:" in verbose_v_res.output

    def test_verbose_vv_exits_with_zero_status(self, verbose_vv_res):
        # Arrange
        # Act
        # Assert
        assert verbose_vv_res.exit_code == 0

    def test_verbose_vv_shows_builtin_section(self, verbose_vv_res):
        # Arrange
        # Act
        # Assert
        assert "Built-in:" in verbose_vv_res.output

    def test_json_flag_exits_with_zero_status(self, json_res):
        # Arrange
        # Act
        # Assert
        assert json_res.exit_code == 0

    def test_json_payload_has_save_key(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "save" in json_payload

    def test_json_payload_has_load_key(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "load" in json_payload

    def test_json_payload_save_has_builtin_key(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "builtin" in json_payload["save"]

    def test_json_payload_save_builtin_is_list(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert isinstance(json_payload["save"]["builtin"], list)


class TestInfoDeprecated:
    @pytest.fixture
    def default_res(self, runner):
        return runner.invoke(info_deprecated, [])

    @pytest.fixture
    def bogus_args_res(self, runner):
        return runner.invoke(info_deprecated, ["--bogus", "arg"])

    def test_default_invoke_exits_with_status_2(self, default_res):
        # Arrange
        # Act
        # Assert
        assert default_res.exit_code == 2

    def test_default_invoke_mentions_show_info_replacement(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "show-info" in default_res.output

    def test_unknown_options_still_exits_with_status_2(self, bogus_args_res):
        # Arrange
        # Act
        # Assert
        assert bogus_args_res.exit_code == 2
