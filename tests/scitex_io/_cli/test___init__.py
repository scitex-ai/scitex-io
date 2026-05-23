"""Test scitex_io._cli package init."""

import scitex_io._cli as cli_pkg


def test_exports_main_hasattr_cli_pkg_main():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert hasattr(cli_pkg, "main")


def test_exports_main_main_in_cli_pkg_all():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert "main" in cli_pkg.__all__




def test_help_has_version_prefix_cli_pkg_main_help():
    # __init__.py injects "scitex-io (vX.Y.Z) — ..." into main.help
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert cli_pkg.main.help


def test_help_has_version_prefix_scitex_io_in_cli_pkg_main_help():
    # __init__.py injects "scitex-io (vX.Y.Z) — ..." into main.help
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert "scitex-io" in cli_pkg.main.help


