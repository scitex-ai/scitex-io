#!/usr/bin/env python3
"""REFERENCE per-edge integration + degradation tests (figrecipe edge).

This file is the **canonical example** for testing an integration edge to an
*optional* dependency in the SciTeX ecosystem. Copy this pattern for any other
package that wires into an optional collaborator (plotly, h5py, torch, ...).

The edge under test
-------------------
``scitex_io.save(fig, "plot.png")`` where ``fig`` is a figrecipe
``RecordingFigure``. figrecipe is an OPTIONAL dependency of scitex-io: when it
is installed, ``save`` produces the image plus a reproducible recipe and the
per-series CSV data sidecars; when it is absent, ``save`` must still degrade
gracefully rather than blowing up the caller with an opaque traceback.

The two test kinds every optional edge should have
--------------------------------------------------
1. INTEGRATION (collaborator PRESENT): exercise the real collaborator and
   assert on the concrete artifacts it produces. Guard with
   ``pytest.importorskip("figrecipe")`` so the suite stays green on minimal
   installs instead of erroring.

2. DEGRADATION (collaborator ABSENT): simulate the dependency being missing in
   a hermetic, reversible way (here: a fixture that sets
   ``sys.modules["figrecipe"] = None`` and reloads the affected modules), then
   assert that the *non-figrecipe* paths keep working and that the
   figrecipe-requiring path fails through the documented, caller-safe contract
   (``save`` returns the ``False`` sentinel) instead of leaking a raw
   ``ImportError`` / ``AttributeError``.

Conventions honoured (so this stays a clean template):
  - One assertion per test (TQ007): the shared, expensive setup (the actual
    ``save``) is lifted into a fixture; each behaviour gets its own named,
    single-assert test, so a red CI line names exactly what broke.
  - Explicit Arrange / Act / Assert markers in every test (TQ002).
  - No ``monkeypatch`` / ``mocker`` (banned by conftest): the figrecipe-absent
    fixture hand-swaps ``sys.modules`` and restores it on teardown.

Empirically verified artifacts (figrecipe present)
---------------------------------------------------
``scitex_io.save(fig, "<stem>.png")`` for a figrecipe ``RecordingFigure``
writes, alongside the PNG:
  - ``<stem>.png``                       the rendered image
  - ``<stem>.yaml``                      the reproducible figrecipe recipe
  - ``<stem>_data/<stem>_000_x.csv``     per-series x data (one col, no header)
  - ``<stem>_data/<stem>_000_y.csv``     per-series y data (one col, no header)
"""

from __future__ import annotations

import importlib
import os
import sys

import pytest

# ===========================================================================
# 1. INTEGRATION  —  figrecipe PRESENT
# ===========================================================================
figrecipe = pytest.importorskip("figrecipe")


class _SavedFigure:
    """Locations of the artifacts a save() produced (lifted shared setup)."""

    def __init__(self, tmp_path, result, stem):
        self.result = result
        self.png = tmp_path / f"{stem}.png"
        self.yaml = tmp_path / f"{stem}.yaml"
        self.data_dir = tmp_path / f"{stem}_data"


@pytest.fixture
def saved_recording_figure(tmp_path):
    """save() a real figrecipe RecordingFigure once; yield the artifact paths."""
    import scitex_io

    fig, ax = figrecipe.subplots()
    ax.plot([0, 1, 2, 3], [10, 20, 15, 25], label="series1")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    result = scitex_io.save(fig, str(tmp_path / "plot.png"), verbose=False)
    return _SavedFigure(tmp_path, result, "plot")


def test_save_recording_figure_returns_non_false(saved_recording_figure):
    """save() succeeds (returns the saved path, not the False sentinel)."""
    # Arrange
    out = saved_recording_figure
    # Act
    result = out.result
    # Assert
    assert result is not False


def test_save_recording_figure_writes_png(saved_recording_figure):
    """The rendered PNG image is written."""
    # Arrange
    out = saved_recording_figure
    # Act
    exists = out.png.exists()
    # Assert
    assert exists


def test_save_recording_figure_writes_yaml_recipe(saved_recording_figure):
    """A figrecipe recipe lands next to the PNG as <stem>.yaml."""
    # Arrange
    out = saved_recording_figure
    # Act
    exists = out.yaml.exists()
    # Assert
    assert exists


def test_save_recording_figure_creates_data_sidecar_dir(saved_recording_figure):
    """Per-series CSV data goes into a <stem>_data/ sidecar directory."""
    # Arrange
    out = saved_recording_figure
    # Act
    is_dir = out.data_dir.is_dir()
    # Assert
    assert is_dir


def test_save_recording_figure_writes_csv_sidecars(saved_recording_figure):
    """At least one CSV data file is written into the sidecar directory."""
    # Arrange
    out = saved_recording_figure
    # Act
    csvs = sorted(p.name for p in out.data_dir.glob("*.csv"))
    # Assert
    assert csvs


def test_save_recording_figure_x_csv_matches_plotted_data(saved_recording_figure):
    """The x CSV sidecar holds exactly the x values we plotted."""
    # Arrange
    x_csv = saved_recording_figure.data_dir / "plot_000_x.csv"
    # Act
    x_vals = [
        float(line.strip()) for line in x_csv.read_text().splitlines() if line.strip()
    ]
    # Assert
    assert x_vals == [0.0, 1.0, 2.0, 3.0]


def test_save_recording_figure_y_csv_matches_plotted_data(saved_recording_figure):
    """The y CSV sidecar holds exactly the y values we plotted."""
    # Arrange
    y_csv = saved_recording_figure.data_dir / "plot_000_y.csv"
    # Act
    y_vals = [
        float(line.strip()) for line in y_csv.read_text().splitlines() if line.strip()
    ]
    # Assert
    assert y_vals == [10.0, 20.0, 15.0, 25.0]


def test_save_recording_figure_yaml_is_a_figrecipe_recipe(saved_recording_figure):
    """The .yaml sidecar is a genuine figrecipe recipe (carries the schema key)."""
    # Arrange
    out = saved_recording_figure
    # Act
    recipe_text = out.yaml.read_text()
    # Assert
    assert "figrecipe:" in recipe_text


# ===========================================================================
# 2. DEGRADATION  —  figrecipe ABSENT
# ===========================================================================
@pytest.fixture
def figrecipe_absent():
    """Make ``import figrecipe`` fail for the duration of the test.

    Hermetic and reversible:
      1. snapshot the whole ``sys.modules`` so teardown can restore it exactly;
      2. pre-import the figrecipe-aware scitex plotting shim (``scitex_plt``)
         so it is fully cached. ``scitex_plt`` re-imports figrecipe at its
         module top level, and ``scitex_io.save``'s error path runs
         ``inspect.stack()``, which walks frame source files and can re-execute
         a *not-yet-cached* module. Pre-caching it means that walk never tries
         to re-run its body under the missing dependency;
      3. evict ``figrecipe`` (and the scitex_io save stack) and shadow
         ``figrecipe`` with ``None`` so a *fresh* ``import figrecipe`` raises
         ImportError, then reload ``scitex_io`` so it re-runs its
         optional-import guards under the missing dependency. Already-cached
         consumers keep the reference they captured before the shim.

    Yields the freshly reloaded top-level ``scitex_io`` module.
    """
    import scitex_io  # noqa: F401  (ensure importable before we tear it down)

    # 1. Full snapshot for an exact restore.
    snapshot = dict(sys.modules)

    # 2. Replace scitex_plt with an inert stub *module* (not None). scitex_plt
    #    re-imports figrecipe at its top level, and scitex_io.save's error path
    #    runs inspect.stack(), which walks frame source files via
    #    inspect.getmodule and can re-execute a module body. A real (but empty)
    #    module object satisfies that walk without ever importing figrecipe,
    #    whereas a None entry would raise "import halted; None in sys.modules".
    import types

    stub_plt = types.ModuleType("scitex_plt")
    stub_plt.__file__ = "<scitex_plt stub: figrecipe absent>"
    for name in [
        n for n in list(sys.modules) if n == "scitex_plt" or n.startswith("scitex_plt.")
    ]:
        del sys.modules[name]
    sys.modules["scitex_plt"] = stub_plt

    # 3. Evict figrecipe + the scitex_io save stack, then block figrecipe.
    def _to_evict(name: str) -> bool:
        return (
            name == "figrecipe"
            or name.startswith("figrecipe.")
            or name == "scitex_io"
            or name.startswith("scitex_io.")
        )

    for name in [n for n in list(sys.modules) if _to_evict(n)]:
        del sys.modules[name]
    sys.modules["figrecipe"] = None  # type: ignore[assignment]
    reloaded = importlib.import_module("scitex_io")

    try:
        yield reloaded
    finally:
        # Restore the exact pre-test module table: drop anything we added or
        # that got (re)imported during the test, then reinstate the snapshot.
        for name in list(sys.modules):
            if name not in snapshot:
                del sys.modules[name]
        sys.modules.update(snapshot)


def test_figrecipe_absent_fixture_blocks_the_import(figrecipe_absent):
    """Sanity: under the fixture, ``import figrecipe`` really does fail."""
    # Arrange
    _ = figrecipe_absent
    # Act
    module_name = "figrecipe"
    # Assert
    with pytest.raises(ImportError):
        importlib.import_module(module_name)


def test_plain_object_still_saves_without_figrecipe(figrecipe_absent, tmp_path):
    """A non-figure object (the common case) is unaffected by figrecipe absence."""
    # Arrange
    spath = str(tmp_path / "data.json")
    # Act
    result = figrecipe_absent.save({"a": [1, 2, 3], "b": "ok"}, spath, verbose=False)
    # Assert
    assert result is not False


def test_plain_object_save_writes_file_without_figrecipe(figrecipe_absent, tmp_path):
    """The non-figure save actually lands a file on disk."""
    # Arrange
    spath = str(tmp_path / "data.json")
    # Act
    figrecipe_absent.save({"a": [1, 2, 3], "b": "ok"}, spath, verbose=False)
    # Assert
    assert os.path.exists(spath)


@pytest.fixture
def saved_plain_mpl_figure(figrecipe_absent, tmp_path):
    """save() a bare matplotlib figure with figrecipe absent; yield artifacts."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [3, 4, 5])
    result = figrecipe_absent.save(fig, str(tmp_path / "mpl.png"), verbose=False)
    # NB: deliberately do NOT call plt.close(fig) here. figrecipe patches
    # plt.close at import time; with figrecipe shimmed out of sys.modules,
    # the patched close re-imports figrecipe internals and explodes. The
    # stray Agg figure is harmless and is reaped at process teardown.
    return _SavedFigure(tmp_path, result, "mpl")


def test_plain_mpl_figure_returns_non_false_without_figrecipe(
    saved_plain_mpl_figure,
):
    """A bare matplotlib figure still saves successfully without figrecipe."""
    # Arrange
    out = saved_plain_mpl_figure
    # Act
    result = out.result
    # Assert
    assert result is not False


def test_plain_mpl_figure_writes_png_without_figrecipe(saved_plain_mpl_figure):
    """The PNG is rendered by matplotlib regardless of figrecipe."""
    # Arrange
    out = saved_plain_mpl_figure
    # Act
    exists = out.png.exists()
    # Assert
    assert exists


def test_plain_mpl_figure_writes_no_recipe_without_figrecipe(
    saved_plain_mpl_figure,
):
    """No .yaml recipe is produced — that sidecar requires figrecipe."""
    # Arrange
    out = saved_plain_mpl_figure
    # Act
    exists = out.yaml.exists()
    # Assert
    assert not exists


def test_plain_mpl_figure_writes_no_data_dir_without_figrecipe(
    saved_plain_mpl_figure,
):
    """No CSV data sidecar dir is produced — that requires figrecipe."""
    # Arrange
    out = saved_plain_mpl_figure
    # Act
    exists = out.data_dir.exists()
    # Assert
    assert not exists


@pytest.fixture
def saved_figrecipe_only_object(figrecipe_absent, tmp_path):
    """Attempt to save a figrecipe-requiring object while figrecipe is absent.

    The object mimics a figrecipe RecordingFigure (it carries ``save_recipe``
    and ``savefig``) but has no working backend, so the save must fail. The
    contract is that ``save`` fails loudly (raises) rather than letting the
    caller continue with a falsy sentinel as if everything had worked.
    (Fail-loud-fail-early policy, 2026-06-01.)
    """

    class FakeRecordingFigure:
        save_recipe = True

        def savefig(self, *args, **kwargs):
            raise RuntimeError("figrecipe backend unavailable")

    spath = str(tmp_path / "fake.png")
    exc: Exception | None = None
    try:
        figrecipe_absent.save(FakeRecordingFigure(), spath, verbose=False)
    except Exception as e:  # noqa: BLE001 — fixture captures whatever raised
        exc = e

    class _Out:
        def __init__(self):
            self.exc = exc
            self.png = tmp_path / "fake.png"

    return _Out()


def test_figrecipe_only_object_raises(saved_figrecipe_only_object):
    """save() raises when its underlying recorder has no working backend."""
    # Arrange
    out = saved_figrecipe_only_object
    # Act
    captured = out.exc
    # Assert — must have raised (fail-loud-fail-early policy)
    assert captured is not None


def test_figrecipe_only_object_writes_no_file(saved_figrecipe_only_object):
    """A failed save leaves no half-written image behind."""
    # Arrange
    out = saved_figrecipe_only_object
    # Act
    exists = out.png.exists()
    # Assert
    assert not exists
