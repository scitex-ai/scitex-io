"""Every public ``save_*`` helper fires the post-save hook with the realpath.

Regression for paper-scitex-clew E1 (2026-11-17): ``stx.io.save_text(text,
"/work/project/REPORT.md")`` under ``@stx.session`` wrote the file but no
post-save observer heard about it, because the public convenience helpers
resolved to the raw per-format handlers (``save()`` was the only writer
that fired the hook). Real files, a real registered hook; no mocks.
"""

from __future__ import annotations

import importlib.util
import os

import pytest

import scitex_io
from scitex_io import _observers, _save_modules


@pytest.fixture
def recorded():
    """Register a real post-save hook; unregister it afterwards."""
    events = []

    def hook(path, obj, kwargs):
        events.append((str(path), kwargs))

    scitex_io.register_post_save_hook(hook)
    try:
        yield events
    finally:
        _observers._post_save_hooks.remove(hook)


@pytest.fixture
def in_dir(tmp_path):
    """chdir into ``tmp_path`` (restored afterwards) for relative paths."""
    before = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(before)


def _has(module):
    return importlib.util.find_spec(module) is not None


def _df():
    import pandas as pd

    return pd.DataFrame({"a": [1, 2], "b": [3.0, 4.0]})


def _arr():
    import numpy as np

    return np.arange(6).reshape(2, 3)


def _fig():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    return fig


# public name -> (needed module or None, object factory, file name)
CASES = {
    "save_text": (None, lambda: "report\n", "REPORT.md"),
    "save_json": (None, lambda: {"a": 1}, "out.json"),
    "save_yaml": ("yaml", lambda: {"a": 1}, "out.yaml"),
    "save_csv": ("pandas", _df, "out.csv"),
    "save_npy": ("numpy", _arr, "out.npy"),
    "save_npz": ("numpy", lambda: {"x": _arr()}, "out.npz"),
    "save_pickle": (None, lambda: {"a": 1}, "out.pkl"),
    "save_pickle_compressed": (None, lambda: {"a": 1}, "out.pkl.gz"),
    "save_joblib": ("joblib", lambda: {"a": 1}, "out.joblib"),
    "save_html": (None, lambda: "<p>hi</p>", "out.html"),
    "save_tex": (None, lambda: r"\alpha", "out.tex"),
    "save_bibtex": (
        "bibtexparser",
        lambda: {"entry_type": "article", "key": "k1", "fields": {"title": "T"}},
        "out.bib",
    ),
    "save_excel": ("openpyxl", _df, "out.xlsx"),
    "save_image": ("matplotlib", _fig, "fig.png"),
    "save_hdf5": ("h5py", lambda: {"x": _arr()}, "out.h5"),
    "save_matlab": ("scipy", lambda: {"x": _arr()}, "out.mat"),
    "save_torch": ("torch", lambda: {"a": 1}, "out.pt"),
    "save_zarr": ("zarr", lambda: {"x": _arr()}, "out.zarr"),
    "save_listed_dfs_as_csv": ("pandas", lambda: [_df(), _df()], "listed.csv"),
    "save_listed_scalars_as_csv": ("pandas", lambda: [1.0, 2.0], "scalars.csv"),
}

# Public helpers not exercised by CASES, with the reason.
ROUTED_THROUGH_SAVE = {"save_optuna_study_as_csv_and_pngs"}
NOT_IN_CASES = ROUTED_THROUGH_SAVE | {
    # Needs a trained CatBoost model / an ffmpeg-rendered 3D animation;
    # both go through the same tracked_save_helper wrapper asserted below.
    "save_catboost",
    "save_mp4",
}


def test_every_public_helper_is_accounted_for():
    # Arrange
    public = set(_save_modules._LAZY_NAMES)
    # Act
    covered = set(CASES) | NOT_IN_CASES
    # Assert
    assert public == covered


def _wrapped_params():
    out = []
    for name, (module, _attr) in sorted(_save_modules._LAZY_NAMES.items()):
        if name in ROUTED_THROUGH_SAVE:
            continue
        missing = importlib.util.find_spec(module) is None
        out.append(
            pytest.param(
                name,
                marks=pytest.mark.skipif(missing, reason=f"{module} missing"),
            )
        )
    return out


def _case_params():
    out = []
    for name in sorted(CASES):
        needed = CASES[name][0]
        missing = needed is not None and not _has(needed)
        out.append(
            pytest.param(
                name,
                marks=pytest.mark.skipif(missing, reason=f"{needed} not installed"),
            )
        )
    return out


@pytest.mark.parametrize("name", _wrapped_params())
def test_public_helper_is_wrapped_by_tracker(name):
    # Arrange
    helper = getattr(_save_modules, name)
    # Act
    tracked = getattr(helper, "__scitex_io_tracked__", False)
    # Assert
    assert tracked


@pytest.mark.parametrize("absolute", [True, False], ids=["absolute", "relative"])
@pytest.mark.parametrize("name", _case_params())
def test_helper_fires_post_save_with_realpath(name, absolute, recorded, in_dir):
    # Arrange
    _needed, make, fname = CASES[name]
    helper = getattr(_save_modules, name)
    target = str(in_dir / fname) if absolute else "./" + fname
    expected = os.path.realpath(in_dir / fname)
    # Act
    helper(make(), target)
    primaries = [p for p, kw in recorded if kw["provenance"]["role"] == "primary"]
    # Assert
    assert primaries == [expected]


@pytest.mark.parametrize("absolute", [True, False], ids=["absolute", "relative"])
def test_top_level_save_text_fires_once_with_realpath(absolute, recorded, in_dir):
    # Arrange
    target = str(in_dir / "REPORT.md") if absolute else "./REPORT.md"
    # Act
    scitex_io.save_text("report\n", target)
    observed = [(p, kw["provenance"]["role"], kw["track"]) for p, kw in recorded]
    # Assert
    assert observed == [(os.path.realpath(in_dir / "REPORT.md"), "primary", True)]


def test_save_text_through_symlinked_dir_reports_realpath(recorded, tmp_path):
    # Arrange
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    # Act
    scitex_io.save_text("x\n", str(link / "notes.txt"))
    # Assert
    assert [p for p, _ in recorded] == [str((real / "notes.txt").resolve())]


def test_helper_forwards_track_and_derived_from(recorded, tmp_path):
    # Arrange
    source = tmp_path / "in.txt"
    source.write_text("in\n")
    # Act
    scitex_io.save_text(
        "out\n", str(tmp_path / "out.txt"), track=False, derived_from=[str(source)]
    )
    ((_path, kwargs),) = recorded
    # Assert
    assert (kwargs["track"], kwargs["derived_from"]) == (
        False,
        [os.path.realpath(source)],
    )


def _save_with_missing_derived_from(target, missing):
    try:
        scitex_io.save_text("x\n", str(target), derived_from=[str(missing)])
    except Exception as exc:  # noqa: BLE001 — the type is asserted below
        return exc
    return None


def test_helper_bad_derived_from_raises(recorded, tmp_path):
    # Arrange
    target = tmp_path / "never.txt"
    # Act
    error = _save_with_missing_derived_from(target, tmp_path / "missing.csv")
    # Assert
    assert error is not None


def test_helper_bad_derived_from_writes_and_reports_nothing(recorded, tmp_path):
    # Arrange
    target = tmp_path / "never.txt"
    # Act
    _save_with_missing_derived_from(target, tmp_path / "missing.csv")
    # Assert
    assert (target.exists(), recorded) == (False, [])


def test_save_still_fires_once_per_file(recorded, tmp_path):
    # Arrange
    target = tmp_path / "REPORT.md"
    # Act
    scitex_io.save("report\n", str(target), verbose=False)
    # Assert
    assert [p for p, _ in recorded] == [os.path.realpath(target)]


def test_helper_registered_as_custom_saver_is_not_double_reported(recorded, tmp_path):
    # Arrange
    scitex_io.register_saver(".stxdouble", scitex_io.save_text)
    target = tmp_path / "x.stxdouble"
    try:
        # Act
        scitex_io.save("hi\n", str(target), verbose=False)
    finally:
        scitex_io.unregister_saver(".stxdouble")
    # Assert
    assert [p for p, _ in recorded] == [os.path.realpath(target)]
