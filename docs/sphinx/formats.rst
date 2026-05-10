Supported Formats
=================

scitex-io supports **30+ file formats** out of the box. Format is determined
automatically from the file extension.

Format Table
------------

.. list-table:: **Table 1.** Built-in formats. All formats use the same ``save()``/``load()`` API.
   :header-rows: 1
   :widths: 20 20 10 10 40

   * - Category
     - Extensions
     - Save
     - Load
     - Backend
   * - **Spreadsheet**
     - ``.csv``, ``.tsv``
     - Yes
     - Yes
     - pandas
   * - **Excel**
     - ``.xlsx``, ``.xls``, ``.xlsm``, ``.xlsb``
     - ``.xlsx``/``.xls`` only
     - Yes
     - openpyxl / xlrd
   * - **Columnar**
     - ``.parquet``, ``.feather``
     - Yes
     - Yes
     - pyarrow / fastparquet
   * - **NumPy**
     - ``.npy``, ``.npz``
     - Yes
     - Yes
     - numpy
   * - **HDF5**
     - ``.hdf5``, ``.h5``
     - Yes
     - Yes
     - h5py
   * - **Zarr**
     - ``.zarr``
     - Yes
     - Yes
     - zarr
   * - **MATLAB**
     - ``.mat``
     - Yes
     - Yes
     - scipy.io
   * - **Pickle**
     - ``.pkl``, ``.pickle``, ``.pkl.gz``
     - Yes
     - Yes
     - pickle / gzip
   * - **Joblib**
     - ``.joblib``
     - Yes
     - Yes
     - joblib
   * - **PyTorch**
     - ``.pth``, ``.pt``
     - Yes
     - Yes
     - torch
   * - **CatBoost**
     - ``.cbm``
     - Yes
     - No
     - catboost
   * - **JSON**
     - ``.json``
     - Yes
     - Yes
     - json (stdlib)
   * - **YAML**
     - ``.yaml``, ``.yml``
     - Yes
     - Yes
     - PyYAML
   * - **Text**
     - ``.txt``, ``.md``, ``.log``, ``.event``, ``.py``, ``.sh``
     - Yes (``.txt``, ``.md``, ``.py``)
     - Yes
     - built-in open()
   * - **PDF**
     - ``.pdf``
     - Yes (figures)
     - Yes (text extract)
     - matplotlib / pdfplumber
   * - **Word**
     - ``.docx``
     - No
     - Yes
     - python-docx
   * - **Code**
     - ``.css``, ``.js``
     - Yes
     - No
     - built-in open()
   * - **Images**
     - ``.png``, ``.jpg``, ``.jpeg``, ``.gif``, ``.tiff``, ``.tif``, ``.svg``
     - Yes
     - Yes
     - PIL / matplotlib
   * - **Video**
     - ``.mp4``
     - Yes
     - No
     - matplotlib.animation
   * - **HTML**
     - ``.html``
     - Yes
     - No
     - built-in
   * - **LaTeX**
     - ``.tex``
     - Yes
     - No
     - built-in
   * - **BibTeX**
     - ``.bib``
     - Yes
     - Yes
     - bibtexparser
   * - **SQLite**
     - ``.db``
     - No
     - Yes
     - sqlite3 (stdlib)
   * - **XML**
     - ``.xml``
     - No
     - Yes
     - xml.etree (stdlib)
   * - **Optuna**
     - (study objects)
     - Yes
     - Yes
     - optuna
   * - **EEG**
     - ``.vhdr``, ``.vmrk``, ``.edf``, ``.bdf``, ``.gdf``, ``.cnt``, ``.egi``, ``.eeg``, ``.set``, ``.con``
     - No
     - Yes
     - mne


Two-Tier Registry
-----------------

.. code-block:: text

   ┌──────────────────────────────────────────┐
   │           Format Lookup Order             │
   ├──────────────────────────────────────────┤
   │  1. User-registered handlers  (priority) │
   │  2. Built-in handlers         (fallback) │
   └──────────────────────────────────────────┘

User handlers always take precedence. This means you can:

- **Override** a built-in format (e.g., use a custom CSV parser)
- **Extend** with new formats (e.g., ``.arrow``, ``.orc``, custom binary)
- **Swap** backends without changing calling code


Optional Dependencies
---------------------

Not all backends are installed by default. If a format's backend is missing,
``save()``/``load()`` will raise an ``ImportError`` with installation instructions.

.. code-block:: python

   >>> load("data.hdf5")
   ImportError: h5py is required for HDF5 support.
   Install with: pip install h5py
