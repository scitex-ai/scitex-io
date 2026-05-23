"""Unit tests for ``scitex_io.save`` path-resolution and feature flags.

from __future__ import annotations
Routing matrix (covered):

| env_type      | input shape          | output sdir                          |
|---------------|----------------------|--------------------------------------|
| jupyter (env) | filename / relative  | <notebook_dir>/<stem>_out/<path>     |
| jupyter (—)   | filename / relative  | <cwd>/notebook_out/<path>  + warn    |
| any           | absolute (`/...`)    | path used as-is                      |

Save flags (covered): ``symlink_from_cwd``, ``symlink_to``, ``dry_run``,
``makedirs``, ``verbose``.

Patching: ``detect_environment`` is imported lazily inside ``save``
from ``scitex_io._utils`` — patch that fully-qualified name.
"""


import sys
from pathlib import Path
from unittest import mock

import numpy as np
import pytest

import scitex_io as sio
import scitex_io._builtin_handlers  # noqa: F401 — register builtin .npy etc.
from scitex_io._utils import get_notebook_info_simple

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cwd_tmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield tmp_path


@pytest.fixture
def reset_warn_latch(monkeypatch):
    import scitex_io._save as _save_mod

    monkeypatch.setattr(_save_mod, "_NOTEBOOK_PATH_WARNED", False)


def _patch_env(env_type: str):
    return mock.patch("scitex_io._utils.detect_environment", return_value=env_type)


# ===========================================================================
# get_notebook_info_simple — return-shape contract
# ===========================================================================


def test_notebook_info_returns_2_tuple_shape_info_is_tuple(monkeypatch):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    # Act
    info = get_notebook_info_simple()
    # Act
    # Assert
    # Assert
    assert isinstance(info, tuple)


def test_notebook_info_returns_2_tuple_shape_len_info_is_2(monkeypatch):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    # Act
    info = get_notebook_info_simple()
    # Act
    # Assert
    # Assert
    assert len(info) == 2




def test_notebook_info_none_when_no_signal(monkeypatch):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    # Act
    # Act
    monkeypatch.setattr(sys, "argv", ["pytest", "test_x.py"])
    # Assert
    # Assert
    assert get_notebook_info_simple() == (None, None)


def test_notebook_info_env_var_override_name_equals_demo_ipynb(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    nb = tmp_path / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    name, dirpath = get_notebook_info_simple()
    # Act
    # Assert
    # Assert
    assert name == "demo.ipynb"


def test_notebook_info_env_var_override_path_dirpath_resolve_tmp_path_resolve(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    nb = tmp_path / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    name, dirpath = get_notebook_info_simple()
    # Act
    # Assert
    # Assert
    assert Path(dirpath).resolve() == tmp_path.resolve()




def test_notebook_info_env_var_falls_through_when_path_missing(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(tmp_path / "nope.ipynb"))
    # Act
    # Act
    monkeypatch.setattr(sys, "argv", ["pytest"])
    # Assert
    # Assert
    assert get_notebook_info_simple() == (None, None)


def test_notebook_info_finds_ipynb_in_argv(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    nb = tmp_path / "fromargv.ipynb"
    nb.write_text("{}")
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.setattr(sys, "argv", ["nbconvert", str(nb)])
    # Act
    # Act
    name, _ = get_notebook_info_simple()
    # Assert
    # Assert
    assert name == "fromargv.ipynb"


# ===========================================================================
# Save routing — absolute path bypasses ALL routing branches
# ===========================================================================


def test_abs_path_used_as_is_in_jupyter_target_is_file(cwd_tmp, monkeypatch):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.setenv("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    target = cwd_tmp / "abs_jupyter.npy"
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1, 2, 3]), str(target))
    # Act
    # Assert
    # Assert
    assert target.is_file()


def test_abs_path_used_as_is_in_jupyter_not_cwd_tmp_notebook_out_exists(cwd_tmp, monkeypatch):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.setenv("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    target = cwd_tmp / "abs_jupyter.npy"
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1, 2, 3]), str(target))
    # Act
    # Assert
    # Assert
    assert not (cwd_tmp / "notebook_out").exists()




def test_abs_path_with_subdirs_creates_them(cwd_tmp):
    # Arrange
    # Arrange
    target = cwd_tmp / "deep" / "nested" / "data.npy"
    # Act
    # Act
    with _patch_env("script"):
        sio.save(np.array([1.0]), str(target))
    # Assert
    # Assert
    assert target.is_file()


def test_abs_path_makedirs_false_returns_false_on_missing_parent_result_is_false(cwd_tmp):
    # Arrange
    # Arrange
    target = cwd_tmp / "missing-parent" / "data.npy"
    # Act
    with _patch_env("script"):
        result = sio.save(np.array([1.0]), str(target), makedirs=False)
    # Act
    # Assert
    # Assert
    assert result is False


def test_abs_path_makedirs_false_returns_false_on_missing_parent_not_target_exists(cwd_tmp):
    # Arrange
    # Arrange
    target = cwd_tmp / "missing-parent" / "data.npy"
    # Act
    with _patch_env("script"):
        result = sio.save(np.array([1.0]), str(target), makedirs=False)
    # Act
    # Assert
    # Assert
    assert not target.exists()




# ===========================================================================
# Save routing — Jupyter with notebook detection (env-var override)
# ===========================================================================


def test_jupyter_filename_only_with_env_routes_under_stem_out(cwd_tmp, monkeypatch):
    """Filename-only input: <cwd>/<stem>_out/<filename>."""
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1, 2]), "result.npy")
    # Assert
    assert (cwd_tmp / "demo_out" / "result.npy").is_file()


def test_jupyter_relative_subdir_with_env_preserves_subdirs(cwd_tmp, monkeypatch):
    # Arrange
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1, 2]), "_assets/figs/01.npy")
    # Assert
    # Assert
    assert (cwd_tmp / "demo_out" / "_assets" / "figs" / "01.npy").is_file()


def test_jupyter_notebook_in_subdir_uses_notebook_dir_not_cwd_nb_dir_demo_out_out_npy_is_file(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    nb_dir = tmp_path / "examples"
    nb_dir.mkdir()
    nb = nb_dir / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.chdir(tmp_path)  # cwd ≠ notebook_dir
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1.0]), "out.npy")
    # Act
    # Assert
    # Assert
    assert (nb_dir / "demo_out" / "out.npy").is_file()


def test_jupyter_notebook_in_subdir_uses_notebook_dir_not_cwd_not_tmp_path_demo_out_out_npy_exists(tmp_path, monkeypatch):
    # Arrange
    # Arrange
    nb_dir = tmp_path / "examples"
    nb_dir.mkdir()
    nb = nb_dir / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.chdir(tmp_path)  # cwd ≠ notebook_dir
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1.0]), "out.npy")
    # Act
    # Assert
    # Assert
    assert not (tmp_path / "demo_out" / "out.npy").exists()




# ===========================================================================
# Save routing — Jupyter without detection (fallback + warning)
# ===========================================================================


def test_jupyter_fallback_to_notebook_out_with_warning_cwd_tmp_notebook_out_fallback_npy_is_file(
    cwd_tmp, monkeypatch, reset_warn_latch, capsys
):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.delenv("SCITEX_IO_QUIET_NOTEBOOK_WARN", raising=False)
    monkeypatch.setattr(sys, "argv", ["pytest"])
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1.0]), "fallback.npy")
    # Act
    # Assert
    # Assert
    assert (cwd_tmp / "notebook_out" / "fallback.npy").is_file()


def test_jupyter_fallback_to_notebook_out_with_warning_notebook_path_could_not_be_auto_detected_in_err(
    cwd_tmp, monkeypatch, reset_warn_latch, capsys
):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.delenv("SCITEX_IO_QUIET_NOTEBOOK_WARN", raising=False)
    monkeypatch.setattr(sys, "argv", ["pytest"])
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1.0]), "fallback.npy")
    # Assert
    assert (cwd_tmp / "notebook_out" / "fallback.npy").is_file()
    err = capsys.readouterr().err
    # Act
    # Assert
    assert "notebook path could not be auto-detected" in err


def test_jupyter_fallback_to_notebook_out_with_warning_scitex_notebook_path_in_err(
    cwd_tmp, monkeypatch, reset_warn_latch, capsys
):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.delenv("SCITEX_IO_QUIET_NOTEBOOK_WARN", raising=False)
    monkeypatch.setattr(sys, "argv", ["pytest"])
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1.0]), "fallback.npy")
    # Assert
    assert (cwd_tmp / "notebook_out" / "fallback.npy").is_file()
    err = capsys.readouterr().err
    # Act
    # Assert
    assert "SCITEX_NOTEBOOK_PATH" in err




def test_jupyter_warning_fires_only_once(
    cwd_tmp, monkeypatch, reset_warn_latch, capsys
):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.delenv("SCITEX_IO_QUIET_NOTEBOOK_WARN", raising=False)
    monkeypatch.setattr(sys, "argv", ["pytest"])
    with _patch_env("jupyter"):
        sio.save(np.array([1.0]), "a.npy")
        sio.save(np.array([2.0]), "b.npy")
        sio.save(np.array([3.0]), "c.npy")
    # Act
    # Act
    err = capsys.readouterr().err
    # Assert
    # Assert
    assert err.count("notebook path could not be auto-detected") == 1


def test_jupyter_warning_silenced_by_env_var_notebook_path_not_in_err(
    cwd_tmp, monkeypatch, reset_warn_latch, capsys
):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.setenv("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    monkeypatch.setattr(sys, "argv", ["pytest"])
    with _patch_env("jupyter"):
        sio.save(np.array([1.0]), "quiet.npy")
    # Act
    err = capsys.readouterr().err
    # Act
    # Assert
    # Assert
    assert "notebook path" not in err


def test_jupyter_warning_silenced_by_env_var_cwd_tmp_notebook_out_quiet_npy_is_file(
    cwd_tmp, monkeypatch, reset_warn_latch, capsys
):
    # Arrange
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.setenv("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    monkeypatch.setattr(sys, "argv", ["pytest"])
    with _patch_env("jupyter"):
        sio.save(np.array([1.0]), "quiet.npy")
    # Act
    err = capsys.readouterr().err
    # Act
    # Assert
    # Assert
    assert (cwd_tmp / "notebook_out" / "quiet.npy").is_file()




# ===========================================================================
# Symlink behaviours
# ===========================================================================


def test_symlink_from_cwd_creates_link_at_cwd_routed_is_file(cwd_tmp, monkeypatch):
    # Arrange
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    with _patch_env("jupyter"):
        sio.save(np.array([7.0]), "real.npy", symlink_from_cwd=True)
    # Act
    routed = cwd_tmp / "demo_out" / "real.npy"
    # Act
    # Assert
    # Assert
    assert routed.is_file()


def test_symlink_from_cwd_creates_link_at_cwd_cwd_link_exists_or_cwd_link_is_symlink(cwd_tmp, monkeypatch):
    # Arrange
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    with _patch_env("jupyter"):
        sio.save(np.array([7.0]), "real.npy", symlink_from_cwd=True)
    # Act
    routed = cwd_tmp / "demo_out" / "real.npy"
    # Assert
    assert routed.is_file()
    cwd_link = cwd_tmp / "real.npy"
    # Act
    # Assert
    assert cwd_link.exists() or cwd_link.is_symlink()




def test_symlink_to_creates_link_at_custom_path_routed_is_file(cwd_tmp, monkeypatch):
    # Arrange
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    custom_link = cwd_tmp / "links" / "x_link.npy"
    with _patch_env("jupyter"):
        sio.save(
            np.array([1.0, 2.0]),
            "x.npy",
            symlink_to=str(custom_link),
        )
    # Act
    routed = cwd_tmp / "demo_out" / "x.npy"
    # Act
    # Assert
    # Assert
    assert routed.is_file()


def test_symlink_to_creates_link_at_custom_path_custom_link_exists_or_custom_link_is_symlink(cwd_tmp, monkeypatch):
    # Arrange
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    custom_link = cwd_tmp / "links" / "x_link.npy"
    with _patch_env("jupyter"):
        sio.save(
            np.array([1.0, 2.0]),
            "x.npy",
            symlink_to=str(custom_link),
        )
    # Act
    routed = cwd_tmp / "demo_out" / "x.npy"
    # Act
    # Assert
    # Assert
    assert custom_link.exists() or custom_link.is_symlink()




def test_load_after_symlink_round_trip(cwd_tmp, monkeypatch):
    """The whole point of symlink_from_cwd: round-trip by filename."""
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    monkeypatch.setenv("SCITEX_NOTEBOOK_PATH", str(nb))
    with _patch_env("jupyter"):
        sio.save(np.array([42.0]), "rt.npy", symlink_from_cwd=True)
    # Act
    arr = sio.load("rt.npy")
    # Assert
    assert arr.tolist() == [42.0]


# ===========================================================================
# dry_run flag
# ===========================================================================


def test_dry_run_does_not_write_file(cwd_tmp):
    # Arrange
    # Arrange
    target = cwd_tmp / "dry.npy"
    # Act
    # Act
    with _patch_env("script"):
        sio.save(np.array([1.0]), str(target), dry_run=True)
    # Assert
    # Assert
    assert not target.exists()


def test_dry_run_returns_without_error(cwd_tmp):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    target = cwd_tmp / "dry2.npy"
    with _patch_env("script"):
        # Should not raise even if the dir doesn't exist with makedirs=False.
        sio.save(np.array([1.0]), str(target), dry_run=True, makedirs=False)


# ===========================================================================
# Defensive — never resurrect the legacy `name/path_out/` shape
# ===========================================================================


def test_never_creates_legacy_name_path_out(cwd_tmp, monkeypatch, reset_warn_latch):
    """Regression: dict-keys-as-tuple bug routed every save to
    ``<cwd>/name/path_out/``."""
    # Arrange
    monkeypatch.delenv("SCITEX_NOTEBOOK_PATH", raising=False)
    monkeypatch.setenv("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    monkeypatch.setattr(sys, "argv", ["pytest"])
    # Act
    with _patch_env("jupyter"):
        sio.save(np.array([1.0]), "x.npy")
    # Assert
    assert not (cwd_tmp / "name").exists()
