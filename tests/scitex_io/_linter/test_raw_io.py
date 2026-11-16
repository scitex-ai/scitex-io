#!/usr/bin/env python3
"""Tests for scitex_io._linter.raw_io — raw file I/O that bypasses stx.io.

Every test runs the REAL scitex-dev ``lint_source`` pipeline with the
installed scitex-io plugin, so the engine's ``research-script`` scope gate
is exercised end to end (no mocks, no hand-built payloads).
"""

from scitex_dev.linter.checker import lint_source
from scitex_dev.linter.config import LinterConfig
from scitex_dev.linter.spi import SCOPE_RESEARCH_SCRIPT

from scitex_io._linter.plugin import get_plugin

_SESSION = (
    "import scitex as stx\n"
    "{imports}"
    "\n"
    "\n"
    "{helpers}"
    "@stx.session\n"
    "def main(\n"
    "    CONFIG=stx.session.INJECTED,\n"
    "    COLORS=stx.session.INJECTED,\n"
    "    logger=stx.session.INJECTED,\n"
    "    plt=stx.session.INJECTED,\n"
    "    rngg=stx.session.INJECTED,\n"
    "):\n"
    "{body}"
    "    return 0\n"
    "\n"
    "\n"
    'if __name__ == "__main__":\n'
    "    main()\n"
)

_RESEARCH = LinterConfig(project_types=["research"])


def _session(body="", imports="from pathlib import Path\n", helpers=""):
    return _SESSION.format(imports=imports, body=body, helpers=helpers)


def _ids(src, filepath="examples/run_analysis.py", config=None, prefix="STX-"):
    issues = lint_source(src, filepath=filepath, config=config or LinterConfig())
    return sorted(i.rule.id for i in issues if i.rule.id.startswith(prefix))


def _raw_ids(src, **kw):
    raw = {"STX-PA002", "STX-IO016", "STX-IO017", "STX-IO018", "STX-IO019"}
    return [rid for rid in _ids(src, **kw) if rid in raw]


# --------------------------------------------------------------------------- #
# Payload                                                                     #
# --------------------------------------------------------------------------- #


def test_payload_declares_raw_io_capability():
    # Arrange
    plugin = get_plugin()
    # Act
    caps = plugin["capabilities"]
    # Assert
    assert "raw-io" in caps


def test_raw_io_rules_are_research_script_scoped():
    # Arrange
    ids = {"STX-PA002", "STX-IO016", "STX-IO017", "STX-IO018", "STX-IO019"}
    # Act
    scopes = {r.scope for r in get_plugin()["rules"] if r.id in ids}
    # Assert
    assert scopes == {SCOPE_RESEARCH_SCRIPT}


def test_raw_io_suggestions_name_stx_io_replacement():
    # Arrange
    ids = {"STX-PA002", "STX-IO016", "STX-IO017", "STX-IO018", "STX-IO019"}
    # Act
    mentions = {"stx.io." in r.suggestion for r in get_plugin()["rules"] if r.id in ids}
    # Assert
    assert mentions == {True}


# --------------------------------------------------------------------------- #
# STX-PA002 — bare open()                                                     #
# --------------------------------------------------------------------------- #


def test_open_in_helper_above_session_main_flags_pa002():
    # Arrange — regression: the engine used to flag open() only textually
    # AFTER the @stx.session decorator.
    helpers = (
        "def write_results(path, text):\n"
        '    with open(path, "w") as f:\n'
        "        f.write(text)\n"
        "\n"
        "\n"
    )
    # Act
    ids = _raw_ids(_session(imports="", helpers=helpers))
    # Assert
    assert ids == ["STX-PA002"]


def test_open_in_research_scripts_dir_without_session_flags_pa002():
    # Arrange — no decorator, but scripts/ of a research project.
    src = 'text = open("data/in.txt").read()\n'
    # Act
    ids = _raw_ids(src, filepath="scripts/pac/load.py", config=_RESEARCH)
    # Assert
    assert ids == ["STX-PA002"]


def test_io_open_alias_in_session_flags_pa002():
    # Arrange
    src = _session('    io.open("x.txt").read()\n', imports="import io\n")
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-PA002"]


def test_open_in_library_module_is_not_flagged():
    # Arrange — library code (no entry point, under src/) is out of scope.
    src = "def read(p):\n    return open(p).read()\n"
    # Act
    ids = _raw_ids(src, filepath="src/pkg/_cache.py", config=_RESEARCH)
    # Assert
    assert ids == []


def test_open_in_session_test_file_is_not_flagged():
    # Arrange
    src = _session('    open("x.txt").read()\n', imports="")
    # Act
    ids = _raw_ids(src, filepath="tests/test_run_analysis.py")
    # Assert
    assert ids == []


def test_open_with_stx_allow_comment_is_suppressed():
    # Arrange
    body = '    open("run.lock", "w")  # stx-allow: STX-PA002  (reason: lock)\n'
    # Act
    ids = _raw_ids(_session(body, imports=""))
    # Assert
    assert ids == []


# --------------------------------------------------------------------------- #
# STX-IO016 / IO017 — pathlib write / read                                    #
# --------------------------------------------------------------------------- #


def test_path_write_text_in_session_flags_io016():
    # Arrange
    src = _session('    Path("out/results.txt").write_text("hello")\n')
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO016"]


def test_path_write_bytes_on_variable_flags_io016():
    # Arrange
    src = _session('    p = Path("out/b.bin")\n    p.write_bytes(b"x")\n')
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO016"]


def test_path_open_write_mode_flags_io016():
    # Arrange
    src = _session(
        '    with Path("out/r.json").open("w") as f:\n        f.write("{}")\n'
    )
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO016"]


def test_path_read_text_in_session_flags_io017():
    # Arrange
    src = _session('    data = Path("data/in.csv").read_text()\n')
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO017"]


def test_joined_path_open_default_mode_flags_io017():
    # Arrange — `(base / "x").open()` reads.
    src = _session(
        '    base = Path("data")\n'
        '    with (base / "in.txt").open() as f:\n'
        "        f.read()\n"
    )
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO017"]


def test_tracked_path_variable_open_flags_io017():
    # Arrange
    src = _session('    p = Path("data") / "in.txt"\n    p.open().read()\n')
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO017"]


def test_non_path_open_attribute_is_not_flagged():
    # Arrange — webbrowser.open(url) is not file I/O.
    src = _session(
        '    webbrowser.open("https://example.org")\n', imports="import webbrowser\n"
    )
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == []


def test_stx_io_save_and_load_are_not_flagged():
    # Arrange
    src = _session(
        '    data = stx.io.load("./data/in.csv")\n'
        '    stx.io.save(data, "./results.csv")\n'
    )
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == []


def test_path_write_in_non_research_scripts_dir_is_not_flagged():
    # Arrange — outside a research project, scripts/ are shell utilities.
    src = 'from pathlib import Path\n\nPath("out.txt").write_text("x")\n'
    # Act
    ids = _raw_ids(src, filepath="scripts/release/bump.py")
    # Assert
    assert ids == []


# --------------------------------------------------------------------------- #
# STX-IO018 — shutil copy / move                                              #
# --------------------------------------------------------------------------- #


def test_shutil_copy_in_session_flags_io018():
    # Arrange
    src = _session(
        '    shutil.copy("data/in.csv", "out/in.csv")\n', imports="import shutil\n"
    )
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO018"]


def test_aliased_shutil_move_flags_io018():
    # Arrange
    src = _session('    sh.move("a.csv", "b.csv")\n', imports="import shutil as sh\n")
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO018"]


def test_from_imported_copytree_flags_io018():
    # Arrange
    src = _session(
        '    copytree("raw", "out/raw")\n', imports="from shutil import copytree\n"
    )
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO018"]


def test_dict_copy_method_is_not_flagged():
    # Arrange — dict.copy() is not a file copy.
    src = _session("    d = {}\n    e = d.copy()\n", imports="")
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == []


# --------------------------------------------------------------------------- #
# STX-IO019 — os.rename / replace / remove on data paths                      #
# --------------------------------------------------------------------------- #


def test_os_rename_of_data_file_flags_io019():
    # Arrange
    src = _session('    os.rename("tmp.csv", "final.csv")\n', imports="import os\n")
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO019"]


def test_os_remove_of_variable_path_flags_io019():
    # Arrange — a non-literal path may be data, so it counts.
    src = _session("    os.remove(out_path)\n", imports="import os\n")
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO019"]


def test_path_unlink_of_tracked_variable_flags_io019():
    # Arrange
    src = _session('    p = Path("out") / "r.npy"\n    p.unlink(missing_ok=True)\n')
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == ["STX-IO019"]


def test_os_remove_of_lock_file_is_not_flagged():
    # Arrange — a literal non-data extension is not a research artefact.
    src = _session('    os.remove("run.lock")\n', imports="import os\n")
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == []


def test_str_replace_method_is_not_flagged():
    # Arrange — str.replace is not Path.replace.
    src = _session('    name = "a-b".replace("-", "_")\n', imports="")
    # Act
    ids = _raw_ids(src)
    # Assert
    assert ids == []


# --------------------------------------------------------------------------- #
# STX-IO012 — PIL image .save()                                               #
# --------------------------------------------------------------------------- #


def test_pil_chained_save_flags_io012():
    # Arrange — Image.new is not itself a call rule, so only .save() fires.
    src = _session(
        '    Image.new("RGB", (4, 4)).convert("L").save("out.png")\n',
        imports="from PIL import Image\n",
    )
    # Act
    count = _ids(src).count("STX-IO012")
    # Assert
    assert count == 1


def test_pil_image_variable_save_flags_io012():
    # Arrange
    src = _session(
        '    img = Image.new("RGB", (4, 4))\n    img.save("out.png")\n',
        imports="from PIL import Image\n",
    )
    # Act
    ids = _ids(src)
    # Assert
    assert "STX-IO012" in ids


def test_non_pil_save_method_is_not_flagged():
    # Arrange — model.save(path) is not a PIL image.
    src = _session('    model.save("weights.bin")\n', imports="")
    # Act
    ids = _ids(src)
    # Assert
    assert "STX-IO012" not in ids


# --------------------------------------------------------------------------- #
# Call-rule gaps closed: np.fromfile/tofile, pd.ExcelWriter, scipy.io aliases #
# --------------------------------------------------------------------------- #


def test_np_fromfile_flags_io002():
    # Arrange
    src = 'import numpy as np\nnp.fromfile("x.bin")\n'
    # Act
    ids = _ids(src)
    # Assert
    assert "STX-IO002" in ids


def test_ndarray_tofile_flags_io001():
    # Arrange
    src = 'arr.tofile("x.bin")\n'
    # Act
    ids = _ids(src)
    # Assert
    assert "STX-IO001" in ids


def test_pd_excel_writer_flags_io004():
    # Arrange
    src = 'import pandas as pd\nw = pd.ExcelWriter("x.xlsx")\n'
    # Act
    ids = _ids(src)
    # Assert
    assert "STX-IO004" in ids


def test_scipy_io_other_alias_savemat_flags_io011():
    # Arrange
    src = 'import scipy.io as spio\nspio.savemat("x.mat", d)\n'
    # Act
    ids = _ids(src)
    # Assert
    assert "STX-IO011" in ids


def test_unaliased_scipy_io_loadmat_flags_io011():
    # Arrange
    src = 'import scipy.io\nscipy.io.loadmat("x.mat")\n'
    # Act
    ids = _ids(src)
    # Assert
    assert "STX-IO011" in ids


def test_from_imported_savemat_flags_io011():
    # Arrange
    src = 'from scipy.io import savemat\nsavemat("x.mat", d)\n'
    # Act
    ids = _ids(src)
    # Assert
    assert "STX-IO011" in ids


def test_from_imported_np_save_flags_io001():
    # Arrange
    src = 'from numpy import save\nsave("x.npy", a)\n'
    # Act
    ids = _ids(src)
    # Assert
    assert "STX-IO001" in ids


# --------------------------------------------------------------------------- #
# Research-project severity                                                   #
# --------------------------------------------------------------------------- #


def test_raw_io_promoted_to_error_in_research_project(tmp_path):
    # Arrange — a real research project, config resolved by load_config.
    from scitex_dev.linter.config import load_config

    (tmp_path / ".scitex" / "dev").mkdir(parents=True)
    (tmp_path / ".scitex" / "dev" / "config.yaml").write_text("project-type: research\n")
    script = tmp_path / "scripts" / "pac" / "calc.py"
    script.parent.mkdir(parents=True)
    src = 'from pathlib import Path\n\nPath("out.txt").write_text("x")\n'
    script.write_text(src)
    # Act
    issues = lint_source(src, filepath=str(script), config=load_config(str(script)))
    sev = {i.rule.severity for i in issues if i.rule.id == "STX-IO016"}
    # Assert
    assert sev == {"error"}
