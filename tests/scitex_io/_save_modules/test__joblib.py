from __future__ import annotations
# Smoke test (TODO: real coverage).
def test_placeholder_true_case():
    # Arrange
    # Act
    # Assert
    # Arrange
    # Act
    # Assert
    assert True

# Add your tests here

if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_joblib.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Timestamp: "2025-05-16 12:22:56 (ywatanabe)"
# # File: /data/gpfs/projects/punim2354/ywatanabe/scitex_repo/src/scitex/io/_save_modules/_joblib.py
#
# import joblib
#
#
# def _save_joblib(obj, spath):
#     """
#     Save an object using joblib serialization.
#
#     Parameters
#     ----------
#     obj : Any
#         Object to serialize.
#     spath : str
#         Path where the joblib file will be saved.
#
#     Returns
#     -------
#     None
#     """
#     with open(spath, "wb") as s:
#         joblib.dump(obj, s, compress=3)

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_joblib.py
# --------------------------------------------------------------------------------


# === merged from test__small_handlers.py ===
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round-trip tests for the small save-handler modules:
  _yaml, _plotly, _text, _csv, _pickle, _joblib, _torch,
  _optuna_study_as_csv_and_pngs

Each test uses real I/O — no mocks. Deps are installed in [dev] extras.
"""


import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from scitex_io._save_modules._csv import _save_csv
from scitex_io._save_modules._joblib import _save_joblib
from scitex_io._save_modules._pickle import _save_pickle
from scitex_io._save_modules._text import _save_text
from scitex_io._save_modules._torch import _save_torch
from scitex_io._save_modules._yaml import _convert_paths_to_strings, _save_yaml

# --- _yaml.py ---------------------------------------------------------------


class TestSaveJoblib:
    def test_array_np_array_equal_back_arr(self, tmp_path):
        # Arrange
        # Act
        # Assert
        # Arrange
        import joblib

        out = tmp_path / "arr.joblib"
        arr = np.arange(100)
        _save_joblib(arr, str(out))
        # Act
        back = joblib.load(out)
        # Assert
        assert np.array_equal(back, arr)


# --- _torch.py -------------------------------------------------------------





def test_missing_joblib_preserves_existing_target(tmp_path, attr_restore):
    """A failed optional import must not truncate the caller's existing file."""
    # Arrange
    import importlib

    module = importlib.import_module("scitex_io._save_modules._joblib")
    target = tmp_path / "existing.joblib"
    original = b"existing caller-owned content"
    target.write_bytes(original)
    attr_restore.set(module, "joblib", None)
    # Act
    try:
        module._save_joblib([1, 2, 3], str(target))
    except ImportError:
        pass
    # Assert
    assert target.read_bytes() == original


def test_missing_joblib_preserves_existing_target_raises_required_dependency_error(tmp_path, attr_restore):
    """A failed optional import must not truncate the caller's existing file."""
    # Arrange
    import importlib

    module = importlib.import_module("scitex_io._save_modules._joblib")
    target = tmp_path / "existing.joblib"
    original = b"existing caller-owned content"
    target.write_bytes(original)
    attr_restore.set(module, "joblib", None)
    # Act
    # Assert
    with pytest.raises(ImportError, match="requires joblib"):
        module._save_joblib([1, 2, 3], str(target))


def test_missing_joblib_does_not_create_target(tmp_path, attr_restore):
    # Arrange
    import importlib

    module = importlib.import_module("scitex_io._save_modules._joblib")
    target = tmp_path / "absent.joblib"
    attr_restore.set(module, "joblib", None)
    # Act
    try:
        module._save_joblib([1, 2, 3], str(target))
    except ImportError:
        pass
    # Assert
    assert not target.exists()


def test_missing_joblib_does_not_create_target_raises_required_dependency_error(tmp_path, attr_restore):
    # Arrange
    import importlib

    module = importlib.import_module("scitex_io._save_modules._joblib")
    target = tmp_path / "absent.joblib"
    attr_restore.set(module, "joblib", None)
    # Act
    # Assert
    with pytest.raises(ImportError, match="requires joblib"):
        module._save_joblib([1, 2, 3], str(target))
