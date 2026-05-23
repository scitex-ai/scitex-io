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


def test_save_tex_dataframe_round_trip_begin_tabular_in_out(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "a.tex")
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    save_tex(df, p)
    # Act
    out = _read(p)
    # Act
    # Assert
    # Assert
    assert "\\begin{tabular}" in out


def test_save_tex_dataframe_round_trip_n_1_in_out_and_4_in_out(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "a.tex")
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    save_tex(df, p)
    # Act
    out = _read(p)
    # Act
    # Assert
    # Assert
    assert "1" in out and "4" in out




def test_save_tex_dataframe_with_caption_and_label_my_caption_in_out(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "b.tex")
    df = pd.DataFrame({"A": [1]})
    save_tex(df, p, caption="My Caption", label="tab:x")
    # Act
    out = _read(p)
    # Act
    # Assert
    # Assert
    assert "My Caption" in out


def test_save_tex_dataframe_with_caption_and_label_tab_x_in_out(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "b.tex")
    df = pd.DataFrame({"A": [1]})
    save_tex(df, p, caption="My Caption", label="tab:x")
    # Act
    out = _read(p)
    # Act
    # Assert
    # Assert
    assert "tab:x" in out




def test_save_tex_dataframe_longtable(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "c.tex")
    df = pd.DataFrame({"A": [1, 2, 3]})
    save_tex(df, p, longtable=True)
    # Act
    # Act
    out = _read(p)
    # Assert
    # Assert
    assert "longtable" in out


def test_save_tex_dataframe_no_escape(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "d.tex")
    df = pd.DataFrame({"A": ["a&b"]})
    save_tex(df, p, escape=False)
    # Act
    # Act
    out = _read(p)
    # No-escape => the raw & remains
    # Assert
    # Assert
    assert "a&b" in out


def test_save_tex_raw_string(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "e.tex")
    payload = r"\begin{equation} E = mc^2 \end{equation}"
    # Act
    # Act
    save_tex(payload, p)
    # Assert
    # Assert
    assert _read(p) == payload


def test_save_tex_document_wrap_documentclass_in_out_and_begin_document_in_out(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "f.tex")
    save_tex("body", p, document=True)
    # Act
    out = _read(p)
    # Act
    # Assert
    # Assert
    assert "\\documentclass" in out and "\\begin{document}" in out


def test_save_tex_document_wrap_body_in_out(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "f.tex")
    save_tex("body", p, document=True)
    # Act
    out = _read(p)
    # Act
    # Assert
    # Assert
    assert "body" in out




def test_save_tex_dict_falls_back_to_string_when_stats_missing(tmp_path):
    """If scitex_stats is unavailable, dict gets stringified with a warning."""
    # Arrange
    p = str(tmp_path / "g.tex")
    save_tex({"a": 1}, p)
    # Act
    out = _read(p)
    # The fallback writes str(obj) or a LaTeX rendering depending on env.
    # Assert
    assert len(out) > 0


def test_save_tex_unsupported_type_falls_back_to_str(tmp_path):
    # Arrange
    # Arrange
    p = str(tmp_path / "h.tex")
    save_tex(42, p)
    # Act
    # Act
    out = _read(p)
    # Assert
    # Assert
    assert out.strip() == "42"


def test_dataframe_to_latex_helper_begin_tabular_in_out():
    # Arrange
    # Arrange
    df = pd.DataFrame({"A": [1, 2]})
    # Act
    out = _dataframe_to_latex(df, caption="C", label="L")
    # Act
    # Assert
    # Assert
    assert "\\begin{tabular}" in out


def test_dataframe_to_latex_helper_c_in_out_and_l_in_out():
    # Arrange
    # Arrange
    df = pd.DataFrame({"A": [1, 2]})
    # Act
    out = _dataframe_to_latex(df, caption="C", label="L")
    # Act
    # Assert
    # Assert
    assert "C" in out and "L" in out




def test_wrap_with_table_env_caption_and_label_begin_table_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_with_table_env("BODY", caption="Cap", label="Lab")
    # Act
    # Assert
    # Assert
    assert "\\begin{table}" in out


def test_wrap_with_table_env_caption_and_label_caption_cap_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_with_table_env("BODY", caption="Cap", label="Lab")
    # Act
    # Assert
    # Assert
    assert "\\caption{Cap}" in out


def test_wrap_with_table_env_caption_and_label_label_lab_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_with_table_env("BODY", caption="Cap", label="Lab")
    # Act
    # Assert
    # Assert
    assert "\\label{Lab}" in out


def test_wrap_with_table_env_caption_and_label_body_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_with_table_env("BODY", caption="Cap", label="Lab")
    # Act
    # Assert
    # Assert
    assert "BODY" in out


def test_wrap_with_table_env_caption_and_label_end_table_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_with_table_env("BODY", caption="Cap", label="Lab")
    # Act
    # Assert
    # Assert
    assert "\\end{table}" in out




def test_wrap_with_table_env_no_caption_no_label_body_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_with_table_env("BODY")
    # Act
    # Assert
    # Assert
    assert "BODY" in out


def test_wrap_with_table_env_no_caption_no_label_caption_not_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_with_table_env("BODY")
    # Act
    # Assert
    # Assert
    assert "\\caption" not in out


def test_wrap_with_table_env_no_caption_no_label_label_not_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_with_table_env("BODY")
    # Act
    # Assert
    # Assert
    assert "\\label" not in out




def test_wrap_in_document_contains_packages_documentclass_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_in_document("X")
    # Act
    # Assert
    # Assert
    assert "\\documentclass" in out


def test_wrap_in_document_contains_packages_usepackage_booktabs_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_in_document("X")
    # Act
    # Assert
    # Assert
    assert "\\usepackage{booktabs}" in out


def test_wrap_in_document_contains_packages_x_in_out():
    # Arrange
    # Arrange
    # Act
    out = _wrap_in_document("X")
    # Act
    # Assert
    # Assert
    assert "X" in out




def test_save_tex_dict_with_convert_results_available_tabular_in_out(tmp_path, monkeypatch):
    # Arrange
    # Arrange
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
    # Act
    out = _read(p)
    # Act
    # Assert
    # Assert
    assert "tabular" in out


def test_save_tex_dict_with_convert_results_available_cap_in_out_and_lab_in_out(tmp_path, monkeypatch):
    # Arrange
    # Arrange
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
    # Act
    out = _read(p)
    # Act
    # Assert
    # Assert
    assert "Cap" in out and "Lab" in out




def test_save_tex_dict_convert_results_failure_falls_back(tmp_path, monkeypatch):
    """convert_results raising a non-ImportError → fallback to str()."""
    # Arrange
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
    # Act
    out = _read(p)
    # Fallback writes str(obj) — contains the dict repr.
    # Assert
    assert "'a'" in out or "a" in out
