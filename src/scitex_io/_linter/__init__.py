"""scitex-io linter plugin package.

Grouped under one subpackage (rather than flat `_linter_*.py` files) so the
source layout stays organized by responsibility — see PS-108.

  plugin.py       — get_plugin(): rules, call_rules, checkers (entry point)
  ext_checker.py  — STX-IO014 unknown-extension AST checker
  raw_io.py       — raw file I/O bypassing stx.io (PA002, IO016-IO019,
                    PIL .save); research-script scoped by the engine
  rules.py        — module+attr shaped IO-bypass targets for callers
"""

from .plugin import get_plugin
from .rules import iter_io_bypass_targets

__all__ = ["get_plugin", "iter_io_bypass_targets"]
