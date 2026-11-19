"""STX-S007 — ``load_configs()`` result bound to a non-UPPER_CASE name.

``load_configs`` is scitex-io's API, so the rule about how its result is
named lives here. Moved from the scitex-dev engine (``_naming_checker``) with
no behaviour change: engine metadata verbatim, the same detection (any
``load_configs(...)`` / ``<x>.load_configs(...)`` call on the right of a plain
``=`` assignment, one finding per non-UPPER_CASE ``Name`` target), emitted
through ``spi.add_issue``. scitex-dev's handover table names scitex-io as the
owner, so the engine stops emitting STX-S007 when this plugin is installed.
"""

from __future__ import annotations

import ast

__all__ = ["S007_SPEC", "bind_config_naming_checker"]

# Engine metadata, verbatim.
S007_SPEC = dict(
    id="STX-S007",
    severity="warning",
    category="structure",
    message="load_configs() result should be assigned to an UPPER_CASE variable",
    suggestion=(
        "Use UPPER_CASE for config variables — they hold project constants:\n"
        "  CONFIG = load_configs()          # good\n"
        "  config = load_configs()          # bad — looks like a local variable"
    ),
    requires="",
)


def _calls_load_configs(value) -> bool:
    if not isinstance(value, ast.Call):
        return False
    func = value.func
    return (isinstance(func, ast.Name) and func.id == "load_configs") or (
        isinstance(func, ast.Attribute) and func.attr == "load_configs"
    )


def bind_config_naming_checker(rule, spi):
    """Return a checker class that emits *rule* (STX-S007)."""

    class ConfigNamingChecker(ast.NodeVisitor):
        category = "structure"
        # Package-availability map for the ``requires`` gate; None = detect.
        available = None

        def __init__(self, source_lines, config):
            self.source_lines = source_lines
            self.config = config
            self.issues = []

        def visit_Assign(self, node):
            if _calls_load_configs(node.value):
                lineno = node.lineno
                source = (
                    self.source_lines[lineno - 1].rstrip()
                    if 1 <= lineno <= len(self.source_lines)
                    else ""
                )
                for target in node.targets:
                    if isinstance(target, ast.Name) and not target.id.isupper():
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

    return ConfigNamingChecker


# EOF
