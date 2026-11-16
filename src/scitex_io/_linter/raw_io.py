"""Raw file I/O that bypasses ``stx.io`` — rules + AST checker.

Owned here (not in the scitex-dev engine) because every rule enforces
scitex-io's API: "write/read through ``stx.io.save`` / ``stx.io.load`` so the
file joins the session's provenance". A research artefact written by
``Path.write_text`` or ``shutil.copy`` gets NO clew edge, so ``clew chain`` on
the result is empty (hands-on finding, 2026-11).

Rules emitted by ``RawIOChecker``:

- STX-PA002 — bare ``open()`` / ``io.open`` / ``codecs.open``
- STX-IO016 — pathlib write: ``.write_text`` / ``.write_bytes`` / ``Path.open('w')``
- STX-IO017 — pathlib read:  ``.read_text``  / ``.read_bytes``  / ``Path.open()``
- STX-IO018 — ``shutil.copy/copy2/copyfile/copytree/move``
- STX-IO019 — ``os.rename/renames/replace/remove/unlink`` and the pathlib
  ``.rename/.replace/.unlink`` on a data path
- STX-IO012 — PIL ``img.save(path)`` (existing image-I/O rule; previously
  only ``Image.open`` was mapped)
- bare calls of from-imported writers/readers (``from scipy.io import
  savemat``; ``from numpy import save``) resolve to the SAME rule the
  attribute form gets through ``call_rules`` (the engine only sees
  ``module.func()`` shapes).

False positives: PA002 and IO016-IO019 declare ``scope="research-script"``.
The ENGINE applies that scope (scitex-dev >= 0.63.0, ``Rule.scope``): they
fire only in research scripts — an ``@stx.session`` / ``@stx.module`` module
or a file under ``scripts/`` of a ``project-type: research`` project — and
never in tests or library code. This checker therefore does not gate.
"""

from __future__ import annotations

import ast
from dataclasses import replace

_STX_ROOTS = frozenset(("stx", "scitex", "scitex_io"))
_OPEN_FUNCS = frozenset(("open", "io.open", "codecs.open"))
_PATH_WRITE = frozenset(("write_text", "write_bytes"))
_PATH_READ = frozenset(("read_text", "read_bytes"))
_PATH_MOVE = frozenset(("rename", "replace", "unlink"))
_PATH_CTORS = frozenset(("Path", "PurePath", "PosixPath", "WindowsPath"))
_SHUTIL_FUNCS = frozenset(
    f"shutil.{f}" for f in ("copy", "copy2", "copyfile", "copytree", "move")
)
_OS_MOVE_FUNCS = frozenset(
    f"os.{f}" for f in ("rename", "renames", "replace", "remove", "unlink")
)
_WRITE_MODE_CHARS = frozenset("wax+")
# keyword arguments of os.rename/remove/... and Path.rename/replace that name a path
_PATH_KWARGS = frozenset(("src", "dst", "path", "target"))

_ALLOW_HINT = (
    "\n  Not research data (a lock file, a log the session already captures)?"
    "\n  Say so on the line:  # stx-allow: {rid}  (reason: <why>)"
)


def make_raw_io_rules(Rule, scope, register_hint):
    """Return ``{short_id: Rule}`` for the raw-I/O family.

    *scope* is scitex-dev's ``SCOPE_RESEARCH_SCRIPT``; *register_hint* the
    shared register_saver/register_loader reminder.
    """

    def _rule(id_, category, msg, sug):
        return Rule(
            id=id_,
            severity="warning",
            category=category,
            message=msg,
            suggestion=sug + _ALLOW_HINT.format(rid=id_) + register_hint,
            requires="scitex",
            scope=scope,
        )

    return {
        "PA002": _rule(
            "STX-PA002",
            "path",
            "`open()` detected — use `stx.io.save()`/`stx.io.load()`, which "
            "records the file in the session's provenance",
            "Replace `open(path)` with `stx.io.load(path)` or "
            "`stx.io.save(obj, path)`.\n"
            "  stx.io logs every I/O operation for provenance tracking.",
        ),
        "IO016": _rule(
            "STX-IO016",
            "io",
            "Raw pathlib write (`.write_text()`/`.write_bytes()`/`Path.open('w')`) "
            "— the output bypasses stx.io, so clew records NO output edge",
            "Write through stx.io so the file joins the session's provenance:\n"
            "  Path('r.txt').write_text(text)  ->  stx.io.save(text, './r.txt')\n"
            "  Path('r.json').write_text(json.dumps(d))  ->  stx.io.save(d, './r.json')",
        ),
        "IO017": _rule(
            "STX-IO017",
            "io",
            "Raw pathlib read (`.read_text()`/`.read_bytes()`/`Path.open()`) — "
            "the input bypasses stx.io, so clew records NO input edge",
            "Read through stx.io so the file joins the session's provenance:\n"
            "  Path('data/in.csv').read_text()  ->  stx.io.load('./data/in.csv')\n"
            "  Path('cfg.yaml').read_text()  ->  CONFIG (injected by @stx.session)",
        ),
        "IO018": _rule(
            "STX-IO018",
            "io",
            "`shutil` copy/move of a file — the destination has no producing "
            "edge and the source no consuming edge in clew",
            "Route the data through stx.io so both ends are recorded:\n"
            "  shutil.copy('data/in.csv', 'out/in.csv')  ->  "
            "stx.io.save(stx.io.load('./data/in.csv'), './in.csv')",
        ),
        "IO019": _rule(
            "STX-IO019",
            "io",
            "`os.rename/replace/remove` (or `Path.rename/replace/unlink`) on a "
            "data path — moving or deleting an artefact outside stx.io breaks "
            "its recorded provenance",
            "Produce the file at its final path with `stx.io.save(obj, './final.ext')` "
            "instead of writing elsewhere and renaming; never delete a recorded output.",
        ),
    }


def _data_extensions():
    from .ext_checker import _builtin_extensions

    return frozenset(_builtin_extensions())


class RawIOChecker(ast.NodeVisitor):
    """Emit raw-file-I/O findings; scope gating is the engine's job."""

    category = "io"
    _RULES = None  # bound by ``bind_raw_io_checker``
    _CALL_RULES = None  # scitex-io's call_rules (for bare from-import calls)
    _IO012 = None

    def __init__(self, lines, config=None):
        self._lines = lines
        self._config = config
        self.issues = []
        self._mod_alias = {}  # local name -> module path ("sh" -> "shutil")
        self._from_alias = {}  # local name -> "module.attr"
        self._path_names = set()  # names bound to a Path expression
        self._pil_names = set()  # names bound to a PIL image
        self._data_exts = _data_extensions()

    # -- name resolution ---------------------------------------------------
    def visit_Module(self, node):
        for sub in ast.walk(node):
            if isinstance(sub, ast.Import):
                for a in sub.names:
                    local = a.asname or a.name.split(".")[0]
                    self._mod_alias[local] = a.name if a.asname else local
            elif isinstance(sub, ast.ImportFrom) and sub.module and not sub.level:
                for a in sub.names:
                    self._from_alias[a.asname or a.name] = f"{sub.module}.{a.name}"
        self.generic_visit(node)

    def _qual(self, expr):
        """Dotted, alias-resolved name of *expr* (``None`` if not a name chain)."""
        if isinstance(expr, ast.Name):
            if expr.id in self._from_alias:
                return self._from_alias[expr.id]
            return self._mod_alias.get(expr.id, expr.id)
        if isinstance(expr, ast.Attribute):
            base = self._qual(expr.value)
            return None if base is None else f"{base}.{expr.attr}"
        return None

    def _root_is_stx(self, expr):
        while isinstance(expr, (ast.Attribute, ast.Call)):
            expr = expr.func if isinstance(expr, ast.Call) else expr.value
        return isinstance(expr, ast.Name) and expr.id in _STX_ROOTS

    def _is_path_expr(self, expr):
        if isinstance(expr, ast.Call):
            q = self._qual(expr.func) or ""
            return q.rsplit(".", 1)[-1] in _PATH_CTORS
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div):
            return True
        return isinstance(expr, ast.Name) and expr.id in self._path_names

    def _is_pil_expr(self, expr):
        if isinstance(expr, ast.Name):
            return expr.id in self._pil_names
        if isinstance(expr, ast.Call):
            q = self._qual(expr.func) or ""
            if q.startswith("PIL.Image."):
                return True
            func = expr.func
            return isinstance(func, ast.Attribute) and self._is_pil_expr(func.value)
        return False

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                if self._is_path_expr(node.value):
                    self._path_names.add(target.id)
                if self._is_pil_expr(node.value):
                    self._pil_names.add(target.id)
        self.generic_visit(node)

    # -- detection ---------------------------------------------------------
    def visit_Call(self, node):
        rule = self._classify(node)
        if rule is not None:
            self._emit(rule, node)
        self.generic_visit(node)

    def _classify(self, node):
        func = node.func
        if isinstance(func, ast.Name):
            q = self._qual(func)
            if q in _OPEN_FUNCS:
                return self._RULES["PA002"]
            if q in _SHUTIL_FUNCS:
                return self._RULES["IO018"]
            if q in _OS_MOVE_FUNCS:
                return self._RULES["IO019"] if self._touches_data(node) else None
            # `from scipy.io import savemat; savemat(...)` — same rule as the
            # attribute form `sio.savemat(...)` gets from call_rules.
            if func.id in self._from_alias and q and "." in q:
                mod, attr = q.rsplit(".", 1)
                return self._CALL_RULES.get((mod, attr))
            return None
        if not isinstance(func, ast.Attribute) or self._root_is_stx(func.value):
            return None
        q = self._qual(func)
        attr = func.attr
        if q in _OPEN_FUNCS - {"open"}:
            return self._RULES["PA002"]
        if q in _SHUTIL_FUNCS:
            return self._RULES["IO018"]
        if q in _OS_MOVE_FUNCS:
            return self._RULES["IO019"] if self._touches_data(node) else None
        if attr in _PATH_WRITE:
            return self._RULES["IO016"]
        if attr in _PATH_READ:
            return self._RULES["IO017"]
        if attr == "open" and self._is_path_expr(func.value):
            write = _WRITE_MODE_CHARS & set(self._open_mode(node))
            return self._RULES["IO016" if write else "IO017"]
        if attr in _PATH_MOVE and self._is_path_expr(func.value):
            return self._RULES["IO019"] if self._touches_data(node) else None
        if attr == "save" and self._is_pil_expr(func.value):
            return self._IO012
        return None

    @staticmethod
    def _open_mode(node):
        mode = node.args[0] if node.args else None
        for kw in node.keywords:
            if kw.arg == "mode":
                mode = kw.value
        if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
            return mode.value
        return ""

    def _touches_data(self, node):
        """Whether a rename/remove may move a data artefact.

        Literal paths are judged by extension (a ``.lock`` / ``.tmp`` file is
        not data); a non-literal path could be anything, so it counts.
        """
        func = node.func
        exprs = list(node.args) + [
            kw.value for kw in node.keywords if kw.arg in _PATH_KWARGS
        ]
        if isinstance(func, ast.Attribute) and self._is_path_expr(func.value):
            exprs.append(func.value)
        if not exprs:
            return True
        for expr in exprs:
            literal = self._literal_path(expr)
            if literal is None:
                return True
            name = literal.rsplit("/", 1)[-1].lower()
            parts = name.split(".")
            candidates = {"." + parts[-1]} if len(parts) > 1 else set()
            if len(parts) > 2:
                candidates.add("." + ".".join(parts[-2:]))
            if candidates & self._data_exts:
                return True
        return False

    def _literal_path(self, expr):
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return expr.value
        if isinstance(expr, ast.Call) and self._is_path_expr(expr) and expr.args:
            return self._literal_path(expr.args[0])
        if isinstance(expr, ast.BinOp) and isinstance(expr.op, ast.Div):
            return self._literal_path(expr.right)
        return None

    def _emit(self, rule, node):
        from scitex_dev.linter.spi import Issue, _is_allowed_by_comment

        line = self._lines[node.lineno - 1] if node.lineno <= len(self._lines) else ""
        cfg = self._config
        if cfg is not None and rule.id in getattr(cfg, "disable", ()):
            return
        if _is_allowed_by_comment(line, rule.id):
            return
        sev = (getattr(cfg, "per_rule_severity", None) or {}).get(rule.id)
        if sev:
            rule = replace(rule, severity=sev)
        self.issues.append(
            Issue(rule=rule, line=node.lineno, col=node.col_offset, source_line=line)
        )


def bind_raw_io_checker(rules, call_rules, io012):
    """Return a ``RawIOChecker`` subclass bound to this plugin's rule objects.

    The engine instantiates checkers as ``cls(lines, config)``, so the rule
    objects travel as class attributes (one source of truth: the same Rule
    instances listed in ``get_plugin()["rules"]``).
    """
    return type(
        "RawIOChecker",
        (RawIOChecker,),
        {
            "_RULES": rules,
            "_CALL_RULES": call_rules,
            "_IO012": io012,
            "__module__": __name__,
            "__qualname__": "RawIOChecker",
        },
    )


__all__ = ["RawIOChecker", "bind_raw_io_checker", "make_raw_io_rules"]
