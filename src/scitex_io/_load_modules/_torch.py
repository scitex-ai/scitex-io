#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2024-11-14 07:41:34 (ywatanabe)"
# File: ./scitex_repo/src/scitex/io/_load_modules/_torch.py


import importlib.util as _importlib_util

# Probe via find_spec instead of `import torch` so double-import during
# audit doesn't trigger TORCH_LIBRARY re-registration.
TORCH_AVAILABLE = _importlib_util.find_spec("torch") is not None


def _load_torch(lpath, **kwargs):
    """Load PyTorch model/checkpoint file."""
    # Lazy import to avoid circular import issues
    import torch

    if not lpath.endswith((".pth", ".pt")):
        raise ValueError("File must have .pth or .pt extension")
    return torch.load(lpath, **kwargs)


# EOF
