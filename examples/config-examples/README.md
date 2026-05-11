# Config examples for `load_configs()`

Reference YAML files demonstrating the shapes `scitex_io.load_configs()`
accepts. Drop any of these into your project's `./config/` directory and
read them with:

```python
import scitex_io as sio
CONFIG = sio.load_configs()        # walks ./config/*.yaml
CONFIG.PATHS.DATA_DIR              # /data/experiment_01
CONFIG.MODEL.ENCODER.HIDDEN_DIM    # 256
```

## Files in this directory

| File | Demonstrates |
|---|---|
| `PATHS.yaml` | **Flat, all-UPPER** — the canonical shape: top-level constants |
| `PREPROCESS.yaml` | **Flat with `DEBUG_*` overrides** — values that flip under `IS_DEBUG=True` |
| `MODEL.yaml` | **Nested groups** (`ENCODER:` / `HEAD:`) accessed as `CONFIG.MODEL.ENCODER.HIDDEN_DIM` |
| `IS_DEBUG.yaml` | **Single boolean** — toggles `DEBUG_*` promotion across every file |
| `lowercase_demo.yaml` | **Case normalisation** — lowercase filename and keys; `load_configs()` upper-cases everything to `CONFIG.LOWERCASE_DEMO.*` |
| `conflict_demo.yaml` *(commented out)* | If you also create `CONFLICT_DEMO.yaml`, `load_configs()` emits a `UserWarning`, keeps the UPPER variant, and drops the lowercase one. See "Case-conflict handling" below. |

## Filename + key conventions

- **Filename stems become top-level keys.** `PATHS.yaml` → `CONFIG.PATHS`.
- **Every key is normalised to UPPER_CASE on load.** Source casing is
  preserved on disk (your YAML can be `model.yaml` with `hidden_dim:`
  if you prefer), but the in-memory shape is always
  `CONFIG.MODEL.HIDDEN_DIM`. Your Python code reads one shape.
- **`DEBUG_<KEY>` siblings override `<KEY>` when `IS_DEBUG=True`.** Set
  this either with `load_configs(IS_DEBUG=True)`, by adding
  `IS_DEBUG.yaml` with `IS_DEBUG: true`, or by setting `CI=True`.
- **Nested groups are accessed via dot-notation.** A YAML mapping
  inside a file becomes a `DotDict`; chain attribute access through
  `CONFIG.<file>.<group>.<key>`.

## Case-conflict handling

If two siblings fold to the same UPPER key, `load_configs()`:

1. Emits a `UserWarning` pointing at the conflict location
   (e.g. `case conflict at CONFIG.* — ['MODEL', 'model'] fold to 'MODEL'`).
2. Keeps the value from the UPPER variant.
3. Drops the lowercase one entirely.

This applies at both filename level (`MODEL.yaml` vs `model.yaml`) and
key level inside a file (`HIDDEN_DIM:` vs `hidden_dim:`).

## Loading these files standalone

```python
import scitex_io as sio
CONFIG = sio.load_configs(config_dir="path/to/this/dir")
```

Or copy them into your project's `./config/` and use the default:

```python
CONFIG = sio.load_configs()
```
