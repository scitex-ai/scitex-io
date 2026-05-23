"""Tests for scitex_io._cli._version (deprecated `version` subcommand)."""

import pytest
from click.testing import CliRunner

from scitex_io._cli._main import main
from scitex_io._cli._version import version as version_cmd


@pytest.fixture
def runner():
    return CliRunner()


class TestVersionDeprecated:
    def test_invokes_to_exit_2_with_message_res_exit_code_equals_n_2(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(version_cmd, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 2

    def test_invokes_to_exit_2_with_message_version_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(version_cmd, [])
        # Act
        # Assert
        # Assert
        assert "--version" in res.output


    def test_through_main_alias_res_exit_code_equals_n_2(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["version"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 2

    def test_through_main_alias_version_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(main, ["version"])
        # Act
        # Assert
        # Assert
        assert "--version" in res.output


    def test_ignores_unknown_options(self, runner):
        # context_settings ignore_unknown_options=True
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(version_cmd, ["--bogus"])
        # Assert
        # Assert
        assert res.exit_code == 2
