"""STX-IO014 unknown-extension checker, extracted from _linter/plugin.py.

Split out under the 512-line-per-file limit (_linter/plugin.py was at the
cap). Purely a mechanical extraction — no behavior change.
"""

import ast

# ---------------------------------------------------------------------------
# Shared hint appended to every IO rule suggestion. Tells users that custom
# formats can be plugged in without leaving the stx.io.save/load API.
# ---------------------------------------------------------------------------
_REGISTER_HINT = (
    "\n  Custom format? Register a handler:\n"
    "    from scitex_io import register_saver, register_loader\n"
    "    @register_saver('.ext')\n"
    "    def save_ext(obj, path, **kw): ...\n"
    "    @register_loader('.ext')\n"
    "    def load_ext(path, **kw): ..."
)


def _builtin_extensions():
    """Return the set of extensions scitex_io currently has handlers for.

    Pulled live from the registry so newly registered (user) handlers count
    as 'known' too — IO014 only fires for genuinely unknown extensions.
    Falls back to a hardcoded set if the registry can't be imported.
    """
    try:
        # _builtin_handlers populates the builtin tier at import time.
        from . import _builtin_handlers  # noqa: F401
        from . import _registry as reg  # noqa: WPS433 (intra-package)

        exts = set()
        for tier in (
            reg._builtin_savers,
            reg._builtin_loaders,
            reg._user_savers,
            reg._user_loaders,
        ):
            exts.update(tier.keys())
        # Composite extension (e.g. .pkl.gz) — track stem too.
        exts.discard("")
        return exts
    except Exception:
        return {
            ".csv",
            ".tsv",
            ".xls",
            ".xlsx",
            ".xlsm",
            ".xlsb",
            ".npy",
            ".npz",
            ".pkl",
            ".pickle",
            ".pkl.gz",
            ".joblib",
            ".pt",
            ".pth",
            ".mat",
            ".cbm",
            ".json",
            ".yaml",
            ".yml",
            ".xml",
            ".bib",
            ".txt",
            ".md",
            ".tex",
            ".log",
            ".rst",
            ".py",
            ".sh",
            ".css",
            ".js",
            ".cfg",
            ".ini",
            ".toml",
            ".html",
            ".hdf5",
            ".h5",
            ".zarr",
            ".db",
            ".con",
            ".mp4",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".tiff",
            ".tif",
            ".svg",
            ".pdf",
            ".docx",
            ".vhdr",
            ".vmrk",
            ".edf",
            ".bdf",
            ".gdf",
            ".cnt",
            ".egi",
            ".eeg",
            ".set",
        }


# ---------------------------------------------------------------------------
# AST checker: STX-IO014 — unknown extension passed to stx.io.save / load
# ---------------------------------------------------------------------------
class _UnknownExtChecker(ast.NodeVisitor):
    """Flag stx.io.save/load calls whose path uses an unregistered extension."""

    category = "io"

    def __init__(self, lines, config=None):  # signature dictated by checker.py
        self._lines = lines
        self._config = config
        self.issues = []
        self._exts = _builtin_extensions()
        self._rule = None  # populated lazily on first match

    # -- helpers -----------------------------------------------------------
    def _source(self, lineno):
        if 1 <= lineno <= len(self._lines):
            return self._lines[lineno - 1]
        return ""

    def _is_stx_io_call(self, node):
        """Return ('save'|'load', path_index) if call is stx.io.save/load."""
        func = node.func
        if not isinstance(func, ast.Attribute):
            return None
        if func.attr not in ("save", "load"):
            return None
        idx = 1 if func.attr == "save" else 0

        # Pattern A: stx.io.save / scitex.io.save / scitex_io.io.save
        if isinstance(func.value, ast.Attribute):
            v = func.value
            if (
                isinstance(v.value, ast.Name)
                and v.value.id in ("stx", "scitex", "scitex_io")
                and v.attr == "io"
            ):
                return func.attr, idx

        # Pattern B: scitex_io.save (bare top-level package call)
        if isinstance(func.value, ast.Name) and func.value.id == "scitex_io":
            return func.attr, idx

        return None

    def _path_string(self, node, idx):
        if len(node.args) > idx:
            arg = node.args[idx]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                return arg.value
        for kw in node.keywords:
            if kw.arg == "path" and isinstance(kw.value, ast.Constant):
                if isinstance(kw.value.value, str):
                    return kw.value.value
        return None

    # -- visitor -----------------------------------------------------------
    def visit_Call(self, node):
        match = self._is_stx_io_call(node)
        if match is not None:
            _func, idx = match
            path_str = self._path_string(node, idx)
            if path_str:
                import os.path as _osp

                basename = _osp.basename(path_str).lower()
                if "." not in basename:
                    self._emit(node, "(no extension)")
                else:
                    parts = basename.split(".")
                    candidates = []
                    if len(parts) >= 3:
                        candidates.append("." + ".".join(parts[-2:]))
                    candidates.append("." + parts[-1])
                    if not any(c in self._exts for c in candidates):
                        self._emit(node, candidates[-1])
        self.generic_visit(node)

    def _emit(self, node, ext):
        if self._rule is None:
            from scitex_dev.linter._rules._base import Rule

            self._rule = Rule(
                id="STX-IO014",
                severity="warning",
                category="io",
                message=(f"Extension `{ext}` has no registered handler in scitex_io"),
                suggestion=(
                    "Register a handler for this extension:\n"
                    "    from scitex_io import register_saver, register_loader\n"
                    f"    @register_saver('{ext}')\n"
                    "    def save_fn(obj, path, **kw): ...\n"
                    f"    @register_loader('{ext}')\n"
                    "    def load_fn(path, **kw): ...\n"
                    "  Or use a built-in extension (.csv, .npy, .pkl, .json, "
                    ".yaml, .h5, .parquet, .pt, .png, ...)."
                ),
                requires="scitex",
            )
        # Rebuild message per-issue so each path's bad ext appears verbatim.
        rule = self._rule
        from dataclasses import replace

        per_issue = replace(
            rule,
            message=f"Extension `{ext}` has no registered handler in scitex_io",
        )
        from scitex_dev.linter.checker import Issue

        self.issues.append(
            Issue(
                rule=per_issue,
                line=node.lineno,
                col=node.col_offset,
                source_line=self._source(node.lineno),
            )
        )


__all__ = ["_REGISTER_HINT", "_builtin_extensions", "_UnknownExtChecker"]
