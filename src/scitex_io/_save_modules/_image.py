#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-05-18 14:52:34 (ywatanabe)"
# File: /ssh:sp:/home/ywatanabe/proj/scitex_repo/src/scitex/io/_save_modules/_save_image.py
# ----------------------------------------
import os

__FILE__ = __file__
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

import io as _io

from scitex_dev import try_import_optional

plotly = try_import_optional("plotly")
Image = try_import_optional("PIL", "Image")


def _is_plotly_figure(obj) -> bool:
    """Safe plotly.Figure check that works when plotly is not installed."""
    if plotly is None:
        return False
    return isinstance(obj, plotly.graph_objs.Figure)


def _is_pil_image(obj) -> bool:
    """Safe PIL.Image.Image check that works when PIL is not installed."""
    if Image is None:
        return False
    return isinstance(obj, Image.Image)


# Keys accepted by ``matplotlib.figure.Figure.savefig``. Any other kwargs
# that reach ``save_image`` from ``stx.io.save`` (e.g. ``verbose``,
# ``track``, ``no_csv``, internal scitex flags) must be filtered out
# before being forwarded, otherwise matplotlib raises TypeError.
#
# ``metadata`` is deliberately EXCLUDED: stx.io.save auto-collects a
# nested dict of scitex-specific metadata for the JSON sidecar, and
# matplotlib's savefig ``metadata`` kwarg expects a flat dict[str, str]
# that it writes into the PNG chunk headers. Forwarding the nested
# scitex dict crashes matplotlib with ``'dict' object has no attribute
# 'encode'``. The scitex metadata still reaches disk through the
# separate ``_save_metadata_json`` path.
_MPL_SAVEFIG_KEYS = frozenset(
    {
        "transparent",
        "dpi",
        "format",
        "bbox_inches",
        "pad_inches",
        "facecolor",
        "edgecolor",
        "backend",
        "orientation",
        "papertype",
        "bbox_extra_artists",
        "pil_kwargs",
    }
)


def _mpl_savefig_kwargs(kwargs):
    return {k: v for k, v in kwargs.items() if k in _MPL_SAVEFIG_KEYS}


def save_image(obj, spath, **kwargs):
    # png
    if spath.endswith(".png"):
        # plotly
        if _is_plotly_figure(obj):
            obj.write_image(file=spath, format="png")
        # PIL image
        elif _is_pil_image(obj):
            obj.save(spath)
        # matplotlib
        else:
            savefig_kwargs = _mpl_savefig_kwargs(kwargs)
            try:
                obj.savefig(spath, **savefig_kwargs)
            except Exception:
                obj.figure.savefig(spath, **savefig_kwargs)
        del obj

    # tiff
    elif spath.endswith(".tiff") or spath.endswith(".tif"):
        # PIL image
        if _is_pil_image(obj):
            obj.save(spath)
        # matplotlib
        else:
            try:
                obj.savefig(spath, dpi=300, format="tiff")
            except:
                obj.figure.savefig(spath, dpi=300, format="tiff")

        del obj

    # jpeg
    elif spath.endswith(".jpeg") or spath.endswith(".jpg"):
        buf = _io.BytesIO()

        # plotly
        if _is_plotly_figure(obj):
            obj.write_image(buf, format="png")
            buf.seek(0)
            img = Image.open(buf)
            img.convert("RGB").save(spath, "JPEG")
            buf.close()

        # PIL image
        elif _is_pil_image(obj):
            obj.save(spath)

        # matplotlib
        else:
            try:
                obj.savefig(buf, format="png")
            except:
                obj.figure.savefig(buf, format="png")

            buf.seek(0)
            img = Image.open(buf)
            img.convert("RGB").save(spath, "JPEG")
            buf.close()
        del obj

    # GIF
    elif spath.endswith(".gif"):
        # PIL image
        if _is_pil_image(obj):
            obj.save(spath, save_all=True)
        # plotly - convert via PNG first
        elif _is_plotly_figure(obj):
            buf = _io.BytesIO()
            obj.write_image(buf, format="png")
            buf.seek(0)
            img = Image.open(buf)
            img.save(spath, "GIF")
            buf.close()
        # matplotlib
        else:
            buf = _io.BytesIO()
            try:
                obj.savefig(buf, format="png")
            except:
                obj.figure.savefig(buf, format="png")
            buf.seek(0)
            img = Image.open(buf)
            img.save(spath, "GIF")
            buf.close()
        del obj

    # SVG
    elif spath.endswith(".svg"):
        # Plotly
        if _is_plotly_figure(obj):
            obj.write_image(file=spath, format="svg")
        # Matplotlib
        else:
            try:
                obj.savefig(spath, format="svg")
            except AttributeError:
                obj.figure.savefig(spath, format="svg")
        del obj

    # PDF
    elif spath.endswith(".pdf"):
        # Plotly
        if _is_plotly_figure(obj):
            obj.write_image(file=spath, format="pdf")
        # PIL Image - convert to PDF
        elif _is_pil_image(obj):
            # Convert RGBA to RGB if needed
            if obj.mode == "RGBA":
                rgb_img = Image.new("RGB", obj.size, (255, 255, 255))
                rgb_img.paste(obj, mask=obj.split()[3])
                rgb_img.save(spath, "PDF")
            else:
                obj.save(spath, "PDF")
        # Matplotlib
        else:
            try:
                obj.savefig(spath, format="pdf")
            except AttributeError:
                obj.figure.savefig(spath, format="pdf")
        del obj


# EOF
