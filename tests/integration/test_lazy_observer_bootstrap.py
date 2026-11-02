"""Real installed observer entry point and first-event public IO regressions."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

CONSUMER = """import json
import os
import threading
from pathlib import Path

_registered = False
attempts = 0
_lock = threading.Lock()

def _event(kind, path):
    with _lock:
        with Path(os.environ["IO_OBSERVER_EVENTS"]).open("a", encoding="utf8") as output:
            output.write(json.dumps([kind, Path(path).name]) + "\\n")

def on_save(path, obj, kwargs):
    _event("save", path)

def on_load(path, result):
    _event("load", path)

def register():
    global _registered, attempts
    attempts += 1
    if _registered:
        return True
    import scitex_io
    scitex_io.register_post_save_hook(on_save)
    scitex_io.register_post_load_hook(on_load)
    _registered = True
    return True
"""


@pytest.fixture
def installed_consumer(tmp_path_factory):
    """Build/install an actual owned consumer wheel; never forge metadata."""
    root = tmp_path_factory.mktemp("io-observer-consumer")
    project = root / "project"
    project.mkdir()
    (project / "io_probe_consumer.py").write_text(CONSUMER)
    (project / "pyproject.toml").write_text("""[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
[project]
name = "io-probe-consumer"
version = "0.0.1"
dependencies = ["scitex-io>=0.4.1"]
[project.entry-points."scitex_io.observers"]
owned-consumer = "io_probe_consumer:register"
[tool.hatch.build.targets.wheel]
include = ["io_probe_consumer.py"]
""")
    subprocess.run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation"],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    (wheel,) = (project / "dist").glob("*.whl")
    prefix = root / "installed"
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--prefix", str(prefix), str(wheel)],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1"},
    )
    (site,) = prefix.glob("lib/python*/site-packages")
    return site


def run_probe(tmp_path, installed_consumer, body):
    script = f"""import sys
sys.path[:0] = {[str(ROOT / "src"), str(installed_consumer)]!r}
from pathlib import Path
import json
{body}
import scitex_io
assert Path(scitex_io.__file__).resolve() == Path({str(ROOT / "src/scitex_io/__init__.py")!r})
"""
    absent_socket = tmp_path / "absent-pg"
    dsn = f"postgresql://io_probe@/io_probe?host={absent_socket}"
    password_file = tmp_path / "empty-pgpass"
    password_file.write_text("")
    password_file.chmod(0o600)
    env = {
        **{key: value for key, value in os.environ.items() if not key.startswith("PG")},
        "SCITEX_DIR": str(tmp_path / "state"),
        "XDG_CONFIG_HOME": str(tmp_path / "config"),
        "XDG_CACHE_HOME": str(tmp_path / "cache"),
        "IO_OBSERVER_EVENTS": str(tmp_path / "events.jsonl"),
        # Never connect to an ambient user's provenance store.
        "SCITEX_STORE_DSN": dsn,
        "SCITEX_CARDS_DB": dsn,
        "PGPASSFILE": str(password_file),
        "SCITEX_CLEW_PROJECT": "owned-io-observer-probe",
    }
    result = subprocess.run(
        [sys.executable, "-I", "-c", script],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout.split("IO_RESULT ")[-1])


def test_pure_import_defers_metadata_and_observer_providers(
    tmp_path, installed_consumer
):
    # Arrange
    body = """before = set(sys.modules)
import scitex_io
added = set(sys.modules) - before
print("IO_RESULT " + json.dumps(sorted(name for name in added if name in
    {"importlib.metadata", "scitex_logging", "scitex_clew", "io_probe_consumer"})))"""
    # Act
    observed = run_probe(tmp_path, installed_consumer, body)
    # Assert
    assert observed == []


def test_public_version_keeps_distribution_string(tmp_path, installed_consumer):
    # Arrange
    body = """import scitex_io
from importlib.metadata import version
print("IO_RESULT " + json.dumps([isinstance(scitex_io.__version__, str),
    scitex_io.__version__ == version("scitex-io")]))"""
    # Act
    observed = run_probe(tmp_path, installed_consumer, body)
    # Assert
    assert observed == [True, True]


def test_actual_discovered_consumer_receives_first_save_and_load(
    tmp_path, installed_consumer
):
    # Arrange
    body = """import scitex_io
scitex_io.save({"value": 7}, str(Path.cwd()/"first.json"), verbose=False)
scitex_io.load(str(Path.cwd()/"first.json"))
import io_probe_consumer
from scitex_clew import _observers as clew
from scitex_io import _observers as hooks
events = [json.loads(line) for line in Path("events.jsonl").read_text().splitlines()]
print("IO_RESULT " + json.dumps([events, io_probe_consumer.attempts,
    hooks._post_save_hooks.count(clew.on_io_save), hooks._post_load_hooks.count(clew.on_io_load)]))"""
    # Act
    observed = run_probe(tmp_path, installed_consumer, body)
    # Assert
    assert observed == [[["save", "first.json"], ["load", "first.json"]], 1, 1, 1]


def test_sequential_manual_callback_order_is_preserved(tmp_path, installed_consumer):
    # Arrange
    body = """import scitex_io
seen = []
scitex_io.register_post_save_hook(lambda *args: seen.append("first"))
scitex_io.register_post_save_hook(lambda *args: seen.append("second"))
neutral = "scitex_clew" not in sys.modules and "io_probe_consumer" not in sys.modules
scitex_io.save({"value": 7}, str(Path.cwd()/"manual.json"), verbose=False)
from scitex_io import _observers as hooks
import io_probe_consumer
print("IO_RESULT " + json.dumps([seen, neutral,
    hooks._post_save_hooks.count(io_probe_consumer.on_save), io_probe_consumer.attempts]))"""
    # Act
    observed = run_probe(tmp_path, installed_consumer, body)
    # Assert
    assert observed == [["first", "second"], True, 1, 1]


def test_concurrent_first_io_and_actual_clew_import_complete_once(
    tmp_path, installed_consumer
):
    # Arrange
    body = """import scitex_io
import concurrent.futures
import threading
barrier = threading.Barrier(9)
def save(index):
    barrier.wait()
    target = Path.cwd()/f"thread-{index}.json"
    scitex_io.save({"value": index}, str(target), verbose=False)
    return scitex_io.load(str(target))["value"]
def import_clew():
    barrier.wait()
    import scitex_clew
    return "clew"
with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
    futures = [executor.submit(save, i) for i in range(8)]
    futures.append(executor.submit(import_clew))
    results = [future.result(timeout=30) for future in futures]
import io_probe_consumer
from scitex_clew import _observers as clew
from scitex_io import _observers as hooks
observed = [json.loads(line) for line in Path("events.jsonl").read_text().splitlines()]
print("IO_RESULT " + json.dumps([results, len(observed), io_probe_consumer.attempts,
    hooks._post_save_hooks.count(clew.on_io_save), hooks._post_load_hooks.count(clew.on_io_load)]))"""
    # Act
    observed = run_probe(tmp_path, installed_consumer, body)
    # Assert
    assert observed == [list(range(8)) + ["clew"], 16, 1, 1, 1]


def test_actual_clew_import_before_io_does_not_duplicate_callbacks(
    tmp_path, installed_consumer
):
    # Arrange
    body = """import scitex_clew
import scitex_io
scitex_io.save({"value": 7}, str(Path.cwd()/"clew-first.json"), verbose=False)
from scitex_clew import _observers as clew
from scitex_io import _observers as hooks
print("IO_RESULT " + json.dumps([hooks._post_save_hooks.count(clew.on_io_save),
    hooks._post_load_hooks.count(clew.on_io_load)]))"""
    # Act
    observed = run_probe(tmp_path, installed_consumer, body)
    # Assert
    assert observed == [1, 1]
