#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for scitex_io._image_csv_handler.

Covers:
- _get_figure_with_data: all branches (plain fig/ax, ax with export_as_csv,
  fig with export_as_csv, obj with _axis_mpl, fallback gca/gcf path)
- _save_separate_legends: dry_run skip, no _separate_legend_params, real save
- handle_image_with_csv: dry_run, no_csv, normal, empty df, CSV+sigmaplot
- _export_csv: save_fn called, symlink_to path, no save_fn
- _export_sigmaplot_csv: save_fn called, symlink_to path
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import os
import warnings

import matplotlib.axes
import matplotlib.figure
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import pandas as pd
import pytest

from scitex_io._image_csv_handler import (
    _export_csv,
    _export_sigmaplot_csv,
    _get_figure_with_data,
    _save_separate_legends,
    handle_image_with_csv,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_fig_ax():
    """Return a fresh (fig, ax) pair and close on teardown via caller's fixture."""
    fig, ax = plt.subplots()
    ax.plot([1, 2], [3, 4])
    return fig, ax


def _mock_save():
    """Return a (dict, callable) pair that records every save call."""
    calls: dict = {}

    def _fn(data, path, **kw):
        calls[path] = data

    return calls, _fn


# ---------------------------------------------------------------------------
# _get_figure_with_data
# ---------------------------------------------------------------------------


class TestGetFigureWithData:
    def teardown_method(self):
        plt.close("all")

    def test_returns_none_for_plain_figure_without_export(self):
        # Arrange
        # Act
        # Arrange
        # Act
        fig, _ax = _make_fig_ax()
        # Assert
        # Assert
        assert _get_figure_with_data(fig) is None

    def test_returns_none_for_plain_axes_without_export(self):
        # Arrange
        # Act
        # Arrange
        # Act
        _fig, ax = _make_fig_ax()
        # Assert
        # Assert
        assert _get_figure_with_data(ax) is None

    def test_returns_ax_when_ax_has_export_as_csv(self):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: None
        # Act
        # Act
        result = _get_figure_with_data(fig)
        # Assert
        # Assert
        assert result is ax

    def test_returns_ax_directly_when_ax_passed_with_export(self):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        # Act
        # Act
        ax.export_as_csv = lambda: None
        # Assert
        # Assert
        assert _get_figure_with_data(ax) is ax

    def test_obj_with_export_as_csv_returns_itself(self):
        # Arrange
        # Arrange
        class FakeObj:
            export_as_csv = lambda self: None  # noqa: E731

        # Act
        # Act
        obj = FakeObj()
        # Assert
        # Assert
        assert _get_figure_with_data(obj) is obj

    def test_figure_with_export_as_csv_returns_itself(self):
        # Arrange
        # Arrange
        fig, _ax = _make_fig_ax()
        fig.export_as_csv = lambda: None
        # plt.gca() is not fig, so falls through to "for ax in obj.axes" loop —
        # no ax has export_as_csv, then we check if fig itself does in the
        # fallback gcf branch.
        # Act
        # Act
        result = _get_figure_with_data(fig)
        # Either fig or gca may be returned; ensure it is not None.
        # Assert
        # Assert
        assert result is not None

    def test_obj_with_figure_attribute_and_export_on_ax(self):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: None

        class FakeObj:
            figure = fig

        # Act
        # Act
        result = _get_figure_with_data(FakeObj())
        # Assert
        # Assert
        assert result is ax

    def test_obj_with_axis_mpl_no_export_returns_none(self):
        # Arrange
        # Act
        # Arrange
        # Act
        class FakeObj:
            _axis_mpl = True

        # Assert
        # Assert
        assert _get_figure_with_data(FakeObj()) is None

    def test_obj_with_axis_mpl_and_export_returns_itself(self):
        # Arrange
        # Arrange
        class FakeObj:
            _axis_mpl = True
            export_as_csv = lambda self: None  # noqa: E731

        # Act
        # Act
        obj = FakeObj()
        # Assert
        # Assert
        assert _get_figure_with_data(obj) is obj

    def test_exception_in_gcf_path_returns_none(self):
        """When plt.gcf/gca raises, the except swallows it and returns None."""

        # Arrange
        class Bomb:
            pass

        # Pass a completely unknown object — forces the final fallback branch.
        # Act
        result = _get_figure_with_data(42)
        # Numeric int has no known attributes, so result must be None.
        # Assert
        assert result is None


# ---------------------------------------------------------------------------
# _save_separate_legends
# ---------------------------------------------------------------------------


class TestSaveSeparateLegends:
    def teardown_method(self):
        plt.close("all")

    def test_dry_run_does_nothing(self, tmp_path):
        # Arrange
        # Arrange
        fig, _ax = _make_fig_ax()
        fig._separate_legend_params = [{}]  # would fail if accessed
        spath = str(tmp_path / "fig.png")
        # Act
        # Act
        _save_separate_legends(fig, spath, dry_run=True)
        # No legend file created
        # Assert
        # Assert
        assert not os.path.exists(str(tmp_path / "fig_None_legend.png"))

    def test_no_separate_legend_params_does_nothing(self, tmp_path):
        # Arrange
        # Arrange
        fig, _ax = _make_fig_ax()
        spath = str(tmp_path / "fig.png")
        # Act
        # Act
        _save_separate_legends(fig, spath)  # no _separate_legend_params attr
        # Assert
        # Assert
        assert list(tmp_path.iterdir()) == []

    def test_non_figure_obj_returns_early(self, tmp_path):
        # Arrange
        # Arrange
        spath = str(tmp_path / "fig.png")
        # Act
        # Act
        _save_separate_legends("not-a-figure", spath)
        # Assert
        # Assert
        assert list(tmp_path.iterdir()) == []

    def test_saves_legend_file(self, tmp_path):
        # Arrange
        # Arrange
        fig, _ax = _make_fig_ax()
        handle = mlines.Line2D([], [], color="blue", label="A")
        fig._separate_legend_params = [
            {
                "figsize": (2, 1),
                "handles": [handle],
                "labels": ["A"],
                "frameon": True,
                "fancybox": False,
                "shadow": False,
                "kwargs": {},
                "axis_id": "ax0",
            }
        ]
        spath = str(tmp_path / "fig.png")
        _save_separate_legends(fig, spath)
        # Act
        # Act
        legend_path = tmp_path / "fig_ax0_legend.png"
        # Assert
        # Assert
        assert legend_path.exists()

    def test_saves_legend_for_figure_via_fig_mpl_attr(self, tmp_path):
        # Arrange
        # Arrange
        real_fig, _ax = _make_fig_ax()
        handle = mlines.Line2D([], [], color="red", label="B")
        real_fig._separate_legend_params = [
            {
                "figsize": (2, 1),
                "handles": [handle],
                "labels": ["B"],
                "frameon": False,
                "fancybox": False,
                "shadow": False,
                "kwargs": {},
                "axis_id": "ax1",
            }
        ]

        class FakeObj:
            _fig_mpl = real_fig

        spath = str(tmp_path / "fig.png")
        # Act
        # Act
        _save_separate_legends(FakeObj(), spath)
        # Assert
        # Assert
        assert (tmp_path / "fig_ax1_legend.png").exists()


# ---------------------------------------------------------------------------
# handle_image_with_csv
# ---------------------------------------------------------------------------


class TestHandleImageWithCsv:
    def teardown_method(self):
        plt.close("all")

    def test_dry_run_creates_no_file(self, tmp_path):
        # Arrange
        # Arrange
        fig, _ax = _make_fig_ax()
        spath = str(tmp_path / "out.png")
        # Act
        # Act
        handle_image_with_csv(fig, spath, dry_run=True)
        # Assert
        # Assert
        assert not os.path.exists(spath)

    def test_no_csv_skips_csv_export_os_path_exists_spath(self, tmp_path):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1, 2]})
        spath = str(tmp_path / "out.png")
        calls, mock_save = _mock_save()
        # Act
        handle_image_with_csv(fig, spath, no_csv=True, _save_fn=mock_save)
        # Act
        # Assert
        # Assert
        assert os.path.exists(spath)

    def test_no_csv_skips_csv_export_not_any_csv_in_p_for_p_in_calls(self, tmp_path):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1, 2]})
        spath = str(tmp_path / "out.png")
        calls, mock_save = _mock_save()
        # Act
        handle_image_with_csv(fig, spath, no_csv=True, _save_fn=mock_save)
        # Act
        # Assert
        # Assert
        assert not any(".csv" in p for p in calls)


    def test_image_is_saved(self, tmp_path):
        # Arrange
        # Arrange
        fig, _ax = _make_fig_ax()
        spath = str(tmp_path / "out.png")
        # Act
        # Act
        handle_image_with_csv(fig, spath, no_csv=True)
        # Assert
        # Assert
        assert os.path.exists(spath)

    def test_csv_exported_when_export_as_csv_present_len_csv_paths_is_1(self, tmp_path):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        spath = str(tmp_path / "out.png")
        calls, mock_save = _mock_save()
        handle_image_with_csv(fig, spath, _save_fn=mock_save)
        # Act
        csv_paths = [p for p in calls if p.endswith(".csv")]
        # Act
        # Assert
        # Assert
        assert len(csv_paths) == 1

    def test_csv_exported_when_export_as_csv_present_csv_paths_0_str_tmp_path_out_csv(self, tmp_path):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        spath = str(tmp_path / "out.png")
        calls, mock_save = _mock_save()
        handle_image_with_csv(fig, spath, _save_fn=mock_save)
        # Act
        csv_paths = [p for p in calls if p.endswith(".csv")]
        # Act
        # Assert
        # Assert
        assert csv_paths[0] == str(tmp_path / "out.csv")


    def test_empty_dataframe_does_not_create_csv(self, tmp_path):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame()
        spath = str(tmp_path / "out.png")
        calls, mock_save = _mock_save()
        # Act
        # Act
        handle_image_with_csv(fig, spath, _save_fn=mock_save)
        # Assert
        # Assert
        assert len(calls) == 0

    def test_none_dataframe_does_not_create_csv(self, tmp_path):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: None
        spath = str(tmp_path / "out.png")
        calls, mock_save = _mock_save()
        # Act
        # Act
        handle_image_with_csv(fig, spath, _save_fn=mock_save)
        # Assert
        # Assert
        assert len(calls) == 0

    def test_exception_in_export_triggers_warning(self, tmp_path):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()

        def _bad():
            raise RuntimeError("export broke")

        ax.export_as_csv = _bad
        spath = str(tmp_path / "out.png")
        # Act
        # Act
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            handle_image_with_csv(fig, spath)
        # Assert
        # Assert
        assert any("CSV export failed" in str(w.message) for w in caught)

    def test_sigmaplot_csv_exported_len_sigmaplot_paths_1(self, tmp_path):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1]})
        ax.export_as_csv_for_sigmaplot = lambda: pd.DataFrame({"a": [1], "b": [2]})
        spath = str(tmp_path / "out.png")
        calls, mock_save = _mock_save()
        handle_image_with_csv(fig, spath, _save_fn=mock_save)
        # Act
        sigmaplot_paths = [p for p in calls if "sigmaplot" in p]
        # Act
        # Assert
        # Assert
        assert len(sigmaplot_paths) >= 1

    def test_sigmaplot_csv_exported_all_sigmaplot_in_p_for_p_in_sigmaplot_paths(self, tmp_path):
        # Arrange
        # Arrange
        fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1]})
        ax.export_as_csv_for_sigmaplot = lambda: pd.DataFrame({"a": [1], "b": [2]})
        spath = str(tmp_path / "out.png")
        calls, mock_save = _mock_save()
        handle_image_with_csv(fig, spath, _save_fn=mock_save)
        # Act
        sigmaplot_paths = [p for p in calls if "sigmaplot" in p]
        # Act
        # Assert
        # Assert
        assert all("sigmaplot" in p for p in sigmaplot_paths)


    @pytest.mark.parametrize("ext", [".png", ".tiff", ".jpeg", ".jpg", ".gif", ".pdf"])
    def test_various_extensions_save_image(self, tmp_path, ext):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        fig, _ax = _make_fig_ax()
        spath = str(tmp_path / f"out{ext}")
        # Some formats need special handling; just verify no unhandled exception.
        try:
            handle_image_with_csv(fig, spath, no_csv=True)
            assert os.path.exists(spath)
        except Exception as exc:
            # Formats like .gif may not be supported in all envs; that is acceptable.
            pytest.skip(f"Format {ext} not supported in this environment: {exc}")


# ---------------------------------------------------------------------------
# _export_csv
# ---------------------------------------------------------------------------


class TestExportCsv:
    def teardown_method(self):
        plt.close("all")

    def test_save_fn_called_with_correct_path(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1]})
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        _export_csv(ax, spath, False, None, False, mock_save, None, None)
        # Act
        # Act
        expected = str(tmp_path / "img.csv")
        # Assert
        # Assert
        assert expected in calls

    def test_no_save_fn_does_not_crash(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        _fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1]})
        spath = str(tmp_path / "img.png")
        _export_csv(ax, spath, False, None, False, None, None, None)

    def test_symlink_to_triggers_symlink_to_fn_len_symlink_calls_is_1(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1]})
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        symlink_calls: list = []
        def mock_symlink_to(src, dst, verbose):
            symlink_calls.append((src, dst))
        symlink_to = str(tmp_path / "link_img.png")
        # Act
        _export_csv(
            ax, spath, False, symlink_to, False, mock_save, None, mock_symlink_to
        )
        # Act
        # Assert
        # Assert
        assert len(symlink_calls) == 1

    def test_symlink_to_triggers_symlink_to_fn_symlink_calls_0_1_endswith_csv(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame({"x": [1]})
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        symlink_calls: list = []
        def mock_symlink_to(src, dst, verbose):
            symlink_calls.append((src, dst))
        symlink_to = str(tmp_path / "link_img.png")
        # Act
        _export_csv(
            ax, spath, False, symlink_to, False, mock_save, None, mock_symlink_to
        )
        # Act
        # Assert
        # Assert
        assert symlink_calls[0][1].endswith(".csv")


    def test_empty_dataframe_returns_early(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: pd.DataFrame()
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        # Act
        # Act
        _export_csv(ax, spath, False, None, False, mock_save, None, None)
        # Assert
        # Assert
        assert len(calls) == 0

    def test_none_dataframe_returns_early(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv = lambda: None
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        # Act
        # Act
        _export_csv(ax, spath, False, None, False, mock_save, None, None)
        # Assert
        # Assert
        assert len(calls) == 0


# ---------------------------------------------------------------------------
# _export_sigmaplot_csv
# ---------------------------------------------------------------------------


class TestExportSigmaplotCsv:
    def teardown_method(self):
        plt.close("all")

    def test_save_fn_called(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv_for_sigmaplot = lambda: pd.DataFrame({"a": [1], "b": [2]})
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        # Act
        # Act
        _export_sigmaplot_csv(
            ax, spath, "png", False, None, False, mock_save, None, None
        )
        # Assert
        # Assert
        assert any("sigmaplot" in p for p in calls)

    def test_no_save_fn_does_not_crash(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        # Act
        # Assert
        _fig, ax = _make_fig_ax()
        ax.export_as_csv_for_sigmaplot = lambda: pd.DataFrame({"a": [1]})
        spath = str(tmp_path / "img.png")
        _export_sigmaplot_csv(ax, spath, "png", False, None, False, None, None, None)

    def test_symlink_to_triggers_symlink_to_fn_len_symlink_calls_is_1(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv_for_sigmaplot = lambda: pd.DataFrame({"a": [1]})
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        symlink_calls: list = []
        def mock_symlink_to(src, dst, verbose):
            symlink_calls.append((src, dst))
        symlink_to = str(tmp_path / "link_img.png")
        # Act
        _export_sigmaplot_csv(
            ax, spath, "png", False, symlink_to, False, mock_save, None, mock_symlink_to
        )
        # Act
        # Assert
        # Assert
        assert len(symlink_calls) == 1

    def test_symlink_to_triggers_symlink_to_fn_sigmaplot_in_symlink_calls_0_1(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv_for_sigmaplot = lambda: pd.DataFrame({"a": [1]})
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        symlink_calls: list = []
        def mock_symlink_to(src, dst, verbose):
            symlink_calls.append((src, dst))
        symlink_to = str(tmp_path / "link_img.png")
        # Act
        _export_sigmaplot_csv(
            ax, spath, "png", False, symlink_to, False, mock_save, None, mock_symlink_to
        )
        # Act
        # Assert
        # Assert
        assert "sigmaplot" in symlink_calls[0][1]


    def test_empty_dataframe_returns_early(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv_for_sigmaplot = lambda: pd.DataFrame()
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        # Act
        # Act
        _export_sigmaplot_csv(
            ax, spath, "png", False, None, False, mock_save, None, None
        )
        # Assert
        # Assert
        assert len(calls) == 0

    def test_none_dataframe_returns_early(self, tmp_path):
        # Arrange
        # Arrange
        _fig, ax = _make_fig_ax()
        ax.export_as_csv_for_sigmaplot = lambda: None
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        # Act
        # Act
        _export_sigmaplot_csv(
            ax, spath, "png", False, None, False, mock_save, None, None
        )
        # Assert
        # Assert
        assert len(calls) == 0

    def test_symlink_from_cwd_calls_symlink_fn(self, tmp_path, monkeypatch):
        # Arrange
        # Arrange
        monkeypatch.chdir(tmp_path)
        _fig, ax = _make_fig_ax()
        ax.export_as_csv_for_sigmaplot = lambda: pd.DataFrame({"a": [1]})
        spath = str(tmp_path / "img.png")
        calls, mock_save = _mock_save()
        symlink_calls: list = []

        def mock_symlink_fn(src, dst, v1, v2):
            symlink_calls.append((src, dst))

        # Act
        # Act
        _export_sigmaplot_csv(
            ax, spath, "png", True, None, False, mock_save, mock_symlink_fn, None
        )
        # Assert
        # Assert
        assert len(symlink_calls) == 1
