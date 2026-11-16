#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``save(..., derived_from=[...])`` reaches post-save hooks, exactly.

Real files in ``tmp_path``, real ``load``/``save``, and a real registered
observer that records the payload it receives. Covers: paths and loaded
objects resolve to realpaths; sidecars carry the same declaration; the
kwarg never reaches the format handler; nothing is inferred when the
caller declares nothing; and unresolvable items fail BEFORE writing.
"""

from __future__ import annotations

import gc
import json
import os

import pandas as pd
import pytest

import scitex_io
from scitex_io._derived_from import loaded_from, resolve_derived_from
from scitex_io._observers import register_post_save_hook
from scitex_io._registry import register_saver, unregister_saver


@pytest.fixture
def inputs(tmp_path):
    used = tmp_path / "used.csv"
    unused = tmp_path / "unused.csv"
    pd.DataFrame({"x": [1, 2, 3]}).to_csv(used, index=False)
    pd.DataFrame({"x": [9, 9, 9]}).to_csv(unused, index=False)
    return used, unused


@pytest.fixture
def payloads(hooks):
    seen = []
    register_post_save_hook(lambda p, obj, kw: seen.append((str(p), kw)))
    return seen


def test_path_declaration_reaches_hook_as_realpath(inputs, payloads, tmp_path):
    # Arrange
    used, _ = inputs
    out = tmp_path / "result.json"
    # Act
    scitex_io.save({"n": 3}, str(out), verbose=False, derived_from=[str(used)])
    # Assert
    assert payloads[0][1]["derived_from"] == [os.path.realpath(used)]


def test_loaded_object_resolves_to_its_source_file(inputs, payloads, tmp_path):
    # Arrange
    used, unused = inputs
    df_used = scitex_io.load(str(used), cache=False)
    scitex_io.load(str(unused), cache=False)
    out = tmp_path / "result.json"
    # Act
    scitex_io.save({"n": len(df_used)}, str(out), verbose=False, derived_from=[df_used])
    # Assert
    assert payloads[0][1]["derived_from"] == [os.path.realpath(used)]


def test_undeclared_save_carries_no_declaration(inputs, payloads, tmp_path):
    # Arrange: the saved object IS a loaded object -- still nothing inferred
    used, _ = inputs
    df = scitex_io.load(str(used), cache=False)
    out = tmp_path / "copy.csv"
    # Act
    scitex_io.save(df, str(out), verbose=False, index=False)
    # Assert
    assert "derived_from" not in payloads[0][1]


def test_declaration_is_not_passed_to_the_format_handler(hooks, inputs, tmp_path):
    # Arrange: a strict saver that rejects unknown kwargs
    received = {}

    def _strict(obj, spath, **kwargs):
        received.update(kwargs)
        with open(spath, "w") as f:
            f.write(str(obj))

    register_saver(".dftest", _strict)
    used, _ = inputs
    try:
        # Act
        scitex_io.save(
            "x", str(tmp_path / "o.dftest"), verbose=False, derived_from=[used]
        )
    finally:
        unregister_saver(".dftest")
    # Assert
    assert "derived_from" not in received


def test_sidecars_carry_the_same_declaration(hooks, inputs, tmp_path):
    # Arrange
    def _with_sidecar(obj, spath, **kwargs):
        with open(spath, "w") as f:
            f.write(str(obj))
        with open(os.path.splitext(spath)[0] + ".meta.json", "w") as f:
            json.dump({}, f)

    register_saver(".dfside", _with_sidecar)
    seen = []
    register_post_save_hook(lambda p, obj, kw: seen.append(kw.get("derived_from")))
    used, _ = inputs
    try:
        # Act
        scitex_io.save(
            "x", str(tmp_path / "o.dfside"), verbose=False, derived_from=[used]
        )
    finally:
        unregister_saver(".dfside")
    # Assert
    assert seen == [[os.path.realpath(used)]] * 2


def _raised(fn):
    """Run ``fn``; return the exception type it raised (None if it returned)."""
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - the type IS the observation
        return type(exc)
    return None


def test_unknown_object_fails_before_writing(payloads, tmp_path):
    # Arrange: a DataFrame never returned by load has no known source
    out = tmp_path / "never.json"
    # Act
    raised = _raised(
        lambda: scitex_io.save(
            {"a": 1}, str(out), verbose=False, derived_from=[pd.DataFrame()]
        )
    )
    # Assert
    assert (raised, out.exists(), payloads) == (TypeError, False, [])


def test_loaded_dict_is_never_resolved_by_id(tmp_path):
    # Arrange: dicts cannot be weakly referenced -> must not be resolvable
    src = tmp_path / "cfg.json"
    src.write_text('{"k": 1}')
    cfg = scitex_io.load(str(src), cache=False)
    # Act
    raised = _raised(lambda: resolve_derived_from([cfg]))
    # Assert
    assert (raised, loaded_from(cfg)) == (TypeError, None)


def test_missing_path_fails(tmp_path):
    # Arrange
    missing = tmp_path / "nope.csv"
    # Act
    raised = _raised(lambda: resolve_derived_from([missing]))
    # Assert
    assert raised is FileNotFoundError


def test_registry_entry_dies_with_its_object(inputs):
    # Arrange
    used, _ = inputs
    df = scitex_io.load(str(used), cache=False)
    key = id(df)
    from scitex_io import _derived_from

    # Act
    del df
    gc.collect()
    # Assert
    assert key not in _derived_from._LOADED


def test_single_path_and_empty_list_are_valid(inputs):
    # Arrange
    used, _ = inputs
    # Act
    observed = (resolve_derived_from(str(used)), resolve_derived_from([]))
    # Assert
    assert observed == ([os.path.realpath(used)], [])


def test_symlinked_path_resolves_to_its_target(inputs, tmp_path):
    # Arrange
    used, _ = inputs
    link = tmp_path / "link.csv"
    link.symlink_to(used)
    # Act
    observed = resolve_derived_from([link, used])
    # Assert: deduplicated on realpath
    assert observed == [os.path.realpath(used)]


# EOF
