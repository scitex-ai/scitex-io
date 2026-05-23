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
    def test_function_with_annotated_default_x_in_out_and_y_in_out(self):
        # Arrange
        # Arrange
        def f(x: int = 1, y: str = "a"):
            pass
        # Act
        out = _format_signature(f)
        # Act
        # Assert
        # Assert
        assert "x" in out and "y" in out

    def test_function_with_annotated_default_int_in_out(self):
        # Arrange
        # Arrange
        def f(x: int = 1, y: str = "a"):
            pass
        # Act
        out = _format_signature(f)
        # Act
        # Assert
        # Assert
        assert "int" in out

    def test_function_with_annotated_default_str_in_out(self):
        # Arrange
        # Arrange
        def f(x: int = 1, y: str = "a"):
            pass
        # Act
        out = _format_signature(f)
        # Act
        # Assert
        # Assert
        assert "str" in out


    def test_function_no_annotations(self):
        # Arrange
        # Arrange
        def f(a, b=2):
            pass

        # Act
        # Act
        out = _format_signature(f)
        # Assert
        # Assert
        assert "a" in out and "b" in out

    def test_function_default_is_truncated(self):
        # Arrange
        # Arrange
        def f(x="abcdefghijklmnopqrstuvwxyz1234567890"):
            pass

        # Act
        # Act
        out = _format_signature(f)
        # Assert
        # Assert
        assert "..." in out

    def test_unsignable_returns_empty(self):
        # builtins like len → may raise; ensure no exception
        # Arrange
        # Act
        # Arrange
        # Act
        out = _format_signature(len)
        # Assert
        # Assert
        assert isinstance(out, str)


class TestGetApis:
    def test_returns_list_of_tuples(self):
        # Arrange
        # Arrange
        import scitex_io

        # Act
        # Act
        results = _get_apis(scitex_io, "scitex_io", max_depth=1)
        # Assert
        # Assert
        assert isinstance(results, list)
        # Each entry: (kind, name, sig, doc)
        for entry in results:
            assert len(entry) == 4
            assert entry[0] in ("F", "C", "M", "V")

    def test_recursion_visit_guard_b_equals_case(self):
        # Arrange
        # Arrange
        import scitex_io
        visited = set()
        a = _get_apis(scitex_io, "scitex_io", max_depth=2, _visited=visited)
        # second call short-circuits when same module is in visited
        # Act
        b = _get_apis(scitex_io, "scitex_io", max_depth=2, _visited=visited)
        # Act
        # Assert
        # Assert
        assert b == []

    def test_recursion_visit_guard_a_is_list(self):
        # Arrange
        # Arrange
        import scitex_io
        visited = set()
        a = _get_apis(scitex_io, "scitex_io", max_depth=2, _visited=visited)
        # second call short-circuits when same module is in visited
        # Act
        b = _get_apis(scitex_io, "scitex_io", max_depth=2, _visited=visited)
        # Act
        # Assert
        # Assert
        assert isinstance(a, list)



class TestListPythonApis:
    def test_help_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["--help"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_help_usage_in_res_output(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["--help"])
        # Act
        # Assert
        # Assert
        assert "Usage:" in res.output


    def test_default_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, [])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_default_res_output_strip(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, [])
        # Act
        # Assert
        # Assert
        assert res.output.strip()  # non-empty


    def test_verbose_v_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["-v"])
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_verbose_vv_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["-vv"])
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_verbose_vvv_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Act
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["-vvv"])
        # Assert
        # Assert
        assert res.exit_code == 0

    def test_json_res_exit_code_equals_n_0(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["--json"])
        # Act
        # Assert
        # Assert
        assert res.exit_code == 0, res.output

    def test_json_payload_module_scitex_io(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["--json"])
        # Assert
        assert res.exit_code == 0, res.output
        payload = json.loads(res.output)
        # Act
        # Assert
        assert payload["module"] == "scitex_io"

    def test_json_isinstance_payload_apis_list(self, runner):
        # Arrange
        # Arrange
        # Act
        res = runner.invoke(list_python_apis, ["--json"])
        # Assert
        assert res.exit_code == 0, res.output
        payload = json.loads(res.output)
        # Act
        # Assert
        assert isinstance(payload["apis"], list)

