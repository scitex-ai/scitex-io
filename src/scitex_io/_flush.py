#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2024-11-02 03:23:44 (ywatanabe)"
# File: ./scitex_repo/src/scitex/io/_flush.py

import os
import sys
import warnings


def flush(sys=sys, *, sync_fn=None):
    """
    Flushes the system's stdout and stderr, and syncs the file system.
    This ensures all pending write operations are completed.

    ``sync_fn`` lets callers (typically tests) substitute :func:`os.sync`
    with a no-op or recording callable. Defaults to :func:`os.sync`.
    """
    if sync_fn is None:
        sync_fn = os.sync
    if sys is None:
        warnings.warn("flush needs sys. Skipping.")
    else:
        sys.stdout.flush()
        sys.stderr.flush()
        sync_fn()


# EOF
