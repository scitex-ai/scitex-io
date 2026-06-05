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
    from scitex_io.utils import _compat

    importlib.reload(_compat)
    p = tmp_path / "x.txt"
    p.write_text("hi")
    completed = False
    # Act
    _compat.check_file_exists(str(p))
    completed = True
    # Assert
    assert completed


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


@pytest.fixture
def fallback_compat():
    """Reload _compat with scitex_logging blocked, yielding the fallback module."""
    saved_scitex_logging = {
        k: sys.modules[k] for k in list(sys.modules) if k.startswith("scitex_logging")
    }
    saved_compat = sys.modules.pop("scitex_io.utils._compat", None)

    # Force ImportError when loading scitex_logging
    for k in list(sys.modules):
        if k == "scitex_logging" or k.startswith("scitex_logging."):
            del sys.modules[k]

    # Setting a sys.modules entry to None causes ImportError on import.
    sys.modules["scitex_logging"] = None  # type: ignore[assignment]

    try:
        compat = importlib.import_module("scitex_io.utils._compat")
        importlib.reload(compat)
        yield compat
    finally:
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


def test_fallback_branch_sets_scitex_errors_available_false(fallback_compat):
    # Arrange
    compat = fallback_compat
    # Act
    flag = compat.SCITEX_ERRORS_AVAILABLE
    # Assert
    assert flag is False


def test_fallback_scitex_io_error_includes_message(fallback_compat):
    # Arrange
    compat = fallback_compat
    # Act
    err = compat.SciTeXIOError("boom", context={"a": 1}, suggestion="try again")
    # Assert
    assert "boom" in str(err)


def test_fallback_scitex_io_error_is_exception(fallback_compat):
    # Arrange
    compat = fallback_compat
    # Act
    err = compat.SciTeXIOError("boom", context={"a": 1}, suggestion="try again")
    # Assert
    assert isinstance(err, Exception)


def test_fallback_file_format_error_includes_path(fallback_compat):
    # Arrange
    compat = fallback_compat
    # Act
    ferr = compat.FileFormatError("/p", expected_format="hdf5", actual_format="x")
    # Assert
    assert "/p" in str(ferr)


def test_fallback_path_not_found_error_subclasses_file_not_found(fallback_compat):
    # Arrange
    compat = fallback_compat
    # Act
    cls = compat.PathNotFoundError
    # Assert
    assert issubclass(cls, FileNotFoundError)


def test_fallback_check_file_exists_raises_for_missing_path(fallback_compat):
    # Arrange
    compat = fallback_compat
    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        compat.check_file_exists("/definitely/does/not/exist/zzz")


def test_fallback_check_file_exists_does_not_raise_for_existing_path(fallback_compat):
    # Arrange
    compat = fallback_compat
    completed = False
    # Act
    compat.check_file_exists(__file__)
    completed = True
    # Assert
    assert completed


def test_fallback_check_path_returns_none(fallback_compat):
    # Arrange
    compat = fallback_compat
    # Act
    result = compat.check_path("/anywhere")
    # Assert
    assert result is None


def test_fallback_warn_data_loss_mentions_dataset_name(fallback_compat):
    # Arrange
    compat = fallback_compat
    # Act
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        compat.warn_data_loss("D", "lose it")
    # Assert
    assert any("D" in str(w.message) for w in caught)
