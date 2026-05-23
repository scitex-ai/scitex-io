"""Tests for scitex_io._cli._main: root group, deprecations, recursive help."""


from __future__ import annotations
import pytest
from click.testing import CliRunner

from scitex_io._cli._main import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestMainHelp:
    def test_help_flag_short_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["-h"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_flag_short_usage_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["-h"])
        # Act
        # Assert
        # Assert
        assert "Usage:" in res.output

    def test_help_flag_short_scitex_io_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["-h"])
        # Act
        # Assert
        # Assert
        assert "scitex-io" in res.output


    def test_help_flag_long_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["--help"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_flag_long_any_cat_in_res_output_for_cat_in_core_i_o_integration_utilit(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["--help"])
        # Act
        # Assert
        # Assert
        assert any(
            cat in res.output for cat in ("Core I/O", "Integration", "Utility", "Other")
        )


    def test_no_subcommand_prints_help_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_no_subcommand_prints_help_usage_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, [])
        # Act
        # Assert
        # Assert
        assert "Usage:" in res.output


    def test_version_long_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["--version"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_version_long_main_in_res_output_or_version_in_res_output_lower(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["--version"])
        # Act
        # Assert
        # Assert
        assert "main" in res.output or "version" in res.output.lower()


    def test_version_short_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(main, ["-V"])
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_recursive_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["--help-recursive"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_recursive_scitex_io_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["--help-recursive"])
        # Act
        # Assert
        # Assert
        assert "scitex-io" in res.output

    def test_help_recursive_show_info_in_res_output_or_load_configs_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["--help-recursive"])
        # Act
        # Assert
        # Assert
        assert "show-info" in res.output or "load-configs" in res.output


    def test_json_flag_propagates(self, runner):
        # --json on root just sets ctx.obj["as_json"], should not crash with no subcommand
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(main, ["--json"])
        # Assert
        # Assert
        assert res.exit_code == 0


class TestMainCategorization:
    def test_help_includes_known_commands(self, runner):
        # Arrange
        # Act
        # Assert
        # Arrange
        res = runner.invoke(main, ["--help"])
        # Act
        out = res.output
        # Assert
        assert all(cmd in out for cmd in ('show-info', 'load-configs', 'list-python-apis', 'mcp')), f'{cmd} missing from --help'

    def test_unknown_command_errors_res_exit_code_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["this-command-does-not-exist"])
        # Act
        # Assert
        # Assert
        assert res.exit_code != 0

    def test_unknown_command_errors_no_such_command_in_res_output_or_error_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["this-command-does-not-exist"])
        # Act
        # Assert
        # Assert
        assert "No such command" in res.output or "Error" in res.output



class TestDeprecatedShellCompletion:
    def test_shell_completion_deprecated_emits_error_res_exit_code_equals_n_2(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["shell-completion"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 2

    def test_shell_completion_deprecated_emits_error_install_shell_completion_in_res_output_or_split_into_in_res_(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["shell-completion"])
        # Act
        # Assert
        # Assert
        assert "install-shell-completion" in res.output or "split into" in res.output

