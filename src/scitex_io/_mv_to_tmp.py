#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2024-11-02 21:25:50 (ywatanabe)"
# File: ./scitex_repo/src/scitex/io/_mv_to_tmp.py

from shutil import move


def _mv_to_tmp(fpath, L=2, *, move_fn=None, tmp_dir="/tmp"):
    """Move ``fpath`` into ``tmp_dir`` joining the last ``L`` path components.

    ``move_fn`` defaults to :func:`shutil.move`; tests pass a callable that
    records arguments instead of touching the real filesystem. ``tmp_dir``
    defaults to ``"/tmp"`` and lets tests redirect to a sandboxed directory.
    """
    if move_fn is None:
        move_fn = move
    try:
        tgt_fname = "-".join(fpath.split("/")[-L:])
        tgt_fpath = "{}/{}".format(tmp_dir, tgt_fname)
        move_fn(fpath, tgt_fpath)
        print("Moved to: {}".format(tgt_fpath))
    except Exception:
        pass


# EOF
