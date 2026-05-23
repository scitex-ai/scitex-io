"""Linter plugin for scitex-io: IO-specific rules (IO001-IO014, PA001-PA005).

Registered via entry point 'scitex_dev.linter.plugins' so scitex-linter
discovers these rules automatically when scitex-io is installed.

Coverage tracks the formats supported by scitex_io._save_modules /
_load_modules: csv, tsv, parquet, excel (xls/xlsx/xlsm/xlsb), hdf5,
feather, pickle, json, yaml, numpy (npy/npz/txt), torch, joblib,
matlab, image (png/jpg/...), mp4, zarr, bibtex, html, tex, plus any
extension a user has added via `register_saver` / `register_loader`.
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


def get_plugin():
    """Return scitex-io linter rules, call mappings, and checkers."""
    from scitex_dev.linter._rules._base import Rule

    def _io(id_, msg, sug):
        """Build an IO Rule with the register-handler hint appended."""
        return Rule(
            id=id_,
            severity="warning",
            category="io",
            message=msg,
            suggestion=sug + _REGISTER_HINT,
            requires="scitex",
        )

    IO001 = _io(
        "STX-IO001",
        "numpy save call detected — use `stx.io.save()` for provenance tracking",
        "Replace `np.save/savez/savetxt(path, arr)` with `stx.io.save(arr, path)`.",
    )
    IO002 = _io(
        "STX-IO002",
        "numpy load call detected — use `stx.io.load()` for provenance tracking",
        "Replace `np.load/loadtxt/genfromtxt(path)` with `stx.io.load(path)`.",
    )
    IO003 = _io(
        "STX-IO003",
        "pandas read function detected — use `stx.io.load()` for provenance tracking",
        "Replace `pd.read_csv/parquet/excel/hdf/pickle/json/feather/table(path)` "
        "with `stx.io.load(path)` (extension dispatched automatically).",
    )
    IO004 = _io(
        "STX-IO004",
        "DataFrame `.to_*` writer detected — use `stx.io.save()` for provenance tracking",
        "Replace `df.to_csv/parquet/excel/hdf/pickle/json/feather/html(path)` "
        "with `stx.io.save(df, path)`.",
    )
    IO005 = _io(
        "STX-IO005",
        "`pickle` call detected — use `stx.io.save()`/`stx.io.load()` for provenance tracking",
        "Replace `pickle.dump(obj, f)` / `pickle.load(f)` with "
        "`stx.io.save(obj, 'file.pkl')` / `stx.io.load('file.pkl')`.",
    )
    IO006 = _io(
        "STX-IO006",
        "`json` call detected — use `stx.io.save()`/`stx.io.load()` for provenance tracking",
        "Replace `json.dump(obj, f)` / `json.load(f)` with "
        "`stx.io.save(obj, 'file.json')` / `stx.io.load('file.json')`.",
    )
    IO007 = _io(
        "STX-IO007",
        "`.savefig()` detected — use `stx.io.save(fig, path)` for metadata embedding",
        "Replace `fig.savefig(path)` with `stx.io.save(fig, path)`.",
    )
    IO008 = _io(
        "STX-IO008",
        "`torch.save()`/`torch.load()` detected — use `stx.io.save()`/`stx.io.load()` for provenance tracking",
        "Replace `torch.save(obj, path)` / `torch.load(path)` with "
        "`stx.io.save(obj, 'file.pt')` / `stx.io.load('file.pt')`.",
    )
    IO009 = _io(
        "STX-IO009",
        "`joblib.dump()`/`joblib.load()` detected — use `stx.io.save()`/`stx.io.load()` for provenance tracking",
        "Replace `joblib.dump(obj, path)` / `joblib.load(path)` with "
        "`stx.io.save(obj, 'file.joblib')` / `stx.io.load('file.joblib')`.",
    )
    IO010 = _io(
        "STX-IO010",
        "`yaml` dump/load detected — use `stx.io.save()`/`stx.io.load()` for provenance tracking",
        "Replace `yaml.dump/safe_dump(obj, f)` / `yaml.safe_load(f)` with "
        "`stx.io.save(obj, 'file.yaml')` / `stx.io.load('file.yaml')`.",
    )
    IO011 = _io(
        "STX-IO011",
        "`scipy.io.savemat()`/`loadmat()` detected — use `stx.io.save()`/`stx.io.load()` for provenance tracking",
        "Replace `savemat(path, d)` / `loadmat(path)` with "
        "`stx.io.save(d, 'file.mat')` / `stx.io.load('file.mat')`.",
    )
    IO012 = _io(
        "STX-IO012",
        "image I/O call detected — use `stx.io.save()`/`stx.io.load()` for provenance tracking",
        "Replace `cv2.imwrite/imread`, `PIL.Image.save/open`, `plt.imsave/imread` with "
        "`stx.io.save(img, 'file.png')` / `stx.io.load('file.png')`.",
    )
    IO013 = _io(
        "STX-IO013",
        "`h5py.File()` detected — use `stx.io.save()`/`stx.io.load()` for HDF5 with provenance tracking",
        "Replace `h5py.File(path, 'w')` writes with `stx.io.save(obj, 'file.h5')`; "
        "reads with `stx.io.load('file.h5')`.",
    )

    # IO014 is emitted by _UnknownExtChecker (rule built lazily there so it
    # can include the offending extension verbatim). Listed here as a stub
    # so it appears in `scitex-linter list-rules`.
    IO014 = Rule(
        id="STX-IO014",
        severity="warning",
        category="io",
        message="Extension has no registered handler in scitex_io",
        suggestion=(
            "Register a handler with `register_saver('.ext')` / "
            "`register_loader('.ext')`, or use a built-in extension."
        ),
        requires="scitex",
    )

    # ------------------------------------------------------------------
    # Path-handling rules (PA001-PA005)
    # ------------------------------------------------------------------
    PA001 = Rule(
        id="STX-PA001",
        severity="warning",
        category="path",
        message="Absolute path in `stx.io` call — use relative paths for reproducibility",
        suggestion="Use `stx.io.save(obj, './relative/path.ext')` — paths resolve to script_out/.",
        requires="scitex",
    )

    PA002 = Rule(
        id="STX-PA002",
        severity="warning",
        category="path",
        message="`open()` detected — use `stx.io.save()`/`stx.io.load()` which includes auto-logging",
        suggestion=(
            "Replace `open(path)` with `stx.io.load(path)` or `stx.io.save(obj, path)`.\n"
            "  stx.io automatically logs all I/O operations for provenance tracking."
            + _REGISTER_HINT
        ),
        requires="scitex",
    )

    PA003 = Rule(
        id="STX-PA003",
        severity="info",
        category="path",
        message="`os.makedirs()`/`mkdir()` detected — `stx.io.save()` creates directories automatically",
        suggestion=(
            "Remove manual directory creation.\n"
            "  `stx.io.save(obj, './subdir/file.ext')` auto-creates `subdir/` inside script_out/."
        ),
        requires="scitex",
    )

    PA004 = Rule(
        id="STX-PA004",
        severity="warning",
        category="path",
        message="`os.chdir()` detected — scripts should be run from project root",
        suggestion="Remove `os.chdir()` and run scripts from the project root directory.",
    )

    PA005 = Rule(
        id="STX-PA005",
        severity="info",
        category="path",
        message="Path without `./` prefix in `stx.io` call — use `./` for explicit relative intent",
        suggestion="Use `./filename.ext` instead of `filename.ext` to clarify relative path intent.",
        requires="scitex",
    )

    call_rules = {
        # IO001 numpy save
        ("np", "save"): IO001,
        ("numpy", "save"): IO001,
        ("np", "savez"): IO001,
        ("numpy", "savez"): IO001,
        ("np", "savez_compressed"): IO001,
        ("numpy", "savez_compressed"): IO001,
        ("np", "savetxt"): IO001,
        ("numpy", "savetxt"): IO001,
        # IO002 numpy load
        ("np", "load"): IO002,
        ("numpy", "load"): IO002,
        ("np", "loadtxt"): IO002,
        ("numpy", "loadtxt"): IO002,
        ("np", "genfromtxt"): IO002,
        ("numpy", "genfromtxt"): IO002,
        # IO003 pandas read_*
        ("pd", "read_csv"): IO003,
        ("pandas", "read_csv"): IO003,
        ("pd", "read_table"): IO003,
        ("pandas", "read_table"): IO003,
        ("pd", "read_parquet"): IO003,
        ("pandas", "read_parquet"): IO003,
        ("pd", "read_excel"): IO003,
        ("pandas", "read_excel"): IO003,
        ("pd", "read_hdf"): IO003,
        ("pandas", "read_hdf"): IO003,
        ("pd", "read_pickle"): IO003,
        ("pandas", "read_pickle"): IO003,
        ("pd", "read_json"): IO003,
        ("pandas", "read_json"): IO003,
        ("pd", "read_feather"): IO003,
        ("pandas", "read_feather"): IO003,
        ("pd", "read_orc"): IO003,
        ("pandas", "read_orc"): IO003,
        # IO004 DataFrame .to_*
        (None, "to_csv"): IO004,
        (None, "to_parquet"): IO004,
        (None, "to_excel"): IO004,
        (None, "to_hdf"): IO004,
        (None, "to_pickle"): IO004,
        (None, "to_json"): IO004,
        (None, "to_feather"): IO004,
        (None, "to_html"): IO004,
        (None, "to_orc"): IO004,
        # IO005 pickle
        ("pickle", "dump"): IO005,
        ("pickle", "dumps"): IO005,
        ("pickle", "load"): IO005,
        ("pickle", "loads"): IO005,
        ("cPickle", "dump"): IO005,
        ("cPickle", "load"): IO005,
        # IO006 json
        ("json", "dump"): IO006,
        ("json", "dumps"): IO006,
        ("json", "load"): IO006,
        ("json", "loads"): IO006,
        # IO007 savefig (any receiver)
        (None, "savefig"): IO007,
        # IO008 torch
        ("torch", "save"): IO008,
        ("torch", "load"): IO008,
        # IO009 joblib
        ("joblib", "dump"): IO009,
        ("joblib", "load"): IO009,
        # IO010 yaml
        ("yaml", "dump"): IO010,
        ("yaml", "safe_dump"): IO010,
        ("yaml", "dump_all"): IO010,
        ("yaml", "load"): IO010,
        ("yaml", "safe_load"): IO010,
        ("yaml", "full_load"): IO010,
        # IO011 scipy.io
        ("sio", "savemat"): IO011,
        ("sio", "loadmat"): IO011,
        # IO012 image I/O
        ("cv2", "imwrite"): IO012,
        ("cv2", "imread"): IO012,
        ("plt", "imsave"): IO012,
        ("plt", "imread"): IO012,
        ("Image", "open"): IO012,
        ("imageio", "imwrite"): IO012,
        ("imageio", "imread"): IO012,
        # IO013 h5py
        ("h5py", "File"): IO013,
        # PA003/004
        ("os", "makedirs"): PA003,
        ("os", "mkdir"): PA003,
        ("os", "chdir"): PA004,
    }

    return {
        "rules": [
            IO001,
            IO002,
            IO003,
            IO004,
            IO005,
            IO006,
            IO007,
            IO008,
            IO009,
            IO010,
            IO011,
            IO012,
            IO013,
            IO014,
            PA001,
            PA002,
            PA003,
            PA004,
            PA005,
        ],
        "call_rules": call_rules,
        "axes_hints": {},
        "checkers": [_UnknownExtChecker],
    }
