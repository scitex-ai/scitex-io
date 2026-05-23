"""Tests for scitex_io._cli._apis: list-python-apis."""

import json

import pytest
from click.testing import CliRunner

from scitex_io._cli._apis import (
    _format_signature,
    _get_apis,
    list_python_apis,
)


@pytest.fixture
def runner():
    return CliRunner()


class TestFormatSignature:
    def test_annotated_signature_contains_x_parameter(self):
        # Arrange
        def f(x: int = 1, y: str = "a"):
            pass
        # Act
        out = _format_signature(f)
        # Assert
        assert "x" in out

    def test_annotated_signature_contains_y_parameter(self):
        # Arrange
        def f(x: int = 1, y: str = "a"):
            pass
        # Act
        out = _format_signature(f)
        # Assert
        assert "y" in out

    def test_annotated_signature_contains_int_annotation(self):
        # Arrange
        def f(x: int = 1, y: str = "a"):
            pass
        # Act
        out = _format_signature(f)
        # Assert
        assert "int" in out

    def test_annotated_signature_contains_str_annotation(self):
        # Arrange
        def f(x: int = 1, y: str = "a"):
            pass
        # Act
        out = _format_signature(f)
        # Assert
        assert "str" in out

    def test_unannotated_signature_contains_first_arg(self):
        # Arrange
        def f(a, b=2):
            pass
        # Act
        out = _format_signature(f)
        # Assert
        assert "a" in out

    def test_unannotated_signature_contains_second_arg(self):
        # Arrange
        def f(a, b=2):
            pass
        # Act
        out = _format_signature(f)
        # Assert
        assert "b" in out

    def test_long_default_value_is_truncated_with_ellipsis(self):
        # Arrange
        def f(x="abcdefghijklmnopqrstuvwxyz1234567890"):
            pass
        # Act
        out = _format_signature(f)
        # Assert
        assert "..." in out

    def test_unsignable_object_returns_string(self):
        # Arrange
        target = len
        # Act
        out = _format_signature(target)
        # Assert
        assert isinstance(out, str)


class TestGetApis:
    def test_get_apis_returns_list_type(self):
        # Arrange
        import scitex_io
        # Act
        results = _get_apis(scitex_io, "scitex_io", max_depth=1)
        # Assert
        assert isinstance(results, list)

    def test_get_apis_entries_have_expected_arity(self):
        # Arrange
        import scitex_io
        # Act
        results = _get_apis(scitex_io, "scitex_io", max_depth=1)
        # Assert
        assert all(len(entry) == 4 for entry in results)

    def test_get_apis_entries_have_known_kind_marker(self):
        # Arrange
        import scitex_io
        # Act
        results = _get_apis(scitex_io, "scitex_io", max_depth=1)
        # Assert
        assert all(entry[0] in ("F", "C", "M", "V") for entry in results)

    def test_recursion_visit_guard_short_circuits_second_call(self):
        # Arrange
        import scitex_io
        visited = set()
        _get_apis(scitex_io, "scitex_io", max_depth=2, _visited=visited)
        # Act
        b = _get_apis(scitex_io, "scitex_io", max_depth=2, _visited=visited)
        # Assert
        assert b == []

    def test_recursion_first_call_returns_list_type(self):
        # Arrange
        import scitex_io
        visited = set()
        # Act
        a = _get_apis(scitex_io, "scitex_io", max_depth=2, _visited=visited)
        # Assert
        assert isinstance(a, list)


class TestListPythonApis:
    @pytest.fixture
    def help_res(self, runner):
        return runner.invoke(list_python_apis, ["--help"])

    @pytest.fixture
    def default_res(self, runner):
        return runner.invoke(list_python_apis, [])

    @pytest.fixture
    def json_res(self, runner):
        return runner.invoke(list_python_apis, ["--json"])

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

    def test_default_run_exits_with_zero_status(self, default_res):
        # Arrange
        # Act
        # Assert
        assert default_res.exit_code == 0, default_res.output

    def test_default_run_produces_nonempty_output(self, default_res):
        # Arrange
        # Act
        # Assert
        assert default_res.output.strip()

    def test_verbose_v_exits_with_zero_status(self, runner):
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["-v"])
        # Assert
        assert res.exit_code == 0

    def test_verbose_vv_exits_with_zero_status(self, runner):
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["-vv"])
        # Assert
        assert res.exit_code == 0

    def test_verbose_vvv_exits_with_zero_status(self, runner):
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["-vvv"])
        # Assert
        assert res.exit_code == 0

    def test_json_flag_exits_with_zero_status(self, json_res):
        # Arrange
        # Act
        # Assert
        assert json_res.exit_code == 0, json_res.output

    def test_json_payload_module_is_scitex_io(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert json_payload["module"] == "scitex_io"

    def test_json_payload_apis_is_list_type(self, json_payload):
        # Arrange
        # Act
        # Assert
        assert isinstance(json_payload["apis"], list)
