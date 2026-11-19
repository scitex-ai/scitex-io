#!/usr/bin/env python3
"""Tests for scitex_io._linter.config_naming — STX-S007 (load_configs naming).

Moved from the scitex-dev engine with no behaviour change; these tests pin
the engine's behaviour and the metadata identical to its compatibility copy.
"""

import ast

from scitex_dev.linter import spi
from scitex_dev.linter.config import LinterConfig

from scitex_io._linter.config_naming import S007_SPEC, bind_config_naming_checker

_Checker = bind_config_naming_checker(spi.Rule(**S007_SPEC), spi)


def _findings(source):
    checker = _Checker(source.splitlines(), LinterConfig())
    checker.visit(ast.parse(source))
    return [(i.rule.id, i.line) for i in checker.issues]


def test_s007_metadata_matches_engine_copy():
    # Arrange
    from scitex_dev.linter.rules import ALL_RULES

    # Act
    ours = spi.Rule(**S007_SPEC)
    # Assert — delete together with the engine copy once the handover ends.
    assert ours == ALL_RULES["STX-S007"]


def test_lowercase_name_for_load_configs_result_is_reported():
    # Arrange
    source = "config = stx.io.load_configs()\ncfg = load_configs()\n"
    # Act
    found = _findings(source)
    # Assert
    assert found == [("STX-S007", 1), ("STX-S007", 2)]


def test_upper_case_and_unpacking_targets_are_not_reported():
    # Arrange
    source = "CONFIG = load_configs()\na, b = load_configs(), 1\n"
    # Act
    found = _findings(source)
    # Assert
    assert found == []


def test_stx_allow_comment_suppresses_s007():
    # Arrange
    source = "cfg = load_configs()  # stx-allow: STX-S007\n"
    # Act
    found = _findings(source)
    # Assert
    assert found == []


# EOF
