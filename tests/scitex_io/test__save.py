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


def test_notebook_info_finds_ipynb_in_argv(tmp_path, env_save_restore, argv_restore):
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


def test_jupyter_relative_subdir_with_env_preserves_subdirs(cwd_tmp, env_save_restore):
    # Arrange
    nb = cwd_tmp / "demo.ipynb"
    nb.write_text("{}")
    env_save_restore.set("SCITEX_NOTEBOOK_PATH", str(nb))
    # Act
    sio.save(np.array([1, 2]), "_assets/figs/01.npy", env_detector=_env("jupyter"))
    # Assert
    assert (cwd_tmp / "demo_out" / "_assets" / "figs" / "01.npy").is_file()


def test_jupyter_notebook_in_subdir_writes_to_notebook_dir(tmp_path, env_save_restore):
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
    sio.save(np.array([1.0]), str(target), dry_run=True, env_detector=_env("script"))
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
# Interactive / IPython routing — in-process ($SCITEX_DIR cache branch)
# ===========================================================================
#
# A bare-REPL / IPython-terminal save (env_type 'interactive' or
# 'ipython') has no script path to anchor `_out/` to, so it routes into
# `$SCITEX_DIR/io/runtime/cache/`. The end-to-end suite below pins this
# via a real `python -c` subprocess — but a subprocess child's coverage
# is not captured by the parent run, so the routing branch shows as
# uncovered. These IN-PROCESS tests exercise the same branch directly
# (real save, real tmp $SCITEX_DIR, no mocks) so the cache-routing lines
# are measured.


@pytest.mark.parametrize("env_type", ["interactive", "ipython"])
def test_interactive_save_routes_into_scitex_dir_cache(
    cwd_tmp, env_save_restore, env_type
):
    # Arrange — point SCITEX_DIR at a tmp dir so we can locate the result.
    scitex_dir = cwd_tmp / "fake_scitex_dir"
    env_save_restore.set("SCITEX_DIR", str(scitex_dir))
    # Act
    sio.save(
        np.array([1.0, 2.0]),
        "interactive_result.npy",
        env_detector=_env(env_type),
    )
    # Assert — file lands under $SCITEX_DIR/io/runtime/cache/.
    expected = scitex_dir / "io" / "runtime" / "cache" / "interactive_result.npy"
    assert expected.is_file()


def test_interactive_save_round_trips_by_cache_path(cwd_tmp, env_save_restore):
    # Arrange
    scitex_dir = cwd_tmp / "fake_scitex_dir"
    env_save_restore.set("SCITEX_DIR", str(scitex_dir))
    sio.save(
        np.array([7.0]),
        "rt_interactive.npy",
        env_detector=_env("interactive"),
    )
    cache_path = scitex_dir / "io" / "runtime" / "cache" / "rt_interactive.npy"
    # Act
    loaded = sio.load(str(cache_path))
    # Assert
    assert loaded.tolist() == [7.0]


def test_interactive_save_defaults_scitex_dir_to_home_when_unset(
    cwd_tmp, env_save_restore
):
    # Arrange — with SCITEX_DIR unset the branch falls back to
    # ~/.scitex; redirect HOME so the write stays inside the sandbox and
    # we don't touch the real home dir.
    env_save_restore.delete("SCITEX_DIR")
    fake_home = cwd_tmp / "fake_home"
    fake_home.mkdir()
    env_save_restore.set("HOME", str(fake_home))
    # Act
    sio.save(
        np.array([3.0]),
        "home_default.npy",
        env_detector=_env("interactive"),
    )
    # Assert — landed under <HOME>/.scitex/io/runtime/cache/.
    expected = fake_home / ".scitex" / "io" / "runtime" / "cache" / "home_default.npy"
    assert expected.is_file()


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


# ===========================================================================
# neurovista 2026-06-27 — symlink helpers must NEVER self-point
# ===========================================================================
#
# Self-referential symlinks (target == link itself) corrupt figure
# outputs: the real artefact is replaced by an ``x -> x`` loop and any
# reader doing ``Path.resolve()`` crashes with "Symlink loop". ``_symlink``
# already guarded this; ``_symlink_to`` did NOT, so ``save(..., symlink_to
# == saved_path)`` destroyed the file. These unit tests pin the guard on
# both helpers via a robust abspath identity check (``_is_self_link``).


def test_is_self_link_same_path_is_true(tmp_path):
    """_is_self_link is True when target and link are the same abs path."""
    # Arrange
    from scitex_io._path_modules._symlink import _is_self_link

    same = str(tmp_path / "sub" / "fig.png")
    # Act
    result = _is_self_link(same, same)
    # Assert
    assert result is True


def test_is_self_link_different_paths_is_false(tmp_path):
    """_is_self_link is False for two distinct paths."""
    # Arrange
    from scitex_io._path_modules._symlink import _is_self_link

    a, b = str(tmp_path / "a.png"), str(tmp_path / "b.png")
    # Act
    result = _is_self_link(a, b)
    # Assert
    assert result is False


def test_symlink_to_refuses_self_pointing_link(tmp_path):
    """_symlink_to(saved, saved) keeps the real file instead of self-looping.

    A self-loop would replace ``f`` with ``f -> fig.png``; reading it then
    raises ELOOP. Asserting the original content survives pins the fix.
    """
    # Arrange
    from scitex_io._path_modules._symlink import _symlink_to

    f = tmp_path / "sub" / "fig.png"
    f.parent.mkdir(parents=True)
    f.write_text("REALDATA")
    # Act
    _symlink_to(str(f), str(f), verbose=False)
    # Assert
    assert f.read_text() == "REALDATA"


def test_symlink_refuses_self_pointing_link(tmp_path):
    """_symlink with target == cwd-anchor keeps the real file."""
    # Arrange
    from scitex_io._path_modules._symlink import _symlink

    f = tmp_path / "sub" / "fig.png"
    f.parent.mkdir(parents=True)
    f.write_text("REALDATA")
    # Act
    _symlink(str(f), str(f), symlink_from_cwd=True, verbose=False, spath_final=str(f))
    # Assert
    assert f.read_text() == "REALDATA"


def test_symlink_to_cross_dir_still_links(tmp_path):
    """The guard must not break legitimate cross-directory symlink_to links."""
    # Arrange
    from scitex_io._path_modules._symlink import _symlink_to

    real = tmp_path / "out" / "fig.png"
    real.parent.mkdir(parents=True)
    real.write_text("R")
    link = tmp_path / "cwd" / "fig.png"
    link.parent.mkdir(parents=True)
    # Act
    _symlink_to(str(real), str(link), verbose=False)
    # Assert
    assert link.resolve() == real.resolve()


# ====================================================================== #
# Operator-dogfood 2026-06-13 path-routing regression suite               #
# ====================================================================== #
# scitex.io.save inside @stx.session saved to ./output/ instead of
# scripts/dataset/tmp_out/. Root causes: (a) detect_environment returned
# only 'jupyter'/'python', leaving the `elif env_type == "script":`
# branch dead → silent <cwd>/output fallback; (b) the script-branch's
# stack-walk used scitex_io's parent dir to detect "scitex frames" via
# filesystem prefix → missed scitex_dev wrapper frames in split installs,
# writing into `scitex_dev/_core/decorators_out/`. Fix lands in this same
# commit; these tests pin the contract end-to-end with real subprocess +
# tmp_path (no mocks, per operator).

import os as _os_module
import subprocess as _subproc
import sys as _sys_module
import textwrap as _textwrap
from pathlib import Path as _Path


def _run_subprocess_script(
    tmp_path,
    script_body: str,
    env: dict | None = None,
) -> _subproc.CompletedProcess:
    """Write ``script_body`` to ``tmp_path/tmp_save_routing.py`` and run it.

    Returns the CompletedProcess so callers inspect stdout / stderr /
    returncode. Subprocess cwd is ``tmp_path`` so any accidental
    ``cwd/output/`` regression is sandboxed.
    """
    script = tmp_path / "tmp_save_routing.py"
    script.write_text(_textwrap.dedent(script_body))
    proc_env = dict(_os_module.environ)
    if env:
        proc_env.update(env)
    return _subproc.run(
        [_sys_module.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=proc_env,
    )


class TestSaveRoutesScriptEnvToScriptOutDirectoryEndToEnd:
    """A real .py subprocess calling ``stx.io.save`` lands in ``<script>_out/``."""

    def test_save_in_script_context_writes_under_script_out_directory(self, tmp_path):
        # Arrange
        script_body = """
            import scitex_io
            scitex_io.save("hello", "./test_save_output.txt")
        """
        # Act
        result = _run_subprocess_script(tmp_path, script_body)
        # Assert — canonical layout is <script_stem>_out/<relpath>.
        expected = tmp_path / "tmp_save_routing_out" / "test_save_output.txt"
        emitted = (result.returncode, expected.is_file())
        assert emitted == (0, True), (
            f"script-context save must land in <script>_out/; "
            f"got returncode={result.returncode}, file-exists={expected.is_file()}; "
            f"expected={expected}; "
            f"stdout={result.stdout!r}; stderr={result.stderr!r}"
        )

    def test_save_must_not_land_in_legacy_cwd_output_directory(self, tmp_path):
        # Arrange — pin that the silent <cwd>/output/ fallback is GONE.
        script_body = """
            import scitex_io
            scitex_io.save("hello", "./test_save_output.txt")
        """
        # Act
        _run_subprocess_script(tmp_path, script_body)
        # Assert — legacy ./output/ MUST NOT exist.
        legacy = tmp_path / "output"
        assert not legacy.exists(), (
            f"script-context save must NOT regress to legacy ./output/; "
            f"found {legacy}/ with contents: "
            f"{list(legacy.iterdir()) if legacy.exists() else '-'}"
        )


class TestSaveRoutesInteractiveEnvToScitexDirCacheEndToEnd:
    """A bare-REPL save lands in ``$SCITEX_DIR/io/runtime/cache/``."""

    def test_python_c_save_writes_to_scitex_dir_cache(self, tmp_path):
        # Arrange — fake SCITEX_DIR so we can locate the result.
        scitex_dir = tmp_path / "fake_scitex_dir"
        env = {"SCITEX_DIR": str(scitex_dir)}
        oneliner = "import scitex_io; scitex_io.save('hello', 'interactive_save.txt')"
        # Act
        result = _subproc.run(
            [_sys_module.executable, "-c", oneliner],
            capture_output=True,
            text=True,
            env={**_os_module.environ, **env},
            cwd=str(tmp_path),
        )
        # Assert — file MUST be inside $SCITEX_DIR/io/runtime/cache/.
        expected = scitex_dir / "io" / "runtime" / "cache" / "interactive_save.txt"
        emitted = (result.returncode, expected.is_file())
        assert emitted == (0, True), (
            f"interactive-context save must land in $SCITEX_DIR/io/runtime/cache/; "
            f"got returncode={result.returncode}, file-exists={expected.is_file()}; "
            f"expected={expected}; "
            f"stdout={result.stdout!r}; stderr={result.stderr!r}"
        )


class TestSaveFailsLoudOnUnknownEnvTypeEndToEnd:
    """An ``env_detector`` returning anything outside the vocabulary raises."""

    def test_unknown_env_type_raises_valueerror_with_diagnostic(self, tmp_path):
        # Arrange — pass an env_detector that returns garbage.
        script_body = """
            import sys
            import scitex_io
            try:
                scitex_io.save(
                    "hello",
                    "./should_not_create.txt",
                    env_detector=lambda: "totally_bogus_env",
                )
            except ValueError as e:
                print("RAISED:", str(e)[:120])
                sys.exit(0)
            else:
                print("DID NOT RAISE")
                sys.exit(2)
        """
        # Act
        result = _run_subprocess_script(tmp_path, script_body)
        # Assert — ValueError raised + documented vocabulary mentioned.
        emitted = (
            result.returncode,
            "RAISED:" in result.stdout,
            "totally_bogus_env" in result.stdout,
            "jupyter" in result.stdout,
        )
        assert emitted == (0, True, True, True), (
            f"unknown env_type must raise ValueError with documented vocabulary; "
            f"got {emitted}; stdout={result.stdout!r}; stderr={result.stderr!r}"
        )

    def test_unknown_env_type_does_not_create_silent_cwd_output_fallback(
        self, tmp_path
    ):
        # Arrange — same as above; verify NO file lands anywhere.
        script_body = """
            import scitex_io
            try:
                scitex_io.save(
                    "hello",
                    "./should_not_create.txt",
                    env_detector=lambda: "totally_bogus_env",
                )
            except ValueError:
                pass
        """
        # Act
        _run_subprocess_script(tmp_path, script_body)
        # Assert — no legacy cwd/output/, no script_out, no plain file.
        bad_paths = [
            tmp_path / "output" / "should_not_create.txt",
            tmp_path / "tmp_save_routing_out" / "should_not_create.txt",
            tmp_path / "should_not_create.txt",
        ]
        existing = [p for p in bad_paths if p.exists()]
        assert existing == [], (
            f"fail-loud raise must NOT silently write anywhere; "
            f"found writes at: {existing}"
        )
