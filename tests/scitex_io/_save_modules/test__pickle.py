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
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_pickle.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Timestamp: "2025-05-16 12:21:07 (ywatanabe)"
# # File: /data/gpfs/projects/punim2354/ywatanabe/scitex_repo/src/scitex/io/_save_modules/_pickle.py
#
# import pickle
# import gzip
#
#
# def _save_pickle(obj, spath):
#     """
#     Save an object using Python's pickle serialization.
#
#     Parameters
#     ----------
#     obj : Any
#         Object to serialize.
#     spath : str
#         Path where the pickle file will be saved.
#
#     Returns
#     -------
#     None
#     """
#     with open(spath, "wb") as s:
#         pickle.dump(obj, s)
#
#
# def _save_pickle_gz(obj, spath):
#     """
#     Save an object using Python's pickle serialization with gzip compression.
#
#     Parameters
#     ----------
#     obj : Any
#         Object to serialize.
#     spath : str
#         Path where the compressed pickle file will be saved.
#
#     Returns
#     -------
#     None
#     """
#     with gzip.open(spath, "wb") as f:
#         pickle.dump(obj, f)

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_pickle.py
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


class TestSavePickle:
    def test_arbitrary_object_back_a_1_2_3(self, tmp_path):
        # Arrange
        # Arrange
        out = tmp_path / "obj.pkl"
        obj = {"a": [1, 2, 3], "b": np.array([4, 5])}
        _save_pickle(obj, str(out))
        # Act
        # Act
        with open(out, "rb") as f:
            back = pickle.load(f)
        # Assert
        # Assert
        assert back["a"] == [1, 2, 3]
        np.testing.assert_array_equal(back["b"], np.array([4, 5]))

    def test_via_sio_save_pkl_gz(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        out = tmp_path / "obj.pkl.gz"
        # Act
        # Act
        sio.save({"x": 1}, str(out), verbose=False)
        # Assert
        # Assert
        assert out.is_file() and out.stat().st_size > 0


# --- _joblib.py ------------------------------------------------------------


