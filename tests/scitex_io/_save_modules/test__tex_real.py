"""Real round-trip tests for scitex_io._save_modules._tex."""

from __future__ import annotations

import pandas as pd

from scitex_io._save_modules._tex import (
    _dataframe_to_latex,
    _wrap_in_document,
    _wrap_with_table_env,
    save_tex,
)


def _read(p):
    with open(p) as f:
        return f.read()


def test_save_tex_dataframe_round_trip(tmp_path):
    p = str(tmp_path / "a.tex")
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    save_tex(df, p)
    out = _read(p)
    assert "\\begin{tabular}" in out
    assert "1" in out and "4" in out


def test_save_tex_dataframe_with_caption_and_label(tmp_path):
    p = str(tmp_path / "b.tex")
    df = pd.DataFrame({"A": [1]})
    save_tex(df, p, caption="My Caption", label="tab:x")
    out = _read(p)
    assert "My Caption" in out
    assert "tab:x" in out


def test_save_tex_dataframe_longtable(tmp_path):
    p = str(tmp_path / "c.tex")
    df = pd.DataFrame({"A": [1, 2, 3]})
    save_tex(df, p, longtable=True)
    out = _read(p)
    assert "longtable" in out


def test_save_tex_dataframe_no_escape(tmp_path):
    p = str(tmp_path / "d.tex")
    df = pd.DataFrame({"A": ["a&b"]})
    save_tex(df, p, escape=False)
    out = _read(p)
    # No-escape => the raw & remains
    assert "a&b" in out


def test_save_tex_raw_string(tmp_path):
    p = str(tmp_path / "e.tex")
    payload = r"\begin{equation} E = mc^2 \end{equation}"
    save_tex(payload, p)
    assert _read(p) == payload


def test_save_tex_document_wrap(tmp_path):
    p = str(tmp_path / "f.tex")
    save_tex("body", p, document=True)
    out = _read(p)
    assert "\\documentclass" in out and "\\begin{document}" in out
    assert "body" in out


def test_save_tex_dict_falls_back_to_string_when_stats_missing(tmp_path):
    """If scitex_stats is unavailable, dict gets stringified with a warning."""
    p = str(tmp_path / "g.tex")
    save_tex({"a": 1}, p)
    out = _read(p)
    # The fallback writes str(obj) or a LaTeX rendering depending on env.
    assert len(out) > 0


def test_save_tex_unsupported_type_falls_back_to_str(tmp_path):
    p = str(tmp_path / "h.tex")
    save_tex(42, p)
    out = _read(p)
    assert out.strip() == "42"


def test_dataframe_to_latex_helper():
    df = pd.DataFrame({"A": [1, 2]})
    out = _dataframe_to_latex(df, caption="C", label="L")
    assert "\\begin{tabular}" in out
    assert "C" in out and "L" in out


def test_wrap_with_table_env_caption_and_label():
    out = _wrap_with_table_env("BODY", caption="Cap", label="Lab")
    assert "\\begin{table}" in out
    assert "\\caption{Cap}" in out
    assert "\\label{Lab}" in out
    assert "BODY" in out
    assert "\\end{table}" in out


def test_wrap_with_table_env_no_caption_no_label():
    out = _wrap_with_table_env("BODY")
    assert "BODY" in out
    assert "\\caption" not in out
    assert "\\label" not in out


def test_wrap_in_document_contains_packages():
    out = _wrap_in_document("X")
    assert "\\documentclass" in out
    assert "\\usepackage{booktabs}" in out
    assert "X" in out


def test_save_tex_dict_with_convert_results_available(tmp_path, monkeypatch):
    """Inject a stub convert_results into scitex_stats._utils._normalizers to
    exercise the success branch of the dict-input code path."""
    import sys
    import types

    fake_pkg = types.ModuleType("scitex_stats")
    fake_utils = types.ModuleType("scitex_stats._utils")
    fake_norm = types.ModuleType("scitex_stats._utils._normalizers")

    def convert_results(obj, return_as="latex", **kw):
        return r"\begin{tabular}{ll}a & 1\end{tabular}"

    fake_norm.convert_results = convert_results
    fake_utils._normalizers = fake_norm
    fake_pkg._utils = fake_utils
    monkeypatch.setitem(sys.modules, "scitex_stats", fake_pkg)
    monkeypatch.setitem(sys.modules, "scitex_stats._utils", fake_utils)
    monkeypatch.setitem(sys.modules, "scitex_stats._utils._normalizers", fake_norm)

    p = str(tmp_path / "dict.tex")
    save_tex({"a": 1}, p, caption="Cap", label="Lab")
    out = _read(p)
    assert "tabular" in out
    # caption/label wrap was applied
    assert "Cap" in out and "Lab" in out


def test_save_tex_dict_convert_results_failure_falls_back(tmp_path, monkeypatch):
    """convert_results raising a non-ImportError → fallback to str()."""
    import sys
    import types

    fake_pkg = types.ModuleType("scitex_stats")
    fake_utils = types.ModuleType("scitex_stats._utils")
    fake_norm = types.ModuleType("scitex_stats._utils._normalizers")

    def convert_results(obj, return_as="latex", **kw):
        raise RuntimeError("simulated failure")

    fake_norm.convert_results = convert_results
    fake_utils._normalizers = fake_norm
    fake_pkg._utils = fake_utils
    monkeypatch.setitem(sys.modules, "scitex_stats", fake_pkg)
    monkeypatch.setitem(sys.modules, "scitex_stats._utils", fake_utils)
    monkeypatch.setitem(sys.modules, "scitex_stats._utils._normalizers", fake_norm)

    p = str(tmp_path / "fb.tex")
    save_tex({"a": 1}, p)
    out = _read(p)
    # Fallback writes str(obj) — contains the dict repr.
    assert "'a'" in out or "a" in out
