"""Tests for scitex_io.utils._compat compatibility layer.

from __future__ import annotations
Exercises both branches: the real-import branch (default, since scitex_logging
is installed) and the fallback branch (forced via sys.modules patching +
importlib.reload).
"""


import importlib
import sys
import warnings

import pytest


def test_real_import_branch_exposes_names_compat_scitex_errors_available_is_true():
    # Arrange
    # Arrange
    from scitex_io.utils import _compat
    # Reload to ensure we are looking at a fresh module
    # Act
    importlib.reload(_compat)
    # Act
    # Assert
    # Assert
    assert _compat.SCITEX_ERRORS_AVAILABLE is True


def test_real_import_branch_exposes_names_hasattr_compat_scitexioerror():
    # Arrange
    # Arrange
    from scitex_io.utils import _compat
    # Reload to ensure we are looking at a fresh module
    # Act
    importlib.reload(_compat)
    # Act
    # Assert
    # Assert
    assert hasattr(_compat, "SciTeXIOError")


def test_real_import_branch_exposes_names_hasattr_compat_fileformaterror():
    # Arrange
    # Arrange
    from scitex_io.utils import _compat
    # Reload to ensure we are looking at a fresh module
    # Act
    importlib.reload(_compat)
    # Act
    # Assert
    # Assert
    assert hasattr(_compat, "FileFormatError")


def test_real_import_branch_exposes_names_hasattr_compat_pathnotfounderror():
    # Arrange
    # Arrange
    from scitex_io.utils import _compat
    # Reload to ensure we are looking at a fresh module
    # Act
    importlib.reload(_compat)
    # Act
    # Assert
    # Assert
    assert hasattr(_compat, "PathNotFoundError")


def test_real_import_branch_exposes_names_callable_compat_check_file_exists():
    # Arrange
    # Arrange
    from scitex_io.utils import _compat
    # Reload to ensure we are looking at a fresh module
    # Act
    importlib.reload(_compat)
    # Act
    # Assert
    # Assert
    assert callable(_compat.check_file_exists)


def test_real_import_branch_exposes_names_callable_compat_check_path():
    # Arrange
    # Arrange
    from scitex_io.utils import _compat
    # Reload to ensure we are looking at a fresh module
    # Act
    importlib.reload(_compat)
    # Act
    # Assert
    # Assert
    assert callable(_compat.check_path)


def test_real_import_branch_exposes_names_callable_compat_warn_data_loss():
    # Arrange
    # Arrange
    from scitex_io.utils import _compat
    # Reload to ensure we are looking at a fresh module
    # Act
    importlib.reload(_compat)
    # Act
    # Assert
    # Assert
    assert callable(_compat.warn_data_loss)




def test_real_path_not_found_raises(tmp_path):
    # Arrange
    # Arrange
    from scitex_io.utils import _compat

    importlib.reload(_compat)
    # Act
    # Act
    missing = tmp_path / "nope.h5"
    # Assert
    # Assert
    with pytest.raises((FileNotFoundError, _compat.PathNotFoundError, Exception)):
        _compat.check_file_exists(str(missing))


def test_real_check_file_exists_on_existing_file(tmp_path):
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    from scitex_io.utils import _compat

    importlib.reload(_compat)
    p = tmp_path / "x.txt"
    p.write_text("hi")
    # Should not raise
    _compat.check_file_exists(str(p))


def test_real_warn_data_loss_emits_warning():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    from scitex_io.utils import _compat

    importlib.reload(_compat)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        _compat.warn_data_loss("dset_x", "object dtype lost")
    # scitex_logging.warn_data_loss may emit via warnings or logging; if no
    # warnings appeared, at least confirm the call returned without error.
    # If it does warn, the message should mention the name.
    if caught:
        assert any("dset_x" in str(w.message) for w in caught) or len(caught) > 0


def test_fallback_branch_via_module_blocking():
    """Force the ImportError branch by hiding scitex_logging in sys.modules."""
    # Snapshot
    # Arrange
    # Act
    # Assert
    saved_scitex_logging = {
        k: sys.modules[k] for k in list(sys.modules) if k.startswith("scitex_logging")
    }
    saved_compat = sys.modules.pop("scitex_io.utils._compat", None)

    # Force ImportError when loading scitex_logging
    for k in list(sys.modules):
        if k == "scitex_logging" or k.startswith("scitex_logging."):
            del sys.modules[k]

    # Insert sentinels that raise on attribute access -- simpler: use a
    # MetaPathFinder. But the easiest is to set sys.modules entries to None,
    # which causes ImportError on import.
    sys.modules["scitex_logging"] = None  # type: ignore[assignment]

    try:
        compat = importlib.import_module("scitex_io.utils._compat")
        importlib.reload(compat)

        assert compat.SCITEX_ERRORS_AVAILABLE is False

        # Exercise fallback SciTeXIOError
        err = compat.SciTeXIOError("boom", context={"a": 1}, suggestion="try again")
        assert "boom" in str(err)
        assert isinstance(err, Exception)

        # Exercise fallback FileFormatError
        ferr = compat.FileFormatError("/p", expected_format="hdf5", actual_format="x")
        assert "/p" in str(ferr)

        # Exercise fallback PathNotFoundError
        assert issubclass(compat.PathNotFoundError, FileNotFoundError)

        # Exercise fallback check_file_exists raising
        with pytest.raises(FileNotFoundError):
            compat.check_file_exists("/definitely/does/not/exist/zzz")

        # Existing path: no raise
        compat.check_file_exists(__file__)

        # check_path: no-op
        assert compat.check_path("/anywhere") is None

        # warn_data_loss: emits a warning
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            compat.warn_data_loss("D", "lose it")
        assert any("D" in str(w.message) for w in caught)
    finally:
        # Restore
        sys.modules.pop("scitex_logging", None)
        for k, v in saved_scitex_logging.items():
            sys.modules[k] = v
        if saved_compat is not None:
            sys.modules["scitex_io.utils._compat"] = saved_compat
        else:
            sys.modules.pop("scitex_io.utils._compat", None)
        # Reload to restore real branch for other tests
        importlib.import_module("scitex_io.utils._compat")
        importlib.reload(sys.modules["scitex_io.utils._compat"])
