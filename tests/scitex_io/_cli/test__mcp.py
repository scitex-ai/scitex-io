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
    def test_no_subcommand_prints_help_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(mcp, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_no_subcommand_prints_help_usage_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(mcp, [])
        # Act
        # Assert
        # Assert
        assert "Usage:" in res.output


    def test_help_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(mcp, ["--help"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_mcp_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(mcp, ["--help"])
        # Act
        # Assert
        # Assert
        assert "MCP" in res.output


    def test_help_recursive_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(mcp, ["--help-recursive"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_recursive_mcp_in_out(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(mcp, ["--help-recursive"])
        # Assert
        assert res.exit_code == 0
        # contains subcommand headers
        out = res.output
        # Act
        # Assert
        assert "mcp" in out

    def test_help_recursive_start_in_out(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(mcp, ["--help-recursive"])
        # Assert
        assert res.exit_code == 0
        # contains subcommand headers
        out = res.output
        # Act
        # Assert
        assert "start" in out

    def test_help_recursive_doctor_in_out(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(mcp, ["--help-recursive"])
        # Assert
        assert res.exit_code == 0
        # contains subcommand headers
        out = res.output
        # Act
        # Assert
        assert "doctor" in out



class TestStartServer:
    def test_help_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(start_server, ["--help"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_host_in_res_output_lower(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(start_server, ["--help"])
        # Act
        # Assert
        # Assert
        assert "host" in res.output.lower()

    def test_help_port_in_res_output_lower(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(start_server, ["--help"])
        # Act
        # Assert
        # Assert
        assert "port" in res.output.lower()


    def test_dry_run_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(start_server, ["--dry-run"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_dry_run_dry_run_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(start_server, ["--dry-run"])
        # Act
        # Assert
        # Assert
        assert "DRY RUN" in res.output

    def test_dry_run_n_127_0_0_1_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(start_server, ["--dry-run"])
        # Act
        # Assert
        # Assert
        assert "127.0.0.1" in res.output

    def test_dry_run_n_8100_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(start_server, ["--dry-run"])
        # Act
        # Assert
        # Assert
        assert "8100" in res.output


    def test_dry_run_custom_host_port_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(
            start_server, ["--dry-run", "--host", "0.0.0.0", "--port", "9100"]
        )
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_dry_run_custom_host_port_n_0_0_0_0_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(
            start_server, ["--dry-run", "--host", "0.0.0.0", "--port", "9100"]
        )
        # Act
        # Assert
        # Assert
        assert "0.0.0.0" in res.output

    def test_dry_run_custom_host_port_n_9100_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(
            start_server, ["--dry-run", "--host", "0.0.0.0", "--port", "9100"]
        )
        # Act
        # Assert
        # Assert
        assert "9100" in res.output



class TestDoctor:
    def test_runs_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(doctor, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_runs_mcp_doctor_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(doctor, [])
        # Act
        # Assert
        # Assert
        assert "MCP Doctor" in res.output

    def test_runs_scitex_io_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(doctor, [])
        # Act
        # Assert
        # Assert
        assert "scitex-io" in res.output


    def test_help_res_exit_code_equals_n_0_2(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(doctor, ["--help"])
        # Assert
        # Assert
        assert res.exit_code == 0


class TestInstall:
    def test_default_pretty_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(install, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_default_pretty_mcp_installation_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(install, [])
        # Act
        # Assert
        # Assert
        assert "MCP Installation" in res.output

    def test_default_pretty_pip_install_scitex_io_mcp_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(install, [])
        # Act
        # Assert
        # Assert
        assert "pip install scitex-io[mcp]" in res.output

    def test_default_pretty_scitex_io_mcp_start_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(install, [])
        # Act
        # Assert
        # Assert
        assert "scitex-io mcp start" in res.output

    def test_default_pretty_scitex_io_mcp_doctor_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(install, [])
        # Act
        # Assert
        # Assert
        assert "scitex-io mcp doctor" in res.output


    def test_json_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(install, ["--json"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_json_payload_install_command_pip_install_scitex_io_mcp(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(install, ["--json"])
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert payload["install_command"] == "pip install scitex-io[mcp]"

    def test_json_mcpservers_in_payload_config(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(install, ["--json"])
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert "mcpServers" in payload["config"]

    def test_json_scitex_io_in_payload_config_mcpservers(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(install, ["--json"])
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert "scitex-io" in payload["config"]["mcpServers"]


    def test_dry_run_and_yes_flags_accepted(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(install, ["--dry-run", "-y"])
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_res_exit_code_equals_n_0_2(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(install, ["--help"])
        # Assert
        # Assert
        assert res.exit_code == 0


class TestInstallationDeprecated:
    def test_emits_error_res_exit_code_equals_n_2(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(installation_deprecated, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 2

    def test_emits_error_mcp_install_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(installation_deprecated, [])
        # Act
        # Assert
        # Assert
        assert "mcp install" in res.output


    def test_show_installation_deprecated_res_exit_code_equals_n_2(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_installation_deprecated, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 2

    def test_show_installation_deprecated_mcp_install_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(show_installation_deprecated, [])
        # Act
        # Assert
        # Assert
        assert "mcp install" in res.output



class TestListTools:
    def test_help_res_exit_code_equals_n_0_2(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(list_tools, ["--help"])
        # Assert
        # Assert
        assert res.exit_code == 0

    def _maybe_skip_if_mcp_missing(self, res):
        # If fastmcp missing, ClickException is raised; surface gracefully
        if res.exit_code != 0 and "MCP not available" in res.output:
            pytest.skip("MCP runtime not installed in this env")

    def test_default_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        res = runner.invoke(list_tools, [])
        # Act
        self._maybe_skip_if_mcp_missing(res)
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_default_mcp_tools_in_res_output_or_no_mcp_tools_in_res_output(self, runner):
        # Arrange
        # Arrange
        res = runner.invoke(list_tools, [])
        # Act
        self._maybe_skip_if_mcp_missing(res)
        # Act
        # Assert
        # Assert
        assert "MCP Tools" in res.output or "No MCP tools" in res.output


    def test_verbose_v_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        res = runner.invoke(list_tools, ["-v"])
        # Act
        # Act
        self._maybe_skip_if_mcp_missing(res)
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_verbose_vv_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        res = runner.invoke(list_tools, ["-vv"])
        # Act
        # Act
        self._maybe_skip_if_mcp_missing(res)
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_json_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        res = runner.invoke(list_tools, ["--json"])
        # Act
        self._maybe_skip_if_mcp_missing(res)
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_json_total_in_payload(self, runner):
        # Arrange
        # Arrange
        res = runner.invoke(list_tools, ["--json"])
        # Act
        self._maybe_skip_if_mcp_missing(res)
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert "total" in payload

    def test_json_tools_in_payload(self, runner):
        # Arrange
        # Arrange
        res = runner.invoke(list_tools, ["--json"])
        # Act
        self._maybe_skip_if_mcp_missing(res)
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert "tools" in payload

    def test_json_isinstance_payload_tools_list(self, runner):
        # Arrange
        # Arrange
        res = runner.invoke(list_tools, ["--json"])
        # Act
        self._maybe_skip_if_mcp_missing(res)
        # Assert
        assert res.exit_code == 0
        payload = json.loads(res.output)
        # Act
        # Assert
        assert isinstance(payload["tools"], list)

