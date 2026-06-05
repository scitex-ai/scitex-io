Interactive Explorers
=====================

scitex-io includes interactive explorers for hierarchical data formats.
These let you browse complex files without loading everything into memory.

H5Explorer
----------

Browse HDF5 files interactively:

.. code-block:: python

   from scitex_io import H5Explorer

   explorer = H5Explorer("experiment.hdf5")

   # List all keys at root level
   explorer.keys()

   # Navigate into groups
   explorer["recordings"].keys()

   # Load specific datasets
   data = explorer["recordings/channel_01"][:]

   # Check if a key exists
   from scitex_io import has_h5_key
   if has_h5_key("experiment.hdf5", "recordings/channel_01"):
       data = explorer["recordings/channel_01"][:]

.. note::

   Requires ``h5py``: ``pip install h5py``

ZarrExplorer
------------

Browse Zarr stores interactively:

.. code-block:: python

   from scitex_io import ZarrExplorer

   explorer = ZarrExplorer("experiment.zarr")

   # List all arrays/groups
   explorer.keys()

   # Load specific arrays
   data = explorer["timeseries"][:]

.. note::

   Requires ``zarr``: ``pip install zarr``

Migration: HDF5 to Zarr
------------------------

Convert HDF5 files to Zarr format for better cloud and parallel access:

.. code-block:: python

   from scitex_io.utils import migrate_h5_to_zarr, migrate_h5_to_zarr_batch

   # Single file
   migrate_h5_to_zarr("data.hdf5", "data.zarr")

   # Batch conversion
   migrate_h5_to_zarr_batch("data_dir/", "zarr_dir/")
