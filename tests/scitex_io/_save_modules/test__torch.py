#!/usr/bin/env python3
from __future__ import annotations
# Time-stamp: "2025-01-08 09:30:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_save_modules/test__torch.py

"""Tests for PyTorch save functionality."""

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
torch = pytest.importorskip("torch")


class TestSaveTorchAvailableFlags:
    """Test _AVAILABLE flags for optional dependencies."""

    def test_torch_available_flag_exists(self):
        """Test that TORCH_AVAILABLE flag is exported."""
        # Arrange
        # Act
        from scitex_io._save_modules._torch import TORCH_AVAILABLE

        # Assert
        assert isinstance(TORCH_AVAILABLE, bool)

    def test_torch_available_is_true_when_torch_installed(self):
        """Test that TORCH_AVAILABLE is True when torch is installed."""
        # Arrange
        # Act
        from scitex_io._save_modules._torch import TORCH_AVAILABLE

        # Assert
        assert TORCH_AVAILABLE is True


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_torch.py
# --------------------------------------------------------------------------------
# #!/usr/bin/env python3
# # Timestamp: "2025-05-16 12:25:14 (ywatanabe)"
# # File: /data/gpfs/projects/punim2354/ywatanabe/scitex_repo/src/scitex/io/_save_modules/_torch.py
#
# try:
#     import torch
#
#     TORCH_AVAILABLE = True
# except ImportError:
#     TORCH_AVAILABLE = False
#
#
# def _save_torch(obj, spath, **kwargs):
#     """
#     Save a PyTorch model or tensor.
#
#     Parameters
#     ----------
#     obj : torch.nn.Module or torch.Tensor
#         The PyTorch model or tensor to save.
#     spath : str
#         Path where the PyTorch file will be saved.
#     **kwargs : dict
#         Additional keyword arguments to pass to torch.save.
#
#     Returns
#     -------
#     None
#     """
#     if not TORCH_AVAILABLE:
#         raise ImportError(
#             "PyTorch is not installed. Please install with: pip install torch"
#         )
#
#     torch.save(obj, spath, **kwargs)

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/scitex-code/src/scitex/io/_save_modules/_torch.py
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


class TestSaveTorch:
    def test_tensor_torch_equal_back_t(self, tmp_path):
        # Arrange
        # Arrange
        import torch

        out = tmp_path / "t.pt"
        t = torch.tensor([1.0, 2.0, 3.0])
        _save_torch(t, str(out))
        # Act
        # Act
        back = torch.load(out, weights_only=False)
        # Assert
        # Assert
        assert torch.equal(back, t)

    def test_state_dict_torch_equal_back_weight_torch_zeros_2_2(self, tmp_path):
        # Arrange
        # Arrange
        import torch
        out = tmp_path / "sd.pt"
        sd = {"weight": torch.zeros(2, 2), "bias": torch.ones(2)}
        _save_torch(sd, str(out))
        # Act
        back = torch.load(out, weights_only=False)
        # Act
        # Assert
        # Assert
        assert torch.equal(back["weight"], torch.zeros(2, 2))

    def test_state_dict_torch_equal_back_bias_torch_ones_2(self, tmp_path):
        # Arrange
        # Arrange
        import torch
        out = tmp_path / "sd.pt"
        sd = {"weight": torch.zeros(2, 2), "bias": torch.ones(2)}
        _save_torch(sd, str(out))
        # Act
        back = torch.load(out, weights_only=False)
        # Act
        # Assert
        # Assert
        assert torch.equal(back["bias"], torch.ones(2))



# --- _plotly.py ------------------------------------------------------------


