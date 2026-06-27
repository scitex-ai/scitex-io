#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._utils.

from __future__ import annotations
Every public helper + the DotDict class. Real fixtures only — no mocks
around the system layer beyond `monkeypatch` for env vars / sys.argv.
"""

import os
import sys
from pathlib import Path

import pytest

from scitex_io._utils import (
    DotDict,
    clean,
    clean_path,
    color_text,
    detect_environment,
    get_notebook_info_simple,
    getsize,
    parse,
    preserve_doc,
    readable_bytes,
    split,
    this_path,
)


class TestStringHelpers:
    def test_clean_path_normalises_clean_path_a_b_c_os_path_normpath_a_b_c(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert clean_path("/a/b/../c") == os.path.normpath("/a/b/../c")

    def test_clean_path_normalises_clean_path_x_y_os_path_normpath_x_y(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert clean_path("./x/./y") == os.path.normpath("./x/./y")

    def test_clean_path_pathlike(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert clean_path(Path("/a") / "b") == os.path.normpath("/a/b")

    def test_color_text_known(self):
        # With colorama installed (it's a transitive dep), expect ANSI
        # escape codes around the text. Without colorama, fall through.
        # Arrange
        # Act
        # Arrange
        # Act
        out = color_text("hi", "green")
        # Assert
        # Assert
        assert "hi" in out

    def test_color_text_unknown_color(self):
        # Arrange
        # Act
        # Arrange
        # Act
        out = color_text("hi", "lavender")
        # Assert
        # Assert
        assert "hi" in out


class TestReadableBytes:
    @pytest.mark.parametrize(
        "size,expected_unit",
        [
            (5, "B"),
            (1500, "KB"),
            (5 * 1024 * 1024, "MB"),
            (3 * 1024**3, "GB"),
            (2 * 1024**4, "TB"),
            (5 * 1024**5, "PB"),
        ],
    )
    def test_units_out_endswith_expected_unit(self, size, expected_unit):
        # Arrange
        # Act
        # Arrange
        # Act
        out = readable_bytes(size)
        # Assert
        # Assert
        assert out.endswith(expected_unit)


class TestDotDictBasics:
    def test_empty_construct_len_d_is_0(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict()
        # Act
        # Assert
        # Assert
        assert len(d) == 0

    def test_empty_construct_bool_d_is_false(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict()
        # Act
        # Assert
        # Assert
        assert bool(d) is False

    def test_from_dict_d_a_equals_n_1(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, "b": "x"})
        # Act
        # Assert
        # Assert
        assert d.a == 1

    def test_from_dict_d_b_equals_x(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, "b": "x"})
        # Act
        # Assert
        # Assert
        assert d.b == "x"

    def test_from_dict_bool_d_is_true(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, "b": "x"})
        # Act
        # Assert
        # Assert
        assert bool(d) is True

    def test_from_dotdict_b_x_equals_n_1(self):
        # Arrange
        # Arrange
        a = DotDict({"x": 1})
        # Act
        # Act
        b = DotDict(a)
        # Assert
        # Assert
        assert b.x == 1

    def test_invalid_input_type(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        with pytest.raises(TypeError):
            DotDict([1, 2, 3])

    def test_nested_dict_wraps_d_top_is_dotdict(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"top": {"inner": 1}})
        # Act
        # Assert
        # Assert
        assert isinstance(d.top, DotDict)

    def test_nested_dict_wraps_d_top_inner_1(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"top": {"inner": 1}})
        # Act
        # Assert
        # Assert
        assert d.top.inner == 1

    def test_attr_access_missing_raises(self):
        # Arrange
        # Act
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Assert
        # Assert
        with pytest.raises(AttributeError):
            _ = d.nonexistent

    def test_attr_set_and_del_d_x_equals_n_5(self):
        # Arrange
        # Arrange
        d = DotDict()
        # Act
        d.x = 5
        # Act
        # Assert
        # Assert
        assert d.x == 5

    def test_attr_del_twice_raises_attributeerror(self):
        # Arrange
        d = DotDict()
        d.x = 5
        del d.x
        # Act
        ctx = pytest.raises(AttributeError)
        # Assert
        with ctx:
            del d.x  # already gone

    def test_item_access_d_a_1(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, 42: "answer"})
        # Act
        # Assert
        # Assert
        assert d["a"] == 1

    def test_item_access_d_42_answer(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, 42: "answer"})
        # Act
        # Assert
        # Assert
        assert d[42] == "answer"

    def test_item_set_string_key_visible_as_attribute(self):
        # Arrange
        d = DotDict({"a": 1, 42: "answer"})
        # Act
        d["new"] = 7
        # Assert
        assert d.new == 7

    def test_item_del_removes_string_key(self):
        # Arrange
        d = DotDict({"a": 1, 42: "answer"})
        # Act
        del d["a"]
        # Assert
        assert "a" not in d

    def test_item_set_wraps_dict_isinstance_d_sub_dotdict(self):
        # Arrange
        # Arrange
        d = DotDict()
        # Act
        d["sub"] = {"k": 1}
        # Act
        # Assert
        # Assert
        assert isinstance(d["sub"], DotDict)

    def test_item_set_wraps_dict_d_sub_k_1(self):
        # Arrange
        # Arrange
        d = DotDict()
        # Act
        d["sub"] = {"k": 1}
        # Act
        # Assert
        # Assert
        assert d["sub"].k == 1


class TestDotDictMappingMethods:
    def test_get_d_get_a_1(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Act
        # Assert
        # Assert
        assert d.get("a") == 1

    def test_get_d_get_missing_default_default(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Act
        # Assert
        # Assert
        assert d.get("missing", "default") == "default"

    def test_keys_values_items_set_d_keys_a_b(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, "b": 2})
        # Act
        # Assert
        # Assert
        assert set(d.keys()) == {"a", "b"}

    def test_keys_values_items_set_d_values_1_2(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, "b": 2})
        # Act
        # Assert
        # Assert
        assert set(d.values()) == {1, 2}

    def test_keys_values_items_set_d_items_a_1_b_2(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, "b": 2})
        # Act
        # Assert
        # Assert
        assert set(d.items()) == {("a", 1), ("b", 2)}

    def test_update_with_dict_d_a_equals_n_99(self):
        # Arrange
        # Arrange
        d = DotDict({"a": 1})
        # Act
        d.update({"b": 2, "a": 99})
        # Act
        # Assert
        # Assert
        assert d.a == 99

    def test_update_with_dict_d_b_equals_n_2(self):
        # Arrange
        # Arrange
        d = DotDict({"a": 1})
        # Act
        d.update({"b": 2, "a": 99})
        # Act
        # Assert
        # Assert
        assert d.b == 2

    def test_update_with_iterable(self):
        # Arrange
        # Arrange
        d = DotDict()
        # Act
        # Act
        d.update([("a", 1), ("b", 2)])
        # Assert
        # Assert
        assert d.a == 1 and d.b == 2

    def test_update_bad_input(self):
        # Arrange
        # Act
        # Arrange
        # Act
        d = DotDict()
        # Assert
        # Assert
        with pytest.raises(TypeError):
            d.update(123)

    def test_setdefault_d_setdefault_a_99_1(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Act
        # Assert
        # Assert
        assert d.setdefault("a", 99) == 1

    def test_setdefault_d_a_equals_n_1(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Act
        # Assert
        # Assert
        assert d.a == 1

    def test_setdefault_d_setdefault_b_7_7(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Act
        # Assert
        # Assert
        assert d.setdefault("b", 7) == 7

    def test_setdefault_d_b_equals_n_7(self):
        # Arrange
        d = DotDict({"a": 1})
        # Act
        d.setdefault("b", 7)
        # Assert
        assert d.b == 7

    def test_pop_d_pop_a_1(self):
        # Arrange
        d = DotDict({"a": 1})
        # Act
        d.pop("a")
        # Assert
        assert d.pop("a", "missing") == "missing"

    def test_pop_a_not_in_d(self):
        # Arrange
        d = DotDict({"a": 1})
        # Act
        d.pop("a")
        # Assert
        assert "a" not in d

    def test_pop_d_pop_missing_default_default(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Act
        # Assert
        # Assert
        assert d.pop("missing", "default") == "default"

    def test_pop_raises_keyerror(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Act
        # Assert
        # Assert
        with pytest.raises(KeyError):
            d.pop("missing")

    def test_pop_raises_typeerror(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Act
        # Assert
        # Assert
        with pytest.raises(TypeError):
            d.pop("a", "b", "c")

    def test_contains_iter_a_in_d(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, "b": 2})
        # Act
        # Assert
        # Assert
        assert "a" in d

    def test_contains_iter_list_iter_d_a_b(self):
        # Arrange
        # Arrange
        # Act
        d = DotDict({"a": 1, "b": 2})
        # Act
        # Assert
        # Assert
        assert list(iter(d)) == ["a", "b"]


class TestDotDictReprAndEq:
    def test_eq_with_dotdict_dotdict_a_1_dotdict_a_1(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert DotDict({"a": 1}) == DotDict({"a": 1})

    def test_eq_with_dotdict_dotdict_a_1_dotdict_a_2(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert DotDict({"a": 1}) != DotDict({"a": 2})

    def test_eq_with_plain_dict_dotdict_a_1_a_1(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert DotDict({"a": 1}) == {"a": 1}

    def test_eq_with_plain_dict_dotdict_a_1_a_2(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert DotDict({"a": 1}) != {"a": 2}

    def test_eq_other_type_returns_false(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert (DotDict({"a": 1}) == 42) is False

    def test_to_dict_recursive_plain_equals_a_1_b_c_2(self):
        # Arrange
        # Arrange
        d = DotDict({"a": 1, "b": {"c": 2}})
        # Act
        plain = d.to_dict()
        # Act
        # Assert
        # Assert
        assert plain == {"a": 1, "b": {"c": 2}}

    def test_to_dict_recursive_not_isinstance_plain_b_dotdict(self):
        # Arrange
        # Arrange
        d = DotDict({"a": 1, "b": {"c": 2}})
        # Act
        plain = d.to_dict()
        # Act
        # Assert
        # Assert
        assert not isinstance(plain["b"], DotDict)

    def test_to_dict_skips_private_keys_secret_not_in_plain(self):
        # Arrange
        # Arrange
        d = DotDict({"_secret": 1, "open": 2})
        # Act
        plain = d.to_dict()
        # Act
        # Assert
        # Assert
        assert "_secret" not in plain

    def test_to_dict_skips_private_keys_plain_open_2(self):
        # Arrange
        # Arrange
        d = DotDict({"_secret": 1, "open": 2})
        # Act
        plain = d.to_dict()
        # Act
        # Assert
        # Assert
        assert plain["open"] == 2

    def test_to_dict_include_private_true_keeps_private_key(self):
        # Arrange
        d = DotDict({"_secret": 1, "open": 2})
        # Act
        plain_all = d.to_dict(include_private=True)
        # Assert
        assert "_secret" in plain_all

    def test_str_is_json(self):
        # Arrange
        # Arrange
        d = DotDict({"a": 1})
        # Act
        # Act
        s = str(d)
        # Assert
        # Assert
        assert '"a": 1' in s

    def test_str_handles_unserialisable(self):
        # Custom non-JSON-serialisable object falls through default_handler
        # Arrange
        # Arrange
        class Weird:
            def __repr__(self):
                return "<weird>"

        d = DotDict({"x": Weird()})
        # Act
        # Act
        s = str(d)
        # Assert
        # Assert
        assert "weird" in s.lower()

    def test_repr_pprint_a_1_in_repr_d(self):
        # Arrange
        # Act
        # Arrange
        # Act
        d = DotDict({"a": 1})
        # Assert
        # Assert
        assert "'a': 1" in repr(d)

    def test_copy_c_equals_d(self):
        # Arrange
        # Arrange
        d = DotDict({"a": 1})
        # Act
        c = d.copy()
        # Act
        # Assert
        # Assert
        assert c == d

    def test_copy_isolates_mutations_from_original(self):
        # Arrange
        d = DotDict({"a": 1})
        c = d.copy()
        # Act
        c["a"] = 99
        # Assert
        assert d.a == 1


class TestPathHelpers:
    def test_preserve_doc_returns_func_g_1(self):
        # Arrange
        # Arrange
        def f():
            "doc"
            return 1

        # Act
        g = preserve_doc(f)
        # Act
        # Assert
        # Assert
        assert g() == 1

    def test_preserve_doc_returns_func_g_doc_equals_doc(self):
        # Arrange
        # Arrange
        def f():
            "doc"
            return 1

        # Act
        g = preserve_doc(f)
        # Act
        # Assert
        # Assert
        assert g.__doc__ == "doc"

    def test_split_a_in_parts_and_b_in_parts_and_c_in_parts(self):
        # Arrange
        # Act
        # Arrange
        # Act
        parts = split("/a/b/c")
        # Assert
        # Assert
        assert "a" in parts and "b" in parts and "c" in parts

    def test_this_path_test_utils_py_in_p(self):
        # Arrange
        # Act
        # Arrange
        # Act
        p = this_path()
        # The function returns the *caller's* file (this test file).
        # Assert
        # Assert
        assert "test__utils.py" in p

    def test_clean_path_c_tmp_path_resolve(self, tmp_path):
        # Arrange
        # Arrange
        p = tmp_path / "sub" / ".."
        # Act
        # Act
        c = clean(str(p))
        # Resolved → tmp_path absolute
        # Assert
        # Assert
        assert Path(c) == tmp_path.resolve()

    def test_getsize_existing_getsize_str_p_len_hello_world(self, tmp_path):
        # Arrange
        # Arrange
        p = tmp_path / "f.txt"
        # Act
        # Act
        p.write_bytes(b"hello world")
        # Assert
        # Assert
        assert getsize(str(p)) == len("hello world")

    def test_getsize_missing_getsize_str_tmp_path_nope_txt_0(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert getsize(str(tmp_path / "nope.txt")) == 0


class TestParse:
    def test_no_pattern_returns_string(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert parse("hello") == "hello"

    def test_matching_path_result_equals_id_1_session_pre(self):
        # Arrange
        # Act
        # Arrange
        # Act
        result = parse(
            "sub_001/ses_pre/data.vhdr",
            "sub_{id}/ses_{session}/data.vhdr",
        )
        # Assert
        # Assert
        assert result == {"id": 1, "session": "pre"}

    def test_non_matching_returns_empty_dict(self):
        # Arrange
        # Act
        # Arrange
        # Act
        result = parse("nope", "sub_{id}/data.vhdr")
        # Assert
        # Assert
        assert result == {}

    def test_wildcard_result_equals_id_42(self):
        # Arrange
        # Act
        # Arrange
        # Act
        result = parse("/foo/bar/sub_42/extra.txt", "*/sub_{id}/extra.txt")
        # Assert
        # Assert
        assert result == {"id": 42}

    def test_non_numeric_id_stays_string(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert parse("sub_abc/x.txt", "sub_{id}/x.txt") == {"id": "abc"}

    def test_negative_int_parse_sub_7_x_txt_sub_id_x_txt_id_7(self):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        assert parse("sub_-7/x.txt", "sub_{id}/x.txt") == {"id": -7}


class TestEnvironmentDetect:
    @pytest.mark.skipif(
        os.environ.get("PYTEST_XDIST_WORKER") is not None,
        reason=(
            "pytest-xdist runs each test in an execnet worker whose __main__ "
            "has no __file__, so detect_environment() truthfully returns "
            "'interactive' there. The 'script' guarantee only holds when "
            "__main__ is a real entrypoint (non-distributed run); the SIF CI "
            "uses `-n WORKERS`, the GitHub-hosted matrix does not."
        ),
    )
    def test_python_env_detect_environment_returns_script(self):
        # In a plain pytest run, no IPython kernel + __main__ has a
        # __file__ (the pytest entry-point) → detect_environment now
        # returns "script" (operator directive 2026-06-13: closed
        # vocabulary jupyter/ipython/script/interactive; old "python"
        # return value retired with the silent <cwd>/output bug it
        # enabled).
        # Arrange
        # Act
        result = detect_environment()
        # Assert
        assert result == "script", (
            f"detect_environment() must return 'script' under pytest "
            f"(closed vocab post 2026-06-13); got {result!r}"
        )

    def test_notebook_path_explicit_env_var_name_equals_demo_ipynb(
        self, tmp_path, env_save_restore
    ):
        # Arrange
        nb = tmp_path / "demo.ipynb"
        nb.write_text("{}")
        env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
        # Act
        name, _dir = get_notebook_info_simple()
        # Assert
        assert name == "demo.ipynb"

    def test_notebook_path_explicit_env_var_dir_equals_str_tmp_path(
        self, tmp_path, env_save_restore
    ):
        # Arrange
        nb = tmp_path / "demo.ipynb"
        nb.write_text("{}")
        env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
        # Act
        _name, dir_ = get_notebook_info_simple()
        # Assert
        assert dir_ == str(tmp_path)

    def test_notebook_path_argv_fallback_name_equals_via_argv_ipynb(
        self, tmp_path, env_save_restore, argv_restore
    ):
        # Arrange
        nb = tmp_path / "via_argv.ipynb"
        nb.write_text("{}")
        env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
        sys.argv[:] = ["jupyter", str(nb)]
        # Act
        name, _dir = get_notebook_info_simple()
        # Assert
        assert name == "via_argv.ipynb"

    def test_notebook_path_argv_fallback_dir_equals_str_tmp_path(
        self, tmp_path, env_save_restore, argv_restore
    ):
        # Arrange
        nb = tmp_path / "via_argv.ipynb"
        nb.write_text("{}")
        env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
        sys.argv[:] = ["jupyter", str(nb)]
        # Act
        _name, dir_ = get_notebook_info_simple()
        # Assert
        assert dir_ == str(tmp_path)

    def test_notebook_path_none_when_no_signal(self, env_save_restore, argv_restore):
        # Arrange
        env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
        sys.argv[:] = ["pytest"]
        # Act
        result = get_notebook_info_simple()
        # Assert
        assert result == (None, None)

    def test_notebook_path_env_var_missing_file(
        self, tmp_path, env_save_restore, argv_restore
    ):
        # Arrange — env var points at a non-existent path → fall through
        env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(tmp_path / "missing.ipynb"))
        sys.argv[:] = ["pytest"]
        # Act
        result = get_notebook_info_simple()
        # Assert
        assert result == (None, None)


# ====================================================================== #
# detect_environment — operator-dogfood 2026-06-13 vocabulary contract    #
# ====================================================================== #
# Previously detect_environment returned only 'jupyter' or 'python'.
# Per operator's directive the vocabulary is now the closed set
# (jupyter, ipython, script, interactive). Pin the script + interactive
# return values via real subprocess (no mocks).


import subprocess as _subproc_dt
import sys as _sys_dt


class TestDetectEnvironmentReturnsClosedVocabulary:
    """The closed vocabulary contract is end-to-end verifiable."""

    def test_returns_script_when_run_as_a_dot_py_subprocess(self, tmp_path):
        # Arrange
        script = tmp_path / "tmp_detect.py"
        script.write_text(
            "from scitex_io._utils import detect_environment\n"
            "print(detect_environment())\n"
        )
        # Act
        result = _subproc_dt.run(
            [_sys_dt.executable, str(script)],
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )
        # Assert
        emitted = (result.returncode, result.stdout.strip())
        assert emitted == (0, "script"), (
            f"detect_environment() in a .py subprocess must return 'script'; "
            f"got {emitted}; stderr={result.stderr!r}"
        )

    def test_returns_interactive_when_run_via_python_c_one_liner(self):
        # Arrange — bare `python -c "..."` has no __main__.__file__.
        # Act
        result = _subproc_dt.run(
            [
                _sys_dt.executable,
                "-c",
                "from scitex_io._utils import detect_environment; "
                "print(detect_environment())",
            ],
            capture_output=True,
            text=True,
        )
        # Assert
        emitted = (result.returncode, result.stdout.strip())
        assert emitted == (0, "interactive"), (
            f"detect_environment() under `python -c` must return 'interactive'; "
            f"got {emitted}; stderr={result.stderr!r}"
        )


# ====================================================================== #
# detect_environment — in-process branch coverage for the IPython paths   #
# ====================================================================== #
# ``detect_environment`` calls a *bare* ``get_ipython()`` and treats a
# ``NameError`` as "no IPython". Under a real IPython/Jupyter kernel,
# ``get_ipython`` is injected into builtins so the bare call resolves.
#
# To exercise the jupyter / ipython branches in-process (the subprocess
# tests above run in a child whose coverage isn't measured, and a plain
# pytest run hits neither IPython branch), we inject a hand-rolled
# ``get_ipython`` *function* into the ``_utils`` module namespace — a real
# callable returning a real shell-like object whose ``type(...).__name__``
# drives the branch. ``attr_restore`` snapshots + removes it after the
# test, so no global IPython state leaks. No mock library is used: the
# injected object is an ordinary class instance.


class _FakeShell:
    """Stand-in IPython shell: only ``type(self).__name__`` is read."""


# NOTE: ``detect_environment`` keys on ``type(shell).__name__ ==
# "ZMQInteractiveShell"`` — an EXACT string match. The fake classes must
# therefore be named EXACTLY as the real IPython shell classes (no
# leading underscore), so ``type(instance).__name__`` produces the
# string the branch compares against.
class ZMQInteractiveShell(_FakeShell):  # noqa: N801 — must match real name
    """Jupyter-kernel shell class name that maps to ``'jupyter'``."""


class TerminalInteractiveShell(_FakeShell):  # noqa: N801 — real IPython name
    """Any non-ZMQ IPython shell → the ``'ipython'`` branch."""


def _install_fake_get_ipython(attr_restore, shell_obj):
    """Inject a real ``get_ipython`` returning ``shell_obj`` into _utils."""
    import scitex_io._utils as _utils_mod

    attr_restore.set(_utils_mod, "get_ipython", lambda: shell_obj)


class TestDetectEnvironmentIPythonBranchesInProcess:
    """In-process coverage of the ``get_ipython()``-present branches."""

    def test_zmq_shell_detected_as_jupyter(self, attr_restore):
        # Arrange — a ZMQInteractiveShell-classed object means a kernel.
        _install_fake_get_ipython(attr_restore, ZMQInteractiveShell())
        # Act
        result = detect_environment()
        # Assert
        assert result == "jupyter"

    def test_terminal_shell_detected_as_ipython(self, attr_restore):
        # Arrange — any other IPython shell class → 'ipython'.
        _install_fake_get_ipython(attr_restore, TerminalInteractiveShell())
        # Act
        result = detect_environment()
        # Assert
        assert result == "ipython"

    def test_no_ipython_and_no_main_file_returns_interactive(self, attr_restore):
        # Arrange — force the no-IPython path: a get_ipython that raises
        # NameError exactly like the absent builtin, plus a __main__ with
        # no __file__ so the final 'interactive' return is reached.
        import sys

        import scitex_io._utils as _utils_mod

        def _raise_nameerror():
            raise NameError("name 'get_ipython' is not defined")

        attr_restore.set(_utils_mod, "get_ipython", _raise_nameerror)

        # Swap __main__ for a bare module object with no __file__ so the
        # `hasattr(_main, "__file__")` test is False (pytest's __main__
        # normally HAS a __file__). attr_restore restores it after.
        import types

        bare_main = types.ModuleType("__main__")  # no __file__ attribute
        saved_main = sys.modules.get("__main__")
        sys.modules["__main__"] = bare_main
        try:
            # Act
            result = detect_environment()
        finally:
            sys.modules["__main__"] = saved_main
        # Assert
        assert result == "interactive"
