#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2024-11-03 18:57:14 (ywatanabe)"
# File: ./src/scitex_io/_mat2py.py

"""Helper script for loading .mat files into python.

For .mat with multiple variables use ``mat2dict`` to get a dictionary
of .mat variables.
For .mat with one matrix use ``mat2npa`` to return a numpy array.
For .mat with one matrix use ``mat2npy`` to save the array to .npy.
For multiple .mat files with one matrix use ``dir2npy`` to save one
.npy file per .mat in a directory.

Ported from scitex_gen._introspect._mat2py (Phase B retirement wave).
The ``import pdb; pdb.set_trace()`` debugger traps in the original
``keys2npa`` and ``mat2npa`` have been removed.

Examples
--------
>>> mat2npa(
...     fname='/path/data.mat', typ=np.float32,
... )
"""

import os
from glob import glob as _glob

import h5py
import numpy as np
from scipy.io import loadmat


def mat2dict(fname):
    """Return a dictionary with the .mat file's variables."""
    try:
        D = h5py.File(fname)
        d = {}
        for key, value in D.items():
            d[key] = value
        d["__hdf__"] = True
    except (OSError, TypeError):
        d = loadmat(fname)
        d["__hdf__"] = False
    return d


def public_keys(d):
    """Return the keys of *d* that do not start with an underscore."""
    return [k for k in d.keys() if not k.startswith("_")]


def keys2npa(d, typ):
    """Convert each public key in *d* to a numpy array of dtype *typ*."""
    d2 = {}
    for key in public_keys(d):
        x = np.array(d[key], dtype=typ)
        if d.get("__hdf__"):
            x = np.squeeze(np.swapaxes(x, 0, -1))
        assert type(x.flatten()[0]) == typ
        d2[key] = x.copy()
    return d2


def mat2npa(fname, typ):
    """Return the first entry of a .mat file as a numpy array."""
    d = keys2npa(mat2dict(fname), typ)
    return d[list(d.keys())[0]]


def save_npa(fname, x):
    """Save *x* to ``fname.npy`` via :func:`numpy.save`."""
    np.save(fname, x)


def mat2npy(fname, typ):
    """Save the first entry of a .mat file to a .npy file."""
    x = mat2npa(fname, typ)
    save_npa(fname=fname.replace(".mat", ""), x=x)


def dir2npy(dir, typ, regex="*"):
    """Save each .mat file matching ``regex`` in *dir* to .npy."""
    os.chdir(dir)
    for fname in _glob(regex + ".mat"):
        print("File " + fname + " to" + " .npa")
        mat2npy(dir + fname, typ)


# EOF
