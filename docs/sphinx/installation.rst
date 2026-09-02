Installation
============

Requirements
------------

- Python >= 3.9

Basic Installation
------------------

.. code-block:: bash

   pip install scitex-io

This installs the core I/O engine with support for common formats
(CSV, JSON, NumPy, pickle, text, YAML, etc.).

With MCP Server
---------------

.. code-block:: bash

   pip install scitex-io[mcp]

Adds `FastMCP <https://github.com/jlowin/fastmcp>`_ for AI agent integration.

Full Installation
-----------------

.. code-block:: bash

   pip install scitex-io[all]

Installs all optional dependencies for maximum format coverage:

.. list-table:: **Optional dependency groups**
   :header-rows: 1
   :widths: 25 35 40

   * - Group
     - Command
     - What it adds
   * - Core
     - ``pip install scitex-io``
     - CSV, JSON, YAML, NPY, PKL, TXT
   * - MCP
     - ``pip install scitex-io[mcp]``
     - MCP server for AI agents
   * - All
     - ``pip install scitex-io[all]``
     - HDF5, Zarr, images, PDF, MATLAB, etc.

SciTeX Users
------------

If you use the main ``scitex`` framework, scitex-io is already included::

   pip install scitex

``scitex.io`` delegates directly to ``scitex_io`` — they share the same API
and format registry.

Development
-----------

.. code-block:: bash

   git clone https://github.com/scitex-ai/scitex-io.git
   cd scitex-io
   pip install -e ".[all]"
