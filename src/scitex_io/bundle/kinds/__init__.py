#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``scitex_io.bundle.kinds`` — pure-I/O bundle kind handlers.

These kinds have zero ecosystem coupling — image/text/shape are simple
annotation primitives, table covers tabular I/O plus LaTeX export.
Domain-coupled kinds (figure, plot, stats) live in their respective
standalone packages (figrecipe.io, scitex_stats.io) and register with
``scitex_io._optional_providers``.
"""

from ._image import load_image, render_image  # noqa: F401
from ._shape import render_shape  # noqa: F401
from ._table import export_to_latex  # noqa: F401
from ._text import render_text  # noqa: F401

__all__ = [
    "render_image",
    "load_image",
    "render_shape",
    "render_text",
    "export_to_latex",
]
