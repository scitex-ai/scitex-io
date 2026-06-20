#!/usr/bin/env python3
"""
Inline utilities to avoid external dependencies.
All utilities needed by scitex-io that would otherwise come from scitex.
"""

import os
from pathlib import Path


# String utilities
def clean_path(path_string):
    """Clean and normalize a file system path."""
    return os.path.normpath(str(path_string))


def color_text(text, color):
    """Simple colored text."""
    try:
        from colorama import Fore, Style

        colors = {
            "green": Fore.GREEN,
            "red": Fore.RED,
            "yellow": Fore.YELLOW,
            "blue": Fore.BLUE,
            "magenta": Fore.MAGENTA,
            "cyan": Fore.CYAN,
        }
        return f"{colors.get(color, '')}{text}{Style.RESET_ALL}"
    except ImportError:
        return text


def readable_bytes(size):
    """Convert bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


# Dict utilities
class DotDict:
    """A dictionary-like object that allows attribute-like access (for valid identifier keys)
    and standard item access for all keys (including integers, etc.).

    Case-insensitive on string-key lookup, storage-stable
    -----------------------------------------------------
    Keys are stored exactly as set (``load_configs`` separately
    normalises every config key to UPPER on load). Lookups, however,
    are **case-insensitive for string keys**: ``d["seizure"]``,
    ``d["SEIZURE"]``, ``d.seizure`` and ``d.SEIZURE`` all resolve to the
    same stored value regardless of the stored case, and
    ``"seizure" in d`` matches a stored ``"SEIZURE"`` (and vice versa).

    This means a config written ``STR2COLOR: {"seizure": "red"}`` —
    which ``load_configs`` stores as ``{"SEIZURE": "red"}`` — can still
    be looked up with the lowercase key the user wrote
    (``CONFIG.X.STR2COLOR["seizure"]``) without a surprise ``KeyError``.

    ``keys()`` / ``values()`` / ``items()`` / iteration return the
    stored (canonical) form — they are NOT case-folded. Non-string keys
    (ints, etc.) are left untouched and matched exactly.
    """

    def __init__(self, dictionary=None):
        super().__setattr__("_data", {})
        if dictionary is not None:
            if isinstance(dictionary, DotDict):
                dictionary = dictionary._data
            elif not isinstance(dictionary, dict):
                raise TypeError("Input must be a dictionary.")
            for key, value in dictionary.items():
                if isinstance(value, dict) and not isinstance(value, DotDict):
                    value = DotDict(value)
                self[key] = value

    def _resolve_key(self, key):
        """Return the stored key matching ``key`` case-insensitively.

        Resolution order, designed so the common (UPPER-stored) path
        stays O(1) and the case-insensitive scan runs only on a genuine
        miss:

        1. Exact match — covers non-string keys and same-case lookups.
        2. For string keys, ``key.upper()`` — covers lowercase lookup of
           an UPPER-stored key (the ``load_configs`` case).
        3. For string keys, a case-insensitive scan over stored string
           keys — covers any other case mix (e.g. lowercase storage).

        Raises ``KeyError`` (carrying the *original* lookup key) when
        nothing matches, so callers see the key they actually asked for.
        """
        data = self._data
        if key in data:
            return key
        if isinstance(key, str):
            upper = key.upper()
            if upper in data:
                return upper
            for stored in data:
                if isinstance(stored, str) and stored.upper() == upper:
                    return stored
        raise KeyError(key)

    def __getattr__(self, key):
        if key.startswith("_"):
            return super().__getattribute__(key)
        try:
            return self._data[self._resolve_key(key)]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'"
            )

    def __setattr__(self, key, value):
        if key == "_data" or key.startswith("_"):
            super().__setattr__(key, value)
        else:
            if isinstance(value, dict) and not isinstance(value, DotDict):
                value = DotDict(value)
            self._data[key] = value

    def __delattr__(self, key):
        if key.startswith("_"):
            super().__delattr__(key)
        else:
            try:
                del self._data[key]
            except KeyError:
                raise AttributeError(
                    f"'{type(self).__name__}' object has no attribute '{key}'"
                )

    def __getitem__(self, key):
        return self._data[self._resolve_key(key)]

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, DotDict):
            value = DotDict(value)
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]

    def get(self, key, default=None):
        # Case-insensitive for string keys, mirroring __getitem__, so
        # d.get("seizure") and d["seizure"] never disagree.
        try:
            return self._data[self._resolve_key(key)]
        except KeyError:
            return default

    def to_dict(self, include_private=False):
        """Recursively convert to plain dict."""
        result = {}
        for key, value in self._data.items():
            if not include_private and isinstance(key, str) and key.startswith("_"):
                continue
            if isinstance(value, DotDict):
                value = value.to_dict(include_private=include_private)
            result[key] = value
        return result

    def __str__(self):
        import json as _json

        def default_handler(obj):
            if isinstance(obj, DotDict):
                return obj.to_dict()
            try:
                _json.dumps(obj)
                return obj
            except (TypeError, OverflowError):
                return str(obj)

        try:
            return _json.dumps(self.to_dict(), indent=4, default=default_handler)
        except TypeError as e:
            return f"<DotDict at {hex(id(self))}, keys: {list(self._data.keys())}> Error: {e}"

    def __repr__(self):
        import pprint as _pprint

        return _pprint.pformat(self.to_dict(include_private=False), indent=2, width=80)

    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def update(self, dictionary):
        if isinstance(dictionary, dict):
            iterator = dictionary.items()
        elif hasattr(dictionary, "__iter__"):
            iterator = dictionary
        else:
            raise TypeError(
                "Input must be a dictionary or an iterable of key-value pairs."
            )
        for key, value in iterator:
            self[key] = value

    def setdefault(self, key, default=None):
        if key not in self._data:
            self[key] = default
            return default
        return self._data[key]

    def pop(self, key, *args):
        if len(args) > 1:
            raise TypeError(f"pop expected at most 2 arguments, got {1 + len(args)}")
        if key not in self._data:
            if args:
                return args[0]
            raise KeyError(key)
        return self._data.pop(key)

    def __contains__(self, key):
        try:
            self._resolve_key(key)
            return True
        except KeyError:
            return False

    def __iter__(self):
        return iter(self._data)

    def copy(self):
        return DotDict(self._data.copy())

    def __eq__(self, other):
        if isinstance(other, DotDict):
            return self._data == other._data
        elif isinstance(other, dict):
            return self._data == other
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __bool__(self):
        return len(self._data) > 0


# Decorator utilities
def preserve_doc(func):
    """Placeholder for preserve_doc decorator."""
    return func


# Path utilities
def split(path):
    """Split path into components."""
    return Path(path).parts


def this_path():
    """Get current file path."""
    import inspect

    frame = inspect.currentframe().f_back
    return frame.f_code.co_filename


def clean(path):
    """Clean path."""
    return str(Path(path).resolve())


def getsize(path):
    """Get file size in bytes."""
    return Path(path).stat().st_size if Path(path).exists() else 0


# String parsing
def parse(string, pattern=None):
    """Extract `{name}` placeholders from a path template into a dict.

    The pattern uses `{name}` for named captures (each capturing a maximal
    non-`/` segment) and `*` as a non-greedy wildcard. Returns `{}` on no
    match. Returns the input string unchanged when no pattern is supplied.
    """
    if pattern is None:
        return string
    import re

    regex = re.escape(pattern)
    regex = re.sub(r"\\{(\w+)\\}", r"(?P<\1>[^/]+?)", regex)
    regex = regex.replace(r"\*", ".*?")
    m = re.fullmatch(regex, string)
    if not m:
        return {}

    def _coerce(v: str):
        # Numeric strings (incl. zero-padded "001") become ints; non-numeric
        # stays as a string. Tests rely on this coercion for IDs / indices.
        if v.lstrip("-").isdigit():
            return int(v)
        return v

    return {k: _coerce(v) for k, v in m.groupdict().items()}


# Environment detection
def detect_environment():
    """Detect the execution environment.

    Returns exactly one of a fixed, documented vocabulary — callers
    (see ``scitex_io._save.save``) route on these strings, and an
    unrecognised value is a fail-fast error there, never a silent
    fallback:

    - ``"jupyter"``     : Jupyter kernel (IPython ``ZMQInteractiveShell``)
    - ``"ipython"``     : IPython *terminal* REPL (``TerminalInteractiveShell``)
    - ``"script"``      : a real ``.py`` run (``__main__`` has a ``__file__``)
    - ``"interactive"`` : bare ``python`` REPL / ``python -i`` / ``-c``

    Detection order: IPython shell class first (jupyter vs ipython),
    then whether ``__main__`` has a ``__file__`` (script vs bare REPL).

    Operator directive 2026-06-13: the previous implementation returned
    only ``"jupyter"`` or ``"python"`` — ``"python"`` was ambiguous (real
    script vs REPL) and ``"script"`` was never returned, leaving
    ``_save.py``'s ``elif env_type == "script"`` branch as dead code and
    routing every script save to ``<cwd>/output/`` via a silent
    fallback. That fallback is removed in this same release; the
    detector now returns the precise string the consumer expects.
    """
    import sys as _sys

    try:
        _shell = get_ipython()  # type: ignore[name-defined]
    except NameError:
        _shell = None

    if _shell is not None:
        if type(_shell).__name__ == "ZMQInteractiveShell":
            return "jupyter"
        # Any other IPython shell (terminal REPL, embedded shell, etc.).
        return "ipython"

    _main = _sys.modules.get("__main__")
    if _main is not None and hasattr(_main, "__file__"):
        return "script"
    return "interactive"


def get_notebook_info_simple():
    """Return ``(notebook_filename, notebook_directory)`` or ``(None, None)``.

    Used by ``scitex_io.save`` to route notebook artefacts to the canonical
    ``<notebook_dir>/<stem>_out/<file>`` location. Detection layers (first
    truthy hit wins):

    1. Explicit env-var override ``SCITEX_NOTEBOOK_PATH`` — set by CI /
       nbconvert wrappers when the notebook path can't be discovered from
       inside the kernel.
    2. VS Code Jupyter — ``__vsc_ipynb_file__`` injected into the user
       namespace by the VS Code Jupyter extension.
    3. JupyterLab / classic notebook — ``__session__`` global, plus
       ``ipynbname.path()`` if the optional ``ipynbname`` package is
       installed (it queries the running Jupyter server).
    4. Fallback to scanning ``sys.argv`` for a ``*.ipynb`` arg (handles
       ``jupyter nbconvert demo.ipynb`` invocations from tools that
       forward argv to the kernel).

    Returns a 2-tuple, never a dict (callers unpack it).
    """
    import os
    import sys

    # 1) Explicit override.
    explicit = os.environ.get("SCITEX_NOTEBOOK_PATH")
    if explicit and os.path.exists(explicit):
        path = os.path.abspath(explicit)
        return os.path.basename(path), os.path.dirname(path) or None

    # 2/3) IPython user namespace (VS Code, JupyterLab).
    try:
        ip = get_ipython()  # type: ignore[name-defined]
    except NameError:
        ip = None
    if ip is not None:
        ns = getattr(ip, "user_ns", {}) or {}
        for key in ("__vsc_ipynb_file__", "__session__", "__notebook__"):
            candidate = ns.get(key)
            if isinstance(candidate, str) and candidate.endswith(".ipynb"):
                if os.path.exists(candidate):
                    path = os.path.abspath(candidate)
                    return os.path.basename(path), os.path.dirname(path) or None

        # ipynbname (best-effort) — only available if the user opted in.
        try:
            import ipynbname  # type: ignore

            path = str(ipynbname.path())
            if path.endswith(".ipynb") and os.path.exists(path):
                return os.path.basename(path), os.path.dirname(path) or None
        except (ImportError, Exception):
            pass

    # 4) sys.argv last-ditch (nbconvert running outside a kernel sometimes
    # passes the path positionally).
    for arg in sys.argv:
        if isinstance(arg, str) and arg.endswith(".ipynb") and os.path.exists(arg):
            path = os.path.abspath(arg)
            return os.path.basename(path), os.path.dirname(path) or None

    return None, None
