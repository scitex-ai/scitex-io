"""Public, importable view of scitex-io's raw-IO detection rules.

``_linter.plugin.get_plugin()["call_rules"]`` is AST-shaped: its keys are
the names as they appear in SOURCE TEXT (``"np"``, ``"pd"``, ``"sio"``,
``"plt"``, ``"Image"``, ...), which is exactly right for a static
text/AST matcher but wrong for a runtime consumer (e.g. a monkeypatch
guard installed at ``@stx.session.start()``) that needs the REAL,
importable module path regardless of what alias a given script's
``import ... as`` happened to pick.

``iter_io_bypass_targets()`` is that runtime-oriented view: canonical
``(module_path, attr, rule_id, severity)`` tuples, generated FROM
``call_rules`` (single source of truth, no second hand-maintained list to
drift out of sync) but deduplicated to one row per real module+attr.
Entries with no derivable module path (e.g. ``(None, "savefig")``,
matched on any receiver's ``.savefig()`` method, not a module-level
call) are skipped — there is nothing to ``importlib.import_module`` for
those.

This module intentionally does NOT decide policy (warn vs. raise, which
severities matter). Callers get the full ``(module_path, attr, rule_id,
severity)`` picture and decide for themselves — the rule DATA lives here
once; what to do with it is a runtime-guard concern (see the operator's
2026-07-05 raw-IO-provenance incident thread, scitex-session's runtime
guard).
"""

from __future__ import annotations

from typing import Iterator, NamedTuple

# Alias (as commonly written in source) -> real importable module path.
# "np"/"pd" are NOT themselves valid import paths (nobody has a module
# literally named "np") — they're bound names, so they need remapping
# same as "sio"/"plt"/"Image" (which have no canonical sibling entry in
# call_rules at all). Listing both alias and canonical explicitly here
# is what lets `iter_io_bypass_targets` collapse them to one row.
_ALIAS_TO_CANONICAL = {
    "np": "numpy",
    "pd": "pandas",
    "sio": "scipy.io",
    "plt": "matplotlib.pyplot",
    "Image": "PIL.Image",
    # cPickle: py2-only real module; in py3 it's always an alias for
    # `pickle` (or `_pickle`). Not a distinct real target — skip via
    # the canonical-name check in `iter_io_bypass_targets` (its rule_id
    # is identical to "pickle"'s, so dropping it loses no coverage).
}

# Aliases with no real-module meaning at all (skip outright).
_SKIP_MODULES = {"cPickle"}


class IOBypassTarget(NamedTuple):
    module_path: str
    attr: str
    rule_id: str
    severity: str


def iter_io_bypass_targets() -> Iterator[IOBypassTarget]:
    """Yield canonical (module_path, attr, rule_id, severity) targets.

    One row per distinct (real module path, attr) — aliases in
    ``call_rules`` that resolve to the same canonical module collapse to
    a single row. Skips rules with no module-level call shape (receiver-
    agnostic method rules like ``.savefig()``).
    """
    from .plugin import get_plugin

    call_rules = get_plugin()["call_rules"]
    seen = set()
    for (module_name, attr), rule in call_rules.items():
        if module_name is None or module_name in _SKIP_MODULES:
            continue
        canonical = _ALIAS_TO_CANONICAL.get(module_name, module_name)
        key = (canonical, attr)
        if key in seen:
            continue
        seen.add(key)
        yield IOBypassTarget(canonical, attr, rule.id, rule.severity)


__all__ = ["IOBypassTarget", "iter_io_bypass_targets"]
