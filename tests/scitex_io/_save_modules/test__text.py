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
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_text.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# # Timestamp: "2025-05-16 12:17:12 (ywatanabe)"
# # File: /data/gpfs/projects/punim2354/ywatanabe/scitex_repo/src/scitex/io/_save_modules/_text.py
#
#
# def _save_text(obj, spath):
#     """
#     Save text content to a file.
#
#     Parameters
#     ----------
#     obj : str
#         The text content to save.
#     spath : str
#         Path where the text file will be saved.
#
#     Returns
#     -------
#     None
#     """
#     with open(spath, "w") as file:
#         file.write(obj)

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_text.py
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


class TestSaveText:
    def test_string_round_trip(self, tmp_path):
        # Arrange
        # Arrange
        out = tmp_path / "note.txt"
        # Act
        # Act
        _save_text("hello world\nline 2\n", str(out))
        # Assert
        # Assert
        assert out.read_text() == "hello world\nline 2\n"

    def test_empty_string_out_read_text(self, tmp_path):
        # Arrange
        # Arrange
        out = tmp_path / "empty.txt"
        # Act
        # Act
        _save_text("", str(out))
        # Assert
        # Assert
        assert out.read_text() == ""

    def test_via_sio_save(self, tmp_path):
        # Arrange
        # Arrange
        import scitex_io as sio

        out = tmp_path / "note.txt"
        # Act
        # Act
        sio.save("hi", str(out), verbose=False)
        # Assert
        # Assert
        assert out.read_text() == "hi"


# --- _csv.py ---------------------------------------------------------------


