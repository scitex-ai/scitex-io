#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Image save handler with CSV data export and legend separation.

The ``save_image`` callable lives in ``_save_modules._image`` and pulls
PIL/matplotlib at import. To keep ``import scitex_io`` (and JSON-only
``save`` paths) free of those heavy imports, the handler is resolved
lazily here via :func:`_get_save_image` — it is only ever called by
:func:`handle_image_with_csv`, which itself only runs when the user
saves an image extension.
"""

import os as _os
import warnings

from ._utils import color_text, getsize, readable_bytes


def _get_save_image():
    """Import ``save_image`` on first use; cache locally for speed."""
    from ._save_modules._image import save_image

    return save_image


def _get_figure_with_data(obj):
    """Extract figure/axes object that may contain plotting data for CSV export."""
    import matplotlib.axes
    import matplotlib.figure
    import matplotlib.pyplot as plt

    if hasattr(obj, "export_as_csv"):
        return obj

    if isinstance(obj, matplotlib.figure.Figure):
        current_ax = plt.gca()
        if hasattr(current_ax, "export_as_csv"):
            return current_ax
        for ax in obj.axes:
            if hasattr(ax, "export_as_csv"):
                return ax
        return None

    if isinstance(obj, matplotlib.axes.Axes):
        if hasattr(obj, "export_as_csv"):
            return obj
        return None

    if hasattr(obj, "figure") and hasattr(obj.figure, "axes"):
        if hasattr(obj, "export_as_csv"):
            return obj
        for ax in obj.figure.axes:
            if hasattr(ax, "export_as_csv"):
                return ax
        return None

    if hasattr(obj, "_axis_mpl") or hasattr(obj, "_ax"):
        if hasattr(obj, "export_as_csv"):
            return obj
        return None

    try:
        current_fig = plt.gcf()
        current_ax = plt.gca()
        if hasattr(current_ax, "export_as_csv"):
            return current_ax
        elif hasattr(current_fig, "export_as_csv"):
            return current_fig
        for ax in current_fig.axes:
            if hasattr(ax, "export_as_csv"):
                return ax
    except Exception:
        pass

    return None


def _save_separate_legends(obj, spath, symlink_from_cwd=False, dry_run=False, **kwargs):
    """Save separate legend files if ax.legend('separate') was used."""
    if dry_run:
        return

    import matplotlib.figure
    import matplotlib.pyplot as plt

    fig = None
    if isinstance(obj, matplotlib.figure.Figure):
        fig = obj
    elif hasattr(obj, "_fig_mpl"):
        fig = obj._fig_mpl
    elif hasattr(obj, "figure"):
        if isinstance(obj.figure, matplotlib.figure.Figure):
            fig = obj.figure
        elif hasattr(obj.figure, "_fig_mpl"):
            fig = obj.figure._fig_mpl

    if fig is None:
        return

    if not hasattr(fig, "_separate_legend_params"):
        return

    base_path = _os.path.splitext(spath)[0]
    ext = _os.path.splitext(spath)[1]

    for legend_params in fig._separate_legend_params:
        legend_fig = plt.figure(figsize=legend_params["figsize"])
        legend_ax = legend_fig.add_subplot(111)

        legend_ax.legend(
            legend_params["handles"],
            legend_params["labels"],
            loc="center",
            frameon=legend_params["frameon"],
            fancybox=legend_params["fancybox"],
            shadow=legend_params["shadow"],
            **legend_params["kwargs"],
        )

        legend_ax.axis("off")
        legend_fig.tight_layout()

        legend_filename = f"{base_path}_{legend_params['axis_id']}_legend{ext}"
        _get_save_image()(legend_fig, legend_filename, **kwargs)
        plt.close(legend_fig)

        if not dry_run and _os.path.exists(legend_filename):
            file_size = readable_bytes(getsize(legend_filename))
            print(
                color_text(
                    f"\nSaved legend to: {legend_filename} ({file_size})",
                    color="yellow",
                )
            )


def handle_image_with_csv(
    obj,
    spath,
    no_csv=False,
    symlink_from_cwd=False,
    dry_run=False,
    symlink_to=None,
    _save_fn=None,
    _symlink_fn=None,
    _symlink_to_fn=None,
    **kwargs,
):
    """Handle image file saving with optional CSV export.

    Parameters
    ----------
    _save_fn : callable
        Reference to _save() from _save.py to avoid circular import.
    _symlink_fn : callable
        Reference to _symlink() from _save.py.
    _symlink_to_fn : callable
        Reference to _symlink_to() from _save.py.
    """
    if dry_run:
        return

    _get_save_image()(obj, spath, **kwargs)

    _save_separate_legends(
        obj, spath, symlink_from_cwd=symlink_from_cwd, dry_run=dry_run, **kwargs
    )

    if no_csv:
        return

    ext = _os.path.splitext(spath)[1].lower()
    ext_wo_dot = ext.replace(".", "")

    try:
        fig_obj = _get_figure_with_data(obj)
        if fig_obj is None:
            return

        if hasattr(fig_obj, "export_as_csv"):
            _export_csv(
                fig_obj,
                spath,
                symlink_from_cwd,
                symlink_to,
                dry_run,
                _save_fn,
                _symlink_fn,
                _symlink_to_fn,
            )

        if hasattr(fig_obj, "export_as_csv_for_sigmaplot"):
            _export_sigmaplot_csv(
                fig_obj,
                spath,
                ext_wo_dot,
                symlink_from_cwd,
                symlink_to,
                dry_run,
                _save_fn,
                _symlink_fn,
                _symlink_to_fn,
            )
    except Exception as e:
        warnings.warn(f"CSV export failed: {e}")
        import traceback

        traceback.print_exc()


def _export_csv(
    fig_obj,
    spath,
    symlink_from_cwd,
    symlink_to,
    dry_run,
    _save_fn,
    _symlink_fn,
    _symlink_to_fn,
):
    """Export CSV data alongside an image."""
    csv_data = fig_obj.export_as_csv()
    if csv_data is None or csv_data.empty:
        return

    csv_path = _os.path.splitext(spath)[0] + ".csv"
    _os.makedirs(_os.path.dirname(csv_path), exist_ok=True)

    if _save_fn:
        _save_fn(
            csv_data,
            csv_path,
            verbose=True,
            symlink_from_cwd=False,
            dry_run=dry_run,
            no_csv=True,
        )

    if symlink_to and _symlink_to_fn:
        csv_symlink_to = _os.path.splitext(symlink_to)[0] + ".csv"
        _symlink_to_fn(csv_path, csv_symlink_to, True)

    if symlink_from_cwd and _symlink_fn:
        import inspect

        frame_info = inspect.stack()
        for frame in frame_info:
            if "specified_path" in frame.frame.f_locals:
                original_path = frame.frame.f_locals["specified_path"]
                if isinstance(original_path, str):
                    csv_relative = original_path.replace(
                        _os.path.splitext(original_path)[1], ".csv"
                    )
                    csv_cwd = _os.path.join(_os.getcwd(), csv_relative)
                    _symlink_fn(csv_path, csv_cwd, True, True)
                    break
        else:
            csv_cwd = _os.getcwd() + "/" + _os.path.basename(csv_path)
            _symlink_fn(csv_path, csv_cwd, True, True)


def _export_sigmaplot_csv(
    fig_obj,
    spath,
    ext_wo_dot,
    symlink_from_cwd,
    symlink_to,
    dry_run,
    _save_fn,
    _symlink_fn,
    _symlink_to_fn,
):
    """Export SigmaPlot CSV data alongside an image."""
    sigmaplot_data = fig_obj.export_as_csv_for_sigmaplot()
    if sigmaplot_data is None or sigmaplot_data.empty:
        return

    csv_sigmaplot_path = spath.replace(ext_wo_dot, "csv").replace(
        ".csv", "_for_sigmaplot.csv"
    )

    if _save_fn:
        _save_fn(
            sigmaplot_data,
            csv_sigmaplot_path,
            verbose=True,
            symlink_from_cwd=False,
            dry_run=dry_run,
            no_csv=True,
        )

    if symlink_to and _symlink_to_fn:
        csv_sigmaplot_symlink_to = (
            _os.path.splitext(symlink_to)[0] + "_for_sigmaplot.csv"
        )
        _symlink_to_fn(csv_sigmaplot_path, csv_sigmaplot_symlink_to, True)

    if symlink_from_cwd and _symlink_fn:
        csv_cwd = _os.getcwd() + "/" + _os.path.basename(csv_sigmaplot_path)
        _symlink_fn(csv_sigmaplot_path, csv_cwd, True, True)
