MCP Server
==========

scitex-io provides a `Model Context Protocol <https://modelcontextprotocol.io/>`_ (MCP)
server, enabling AI agents to save, load, and discover file formats autonomously.

Installation
------------

.. code-block:: bash

   pip install scitex-io[mcp]

Starting the Server
-------------------

.. code-block:: bash

   scitex-io mcp start

MCP Client Configuration
-------------------------

Add to your MCP client configuration (e.g., Claude Desktop, Cursor):

.. code-block:: json

   {
     "mcpServers": {
       "scitex-io": {
         "command": "scitex-io",
         "args": ["mcp", "start"]
       }
     }
   }

Available Tools
---------------

.. list-table:: **Table 3.** MCP tools for AI-assisted file I/O. All tools accept JSON parameters and return JSON results.
   :header-rows: 1
   :widths: 25 75

   * - Tool
     - Description
   * - ``io_list_formats``
     - List all registered save/load format extensions
   * - ``io_load``
     - Load data from any supported file format. Returns type, shape, and preview.
   * - ``io_save``
     - Save data (as JSON string) to any supported format
   * - ``io_load_configs``
     - Load YAML project configurations from a directory. Returns namespaced config dict.
   * - ``io_register_info``
     - Show how to register custom format handlers with examples
   * - ``io_glob`` / ``io_parse_glob``
     - Natsort-ordered globbing; ``parse_glob`` extracts ``{placeholder}`` values
   * - ``io_get_loader`` / ``io_get_saver``
     - Look up the registered handler function for a given extension
   * - ``io_read_metadata`` / ``io_has_metadata`` / ``io_embed_metadata``
     - Inspect / verify / write provenance metadata embedded in PNG/JPEG by ``io_save``
   * - ``io_get_cache_info`` / ``io_clear_load_cache`` / ``io_configure_cache``
     - Inspect, clear, or reconfigure the load-side cache
   * - ``io_explore_h5`` / ``io_explore_zarr``
     - Print group/dataset trees for HDF5 and Zarr stores
   * - ``io_has_h5_key`` / ``io_has_zarr_key``
     - Cheap existence check for a key inside an HDF5 file or Zarr store
   * - ``io_json2md``
     - Render a JSON object as Markdown headings + bullet lists
   * - ``io_skills_list`` / ``io_skills_get``
     - Discover and fetch the skill pages shipped with scitex-io

Tool Details
------------

**io_load**

.. code-block:: json

   {
     "path": "/data/experiment.csv",
     "format": null,
     "cache": true
   }

Returns shape/length, type name, and a truncated preview of the loaded data.

**io_save**

.. code-block:: json

   {
     "data_json": "{\"x\": [1, 2, 3], \"y\": [4, 5, 6]}",
     "path": "/data/output.json",
     "verbose": false
   }

Diagnostics
-----------

.. code-block:: bash

   scitex-io mcp doctor          # Check MCP dependencies
   scitex-io mcp list-tools      # List available tools
   scitex-io mcp list-tools -vv  # With full parameter descriptions
