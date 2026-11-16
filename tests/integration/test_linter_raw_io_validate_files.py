#!/usr/bin/env python3
"""Integration: ``scitex-dev linter validate-files`` + the installed scitex-io plugin.

Runs the real CLI (a subprocess, the same entry point an agent's edit hook
uses) on a throw-away research project and checks that raw file I/O in a
research script is reported while the same code in library ``src/`` is not.
"""

import json
import subprocess
import sys
from pathlib import Path

_SCRIPT = '''\
#!/usr/bin/env python3
"""Compute PAC and write results."""

import shutil
from pathlib import Path

import scitex as stx


def write_results(path, text):
    with open(path, "w") as f:
        f.write(text)


@stx.session
def main(
    CONFIG=stx.session.INJECTED,
    COLORS=stx.session.INJECTED,
    logger=stx.session.INJECTED,
    plt=stx.session.INJECTED,
    rngg=stx.session.INJECTED,
):
    text = Path("data/in.txt").read_text()
    write_results("out/results.txt", text)
    Path("out/summary.txt").write_text(text)
    shutil.copy("data/in.csv", "out/in.csv")
    return 0


if __name__ == "__main__":
    main()

# EOF
'''

_LIBRARY = '''\
"""Cache helper."""

from pathlib import Path


def cache(p, text):
    Path(p).write_text(text)
    return open(p).read()
'''


def _research_project(root: Path) -> Path:
    (root / ".scitex" / "dev").mkdir(parents=True)
    (root / ".scitex" / "dev" / "config.yaml").write_text("project-type: research\n")
    script = root / "scripts" / "pac" / "calc_pac.py"
    script.parent.mkdir(parents=True)
    script.write_text(_SCRIPT)
    lib = root / "src" / "pkg" / "_cache.py"
    lib.parent.mkdir(parents=True)
    lib.write_text(_LIBRARY)
    return root


def _validate(target: Path) -> dict:
    cli = Path(sys.executable).with_name("scitex-dev")
    proc = subprocess.run(
        [str(cli), "linter", "validate-files", str(target), "--json"],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=target,
    )
    return json.loads(proc.stdout)


def _ids(report: dict, needle: str) -> list:
    for path, entry in report.items():
        if path == "_meta":
            continue
        if path.endswith(needle):
            return sorted(i["rule_id"] for i in entry["issues"])
    return []


_RAW = {"STX-PA002", "STX-IO016", "STX-IO017", "STX-IO018"}


def test_validate_files_reports_raw_io_in_research_script(tmp_path):
    # Arrange
    root = _research_project(tmp_path)
    # Act
    ids = _ids(_validate(root), "calc_pac.py")
    # Assert
    assert sorted(set(ids) & _RAW) == sorted(_RAW)


def test_validate_files_skips_raw_io_in_library_module(tmp_path):
    # Arrange
    root = _research_project(tmp_path)
    # Act
    ids = _ids(_validate(root), "_cache.py")
    # Assert
    assert set(ids) & _RAW == set()
