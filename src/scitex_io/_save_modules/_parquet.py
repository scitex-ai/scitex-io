#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Save handler for Apache Parquet files (.parquet)."""


def _save_parquet(obj, spath: str, **kwargs) -> None:
    """Save a DataFrame (or DataFrame-coercible object) to Parquet.

    Parameters
    ----------
    obj : pandas.DataFrame | dict | numpy.ndarray
        Object to save. Non-DataFrame inputs are coerced via `pd.DataFrame(obj)`.
    spath : str
        Output file path (must end in `.parquet`).
    **kwargs
        Forwarded to `pandas.DataFrame.to_parquet()`.

    Notes
    -----
    Requires `pyarrow` or `fastparquet` to be installed.
    """
    import pandas as pd

    if not isinstance(obj, pd.DataFrame):
        obj = pd.DataFrame(obj)
    obj.to_parquet(spath, **kwargs)


# EOF
