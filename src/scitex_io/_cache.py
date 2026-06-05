#!./env/bin/python3
# -*- coding: utf-8 -*-
# Time-stamp: "2024-08-20 19:42:38 (ywatanabe)"
# ./src/scitex/io/_cache.py


import os as _os
import pickle
import sys
from pathlib import Path


def _default_cache_dir() -> Path:
    """Canonical cache directory for scitex-io.

    Returns ``$SCITEX_DIR/io/runtime/cache/`` (defaulting to
    ``~/.scitex/io/runtime/cache/``), creating it on first use.
    Follows the scitex local-state-directories convention — see
    scitex-dev skills/general ``01_ecosystem/06_local-state-directories.md`` §4c.
    """
    scitex_dir = _os.environ.get(
        "SCITEX_DIR",
        _os.path.join(_os.path.expanduser("~"), ".scitex"),
    )
    d = Path(scitex_dir) / "io" / "runtime" / "cache"
    d.mkdir(parents=True, exist_ok=True)
    return d


def cache(id, *args, cache_root=None):
    """Store or fetch data using a pickle file.

    This function provides a simple caching mechanism for storing and
    retrieving Python objects. It uses pickle to serialize the data
    and stores it in a file with a unique identifier. If the data is
    already cached, it can be retrieved without recomputation.

    :param id: A unique identifier for the cache file.
    :type id: str
    :param \\*args: Variable names to be cached or loaded.
    :type \\*args: str
    :param cache_root: Explicit cache directory. Defaults to
        ``$SCITEX_DIR/io/runtime/cache/`` (``~/.scitex/io/runtime/cache/``
        fallback), honouring the canonical scitex local-state convention.
    :type cache_root: Path or None, optional
    :returns: A tuple of cached values corresponding to the input variable names.
    :rtype: tuple
    :raises ValueError: If the cache file is not found and not all variables
        are defined.

    Example
    -------
    >>> import scitex
    >>> import numpy as np
    >>>
    >>> # Variables to cache
    >>> var1 = "x"
    >>> var2 = 1
    >>> var3 = np.ones(10)
    >>>
    >>> # Saving
    >>> var1, var2, var3 = scitex.io.cache("my_id", "var1", "var2", "var3")
    >>> print(var1, var2, var3)
    >>>
    >>> # Loading when not all variables are defined and the id exists
    >>> del var1, var2, var3
    >>> var1, var2, var3 = scitex.io.cache("my_id", "var1", "var2", "var3")
    >>> print(var1, var2, var3)
    """
    if cache_root is not None:
        cache_dir = Path(cache_root)
    else:
        cache_dir = _default_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{id}.pkl"

    does_cache_file_exist = cache_file.exists()

    # Get the caller's local variables
    caller_locals = sys._getframe(1).f_locals
    are_all_variables_defined = all(arg in caller_locals for arg in args)

    if are_all_variables_defined:
        # If all variables are defined, save them to cache and return as-is
        data_to_cache = {arg: caller_locals[arg] for arg in args}
        with cache_file.open("wb") as f:
            pickle.dump(data_to_cache, f)
        return tuple(data_to_cache.values())
    else:
        if does_cache_file_exist:
            # If cache exists, load and return the values
            with cache_file.open("rb") as f:
                loaded_data = pickle.load(f)
            return tuple(loaded_data[arg] for arg in args)
        else:
            raise ValueError("Cache file not found and not all variables are defined.")


# Usage example
if __name__ == "__main__":
    import numpy as np
    import scitex

    # Variables to cache
    var1 = "x"
    var2 = 1
    var3 = np.ones(10)

    # Saving
    var1, var2, var3 = scitex.io.cache("my_id", "var1", "var2", "var3")
    print(var1, var2, var3)

    # Loading when not all variables are defined and the id exists
    del var1, var2, var3
    var1, var2, var3 = scitex.io.cache("my_id", "var1", "var2", "var3")
    print(var1, var2, var3)
