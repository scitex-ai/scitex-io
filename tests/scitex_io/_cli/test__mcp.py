"""Tests for scitex_io._cli._mcp: mcp group + start/doctor/install/list-tools."""

import json

import pytest
from click.testing import CliRunner

from scitex_io._cli._mcp import (
    doctor,
    install,
    installation_deprecated,
    list_tools,
    mcp,
    show_installation_deprecated,
    start_server,
)


@pytest.fixture
def runner():
    return CliRunner()


class TestMcpGroup:
    @pytest.fixture
    def no_subcommand_res(self, runner):
        return runner.invoke(mcp, [])

    @pytest.fixture
    def help_res(self, runner):
        return runner.invoke(mcp, ["--help"])

    @pytest.fixture
    def help_recursive_res(self, runner):
        return runner.invoke(mcp, ["--help-recursive"])

    def test_no_subcommand_exits_with_zero_status(self, no_subcommand_res):
        # Arrange
        # Act
        # Assert
        assert no_subcommand_res.exit_code == 0

    def test_no_subcommand_prints_usage_line(self, no_subcommand_res):
        # Arrange
        # Act
        # Assert
        assert "Usage:" in no_subcommand_res.output

    def test_help_flag_exits_with_zero_status(self, help_res):
        # Arrange
        # Act
        # Assert
        assert help_res.exit_code == 0

    def test_help_flag_mentions_mcp_in_output(self, help_res):
        # Arrange
        # Act
        # Assert
        assert "MCP" in help_res.output

    def test_help_recursive_exits_with_zero_status(self, help_recursive_res):
        # Arrange
        # Act
        # Assert
        assert help_recursive_res.exit_code == 0

    def test_help_recursive_mentions_mcp_subcommand(self, help_recursive_res):
        # Arrange
        # Act
        # Assert
        assert "mcp" in help_recursive_res.output

    def test_help_recursive_mentions_start_subcommand(self, help_recursive_res):
        # Arrange
        # Act
        # Assert
        assert "start" in help_recursive_res.output

    def test_help_recursive_mentions_doctor_subcommand(self, help_recursive_res):
        # Arrange
        # Act
        # Assert
        assert "doctor" in help_recursive_res.output


class TestStartServer:
    @pytest.fixture
    def help_res(self, runner):
        return runner.invoke(start_server, ["--help"])

    @pytest.fixture
    def dry_run_res(self, runner):
        return runner.invoke(start_server, ["--dry-run"])

    @pytest.fixture
    def dry_run_custom_res(self, runner):
        return runner.invoke(
            start_server, ["--dry-run", "--host", "0.0.0.0", "--port", "9100"]
        )

    def test_help_flag_exits_with_zero_status(self, help_res):
        # Arrange
        # Act
        # Assert
        assert help_res.exit_code == 0

    def test_help_mentions_host_flag(self, help_res):
        # Arrange
        # Act
        # Assert
        assert "host" in help_res.output.lower()

    def test_help_mentions_port_flag(self, help_res):
        # Arrange
        # Act
        # Assert
        assert "port" in help_res.output.lower()

    def test_dry_run_exits_with_zero_status(self, dry_run_res):
        # Arrange
        # Act
        # Assert
        assert dry_run_res.exit_code == 0

    def test_dry_run_output_says_dry_run(self, dry_run_res):
        # Arrange
        # Act
        # Assert
        assert "DRY RUN" in dry_run_res.output

    def test_dry_run_output_shows_default_host(self, dry_run_res):
        # Arrange
        # Act
        # Assert
        assert "127.0.0.1" in dry_run_res.output

    def test_dry_run_output_shows_default_port(self, dry_run_res):
        # Arrange
        # Act
        # Assert
        assert "8100" in dry_run_res.output

    def test_dry_run_custom_host_port_exits_with_zero_status(self, dry_run_custom_res):
        # Arrange
        # Act
        # Assert
        assert dry_run_custom_res.exit_code == 0

    def test_dry_run_custom_host_shows_in_output(self, dry_run_custom_res):
        # Arrange
        # Act
        # Assert
        assert "0.0.0.0" in dry_run_custom_res.output

    def test_dry_run_custom_port_shows_in_output(self, dry_run_custom_res):
        # Arrange
        # Act
        # Assert
        assert "9100" in dry_run_custom_res.output


class TestDoctor:
    @pytest.fixture
    def default_res(self, runner):
        return runner.invoke(doctor, [])

    @pytest.fixture
    def help_res(self, runner):
        return runner.invoke(doctor, ["--help"])

    def test_default_run_exits_with_zero_status(self, default_res):
        # Arrange
        # Act
        # Assert
        assert default_res.exit_code == 0

    def test_default_run_says_mcp_doctor(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "MCP Doctor" in default_res.output

    def test_default_run_mentions_scitex_io(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "scitex-io" in default_res.output

    def test_help_flag_exits_with_zero_status(self, help_res):
        # Arrange
        # Act
        # Assert
        assert help_res.exit_code == 0


class TestInstall:
    @pytest.fixture
    def default_res(self, runner):
        return runner.invoke(install, [])

    @pytest.fixture
    def json_res(self, runner):
        return runner.invoke(install, ["--json"])

    @pytest.fixture
    def json_payload(self, json_res):
        return json.loads(json_res.output)

    @pytest.fixture
    def dry_run_yes_res(self, runner):
        return runner.invoke(install, ["--dry-run", "-y"])

    @pytest.fixture
    def help_res(self, runner):
        return runner.invoke(install, ["--help"])

    def test_default_pretty_exits_with_zero_status(self, default_res):
        # Arrange
        # Act
        # Assert
        assert default_res.exit_code == 0

    def test_default_pretty_mentions_mcp_installation(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "MCP Installation" in default_res.output

    def test_default_pretty_shows_pip_install_command(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "pip install scitex-io[mcp]" in default_res.output

    def test_default_pretty_shows_mcp_start_command(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "scitex-io mcp start" in default_res.output

    def test_default_pretty_shows_mcp_doctor_command(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "scitex-io mcp doctor" in default_res.output

    def test_json_flag_exits_with_zero_status(self, json_res):
        # Arrange
        # Act
        # Assert
        assert json_res.exit_code == 0

    def test_json_payload_has_install_command(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert json_payload["install_command"] == "pip install scitex-io[mcp]"

    def test_json_payload_config_has_mcp_servers(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "mcpServers" in json_payload["config"]

    def test_json_payload_mcp_servers_lists_scitex_io(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "scitex-io" in json_payload["config"]["mcpServers"]

    def test_dry_run_yes_flags_exit_with_zero_status(self, dry_run_yes_res):
        # Arrange
        # Act
        # Assert
        assert dry_run_yes_res.exit_code == 0

    def test_help_flag_exits_with_zero_status(self, help_res):
        # Arrange
        # Act
        # Assert
        assert help_res.exit_code == 0


class TestInstallationDeprecated:
    @pytest.fixture
    def deprecated_res(self, runner):
        return runner.invoke(installation_deprecated, [])

    @pytest.fixture
    def show_deprecated_res(self, runner):
        return runner.invoke(show_installation_deprecated, [])

    def test_installation_deprecated_exits_with_status_2(self, deprecated_res):
        # Arrange
        # Act
        # Assert
        assert deprecated_res.exit_code == 2

    def test_installation_deprecated_mentions_mcp_install(self, deprecated_res):
        # Arrange
        # Act
        # Assert
        assert "mcp install" in deprecated_res.output

    def test_show_installation_deprecated_exits_with_status_2(self, show_deprecated_res):
        # Arrange
        # Act
        # Assert
        assert show_deprecated_res.exit_code == 2

    def test_show_installation_deprecated_mentions_mcp_install(self, show_deprecated_res):
        # Arrange
        # Act
        # Assert
        assert "mcp install" in show_deprecated_res.output


def _maybe_skip_if_mcp_missing(res):
    # If fastmcp missing, ClickException is raised; surface gracefully
    if res.exit_code != 0 and "MCP not available" in res.output:
        pytest.skip("MCP runtime not installed in this env")


class TestListTools:
    @pytest.fixture
    def help_res(self, runner):
        return runner.invoke(list_tools, ["--help"])

    @pytest.fixture
    def default_res(self, runner):
        res = runner.invoke(list_tools, [])
        _maybe_skip_if_mcp_missing(res)
        return res

    @pytest.fixture
    def verbose_v_res(self, runner):
        res = runner.invoke(list_tools, ["-v"])
        _maybe_skip_if_mcp_missing(res)
        return res

    @pytest.fixture
    def verbose_vv_res(self, runner):
        res = runner.invoke(list_tools, ["-vv"])
        _maybe_skip_if_mcp_missing(res)
        return res

    @pytest.fixture
    def json_res(self, runner):
        res = runner.invoke(list_tools, ["--json"])
        _maybe_skip_if_mcp_missing(res)
        return res

    @pytest.fixture
    def json_payload(self, json_res):
        return json.loads(json_res.output)

    def test_help_flag_exits_with_zero_status(self, help_res):
        # Arrange
        # Act
        # Assert
        assert help_res.exit_code == 0

    def test_default_run_exits_with_zero_status(self, default_res):
        # Arrange
        # Act
        # Assert
        assert default_res.exit_code == 0, default_res.output

    def test_default_run_shows_tools_or_empty_message(self, default_res):
        # Arrange
        # Act
        # Assert
        assert "MCP Tools" in default_res.output or "No MCP tools" in default_res.output

    def test_verbose_v_exits_with_zero_status(self, verbose_v_res):
        # Arrange
        # Act
        # Assert
        assert verbose_v_res.exit_code == 0

    def test_verbose_vv_exits_with_zero_status(self, verbose_vv_res):
        # Arrange
        # Act
        # Assert
        assert verbose_vv_res.exit_code == 0

    def test_json_exits_with_zero_status(self, json_res):
        # Arrange
        # Act
        # Assert
        assert json_res.exit_code == 0

    def test_json_payload_has_total_key(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "total" in json_payload

    def test_json_payload_has_tools_key(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert "tools" in json_payload

    def test_json_payload_tools_is_list_type(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert isinstance(json_payload["tools"], list)
