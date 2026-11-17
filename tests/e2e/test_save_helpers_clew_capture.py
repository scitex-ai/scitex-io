"""Real scitex-clew store: public ``save_*`` writes are session outputs.

Regression for paper-scitex-clew E1 (2026-11-17). A ``@session`` script
wrote ``REPORT.md`` via ``stx.io.save_text(text, "/abs/REPORT.md")``; strace
saw the write but clew did not record it (capture recall 4/5).

This runs a real ``@scitex_session.session`` script in a subprocess against
a real PostgreSQL store and reads the session's recorded outputs back from
clew. Gate: ``RUN_E2E=1`` plus ``SCITEX_IO_E2E_CLEW_DSN`` naming a private,
disposable store (a Unix-socket DSN you own -- never a fleet store).
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

DSN = os.environ.get("SCITEX_IO_E2E_CLEW_DSN", "")

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        os.environ.get("RUN_E2E") != "1" or not DSN,
        reason="needs RUN_E2E=1 and SCITEX_IO_E2E_CLEW_DSN (private store)",
    ),
    pytest.mark.skipif(
        importlib.util.find_spec("scitex_clew") is None
        or importlib.util.find_spec("scitex_session") is None,
        reason="scitex-clew and scitex-session must be installed",
    ),
]

SCRIPT = """
import json
import os
import sys
from pathlib import Path

import scitex_io as sio
from scitex_io import _save_modules as sm
from scitex_session import session

HERE = Path(__file__).resolve().parent
SEEN = {}


@session(verbose=False)
def main(CONFIG=None):
    from scitex_clew._tracker import get_tracker

    SEEN["session_id"] = get_tracker().session_id
    os.chdir(HERE)
    sio.save_text("abs report\\n", str(HERE / "REPORT_abs.md"))
    sio.save_text("rel report\\n", "./REPORT_rel.md")
    sm.save_json({"a": 1}, str(HERE / "helper.json"))
    sm.save_yaml({"a": 1}, "helper.yaml")
    sm.save_pickle({"a": 1}, str(HERE / "helper.pkl"))
    sm.save_html("<p>x</p>", "helper.html")
    sio.save_listed_scalars_as_csv([1.0, 2.0], str(HERE / "scalars.csv"))
    sio.save({"a": 1}, str(HERE / "via_save_abs.json"), verbose=False)
    return 0


if __name__ == "__main__":
    main()
    from scitex_clew._db import get_db

    outputs = get_db().get_file_hashes(SEEN["session_id"], role="output")
    print("CLEW_OUTPUTS " + json.dumps(sorted(outputs)))
"""

EXPECTED = [
    "REPORT_abs.md",
    "REPORT_rel.md",
    "helper.json",
    "helper.yaml",
    "helper.pkl",
    "helper.html",
    "scalars.csv",
    "via_save_abs.json",
]


@pytest.fixture(scope="module")
def recorded_outputs(tmp_path_factory):
    work = tmp_path_factory.mktemp("clew-capture")
    (work / "capture_script.py").write_text(SCRIPT)
    env = {
        **{k: v for k, v in os.environ.items() if not k.startswith("PG")},
        "SCITEX_DIR": str(work / "state"),
        "SCITEX_STORE_DSN": DSN,
        "SCITEX_CARDS_DB": DSN,
        "SCITEX_CLEW_PROJECT": "io-save-helpers-" + work.name,
    }
    result = subprocess.run(
        [sys.executable, str(work / "capture_script.py")],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode == 0, result.stdout[-4000:] + result.stderr[-4000:]
    line = [ln for ln in result.stdout.splitlines() if ln.startswith("CLEW_OUTPUTS ")]
    return work, set(json.loads(line[-1].split(" ", 1)[1]))


@pytest.mark.parametrize("fname", EXPECTED)
def test_clew_records_helper_write_as_session_output(fname, recorded_outputs):
    # Arrange
    work, outputs = recorded_outputs
    # Act
    expected = os.path.realpath(Path(work) / fname)
    # Assert
    assert expected in outputs
