"""STX-I003 — ``import pickle`` (use ``stx.io``).

Moved here from the scitex-dev engine, whose handover table names scitex-io
as the owner: same id, severity, category, message, suggestion and
``requires`` gate, emitted through the engine's own gate
(``spi.add_issue``), so findings are unchanged. With this plugin installed
the engine stops emitting STX-I003; with an older scitex-io the engine's
compatibility copy still does.

Only the bare ``import pickle`` statement is flagged (one finding per
``pickle`` alias), exactly as before; ``pickle.dump``/``load`` CALLS are
STX-IO005.
"""

from __future__ import annotations

import ast

__all__ = ["I003_SPEC", "bind_pickle_import_checker"]

# Engine metadata, verbatim.
I003_SPEC = dict(
    id="STX-I003",
    severity="warning",
    category="import",
    message="Use `stx.io` instead of pickle for file I/O",
    suggestion="Replace with `stx.io.save(obj, 'file.pkl')` / `stx.io.load('file.pkl')`.",
    requires="scitex",
)


def bind_pickle_import_checker(rule, spi):
    """Return a checker class that emits *rule* for ``import pickle``."""

    class PickleImportChecker(ast.NodeVisitor):
        category = "import"
        # Package-availability map for the ``requires`` gate; None = detect.
        available = None

        def __init__(self, source_lines, config):
            self.source_lines = source_lines
            self.config = config
            self.issues = []

        def visit_Import(self, node):
            lineno = node.lineno
            source = (
                self.source_lines[lineno - 1].rstrip()
                if 1 <= lineno <= len(self.source_lines)
                else ""
            )
            for alias in node.names:
                if alias.name == "pickle":
                    spi.add_issue(
                        self.issues,
                        rule,
                        lineno,
                        node.col_offset,
                        source,
                        self.config,
                        available=self.available,
                    )
            self.generic_visit(node)

    return PickleImportChecker


# EOF
