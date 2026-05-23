#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2024-11-14 07:41:31 (ywatanabe)"
# File: ./scitex_repo/src/scitex/io/_load_modules/_pandas.py


def _load_csv(lpath, **kwargs):
    """Load CSV files."""
    # Lazy import to avoid circular import issues
    import pandas as pd

    if not lpath.endswith(".csv"):
        raise ValueError("File must have .csv extension")

    # Handle index column - default to None to match default index=False in saving
    index_col = kwargs.pop("index_col", None)
    obj = pd.read_csv(lpath, index_col=index_col, **kwargs)

    # Remove unnamed columns when the CSV had a text header. `.str` on a
    # non-string Index (e.g. RangeIndex from header=None) raises
    # AttributeError; we use try/except instead of a dtype check so this
    # works across pandas versions (object, "string", pyarrow-backed "str").
    try:
        unnamed_cols = obj.columns.str.contains("^Unnamed")
    except (AttributeError, TypeError):
        unnamed_cols = None
    if unnamed_cols is not None and unnamed_cols.any():
        obj = obj.loc[:, ~unnamed_cols]

    return obj


# def _load_csv(lpath, **kwargs):
#     """Load CSV files."""
#     if not lpath.endswith('.csv'):
#         raise ValueError("File must have .csv extension")
#     index_col = kwargs.get("index_col", 0)
#     obj = pd.read_csv(lpath, **kwargs)
#     return obj.loc[:, ~obj.columns.str.contains("^Unnamed")]


def _load_tsv(lpath, **kwargs):
    """Load TSV files."""
    import pandas as pd

    if not lpath.endswith(".tsv"):
        raise ValueError("File must have .tsv extension")
    return pd.read_csv(lpath, sep="\t", **kwargs)


def _load_excel(lpath, **kwargs):
    """Load Excel files."""
    import pandas as pd

    if not lpath.endswith((".xls", ".xlsx", ".xlsm", ".xlsb")):
        raise ValueError("File must have Excel extension")
    return pd.read_excel(lpath, **kwargs)


def _load_parquet(lpath, **kwargs):
    """Load Parquet files."""
    import pandas as pd

    if not lpath.endswith(".parquet"):
        raise ValueError("File must have .parquet extension")
    return pd.read_parquet(lpath, **kwargs)


def _load_feather(lpath, **kwargs):
    """Load Feather (Arrow IPC) files."""
    import pandas as pd

    if not lpath.endswith(".feather"):
        raise ValueError("File must have .feather extension")
    return pd.read_feather(lpath, **kwargs)


# def _load_excel(lpath):
#     workbook = openpyxl.load_workbook(lpath)
#     all_text = []
#     for sheet in workbook:
#         for row in sheet.iter_rows(values_only=True):
#             all_text.append(
#                 " ".join(
#                     [str(cell) if cell is not None else "" for cell in row]
#                 )
#             )
#     return "\n".join(all_text)


# EOF
