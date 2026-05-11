#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io image / mp4 / metadata modules.

Covers:
- src/scitex_io/_image_csv_handler.py
- src/scitex_io/_save_modules/_image.py
- src/scitex_io/_save_modules/_mp4.py
- src/scitex_io/_metadata_modules/embed_metadata_{jpeg,pdf}.py
- src/scitex_io/_metadata_modules/read_metadata_{jpeg,pdf}.py
"""

import json
import os
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from PIL import Image

from scitex_io._image_csv_handler import (
    _export_csv,
    _export_sigmaplot_csv,
    _get_figure_with_data,
    _save_separate_legends,
    handle_image_with_csv,
)
from scitex_io._metadata_modules.embed_metadata_jpeg import embed_metadata_jpeg
from scitex_io._metadata_modules.embed_metadata_pdf import embed_metadata_pdf
from scitex_io._metadata_modules.read_metadata_jpeg import read_metadata_jpeg
from scitex_io._metadata_modules.read_metadata_pdf import read_metadata_pdf
from scitex_io._save_modules._image import (
    _is_pil_image,
    _is_plotly_figure,
    _mpl_savefig_kwargs,
    save_image,
)
from scitex_io._save_modules._mp4 import _mk_mp4

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mpl_fig():
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2, 3], [0, 1, 4, 9], label="quadratic")
    ax.set_title("test")
    yield fig
    plt.close(fig)


@pytest.fixture
def pil_image_rgb():
    img = Image.new("RGB", (32, 24), (255, 0, 0))
    return img


@pytest.fixture
def pil_image_rgba():
    return Image.new("RGBA", (16, 16), (0, 255, 0, 200))


# ---------------------------------------------------------------------------
# save_image: matplotlib figure round-trips for all formats
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "ext", [".png", ".tiff", ".tif", ".jpeg", ".jpg", ".gif", ".svg", ".pdf"]
)
def test_save_image_matplotlib_all_formats(tmp_path, mpl_fig, ext):
    spath = str(tmp_path / f"out{ext}")
    save_image(mpl_fig, spath)
    assert os.path.exists(spath)
    assert os.path.getsize(spath) > 0


@pytest.mark.parametrize("ext", [".png", ".tiff", ".jpeg", ".gif", ".pdf"])
def test_save_image_pil_all_formats(tmp_path, pil_image_rgb, ext):
    spath = str(tmp_path / f"out{ext}")
    save_image(pil_image_rgb, spath)
    assert os.path.exists(spath)
    assert os.path.getsize(spath) > 0
    if ext == ".pdf":
        # PIL writes PDF but PIL.Image.open can't read it back; just verify header
        with open(spath, "rb") as f:
            assert f.read(4) == b"%PDF"
    else:
        img = Image.open(spath)
        img.load()
        assert img.size == (32, 24)


def test_save_image_pdf_pil_rgba_conversion(tmp_path, pil_image_rgba):
    spath = str(tmp_path / "rgba.pdf")
    save_image(pil_image_rgba, spath)
    assert os.path.getsize(spath) > 0


def test_save_image_kwargs_filter():
    # Drop unknown kwargs; keep valid mpl savefig kwargs.
    kept = _mpl_savefig_kwargs(
        {
            "dpi": 100,
            "transparent": True,
            "verbose": True,
            "no_csv": True,
            "track": False,
        }
    )
    assert kept == {"dpi": 100, "transparent": True}


def test_save_image_mpl_kwargs_forwarded(tmp_path, mpl_fig):
    spath = str(tmp_path / "kw.png")
    # `verbose` is not a savefig kwarg — must be filtered, not raise.
    save_image(mpl_fig, spath, dpi=72, verbose=True, no_csv=True)
    assert os.path.exists(spath)


def test_save_image_ax_fallback_to_figure(tmp_path):
    # Pass an Axes; save_image's matplotlib branch calls obj.savefig first
    # which works directly because Axes have .figure; the try-except fallback
    # branch (AttributeError on obj.savefig for SVG/PDF) is also exercised
    # by passing an object without savefig.
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3])
    # An Axes does NOT have savefig — triggers the except path.
    for ext in (".png", ".tiff", ".jpeg", ".gif", ".svg", ".pdf"):
        spath = str(tmp_path / f"ax{ext}")
        save_image(ax, spath)
        assert os.path.exists(spath)
    plt.close(fig)


def test_is_pil_image_true_false(pil_image_rgb):
    assert _is_pil_image(pil_image_rgb) is True
    assert _is_pil_image(object()) is False
    assert _is_pil_image("not an image") is False


def test_is_plotly_figure_false_for_non_plotly(mpl_fig, pil_image_rgb):
    # plotly may or may not be installed; must always return False for non-Figures.
    assert _is_plotly_figure(mpl_fig) is False
    assert _is_plotly_figure(pil_image_rgb) is False
    assert _is_plotly_figure(object()) is False


# ---------------------------------------------------------------------------
# _image_csv_handler: handle_image_with_csv
# ---------------------------------------------------------------------------


class _FakeAxisWithExport:
    """Stand-in for an Axes that exposes export_as_csv (and optionally
    sigmaplot). The handler only checks for these methods via hasattr."""

    def __init__(self, df, sigma_df=None):
        self._df = df
        self._sigma_df = sigma_df

    def export_as_csv(self):
        return self._df

    def export_as_csv_for_sigmaplot(self):
        return self._sigma_df


def test_handle_image_dry_run(tmp_path, mpl_fig):
    spath = str(tmp_path / "dry.png")
    handle_image_with_csv(mpl_fig, spath, dry_run=True)
    assert not os.path.exists(spath)


def test_handle_image_no_csv_just_saves_png(tmp_path, mpl_fig):
    spath = str(tmp_path / "plain.png")
    handle_image_with_csv(mpl_fig, spath, no_csv=True)
    assert os.path.exists(spath)
    assert not os.path.exists(str(tmp_path / "plain.csv"))


def test_handle_image_no_figure_data_skips_csv(tmp_path, mpl_fig):
    """When no axes expose export_as_csv, the .csv sidecar isn't written."""
    spath = str(tmp_path / "no_export.png")
    handle_image_with_csv(mpl_fig, spath)
    assert os.path.exists(spath)
    assert not os.path.exists(str(tmp_path / "no_export.csv"))


def test_handle_image_with_export_writes_csv_sidecar(tmp_path):
    df = pd.DataFrame({"x": [0, 1, 2], "y": [0.0, 1.0, 4.0]})
    fake = _FakeAxisWithExport(df)

    saved = []

    def _save_fn(obj, csv_path, **kw):
        saved.append((csv_path, obj))
        # actually write so the rest of handler sees the file
        obj.to_csv(csv_path, index=False)

    spath = str(tmp_path / "plot.png")

    # save_image will fail on the fake object — wrap by saving a real fig too,
    # but the handler's try/except is only around the csv part; the call to
    # save_image happens first and would raise. So patch by giving the fake
    # a .savefig that does nothing. Easier path: pre-create the png file and
    # bypass save_image by giving fake a matching attribute? Instead just
    # give the fake a savefig.
    def _savefig(p, **kw):
        Path(p).write_bytes(b"fake-png")

    fake.savefig = _savefig

    handle_image_with_csv(fake, spath, _save_fn=_save_fn)
    assert os.path.exists(spath)
    assert len(saved) == 1
    csv_path = saved[0][0]
    assert csv_path.endswith(".csv")
    assert os.path.exists(csv_path)
    df_back = pd.read_csv(csv_path)
    assert list(df_back.columns) == ["x", "y"]
    assert df_back["y"].tolist() == [0.0, 1.0, 4.0]


def test_handle_image_with_sigmaplot_export(tmp_path):
    df = pd.DataFrame({"a": [1, 2]})
    sigma = pd.DataFrame({"g1": [1, 2], "g2": [3, 4]})
    fake = _FakeAxisWithExport(df, sigma_df=sigma)

    def _savefig(p, **kw):
        Path(p).write_bytes(b"fake")

    fake.savefig = _savefig

    saves = []

    def _save_fn(obj, p, **kw):
        saves.append(p)
        obj.to_csv(p, index=False)

    spath = str(tmp_path / "plot.png")
    handle_image_with_csv(fake, spath, _save_fn=_save_fn)
    # Both .csv and _for_sigmaplot.csv should have been written.
    assert any(p.endswith("plot.csv") for p in saves)
    assert any(p.endswith("_for_sigmaplot.csv") for p in saves)


def test_handle_image_empty_export_no_sidecar(tmp_path):
    """If export_as_csv returns empty df → no sidecar written."""
    fake = _FakeAxisWithExport(pd.DataFrame())
    fake.savefig = lambda p, **kw: Path(p).write_bytes(b"fake")
    saved = []

    def _save_fn(obj, p, **kw):
        saved.append(p)

    spath = str(tmp_path / "empty.png")
    handle_image_with_csv(fake, spath, _save_fn=_save_fn)
    assert saved == []


def test_handle_image_none_export_no_sidecar(tmp_path):
    """export_as_csv returning None → no sidecar written."""

    class _NoneExport:
        def export_as_csv(self):
            return None

        def savefig(self, p, **kw):
            Path(p).write_bytes(b"x")

    saved = []
    handle_image_with_csv(
        _NoneExport(), str(tmp_path / "n.png"), _save_fn=lambda *a, **k: saved.append(a)
    )
    assert saved == []


def test_handle_image_export_error_warns(tmp_path):
    class _Boom:
        def export_as_csv(self):
            raise RuntimeError("nope")

        def savefig(self, p, **kw):
            Path(p).write_bytes(b"x")

    with pytest.warns(UserWarning, match="CSV export failed"):
        handle_image_with_csv(_Boom(), str(tmp_path / "b.png"))


def test_handle_image_symlink_to_invokes_callback(tmp_path):
    df = pd.DataFrame({"x": [1]})
    fake = _FakeAxisWithExport(df)
    fake.savefig = lambda p, **kw: Path(p).write_bytes(b"x")
    save_calls, symlink_to_calls = [], []
    spath = str(tmp_path / "out.png")
    sym_target = str(tmp_path / "linked.png")
    handle_image_with_csv(
        fake,
        spath,
        symlink_to=sym_target,
        _save_fn=lambda o, p, **k: (save_calls.append(p), o.to_csv(p, index=False)),
        _symlink_to_fn=lambda src, dst, force: symlink_to_calls.append((src, dst)),
    )
    assert symlink_to_calls and symlink_to_calls[0][1].endswith("linked.csv")


def test_handle_image_symlink_from_cwd_invokes_callback(tmp_path, monkeypatch):
    df = pd.DataFrame({"x": [1]})
    fake = _FakeAxisWithExport(df)
    fake.savefig = lambda p, **kw: Path(p).write_bytes(b"x")
    monkeypatch.chdir(tmp_path)
    sym_calls = []
    handle_image_with_csv(
        fake,
        str(tmp_path / "out.png"),
        symlink_from_cwd=True,
        _save_fn=lambda o, p, **k: o.to_csv(p, index=False),
        _symlink_fn=lambda src, dst, *a, **k: sym_calls.append((src, dst)),
    )
    assert sym_calls
    assert sym_calls[0][1].endswith(".csv")


# ---------------------------------------------------------------------------
# _get_figure_with_data
# ---------------------------------------------------------------------------


def test_get_figure_with_data_direct_export_attr():
    obj = _FakeAxisWithExport(pd.DataFrame())
    assert _get_figure_with_data(obj) is obj


def test_get_figure_with_data_figure_with_export_axis():
    fig, ax = plt.subplots()
    ax.export_as_csv = lambda: pd.DataFrame({"a": [1]})
    try:
        result = _get_figure_with_data(fig)
        assert result is ax
    finally:
        plt.close(fig)


def test_get_figure_with_data_figure_no_export():
    fig, ax = plt.subplots()
    try:
        assert _get_figure_with_data(fig) is None
    finally:
        plt.close(fig)


def test_get_figure_with_data_axes_without_export():
    fig, ax = plt.subplots()
    try:
        # bare Axes, no export_as_csv
        assert _get_figure_with_data(ax) is None
    finally:
        plt.close(fig)


def test_get_figure_with_data_axes_with_export():
    fig, ax = plt.subplots()
    ax.export_as_csv = lambda: pd.DataFrame()
    try:
        assert _get_figure_with_data(ax) is ax
    finally:
        plt.close(fig)


def test_get_figure_with_data_wrapper_with_figure_attr():
    fig, ax = plt.subplots()
    ax.export_as_csv = lambda: pd.DataFrame({"x": [1]})

    class _Wrapper:
        pass

    w = _Wrapper()
    w.figure = fig
    try:
        # Wrapper itself doesn't have export_as_csv, falls through to axes
        result = _get_figure_with_data(w)
        assert result is ax
    finally:
        plt.close(fig)


def test_get_figure_with_data_axis_mpl_attribute():
    class _AxWrap:
        def __init__(self):
            self._axis_mpl = object()

    w = _AxWrap()
    # no export_as_csv → returns None
    assert _get_figure_with_data(w) is None

    w.export_as_csv = lambda: pd.DataFrame()
    assert _get_figure_with_data(w) is w


# ---------------------------------------------------------------------------
# _save_separate_legends
# ---------------------------------------------------------------------------


def test_save_separate_legends_dry_run_noop(tmp_path, mpl_fig):
    # Should do nothing; no exception.
    _save_separate_legends(mpl_fig, str(tmp_path / "x.png"), dry_run=True)


def test_save_separate_legends_no_params_attr_noop(tmp_path, mpl_fig):
    _save_separate_legends(mpl_fig, str(tmp_path / "x.png"))
    # nothing crashed; no legend files written
    assert list(tmp_path.glob("*legend*")) == []


def test_save_separate_legends_with_params(tmp_path):
    fig, ax = plt.subplots()
    (h,) = ax.plot([1, 2, 3], label="A")
    fig._separate_legend_params = [
        {
            "figsize": (2, 1),
            "handles": [h],
            "labels": ["A"],
            "frameon": True,
            "fancybox": False,
            "shadow": False,
            "kwargs": {},
            "axis_id": "ax0",
        }
    ]
    spath = str(tmp_path / "plot.png")
    _save_separate_legends(fig, spath)
    expected = tmp_path / "plot_ax0_legend.png"
    assert expected.exists()
    plt.close(fig)


def test_save_separate_legends_fig_wrapper(tmp_path):
    """Object exposing _fig_mpl is treated like the figure."""

    class _Wrap:
        pass

    fig, ax = plt.subplots()
    (h,) = ax.plot([1], label="A")
    fig._separate_legend_params = [
        {
            "figsize": (1, 1),
            "handles": [h],
            "labels": ["A"],
            "frameon": False,
            "fancybox": False,
            "shadow": False,
            "kwargs": {},
            "axis_id": "z",
        }
    ]
    w = _Wrap()
    w._fig_mpl = fig
    _save_separate_legends(w, str(tmp_path / "wrap.png"))
    assert (tmp_path / "wrap_z_legend.png").exists()
    plt.close(fig)


def test_save_separate_legends_obj_no_fig_returns(tmp_path):
    # Object with neither figure nor _fig_mpl: bail silently.
    _save_separate_legends(object(), str(tmp_path / "o.png"))


# ---------------------------------------------------------------------------
# _export_csv / _export_sigmaplot_csv branches
# ---------------------------------------------------------------------------


def test_export_csv_none_returns_early(tmp_path):
    class F:
        def export_as_csv(self):
            return None

    _export_csv(F(), str(tmp_path / "x.png"), False, None, False, None, None, None)


def test_export_csv_empty_returns_early(tmp_path):
    class F:
        def export_as_csv(self):
            return pd.DataFrame()

    _export_csv(F(), str(tmp_path / "x.png"), False, None, False, None, None, None)


def test_export_sigmaplot_csv_none(tmp_path):
    class F:
        def export_as_csv_for_sigmaplot(self):
            return None

    _export_sigmaplot_csv(
        F(), str(tmp_path / "x.png"), "png", False, None, False, None, None, None
    )


def test_export_sigmaplot_csv_writes(tmp_path):
    class F:
        def export_as_csv_for_sigmaplot(self):
            return pd.DataFrame({"a": [1]})

    saved = []
    _export_sigmaplot_csv(
        F(),
        str(tmp_path / "x.png"),
        "png",
        False,
        None,
        False,
        lambda o, p, **k: (saved.append(p), o.to_csv(p, index=False)),
        None,
        None,
    )
    assert saved and saved[0].endswith("_for_sigmaplot.csv")


def test_export_sigmaplot_csv_symlink_to(tmp_path):
    class F:
        def export_as_csv_for_sigmaplot(self):
            return pd.DataFrame({"a": [1]})

    sym = []
    _export_sigmaplot_csv(
        F(),
        str(tmp_path / "x.png"),
        "png",
        False,
        str(tmp_path / "L.png"),
        False,
        lambda o, p, **k: o.to_csv(p, index=False),
        None,
        lambda src, dst, force: sym.append((src, dst)),
    )
    assert sym and sym[0][1].endswith("_for_sigmaplot.csv")


def test_export_sigmaplot_csv_symlink_from_cwd(tmp_path, monkeypatch):
    class F:
        def export_as_csv_for_sigmaplot(self):
            return pd.DataFrame({"a": [1]})

    monkeypatch.chdir(tmp_path)
    sym = []
    _export_sigmaplot_csv(
        F(),
        str(tmp_path / "x.png"),
        "png",
        True,
        None,
        False,
        lambda o, p, **k: o.to_csv(p, index=False),
        lambda src, dst, *a, **k: sym.append((src, dst)),
        None,
    )
    assert sym


# ---------------------------------------------------------------------------
# JPEG metadata round-trip
# ---------------------------------------------------------------------------


def test_jpeg_metadata_roundtrip(tmp_path):
    img = Image.new("RGB", (100, 100), (50, 100, 150))
    p = str(tmp_path / "img.jpg")
    img.save(p, "JPEG")
    payload = {"experiment": "alpha", "n": 42, "tags": ["a", "b"]}
    embed_metadata_jpeg(p, json.dumps(payload))
    got = read_metadata_jpeg(p)
    assert got == payload


def test_jpeg_metadata_rgba_input_converted(tmp_path):
    # Save an RGBA PNG; embed_metadata_jpeg opens it, detects RGBA, converts
    # to RGB, then writes back as JPEG (overwriting the .png path with JPEG bytes).
    p = str(tmp_path / "rgba_only.png")
    Image.new("RGBA", (40, 40), (1, 2, 3, 200)).save(p)
    embed_metadata_jpeg(p, json.dumps({"k": "v"}))
    got = read_metadata_jpeg(p)
    assert got == {"k": "v"}


def test_jpeg_metadata_palette_mode(tmp_path):
    img = Image.new("P", (40, 40))
    p = str(tmp_path / "pal.png")
    img.save(p)
    embed_metadata_jpeg(p, json.dumps({"mode": "P"}))
    got = read_metadata_jpeg(p)
    assert got == {"mode": "P"}


def test_jpeg_metadata_la_mode(tmp_path):
    img = Image.new("LA", (30, 30))
    p = str(tmp_path / "la.png")
    img.save(p)
    embed_metadata_jpeg(p, json.dumps({"mode": "LA"}))
    got = read_metadata_jpeg(p)
    assert got == {"mode": "LA"}


def test_read_jpeg_no_metadata_returns_none(tmp_path):
    img = Image.new("RGB", (10, 10))
    p = str(tmp_path / "bare.jpg")
    img.save(p, "JPEG")
    assert read_metadata_jpeg(p) is None


def test_read_jpeg_non_json_description_returns_raw(tmp_path):
    import piexif

    img = Image.new("RGB", (10, 10))
    p = str(tmp_path / "raw.jpg")
    exif = {
        "0th": {piexif.ImageIFD.ImageDescription: b"just-a-string"},
        "Exif": {},
        "GPS": {},
        "1st": {},
    }
    img.save(p, "JPEG", exif=piexif.dump(exif))
    got = read_metadata_jpeg(p)
    assert got == {"raw": "just-a-string"}


# ---------------------------------------------------------------------------
# PDF metadata round-trip
# ---------------------------------------------------------------------------


def _make_pdf(path):
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2])
    fig.savefig(path, format="pdf")
    plt.close(fig)


def test_pdf_metadata_roundtrip(tmp_path):
    p = str(tmp_path / "doc.pdf")
    _make_pdf(p)
    payload = {"title": "T", "author": "A", "extra": [1, 2, 3]}
    embed_metadata_pdf(p, json.dumps(payload), payload)
    got = read_metadata_pdf(p)
    assert got == payload


def test_pdf_metadata_subject_non_json(tmp_path):
    """When Subject is non-JSON, read returns a dict assembled from fields."""
    from pypdf import PdfReader, PdfWriter

    p = str(tmp_path / "doc.pdf")
    _make_pdf(p)
    reader = PdfReader(p)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata(
        {
            "/Title": "MyTitle",
            "/Author": "MyAuthor",
            "/Subject": "not-json-at-all",
            "/Creator": "C",
        }
    )
    with open(p, "wb") as f:
        writer.write(f)
    got = read_metadata_pdf(p)
    assert got["title"] == "MyTitle"
    assert got["author"] == "MyAuthor"
    assert got["subject"] == "not-json-at-all"
    assert got["creator"] == "C"


def test_pdf_read_no_metadata(tmp_path):
    """PDF without /Subject → None."""
    p = str(tmp_path / "bare.pdf")
    _make_pdf(p)
    # Default mpl writes some metadata but not /Subject; verify None or absent /Subject.
    got = read_metadata_pdf(p)
    assert got is None


def test_pdf_read_corrupted_returns_none(tmp_path):
    p = str(tmp_path / "garbage.pdf")
    Path(p).write_bytes(b"not a real pdf")
    assert read_metadata_pdf(p) is None


# ---------------------------------------------------------------------------
# MP4 save
# ---------------------------------------------------------------------------


def test_get_figure_with_data_figure_first_axes_has_export():
    """obj.axes loop returns the first axes with export_as_csv."""
    fig, (ax0, ax1) = plt.subplots(1, 2)
    ax1.export_as_csv = lambda: pd.DataFrame({"x": [1]})
    try:
        # gca() returns the last-active axes — make ax0 active without export,
        # so we fall into the for-ax-in-fig.axes loop and find ax1.
        plt.sca(ax0)
        result = _get_figure_with_data(fig)
        assert result is ax1
    finally:
        plt.close(fig)


def test_get_figure_with_data_wrapper_self_has_export():
    """Wrapper with .figure AND .export_as_csv returns the wrapper itself."""
    fig, ax = plt.subplots()

    class _W:
        pass

    w = _W()
    w.figure = fig
    w.export_as_csv = lambda: pd.DataFrame({"x": [1]})
    try:
        assert _get_figure_with_data(w) is w
    finally:
        plt.close(fig)


def test_get_figure_with_data_gcf_fallback():
    """Final gcf/gca fallback path."""
    fig, ax = plt.subplots()
    ax.export_as_csv = lambda: pd.DataFrame({"x": [1]})
    try:
        plt.figure(fig.number)
        plt.sca(ax)
        # Object with no recognized hooks → fallback to gcf/gca path.
        assert _get_figure_with_data(object()) is ax
    finally:
        plt.close(fig)


def test_get_figure_with_data_gcf_fallback_fig_has_export():
    """gcf has export_as_csv but gca does not → return fig."""
    fig, ax = plt.subplots()
    fig.export_as_csv = lambda: pd.DataFrame({"x": [1]})
    try:
        plt.figure(fig.number)
        plt.sca(ax)
        assert _get_figure_with_data(object()) is fig
    finally:
        plt.close(fig)


def test_save_separate_legends_wrapper_with_figure_attr(tmp_path):
    """Object with .figure that is a real Figure with _separate_legend_params."""
    fig, ax = plt.subplots()
    (h,) = ax.plot([1, 2], label="A")
    fig._separate_legend_params = [
        {
            "figsize": (1, 1),
            "handles": [h],
            "labels": ["A"],
            "frameon": False,
            "fancybox": False,
            "shadow": False,
            "kwargs": {},
            "axis_id": "k",
        }
    ]

    class _W:
        pass

    w = _W()
    w.figure = fig
    _save_separate_legends(w, str(tmp_path / "w.png"))
    assert (tmp_path / "w_k_legend.png").exists()
    plt.close(fig)


def test_save_separate_legends_wrapper_figure_has_fig_mpl(tmp_path):
    """Object whose .figure exposes ._fig_mpl."""
    fig, ax = plt.subplots()
    (h,) = ax.plot([1, 2], label="A")
    fig._separate_legend_params = [
        {
            "figsize": (1, 1),
            "handles": [h],
            "labels": ["A"],
            "frameon": False,
            "fancybox": False,
            "shadow": False,
            "kwargs": {},
            "axis_id": "m",
        }
    ]

    class _FigShim:
        pass

    class _Wrap:
        pass

    fshim = _FigShim()
    fshim._fig_mpl = fig
    w = _Wrap()
    w.figure = fshim
    _save_separate_legends(w, str(tmp_path / "fm.png"))
    assert (tmp_path / "fm_m_legend.png").exists()
    plt.close(fig)


def test_handle_image_symlink_from_cwd_with_specified_path(tmp_path, monkeypatch):
    """symlink_from_cwd path where caller frame has `specified_path` local."""
    df = pd.DataFrame({"x": [1]})
    fake = _FakeAxisWithExport(df)
    fake.savefig = lambda p, **kw: Path(p).write_bytes(b"x")
    monkeypatch.chdir(tmp_path)
    sym_calls = []

    def _caller():
        # Local named specified_path is detected by the handler's inspect.stack walk.
        specified_path = "myplot.png"  # noqa: F841
        handle_image_with_csv(
            fake,
            str(tmp_path / "out.png"),
            symlink_from_cwd=True,
            _save_fn=lambda o, p, **k: o.to_csv(p, index=False),
            _symlink_fn=lambda src, dst, *a, **k: sym_calls.append((src, dst)),
        )

    _caller()
    assert sym_calls
    # dst should derive from `specified_path`, replacing .png with .csv
    assert sym_calls[0][1].endswith("myplot.csv")


def test_embed_jpeg_raises_without_piexif(tmp_path, monkeypatch):
    """ImportError branch when piexif is unavailable."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "piexif":
            raise ImportError("simulated")
        return real_import(name, *a, **kw)

    p = str(tmp_path / "x.jpg")
    Image.new("RGB", (5, 5)).save(p, "JPEG")
    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="piexif is required"):
        embed_metadata_jpeg(p, "{}")


def test_embed_pdf_raises_without_pypdf(tmp_path, monkeypatch):
    """ImportError branch when pypdf is unavailable."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "pypdf":
            raise ImportError("simulated")
        return real_import(name, *a, **kw)

    p = str(tmp_path / "x.pdf")
    _make_pdf(p)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ImportError, match="pypdf is required"):
        embed_metadata_pdf(p, "{}", {})


def test_read_jpeg_without_piexif(tmp_path, monkeypatch):
    """piexif missing → returns None gracefully (no raise)."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "piexif":
            raise ImportError("simulated")
        return real_import(name, *a, **kw)

    p = str(tmp_path / "any.jpg")
    Image.new("RGB", (5, 5)).save(p, "JPEG")
    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert read_metadata_jpeg(p) is None


def test_read_jpeg_corrupted_exif(tmp_path, monkeypatch):
    """piexif.load raising Exception → caught, returns None."""
    import piexif

    p = str(tmp_path / "c.jpg")
    Image.new("RGB", (5, 5)).save(p, "JPEG")
    monkeypatch.setattr(
        piexif, "load", lambda *a, **k: (_ for _ in ()).throw(ValueError("bad"))
    )
    # Image.info needs 'exif' key — embed something first
    import piexif as real_piexif

    Image.new("RGB", (5, 5)).save(
        p, "JPEG", exif=real_piexif.dump({"0th": {}, "Exif": {}, "GPS": {}, "1st": {}})
    )
    monkeypatch.setattr(
        piexif, "load", lambda *a, **k: (_ for _ in ()).throw(ValueError("bad"))
    )
    assert read_metadata_jpeg(p) is None


def test_read_pdf_without_pypdf(tmp_path, monkeypatch):
    """pypdf missing → returns None."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "pypdf":
            raise ImportError("simulated")
        return real_import(name, *a, **kw)

    p = str(tmp_path / "x.pdf")
    _make_pdf(p)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert read_metadata_pdf(p) is None


def test_jpeg_metadata_preserves_existing_exif(tmp_path):
    """Existing EXIF in other IFDs is preserved during embedding."""
    import piexif

    p = str(tmp_path / "preexif.jpg")
    pre_exif = {
        "0th": {},
        "Exif": {piexif.ExifIFD.UserComment: b"prior-comment"},
        "GPS": {},
        "1st": {},
    }
    Image.new("RGB", (20, 20)).save(p, "JPEG", exif=piexif.dump(pre_exif))
    embed_metadata_jpeg(p, json.dumps({"new": 1}))
    # New metadata is readable
    assert read_metadata_jpeg(p) == {"new": 1}
    # Old EXIF UserComment preserved
    full = piexif.load(Image.open(p).info["exif"])
    assert full["Exif"].get(piexif.ExifIFD.UserComment) == b"prior-comment"


def test_save_image_plotly_png(tmp_path):
    import plotly.graph_objects as go

    fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[1, 2, 3])])
    p = str(tmp_path / "plotly.png")
    save_image(fig, p)
    assert os.path.getsize(p) > 0


def test_save_image_plotly_jpeg(tmp_path):
    import plotly.graph_objects as go

    fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[1, 2, 3])])
    p = str(tmp_path / "plotly.jpg")
    save_image(fig, p)
    assert os.path.getsize(p) > 0


def test_save_image_plotly_gif(tmp_path):
    import plotly.graph_objects as go

    fig = go.Figure(data=[go.Scatter(x=[1, 2], y=[1, 2])])
    p = str(tmp_path / "plotly.gif")
    save_image(fig, p)
    assert os.path.getsize(p) > 0


def test_save_image_plotly_svg(tmp_path):
    import plotly.graph_objects as go

    fig = go.Figure(data=[go.Scatter(x=[1, 2], y=[1, 2])])
    p = str(tmp_path / "plotly.svg")
    save_image(fig, p)
    assert os.path.getsize(p) > 0


def test_save_image_plotly_pdf(tmp_path):
    import plotly.graph_objects as go

    fig = go.Figure(data=[go.Scatter(x=[1, 2], y=[1, 2])])
    p = str(tmp_path / "plotly.pdf")
    save_image(fig, p)
    assert os.path.getsize(p) > 0


def test_read_jpeg_no_exif_info(tmp_path):
    """JPEG without any 'exif' key in img.info → returns None."""
    p = str(tmp_path / "noexif.jpg")
    Image.new("RGB", (5, 5)).save(p, "JPEG")
    # PIL may add empty exif on save; ensure no metadata embedded.
    img = Image.open(p)
    # remove exif if present
    img.save(p, "JPEG")
    assert read_metadata_jpeg(p) is None


def test_pdf_subject_field_only_in_reader(tmp_path):
    """PDF where reader.metadata exists but has no /Subject → still None."""
    from pypdf import PdfReader, PdfWriter

    p = str(tmp_path / "no_subj.pdf")
    _make_pdf(p)
    reader = PdfReader(p)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata({"/Title": "OnlyTitle"})
    with open(p, "wb") as f:
        writer.write(f)
    got = read_metadata_pdf(p)
    assert got is None


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not installed")
def test_mk_mp4_creates_file(tmp_path):
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    fig = plt.figure(figsize=(2, 2))
    ax = fig.add_subplot(111, projection="3d")
    xs = np.linspace(0, 1, 10)
    ax.plot(xs, xs, xs)

    # Patch FuncAnimation to use only 2 frames so the test is fast.
    import matplotlib.animation as manim

    orig = manim.FuncAnimation

    class _FastAnim(orig):
        def __init__(
            self, fig, func, *, frames=2, interval=20, blit=True, init_func=None, **kw
        ):
            super().__init__(
                fig,
                func,
                frames=2,
                interval=interval,
                blit=blit,
                init_func=init_func,
                **kw,
            )

    manim.FuncAnimation = _FastAnim
    try:
        out = str(tmp_path / "out.mp4")
        _mk_mp4(fig, out)
        assert os.path.exists(out)
        assert os.path.getsize(out) > 0
    finally:
        manim.FuncAnimation = orig
        plt.close(fig)
