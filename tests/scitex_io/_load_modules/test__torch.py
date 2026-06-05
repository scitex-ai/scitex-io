#!/usr/bin/env python3
# Time-stamp: "2025-06-02 14:45:00 (ywatanabe)"
# File: ./scitex_repo/tests/scitex/io/_load_modules/test__torch.py

"""Tests for PyTorch file loading functionality.

This module tests the _load_torch function from scitex_io._load_modules._torch,
which handles loading PyTorch model and checkpoint files.
"""

import os
import tempfile

import pytest

# Required for scitex.io module
pytest.importorskip("h5py")
pytest.importorskip("zarr")
torch = pytest.importorskip("torch")
import torch.nn as nn


def test_torch_available_flag_is_bool():
    # Arrange
    from scitex_io._load_modules._torch import TORCH_AVAILABLE

    # Act
    actual = TORCH_AVAILABLE
    # Assert
    assert isinstance(actual, bool)


def test_torch_available_flag_is_true_when_torch_installed():
    # Arrange
    from scitex_io._load_modules._torch import TORCH_AVAILABLE

    # Act
    actual = TORCH_AVAILABLE
    # Assert
    assert actual is True


def test_load_torch_tensor_round_trips_values():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    tensor_2d = torch.randn(10, 20)
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        torch.save(tensor_2d, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_tensor = _load_torch(temp_path)
        # Assert
        assert torch.allclose(loaded_tensor, tensor_2d)
    finally:
        os.unlink(temp_path)


def test_load_torch_tensor_round_trips_shape():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    tensor_2d = torch.randn(10, 20)
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        torch.save(tensor_2d, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_tensor = _load_torch(temp_path)
        # Assert
        assert loaded_tensor.shape == (10, 20)
    finally:
        os.unlink(temp_path)


class _SimpleModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(10, 20)
        self.fc2 = nn.Linear(20, 10)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        return self.fc2(x)


def test_load_torch_state_dict_round_trips_keys():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    model = _SimpleModel()
    state_dict = model.state_dict()
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        torch.save(state_dict, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_state_dict = _load_torch(temp_path)
        # Assert
        assert set(loaded_state_dict.keys()) == set(state_dict.keys())
    finally:
        os.unlink(temp_path)


def test_load_torch_state_dict_round_trips_first_tensor():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    model = _SimpleModel()
    state_dict = model.state_dict()
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        torch.save(state_dict, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_state_dict = _load_torch(temp_path)
        # Assert
        first_key = next(iter(state_dict))
        assert torch.allclose(loaded_state_dict[first_key], state_dict[first_key])
    finally:
        os.unlink(temp_path)


def test_load_torch_checkpoint_round_trips_epoch():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    checkpoint = {"epoch": 10, "loss": 0.123}
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        torch.save(checkpoint, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_checkpoint = _load_torch(temp_path)
        # Assert
        assert loaded_checkpoint["epoch"] == 10
    finally:
        os.unlink(temp_path)


def test_load_torch_checkpoint_round_trips_loss():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    checkpoint = {"epoch": 10, "loss": 0.123}
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        torch.save(checkpoint, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_checkpoint = _load_torch(temp_path)
        # Assert
        assert loaded_checkpoint["loss"] == 0.123
    finally:
        os.unlink(temp_path)


def test_load_torch_pt_extension_round_trips():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    data = {"test": torch.tensor([1, 2, 3])}
    with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
        torch.save(data, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_data = _load_torch(temp_path)
        # Assert
        assert torch.equal(loaded_data["test"], data["test"])
    finally:
        os.unlink(temp_path)


def test_load_torch_invalid_pkl_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    # Act
    ctx = pytest.raises(ValueError, match="File must have .pth or .pt extension")
    # Assert
    with ctx:
        _load_torch("model.pkl")


def test_load_torch_invalid_json_extension_raises_valueerror():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    # Act
    ctx = pytest.raises(ValueError, match="File must have .pth or .pt extension")
    # Assert
    with ctx:
        _load_torch("/path/to/file.json")


def test_load_torch_map_location_cpu_string_returns_cpu_tensor():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    tensor = torch.randn(5, 5)
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        torch.save(tensor, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_tensor = _load_torch(temp_path, map_location="cpu")
        # Assert
        assert loaded_tensor.device.type == "cpu"
    finally:
        os.unlink(temp_path)


def test_load_torch_map_location_device_object_returns_cpu_tensor():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    tensor = torch.randn(5, 5)
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        torch.save(tensor, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_tensor = _load_torch(temp_path, map_location=torch.device("cpu"))
        # Assert
        assert loaded_tensor.device.type == "cpu"
    finally:
        os.unlink(temp_path)


def test_load_torch_nonexistent_path_raises_filenotfounderror():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        _load_torch("/nonexistent/path/model.pth")


def test_load_torch_multiple_objects_round_trips_tensor_count():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    objects = {"tensors": [torch.randn(3, 3) for _ in range(5)]}
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        torch.save(objects, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_objects = _load_torch(temp_path)
        # Assert
        assert len(loaded_objects["tensors"]) == 5
    finally:
        os.unlink(temp_path)


def test_load_torch_multiple_objects_round_trips_config():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    objects = {"model_config": {"hidden_size": 256, "num_layers": 3, "dropout": 0.1}}
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        torch.save(objects, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_objects = _load_torch(temp_path)
        # Assert
        assert loaded_objects["model_config"]["hidden_size"] == 256
    finally:
        os.unlink(temp_path)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_load_torch_cuda_tensor_to_cpu_returns_cpu_device():
    # Arrange
    from scitex_io._load_modules._torch import _load_torch

    cuda_tensor = torch.randn(5, 5).cuda()
    with tempfile.NamedTemporaryFile(suffix=".pth", delete=False) as f:
        torch.save(cuda_tensor, f.name)
        temp_path = f.name
    try:
        # Act
        loaded_tensor = _load_torch(temp_path, map_location="cpu")
        # Assert
        assert loaded_tensor.device.type == "cpu"
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    import os

    import pytest

    pytest.main([os.path.abspath(__file__)])
