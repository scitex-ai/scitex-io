Quickstart
==========

Save and Load
-------------

Format is auto-detected from the file extension:

.. code-block:: python

   from scitex_io import save, load

   # DataFrames
   import pandas as pd
   df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
   save(df, "data.csv")
   loaded = load("data.csv")

   # NumPy arrays
   import numpy as np
   save(np.array([1, 2, 3]), "data.npy")

   # Dictionaries
   save({"key": "value"}, "config.yaml")
   save({"nested": [1, 2]}, "data.json")

   # Any Python object
   save({"complex": object()}, "data.pkl")

One function for save, one for load — 30+ formats work the same way.


Editing ZIP Bundles
-------------------

``scitex_io.bundle.ZipBundle`` edits named members without interpreting their
schema. Append mode retains untouched payloads, their ZIP metadata and the
archive comment. Repeated writes to one name commit its final value once.
An exception or explicit ``close()`` discards pending changes; ``mode="w"``
intentionally replaces the archive contents.

This example uses a temporary directory and leaves existing research files alone:

.. code-block:: python

   from pathlib import Path
   from tempfile import TemporaryDirectory
   from scitex_io.bundle import ZipBundle

   with TemporaryDirectory() as directory:
       path = Path(directory) / "example.plot.zip"
       with ZipBundle(path, "w") as bundle:
           bundle.write_json("spec.json", {"title": "Initial"})
           bundle.write_bytes("payload/data.csv", b"x,y\n1,2\n")
       with ZipBundle(path, "a") as bundle:
           spec = bundle.read_json()
           spec["title"] = "Updated"
           bundle.write_json("spec.json", spec)
       with ZipBundle(path) as bundle:
           assert bundle.read_json()["title"] == "Updated"
           assert bundle.read_bytes("payload/data.csv") == b"x,y\n1,2\n"


List Available Formats
----------------------

.. code-block:: python

   from scitex_io import list_formats

   formats = list_formats()
   print(f"Save: {len(formats['save']['builtin'])} built-in formats")
   print(f"Load: {len(formats['load']['builtin'])} built-in formats")

.. code-block:: text

   Save: 24 built-in formats
   Load: 29 built-in formats


Custom Format Registration
--------------------------

Register handlers for any file extension:

.. code-block:: python

   from scitex_io import register_saver, register_loader, save, load

   @register_saver(".tsv3")
   def save_tsv3(obj, path, **kwargs):
       """Save with 3-space-separated values."""
       with open(path, "w") as f:
           for row in obj:
               f.write("   ".join(str(v) for v in row) + "\n")

   @register_loader(".tsv3")
   def load_tsv3(path, **kwargs):
       """Load 3-space-separated values."""
       with open(path) as f:
           return [line.strip().split("   ") for line in f]

   # Now .tsv3 works like any built-in format
   save([[1, 2], [3, 4]], "data.tsv3")
   assert load("data.tsv3") == [["1", "2"], ["3", "4"]]

.. note::

   User-registered handlers take priority over built-in ones for the same
   extension. This lets you override default behavior without modifying
   the library.


Project Configuration
---------------------

Most research projects have hard-coded parameters scattered across scripts — sample rates,
thresholds, model hyperparameters, plot dimensions. ``load_configs`` centralizes them in
YAML files under a ``config/`` directory:

.. code-block:: text

   project/
     config/
       PATHS.yaml          # DATA_DIR: /data/experiment_01
       PREPROCESS.yaml     # SAMPLE_RATE: 1000, BANDPASS: [0.5, 40]
       MODEL.yaml          # HIDDEN_DIM: 256, DROPOUT: 0.3
       PLOT.yaml           # FIGSIZE: [180, 60], DPI: 300
       IS_DEBUG.yaml       # IS_DEBUG: true

.. code-block:: python

   from scitex_io import load_configs

   # One call loads all YAML files, namespaced by filename
   CONFIG = load_configs()                            # ./config/*.yaml
   CONFIG = load_configs(config_dir="./my_configs")   # custom path

   CONFIG.PATHS.DATA_DIR            # "/data/experiment_01"
   CONFIG.PREPROCESS.SAMPLE_RATE    # 1000
   CONFIG.MODEL.HIDDEN_DIM          # 256

   # Debug mode: keys prefixed with DEBUG_ override their counterparts
   # In MODEL.yaml:  HIDDEN_DIM: 256, DEBUG_HIDDEN_DIM: 32
   CONFIG = load_configs(IS_DEBUG=True)
   CONFIG.MODEL.HIDDEN_DIM          # 32 (debug value promoted)

Returns a ``DotDict`` — a nested dictionary with dot-notation access. Config keys should
use **UPPER_CASE** to signal that they are user-defined constants, not runtime variables.


DotDict
-------

``DotDict`` gives dot-notation access to nested dictionaries:

.. code-block:: python

   from scitex_io import DotDict

   d = DotDict({"MODEL": {"HIDDEN_DIM": 256, "LAYERS": 4}})
   d.MODEL.HIDDEN_DIM    # 256
   d.MODEL.LAYERS        # 4

   # Standard dict operations work too
   d["MODEL"]["HIDDEN_DIM"]    # 256
   d.MODEL.keys()              # dict_keys(["HIDDEN_DIM", "LAYERS"])
   d.MODEL.to_dict()           # {"HIDDEN_DIM": 256, "LAYERS": 4}


Metadata Embedding
------------------

A saved PNG has no record of the code, parameters, or session that produced it.
``embed_metadata`` solves this by writing provenance directly into the file:

.. code-block:: python

   from scitex_io import embed_metadata, read_metadata, has_metadata

   # Embed metadata into a figure
   embed_metadata("figure.png", {
       "experiment": "exp_042",
       "model": "resnet50",
       "accuracy": 0.94,
       "timestamp": "2026-03-11",
   })

   # Read it back — months later, from the file alone
   meta = read_metadata("figure.png")
   meta["experiment"]    # "exp_042"

   # Check if a file carries metadata
   has_metadata("figure.png")   # True

Supports PNG (tEXt chunks), JPEG (EXIF), SVG (XML metadata), and PDF
(XMP metadata). The figure carries its own history — no external database needed.


Auto Path Routing
-----------------

When ``save()`` receives a relative path, the output directory is determined
automatically from the execution context:

.. list-table::
   :header-rows: 1
   :widths: 25 40 35

   * - Context
     - Output directory
     - Example
   * - Script ``analysis.py``
     - ``analysis_out/{path}``
     - ``analysis_out/results.csv``
   * - Notebook ``exp.ipynb``
     - ``exp_out/{path}``
     - ``exp_out/fig.png``
   * - Interactive / IPython
     - ``/tmp/{USER}/{path}``
     - ``/tmp/ywatanabe/data.csv``
   * - Absolute path
     - Used as-is
     - ``/data/output/results.csv``

.. code-block:: python

   # In ~/proj/scripts/analysis.py:
   save(df, "results.csv")
   # → ~/proj/scripts/analysis_out/results.csv

   # Absolute path bypasses routing:
   save(df, "/data/shared/results.csv")
   # → /data/shared/results.csv


Advanced Save Options
---------------------

.. code-block:: python

   from scitex_io import save

   # Symlink from cwd to saved file
   save(df, "results.csv", symlink_from_cwd=True)

   # Symlink at a specific path
   save(fig, "fig1.png", symlink_to="/data/latest/fig1.png")

   # Skip auto CSV export for image saves (default: images get .csv companion)
   save(fig, "plot.png", no_csv=True)

   # Resolve path from the calling script, not the immediate caller.
   # Essential when save() is called through library wrappers.
   save(df, "results.csv", use_caller_path=True)

   # Dry run — print resolved path without writing
   save(df, "results.csv", dry_run=True)


Glob and Pattern Matching
-------------------------

Natural-sorted file matching with named placeholder parsing:

.. code-block:: python

   from scitex_io import glob, parse_glob, load

   # Natural sort (1, 2, 10 — not 1, 10, 2)
   paths = glob("data/**/*.csv")

   # Brace expansion
   paths = glob("results/{exp1,exp2}/*.npy")

   # Parse named placeholders from paths
   paths, parsed = parse_glob("sub_{id}/ses_{session}/*.vhdr")
   # parsed = [{'id': '001', 'session': 'pre'}, ...]

   # Glob works directly in load()
   dfs = load("results/*.csv")  # → list of DataFrames


Caching
-------

Repeated loads are cached automatically by path + mtime:

.. code-block:: python

   from scitex_io import load, get_cache_info, configure_cache, clear_load_cache

   data1 = load("large_file.hdf5")   # reads from disk
   data2 = load("large_file.hdf5")   # returns cached copy (instant)

   info = get_cache_info()
   print(f"Cache hits: {info['stats']['hits']}, misses: {info['stats']['misses']}")

   configure_cache(max_size=64)  # increase cache size (default: 32)
   clear_load_cache()            # free memory
