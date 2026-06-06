#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2024-10-13 18:53:04 (ywatanabe)"
# File: ./src/scitex_io/_print_config.py
"""
1. Functionality:
   - Prints configuration values from YAML files via ``scitex_io.load_configs``
2. Input:
   - Configuration key (dot-separated for nested structures)
3. Output:
   - Corresponding configuration value

Ported from scitex_gen._fs._print_config (Phase B retirement wave).
The original referenced ``scitex.io.load_configs`` and
``scitex.gen.utils._DotDict``; both now live in ``scitex_io``.

Example:
    python -m scitex_io._print_config PATH.TITAN.MAT
"""

import argparse
import sys
from pprint import pprint


def print_config(key):
    """Print the value at the dot-separated ``key`` in the merged config."""
    # Local imports to keep module-level import side-effect free.
    from scitex_io import load_configs
    from scitex_io._utils import DotDict

    CONFIG = load_configs()

    if key is None:
        print("Available configurations:")
        pprint(CONFIG)
        return

    value = CONFIG
    try:
        keys = key.split(".")
        for k in keys:
            if isinstance(value, (dict, DotDict)):
                value = value.get(k)

            elif isinstance(value, list):
                try:
                    value = value[int(k)]
                except (ValueError, IndexError):
                    value = None

            elif isinstance(value, str):
                break

            else:
                value = None

            if value is None:
                break

        print(value)

    except Exception as e:
        print(f"Error: {e}")
        print("Available configurations:")
        pprint(value)


def print_config_main(args=None):
    """CLI entry point for ``print_config``."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Print configuration values")
    parser.add_argument(
        "key",
        nargs="?",
        default=None,
        help="Configuration key (dot-separated for nested structures)",
    )
    parsed_args = parser.parse_args(args)
    print_config(parsed_args.key)


if __name__ == "__main__":
    print_config_main()
