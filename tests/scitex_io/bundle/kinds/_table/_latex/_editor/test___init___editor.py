#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Surface contract for the LaTeX editor subpackage."""

import scitex_io.bundle.kinds._table._latex._editor as editor


def test_editor_exposes_launch_editor():
    # Arrange
    # Act
    attr = getattr(editor, "launch_editor", None)
    # Assert
    assert attr is not None
