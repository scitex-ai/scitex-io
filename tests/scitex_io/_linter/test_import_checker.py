#!/usr/bin/env python3
"""Tests for scitex_io._linter.import_checker — STX-I003 (`import pickle`).

STX-I003 moved here from the scitex-dev engine with no behaviour change, so
these tests pin the engine's exact behaviour: one finding per ``pickle``
alias of a bare ``import``, none for ``from pickle import ...``, the engine's
``# stx-allow`` / disable / severity gates, and metadata identical to the
engine's compatibility copy.
"""

import ast

from scitex_dev.linter import spi
from scitex_dev.linter.config import LinterConfig

from scitex_io._linter.import_checker import I003_SPEC, bind_pickle_import_checker
from scitex_io._linter.plugin import get_plugin

_RULE = spi.Rule(**I003_SPEC)


class _Checker(bind_pickle_import_checker(_RULE, spi)):
    # The umbrella `scitex` (the rule's `requires`) may be absent in this
    # env; pin availability so the checker's own logic is what is tested.
    available = {"scitex": True}


def _findings(source, config=None):
    checker = _Checker(source.splitlines(), config or LinterConfig())
    checker.visit(ast.parse(source))
    return [(i.rule.id, i.line, i.rule.severity) for i in checker.issues]


def test_plugin_declares_i003_with_engine_metadata():
    # Arrange
    from scitex_dev.linter.rules import ALL_RULES

    # Act
    declared = {r.id: r for r in get_plugin()["rules"]}["STX-I003"]
    # Assert — identical to the engine's compatibility copy (delete this
    # test together with that copy once the handover completes).
    assert declared == ALL_RULES["STX-I003"]


def test_import_pickle_is_flagged_once_per_alias():
    # Arrange
    source = "import pickle\nimport os, pickle as pk\n"
    # Act
    found = _findings(source)
    # Assert
    assert found == [("STX-I003", 1, "warning"), ("STX-I003", 2, "warning")]


def test_from_pickle_import_is_not_flagged():
    # Arrange
    source = "from pickle import dumps\n"
    # Act
    found = _findings(source)
    # Assert
    assert found == []


def test_stx_allow_comment_suppresses_i003():
    # Arrange
    source = "import pickle  # stx-allow: STX-I003\n"
    # Act
    found = _findings(source)
    # Assert
    assert found == []


def test_per_rule_severity_pin_applies_to_i003():
    # Arrange
    config = LinterConfig(per_rule_severity={"STX-I003": "info"})
    # Act
    found = _findings("import pickle\n", config)
    # Assert
    assert found == [("STX-I003", 1, "info")]


def test_disabled_i003_is_not_reported():
    # Arrange
    config = LinterConfig(disable=["STX-I003"])
    # Act
    found = _findings("import pickle\n", config)
    # Assert
    assert found == []


# EOF
