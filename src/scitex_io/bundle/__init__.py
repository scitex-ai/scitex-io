#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""``scitex_io.bundle`` — the multi-kind bundle dispatcher.

This package owns the bundle plumbing (types, dataclasses, manifest,
storage, zip, validation) AND the dispatcher (Bundle class, load/save/
validate, kind handlers). Domain-coupled kinds (figure, plot, stats)
keep their handlers here but import their domain dataclasses (figrecipe,
scitex_stats) lazily — installing each ecosystem package opens up its
kind; without the package, only pure-I/O kinds (image, text, shape,
table) are available.

The umbrella ``scitex.io.bundle`` is now a thin re-export of this
package.
"""

from . import _nested as nested  # noqa: F401
from ._Bundle import Bundle, create_bundle, from_matplotlib, load_bundle  # noqa: F401
from ._core import (  # noqa: F401
    copy,
    dir_to_zip_path,
    get_type,
    is_bundle,
    load,
    pack,
    save,
    unpack,
    validate,
    validate_spec,
    zip_to_dir_path,
)
from ._dataclasses import (  # noqa: F401
    DATA_INFO_VERSION,
    Axes,
    BBox,
    ColumnDef,
    DataFormat,
    DataInfo,
    DataSource,
    ShapeParams,
    SizeMM,
    Spec,
    SpecRefs,
    TextContent,
)
from ._manifest import (  # noqa: F401
    MANIFEST_FILENAME,
    create_manifest,
    get_type_from_manifest,
    read_manifest,
    write_manifest,
)
from ._storage import (  # noqa: F401
    DirStorage,
    Storage,
    ZipStorage,
    get_storage,
)
from ._types import (  # noqa: F401
    DIR_EXTENSIONS,
    EXTENSIONS,
    FIGURE,
    PLOT,
    STATS,
    BundleError,
    BundleNotFoundError,
    BundleType,
    BundleValidationError,
    NestedBundleNotFoundError,
)
from ._validation import (  # noqa: F401
    SCHEMA_DIR,
    SCHEMA_VERSION,
    ValidationResult,
    load_schema,
    validate_bundle,
    validate_data_info,
    validate_encoding,
    validate_schema,
    validate_semantic,
    validate_stats,
    validate_strict,
    validate_theme,
)
from ._zip import (  # noqa: F401
    ZipBundle,
    zip_directory,
)
from ._zip import (
    create as create_zip,
)
from ._zip import (
    open as open_zip,
)

__all__ = [
    # Bundle dispatcher / class.
    "Bundle",
    "load_bundle",
    "create_bundle",
    "from_matplotlib",
    "load",
    "save",
    "copy",
    "pack",
    "unpack",
    "validate",
    "validate_spec",
    "is_bundle",
    "get_type",
    "dir_to_zip_path",
    "zip_to_dir_path",
    # Types.
    "BundleType",
    "BundleError",
    "BundleValidationError",
    "BundleNotFoundError",
    "NestedBundleNotFoundError",
    "EXTENSIONS",
    "DIR_EXTENSIONS",
    "FIGURE",
    "PLOT",
    "STATS",
    # Dataclasses.
    "BBox",
    "SizeMM",
    "Axes",
    "Spec",
    "SpecRefs",
    "TextContent",
    "ShapeParams",
    "DATA_INFO_VERSION",
    "DataSource",
    "DataFormat",
    "DataInfo",
    "ColumnDef",
    # Manifest.
    "MANIFEST_FILENAME",
    "create_manifest",
    "get_type_from_manifest",
    "read_manifest",
    "write_manifest",
    # Storage.
    "Storage",
    "ZipStorage",
    "DirStorage",
    "get_storage",
    # Zip.
    "ZipBundle",
    "open_zip",
    "create_zip",
    "zip_directory",
    # Validation.
    "SCHEMA_DIR",
    "SCHEMA_VERSION",
    "ValidationResult",
    "load_schema",
    "validate_bundle",
    "validate_data_info",
    "validate_encoding",
    "validate_schema",
    "validate_semantic",
    "validate_stats",
    "validate_strict",
    "validate_theme",
    # Nested namespace.
    "nested",
]
