#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save handler for Apache Arrow Feather v2 files (.feather)."""


def _save_feather(obj, spath: str, **kwargs) -> None:
    """Save a DataFrame to Feather v2.

    Parameters
    ----------
    obj : pandas.DataFrame | dict | numpy.ndarray
        Object to save. Non-DataFrame inputs are coerced via `pd.DataFrame(obj)`.
    spath : str
        Output file path (must end in `.feather`).
    **kwargs
        Forwarded to `pandas.DataFrame.to_feather()`.

    Notes
    -----
    Requires `pyarrow` to be installed.
    """
    import pandas as pd

    if not isinstance(obj, pd.DataFrame):
        obj = pd.DataFrame(obj)
    obj.to_feather(spath, **kwargs)


# EOF
