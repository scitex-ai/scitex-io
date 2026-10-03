#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-05-16 12:22:56 (ywatanabe)"
# File: /data/gpfs/projects/punim2354/ywatanabe/scitex_repo/src/scitex/io/_save_modules/_joblib.py

try:
    import joblib
except ImportError:  # optional: pip install scitex-io[dev]
    joblib = None


def _save_joblib(obj, spath):
    """
    Save an object using joblib serialization.
    
    Parameters
    ----------
    obj : Any
        Object to serialize.
    spath : str
        Path where the joblib file will be saved.
        
    Returns
    -------
    None
    """
    if joblib is None:
        raise ImportError(
            "Joblib serialization requires joblib; install scitex-io[dev]."
        )
    with open(spath, "wb") as s:
        joblib.dump(obj, s, compress=3)
