"""Unit tests for ``scitex_io.save`` path-resolution and feature flags.

Routing matrix (covered):

| env_type      | input shape          | output sdir                          |
|---------------|----------------------|--------------------------------------|
| jupyter (env) | filename / relative  | <notebook_dir>/<stem>_out/<path>     |
| jupyter (—)   | filename / relative  | <cwd>/notebook_out/<path>  + warn    |
| any           | absolute (`/...`)    | path used as-is                      |

Save flags (covered): ``symlink_from_cwd``, ``symlink_to``, ``dry_run``,
``makedirs``, ``verbose``.

Real-collaborator style: the production ``save()`` accepts an
``env_detector`` kwarg (defaults to the real ``detect_environment``);
tests pass a no-arg lambda returning the desired environment string,
instead of patching ``scitex_io._utils.detect_environment``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

import scitex_io as sio
import scitex_io._builtin_handlers  # noqa: F401 — register builtin .npy etc.
from scitex_io._utils import get_notebook_info_simple


def _env(env_type: str):
    """Return a no-arg callable suitable as ``env_detector=`` kwarg."""
    return lambda: env_type


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def cwd_tmp(chdir_tmp):
    """Alias for the conftest ``chdir_tmp`` (cwd → tmp_path, restored)."""
    return chdir_tmp


@pytest.fixture
def reset_warn_latch(attr_restore):
    """Reset the module-level ``_NOTEBOOK_PATH_WARNED`` latch for the test.

    The latch is a real module attribute on ``scitex_io._save``; use
    ``attr_restore`` so the snapshot/restore is structural (not a
    monkeypatch fixture parameter).
    """
    import scitex_io._save as _save_mod

    attr_restore.set(_save_mod, "_NOTEBOOK_PATH_WARNED", False)


# ===========================================================================
# get_notebook_info_simple — return-shape contract
# ===========================================================================


def test_notebook_info_returns_2_tuple_shape_info_is_tuple(env_save_restore):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    # Act
    info = get_notebook_info_simple()
    # Assert
    assert isinstance(info, tuple)


def test_notebook_info_returns_2_tuple_shape_len_info_is_2(env_save_restore):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    # Act
    info = get_notebook_info_simple()
    # Assert
    assert len(info) == 2


def test_notebook_info_none_when_no_signal(env_save_restore, argv_restore):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    sys.argv[:] = ["pytest", "test_x.py"]
    # Act
    info = get_notebook_info_simple()
    # Assert
    assert info == (None, None)


def test_notebook_info_env_var_override_name_equals_demo_ipynb(
    tmp_path, env_save_restore
):
    # Arrange
    nb = tmp_path / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    name, _dirpath = get_notebook_info_simple()
    # Assert
    assert name == "demo.ipynb"


def test_notebook_info_env_var_override_path_dirpath_resolve_tmp_path_resolve(
    tmp_path, env_save_restore
):
    # Arrange
    nb = tmp_path / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    _name, dirpath = get_notebook_info_simple()
    # Assert
    assert Path(dirpath).resolve() == tmp_path.resolve()


def test_notebook_info_env_var_falls_through_when_path_missing(
    tmp_path, env_save_restore, argv_restore
):
    # Arrange
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(tmp_path / "nope.ipynb"))
    sys.argv[:] = ["pytest"]
    # Act
    info = get_notebook_info_simple()
    # Assert
    assert info == (None, None)


def test_notebook_info_finds_ipynb_in_argv(
    tmp_path, env_save_restore, argv_restore
):
    # Arrange
    nb = tmp_path / "fromargv.ipynb"
    nb.write_text("{}")
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    sys.argv[:] = ["nbconvert", str(nb)]
    # Act
    name, _ = get_notebook_info_simple()
    # Assert
    assert name == "fromargv.ipynb"


# ===========================================================================
# Save routing — absolute path bypasses ALL routing branches
# ===========================================================================


def test_abs_path_used_as_is_in_jupyter_target_is_file(cwd_tmp, env_save_restore):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    env_save_restore.set("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    target = cwd_tmp / "abs_jupyter.npy"
    # Act
    sio.save(np.array([1, 2, 3]), str(target), env_detector=_env("jupyter"))
    # Assert
    assert target.is_file()


def test_abs_path_used_as_is_in_jupyter_no_notebook_out_dir_created(
    cwd_tmp, env_save_restore
):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    env_save_restore.set("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    target = cwd_tmp / "abs_jupyter.npy"
    # Act
    sio.save(np.array([1, 2, 3]), str(target), env_detector=_env("jupyter"))
    # Assert
    assert not (cwd_tmp / "notebook_out").exists()


def test_abs_path_with_subdirs_creates_them(cwd_tmp):
    # Arrange
    target = cwd_tmp / "deep" / "nested" / "data.npy"
    # Act
    sio.save(np.array([1.0]), str(target), env_detector=_env("script"))
    # Assert
    assert target.is_file()


def test_abs_path_makedirs_false_raises_on_missing_parent(cwd_tmp):
    # makedirs=False with a missing parent now raises (fail-loud-fail-
    # early policy, 2026-06-01). Previously this branch returned a
    # `False` sentinel which let callers think the save had succeeded.
    import pytest
    # Arrange
    target = cwd_tmp / "missing-parent" / "data.npy"
    # Act
    ctx = pytest.raises(Exception)
    # Assert
    with ctx:
        sio.save(
            np.array([1.0]),
            str(target),
            makedirs=False,
            env_detector=_env("script"),
        )


def test_abs_path_makedirs_false_does_not_create_target(cwd_tmp):
    # Even though save() now raises on failure (fail-loud policy,
    # 2026-06-01), the no-half-written-file invariant must still hold:
    # the target path must not appear on disk after the raise. This
    # test owns that invariant; the sibling test owns the raise.
    import contextlib
    # Arrange
    target = cwd_tmp / "missing-parent" / "data.npy"
    with contextlib.suppress(Exception):
        sio.save(
            np.array([1.0]),
            str(target),
            makedirs=False,
            env_detector=_env("script"),
        )
    # Act
    target_exists = target.exists()
    # Assert
    assert not target_exists


# ===========================================================================
# Save routing — Jupyter with notebook detection (env-var override)
# ===========================================================================


def test_jupyter_filename_only_with_env_routes_under_stem_out(
    cwd_tmp, env_save_restore
):
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    sio.save(np.array([1, 2]), "result.npy", env_detector=_env("jupyter"))
    # Assert
    assert (cwd_tmp / "demo_out" / "result.npy").is_file()


def test_jupyter_relative_subdir_with_env_preserves_subdirs(
    cwd_tmp, env_save_restore
):
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    sio.save(
        np.array([1, 2]), "_assets/figs/01.npy", env_detector=_env("jupyter")
    )
    # Assert
    assert (cwd_tmp / "demo_out" / "_assets" / "figs" / "01.npy").is_file()


def test_jupyter_notebook_in_subdir_writes_to_notebook_dir(
    tmp_path, env_save_restore
):
    # Arrange
    nb_dir = tmp_path / "examples"
    nb_dir.mkdir()
    nb = nb_dir / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    # cwd ≠ notebook_dir
    import os

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Act
        sio.save(np.array([1.0]), "out.npy", env_detector=_env("jupyter"))
        target_exists = (nb_dir / "demo_out" / "out.npy").is_file()
    finally:
        os.chdir(old_cwd)
    # Assert
    assert target_exists


def test_jupyter_notebook_in_subdir_does_not_route_under_cwd(
    tmp_path, env_save_restore
):
    # Arrange
    nb_dir = tmp_path / "examples"
    nb_dir.mkdir()
    nb = nb_dir / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    import os

    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Act
        sio.save(np.array([1.0]), "out.npy", env_detector=_env("jupyter"))
        cwd_routed = (tmp_path / "demo_out" / "out.npy").exists()
    finally:
        os.chdir(old_cwd)
    # Assert
    assert not cwd_routed


# ===========================================================================
# Save routing — Jupyter without detection (fallback + warning)
# ===========================================================================


def test_jupyter_fallback_to_notebook_out_writes_file(
    cwd_tmp, env_save_restore, reset_warn_latch, argv_restore
):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    env_save_restore.delete("SCITEX_IO_QUIET_NOTEBOOK_WARN")
    sys.argv[:] = ["pytest"]
    # Act
    sio.save(np.array([1.0]), "fallback.npy", env_detector=_env("jupyter"))
    # Assert
    assert (cwd_tmp / "notebook_out" / "fallback.npy").is_file()


def test_jupyter_fallback_emits_auto_detected_warning(
    cwd_tmp, env_save_restore, reset_warn_latch, argv_restore, capsys
):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    env_save_restore.delete("SCITEX_IO_QUIET_NOTEBOOK_WARN")
    sys.argv[:] = ["pytest"]
    sio.save(np.array([1.0]), "fallback.npy", env_detector=_env("jupyter"))
    # Act
    err = capsys.readouterr().err
    # Assert
    assert "notebook path could not be auto-detected" in err


def test_jupyter_fallback_warning_mentions_scitex_notebook_path(
    cwd_tmp, env_save_restore, reset_warn_latch, argv_restore, capsys
):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    env_save_restore.delete("SCITEX_IO_QUIET_NOTEBOOK_WARN")
    sys.argv[:] = ["pytest"]
    sio.save(np.array([1.0]), "fallback.npy", env_detector=_env("jupyter"))
    # Act
    err = capsys.readouterr().err
    # Assert
    assert "SCITEX_NOTEBOOK_PATH" in err


def test_jupyter_warning_fires_only_once(
    cwd_tmp, env_save_restore, reset_warn_latch, argv_restore, capsys
):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    env_save_restore.delete("SCITEX_IO_QUIET_NOTEBOOK_WARN")
    sys.argv[:] = ["pytest"]
    sio.save(np.array([1.0]), "a.npy", env_detector=_env("jupyter"))
    sio.save(np.array([2.0]), "b.npy", env_detector=_env("jupyter"))
    sio.save(np.array([3.0]), "c.npy", env_detector=_env("jupyter"))
    # Act
    err = capsys.readouterr().err
    # Assert
    assert err.count("notebook path could not be auto-detected") == 1


def test_jupyter_warning_silenced_by_env_var(
    cwd_tmp, env_save_restore, reset_warn_latch, argv_restore, capsys
):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    env_save_restore.set("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    sys.argv[:] = ["pytest"]
    sio.save(np.array([1.0]), "quiet.npy", env_detector=_env("jupyter"))
    # Act
    err = capsys.readouterr().err
    # Assert
    assert "notebook path" not in err


def test_jupyter_warning_silenced_still_writes_file(
    cwd_tmp, env_save_restore, reset_warn_latch, argv_restore
):
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    env_save_restore.set("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    sys.argv[:] = ["pytest"]
    # Act
    sio.save(np.array([1.0]), "quiet.npy", env_detector=_env("jupyter"))
    # Assert
    assert (cwd_tmp / "notebook_out" / "quiet.npy").is_file()


# ===========================================================================
# Symlink behaviours
# ===========================================================================


def test_symlink_from_cwd_creates_routed_file(cwd_tmp, env_save_restore):
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    sio.save(
        np.array([7.0]),
        "real.npy",
        symlink_from_cwd=True,
        env_detector=_env("jupyter"),
    )
    # Act
    routed = cwd_tmp / "demo_out" / "real.npy"
    # Assert
    assert routed.is_file()


def test_symlink_from_cwd_creates_symlink_at_cwd(cwd_tmp, env_save_restore):
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    sio.save(
        np.array([7.0]),
        "real.npy",
        symlink_from_cwd=True,
        env_detector=_env("jupyter"),
    )
    # Act
    cwd_link = cwd_tmp / "real.npy"
    # Assert
    assert cwd_link.exists() or cwd_link.is_symlink()


def test_symlink_to_creates_routed_file(cwd_tmp, env_save_restore):
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    custom_link = cwd_tmp / "links" / "x_link.npy"
    sio.save(
        np.array([1.0, 2.0]),
        "x.npy",
        symlink_to=str(custom_link),
        env_detector=_env("jupyter"),
    )
    # Act
    routed = cwd_tmp / "demo_out" / "x.npy"
    # Assert
    assert routed.is_file()


def test_symlink_to_creates_symlink_at_custom_path(cwd_tmp, env_save_restore):
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    custom_link = cwd_tmp / "links" / "x_link.npy"
    sio.save(
        np.array([1.0, 2.0]),
        "x.npy",
        symlink_to=str(custom_link),
        env_detector=_env("jupyter"),
    )
    # Act
    link_present = custom_link.exists() or custom_link.is_symlink()
    # Assert
    assert link_present


def test_load_after_symlink_round_trip(cwd_tmp, env_save_restore):
    """The whole point of symlink_from_cwd: round-trip by filename."""
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    sio.save(
        np.array([42.0]),
        "rt.npy",
        symlink_from_cwd=True,
        env_detector=_env("jupyter"),
    )
    # Act
    arr = sio.load("rt.npy")
    # Assert
    assert arr.tolist() == [42.0]


# ===========================================================================
# dry_run flag
# ===========================================================================


def test_dry_run_does_not_write_file(cwd_tmp):
    # Arrange
    target = cwd_tmp / "dry.npy"
    # Act
    sio.save(
        np.array([1.0]), str(target), dry_run=True, env_detector=_env("script")
    )
    # Assert
    assert not target.exists()


def test_dry_run_returns_without_error(cwd_tmp):
    # Arrange
    target = cwd_tmp / "dry2.npy"
    completed = False
    # Act
    sio.save(
        np.array([1.0]),
        str(target),
        dry_run=True,
        makedirs=False,
        env_detector=_env("script"),
    )
    completed = True
    # Assert
    assert completed


# ===========================================================================
# Defensive — never resurrect the legacy `name/path_out/` shape
# ===========================================================================


def test_never_creates_legacy_name_path_out(
    cwd_tmp, env_save_restore, reset_warn_latch, argv_restore
):
    """Regression: dict-keys-as-tuple bug routed every save to
    ``<cwd>/name/path_out/``."""
    # Arrange
    env_save_restore.delete("SCITEX_NOTEBOOK_PATH")
    env_save_restore.set("SCITEX_IO_QUIET_NOTEBOOK_WARN", "1")
    sys.argv[:] = ["pytest"]
    # Act
    sio.save(np.array([1.0]), "x.npy", env_detector=_env("jupyter"))
    # Assert
    assert not (cwd_tmp / "name").exists()


# ===========================================================================
# Regression — ``track=`` must NOT leak to format handlers (pkl/yaml take
# no extra kwargs). Unblocks stx.session teardown (CONFIG.pkl/yaml saves).
# ===========================================================================


def test_save_pickle_with_track_false_does_not_raise(cwd_tmp):
    # Arrange
    target = cwd_tmp / "cfg_track.pkl"
    # Act
    sio.save({"a": 1}, str(target), track=False, env_detector=_env("script"))
    # Assert
    assert target.is_file()


def test_save_yaml_with_track_false_does_not_raise(cwd_tmp):
    # Arrange
    target = cwd_tmp / "cfg_track.yaml"
    # Act
    sio.save({"a": 1}, str(target), track=False, env_detector=_env("script"))
    # Assert
    assert target.is_file()


def test_save_pickle_with_track_true_default_still_works(cwd_tmp):
    # Arrange
    target = cwd_tmp / "cfg_default.pkl"
    # Act
    sio.save({"a": 1}, str(target), track=True, env_detector=_env("script"))
    # Assert
    assert target.is_file()


def test_save_pickle_without_track_arg_still_works(cwd_tmp):
    # Arrange
    target = cwd_tmp / "cfg_no_track.pkl"
    # Act
    sio.save({"a": 1}, str(target), env_detector=_env("script"))
    # Assert
    assert target.is_file()


# ===========================================================================
# scitex-io#55 — repeat ``save(symlink_from_cwd=True)`` must not self-loop
# ===========================================================================
#
# Two consecutive ``save(obj, "./x.csv", symlink_from_cwd=True)`` calls
# from the same cwd used to leave a ``./x.csv -> x.csv`` (or
# repro_out-local) self-loop symlink, because:
#
# 1. ``spath_cwd = clean(spath_cwd)`` did ``Path.resolve()``, which on
#    call 2 followed call 1's symlink and silently rebound the cwd
#    anchor onto the target file inside repro_out.
# 2. ``_symlink`` was then passed the un-normalised ``spath`` containing
#    ``./``, and ``ln -sfr`` collapsed the relative target to the
#    symlink's own basename in its own dir.
#
# The fix uses ``normpath`` for ``spath_cwd`` (anchor stays at the
# literal cwd location) and passes ``spath_final`` (cleaned) into
# ``_symlink`` with a defensive self-loop guard. These tests pin the
# end-to-end behaviour.


def test_double_save_does_not_self_loop_cwd_anchor(cwd_tmp):
    """After two saves, the cwd anchor symlink target is NOT its own basename."""
    # Arrange
    import os
    import pandas as pd

    df = pd.DataFrame({"a": [1]})
    sio.save(df, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    sio.save(df, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    # Act
    link_target = os.readlink(cwd_tmp / "x.csv")
    # Assert
    assert link_target != "x.csv"


def test_double_save_does_not_self_loop_routed_target(cwd_tmp):
    """After two saves, the routed file is NOT itself a symlink to itself."""
    # Arrange
    import pandas as pd

    df = pd.DataFrame({"a": [1]})
    sio.save(df, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    sio.save(df, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    # Act
    # Resolve the cwd anchor — must succeed (no Errno 40).
    resolved = Path(cwd_tmp / "x.csv").resolve()
    # Assert
    assert resolved.is_file()


def test_double_save_then_third_save_does_not_raise(cwd_tmp):
    """Third save() must not blow up on a stale self-loop from prior runs."""
    # Arrange
    import pandas as pd

    df = pd.DataFrame({"a": [1]})
    sio.save(df, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    sio.save(df, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    completed = False
    # Act
    sio.save(df, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    completed = True
    # Assert
    assert completed


def test_double_save_content_round_trip_matches(cwd_tmp):
    """After two saves with symlink_from_cwd, loading by filename returns latest data."""
    # Arrange
    import pandas as pd

    df_first = pd.DataFrame({"a": [1]})
    df_second = pd.DataFrame({"a": [2]})
    sio.save(df_first, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    sio.save(df_second, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    # Act
    loaded = sio.load(str(cwd_tmp / "x.csv"))
    # Assert
    assert loaded["a"].tolist() == [2]


def test_stale_self_loop_symlink_at_cwd_anchor_is_cleaned(cwd_tmp):
    """A pre-existing self-loop symlink at the cwd anchor is removed by save()."""
    # Arrange
    import os
    import pandas as pd

    bad_link = cwd_tmp / "x.csv"
    # Plant a self-looping symlink that would otherwise trip Path.resolve()
    # with OSError [Errno 40] inside clean() on the next save().
    os.symlink("x.csv", str(bad_link))
    df = pd.DataFrame({"a": [1]})
    # Act
    sio.save(df, "./x.csv", symlink_from_cwd=True, env_detector=_env("script"))
    link_target = os.readlink(bad_link)
    # Assert
    assert link_target != "x.csv"
