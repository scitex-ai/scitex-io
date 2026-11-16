Examples
========

scitex-io ships with example scripts in the ``examples/`` directory.
Run them all at once:

.. code-block:: bash

   cd examples/
   ./00_run_all.sh

Example 1: Basic Save/Load
---------------------------

Save and load common scientific data formats.

.. code-block:: python

   from scitex_io import save, load
   import numpy as np

   # NumPy array
   arr = np.arange(12).reshape(3, 4)
   save(arr, "array.npy")
   loaded = load("array.npy")
   assert (loaded == arr).all()

   # Dictionary as JSON
   config = {"learning_rate": 0.001, "epochs": 100, "model": "resnet"}
   save(config, "config.json")
   assert load("config.json")["learning_rate"] == 0.001

   # Dictionary as YAML
   save(config, "config.yaml")

   # CSV via pandas
   import pandas as pd
   df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
   save(df, "data.csv")

Output saved to ``examples/01_basic_save_load_out/``:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - File
     - Content
   * - ``array.npy``
     - 3x4 NumPy array
   * - ``config.json``
     - Training configuration
   * - ``config.yaml``
     - Same config in YAML format
   * - ``data.csv``
     - Simple DataFrame


Example 2: Custom Format
-------------------------

Register and use a custom format handler.

.. code-block:: python

   from scitex_io import register_saver, register_loader, save, load

   @register_saver(".tsv3")
   def save_tsv3(obj, path, **kwargs):
       with open(path, "w") as f:
           for row in obj:
               f.write("   ".join(str(v) for v in row) + "\n")

   @register_loader(".tsv3")
   def load_tsv3(path, **kwargs):
       with open(path) as f:
           return [line.strip().split("   ") for line in f]

   data = [["Alice", "30"], ["Bob", "25"]]
   save(data, "custom.tsv3")
   assert load("custom.tsv3") == data

Output saved to ``examples/02_custom_format_out/custom.tsv3``.


Example 3: Project Configuration
----------------------------------

Centralize hard-coded parameters (magic numbers) in YAML config files.
Convention: use **UPPER_CASE** for config keys to signal user-defined constants.

.. code-block:: text

   project/
     config/
       PATHS.yaml          # DATA_DIR: /data/experiment_01
       PREPROCESS.yaml     # SAMPLE_RATE: 1000, BANDPASS: [0.5, 40]
       MODEL.yaml          # HIDDEN_DIM: 256, DEBUG_HIDDEN_DIM: 32
       IS_DEBUG.yaml       # IS_DEBUG: false

.. code-block:: python

   from scitex_io import load_configs

   # Load all YAML files at once — namespaced by filename
   CONFIG = load_configs(config_dir="./config")

   CONFIG.PATHS.DATA_DIR            # "/data/experiment_01"
   CONFIG.PREPROCESS.SAMPLE_RATE    # 1000
   CONFIG.MODEL.HIDDEN_DIM          # 256

   # Debug mode promotes DEBUG_ prefixed keys
   CONFIG = load_configs(config_dir="./config", IS_DEBUG=True)
   CONFIG.MODEL.HIDDEN_DIM          # 32

   # Export merged config for reproducibility
   save(CONFIG.to_dict(), "merged_config.json")

Run the full example:

.. code-block:: bash

   python3 examples/03_load_configs.py


Example 4: DotDict
--------------------

``DotDict`` is the return type of ``load_configs()``. It wraps nested dictionaries
with dot-notation access:

.. code-block:: python

   from scitex_io import DotDict

   PARAMS = DotDict({
       "MODEL": {"HIDDEN_DIM": 256, "DROPOUT": 0.3},
       "TRAINING": {"BATCH_SIZE": 64, "EPOCHS": 100},
   })

   PARAMS.MODEL.HIDDEN_DIM       # 256
   PARAMS.TRAINING.BATCH_SIZE    # 64

   list(PARAMS.keys())           # ["MODEL", "TRAINING"]
   PARAMS.to_dict()              # plain dict for serialization

Run:

.. code-block:: bash

   python3 examples/04_dotdict.py


Example 5: Metadata Embedding
------------------------------

Embed provenance into figures so they carry their own history. Months later, you can
read metadata from the file alone — no external tracking needed.

.. code-block:: python

   from scitex_io import embed_metadata, read_metadata, has_metadata

   # Create a simple figure
   import matplotlib.pyplot as plt
   fig, ax = plt.subplots()
   ax.plot([1, 2, 3], [4, 5, 6])
   fig.savefig("figure.png")
   plt.close()

   # Embed experiment metadata into the PNG
   embed_metadata("figure.png", {
       "EXPERIMENT": "exp_042",
       "MODEL": "resnet50",
       "ACCURACY": 0.94,
       "TIMESTAMP": "2026-03-11",
   })

   # Verify metadata was embedded
   assert has_metadata("figure.png")

   # Read it back
   meta = read_metadata("figure.png")
   assert meta["EXPERIMENT"] == "exp_042"
   assert meta["ACCURACY"] == "0.94"   # stored as string in PNG tEXt

Supported formats:

.. list-table::
   :header-rows: 1
   :widths: 20 40

   * - Format
     - Storage mechanism
   * - PNG
     - tEXt chunks
   * - JPEG
     - EXIF UserComment
   * - SVG
     - XML ``<metadata>`` element
   * - PDF
     - Info Dictionary

Run:

.. code-block:: bash

   python3 examples/05_metadata_embedding.py


Part of SciTeX
--------------

When used inside the `SciTeX framework <https://scitex.ai>`_, I/O is
automatically tracked for reproducibility:

.. code-block:: python

   import scitex

   @scitex.session
   def main(CONFIG=scitex.session.INJECTED):
       data = scitex.io.load("input.csv")     # auto-tracked by clew
       result = process(data)
       scitex.io.save(result, "output.csv")   # auto-tracked by clew
       return 0

``scitex.io`` delegates to ``scitex_io`` — they share the same API and registry.
