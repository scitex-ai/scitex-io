"""Require first-save provenance through a real private PG consumer, offline."""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

_guard_path = Path(__file__).resolve().with_name("io_test_store.py")
_guard_spec = importlib.util.spec_from_file_location(
    "_io_test_store_guard", _guard_path
)
_guard = importlib.util.module_from_spec(_guard_spec)
_guard_spec.loader.exec_module(_guard)


CHILD = r"""
import ctypes
import errno
import json
import platform
import socket
import sys
from pathlib import Path

if platform.system() != "Linux" or platform.machine() != "x86_64":
    raise RuntimeError("offline observer probe requires the reviewed Linux X64 profile")

class Filter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]

class Program(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("filters", ctypes.POINTER(Filter))]

# Enforce the declared architecture, normalize the x32 syscall bit, and deny
# Internet/raw socket creation in C extensions as well as in Python. Existing
# descriptors are only the child's closed-fds standard streams.
allow = 0x7fff0000
refuse = 0x00050000 | errno.EPERM
instructions = [
    Filter(0x20, 0, 0, 4),                 # seccomp_data.arch
    Filter(0x15, 1, 0, 0xc000003e),        # AUDIT_ARCH_X86_64
    Filter(0x06, 0, 0, refuse),
    Filter(0x20, 0, 0, 0),                 # syscall number
    Filter(0x54, 0, 0, 0xbfffffff),        # clear __X32_SYSCALL_BIT
    Filter(0x15, 0, 3, 41),                # __NR_socket
    Filter(0x20, 0, 0, 16),                # socket domain
    Filter(0x15, 1, 0, socket.AF_UNIX),
    Filter(0x06, 0, 0, refuse),
    Filter(0x06, 0, 0, allow),
]
array = (Filter * len(instructions))(*instructions)
program = Program(len(instructions), array)
libc = ctypes.CDLL(None, use_errno=True)
if libc.prctl(38, 1, 0, 0, 0) != 0:        # PR_SET_NO_NEW_PRIVS
    raise OSError(ctypes.get_errno(), "cannot require no-new-privileges")
if libc.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:  # PR_SET_SECCOMP, FILTER
    raise OSError(ctypes.get_errno(), "cannot enforce offline observer probe")
for family in (socket.AF_INET, socket.AF_INET6):
    try:
        socket.socket(family)
    except PermissionError:
        pass
    else:
        raise AssertionError("Internet socket creation was not denied")

socket_path = Path(sys.argv[1]) / ".s.PGSQL.5432"
def audit(event, arguments):
    if event == "socket.connect":
        connection, address = arguments
        if connection.family != socket.AF_UNIX or Path(address) != socket_path:
            raise RuntimeError("unowned socket connection refused")
sys.addaudithook(audit)

import scitex_io
if "scitex_clew" in sys.modules:
    raise AssertionError("consumer was eagerly imported before first IO")
artifact = {"schema": "scitex-clew/citations/v1",
            "citations": [{"cite_key": "OwnedFirstIOProbe"}]}
scitex_io.save(artifact, str(Path.cwd()/"first-citation.json"), verbose=False)
from scitex_clew import list_citations
rows = list_citations()
if [item.cite_key for item in rows] != ["OwnedFirstIOProbe"]:
    raise AssertionError("first save was not consumed by the real Clew ledger")
sys.stdout.write(json.dumps({"first_save_real_clew_ledger": True,
                             "internet_socket_creation_denied": True}) + "\n")
"""


def live_process_birth(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    except FileNotFoundError:
        return None
    return None if fields[0] in {"Z", "X"} else fields[19]


def interrupted(signum, _frame):
    raise SystemExit(128 + signum)


def main(arguments):
    first_event = arguments[:1] == ["--first-event"]
    if first_event:
        arguments = arguments[1:]
    command = arguments[1:] if arguments[:1] == ["--"] else arguments
    if not command:
        raise SystemExit(
            "usage: probe-first-observer.py [--first-event] -- COMMAND [ARGS...]"
        )
    # Never leave a store-aware tooling import with an unset/ambient DSN.
    # Only command children receive the subsequently minted live PG context.
    refusal = _guard.force_unavailable_store(os.environ)
    os.environ["PGPORT"] = "5432"
    handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    for sig in handlers:
        signal.signal(sig, interrupted)
    try:
        from scitex_dev.store.testing import ephemeral_cluster_dsn

        with contextlib.ExitStack() as owned:
            authfile = owned.enter_context(
                tempfile.NamedTemporaryFile(prefix="io-pgpass-")
            )
            os.environ["PGPASSFILE"] = authfile.name
            dsn = owned.enter_context(ephemeral_cluster_dsn())
            parsed = urlsplit(dsn)
            socket_directory = Path(parse_qs(parsed.query)["host"][0])
            root = Path(os.environ["TMPDIR"]).resolve()
            if (
                parsed.hostname is not None
                or not socket_directory.resolve().is_relative_to(root)
            ):
                raise RuntimeError("PG probe requires its newly owned Unix socket")
            project = owned.enter_context(
                tempfile.TemporaryDirectory(prefix="io-first-observer-")
            )
            with (socket_directory.parent / "data/postmaster.pid").open() as identity:
                postmaster_pid = int(identity.readline().strip())
            postmaster_birth = live_process_birth(postmaster_pid)
            if postmaster_birth is None:
                raise RuntimeError("private PG postmaster is not live")
            scope = "owned-io-" + uuid.uuid4().hex
            environment = {
                **os.environ,
                "SCITEX_STORE_DSN": dsn,
                "PGHOST": str(socket_directory),
                "PGUSER": "postgres",
                "PGDATABASE": "postgres",
                "SCITEX_CARDS_DB": dsn,
                "SCITEX_CLEW_PROJECT": scope,
                "SCITEX_IO_TEST_PG_REQUIRED": "1",
                "SCITEX_IO_TEST_PG_DSN": dsn,
                "SCITEX_IO_TEST_PG_ROOT": str(socket_directory.parent),
                "SCITEX_IO_TEST_PG_ROOT_ID": _guard.directory_identity(
                    socket_directory.parent
                ),
                "SCITEX_IO_TEST_PG_SCOPE": scope,
            }
            _guard.validate_private_environment(environment)
            try:
                if first_event:
                    subprocess.run(
                        [sys.executable, "-I", "-c", CHILD, str(socket_directory)],
                        cwd=project,
                        env=environment,
                        check=True,
                        timeout=60,
                        close_fds=True,
                    )
                # The complete suite or real installed-wheel smoke shares this
                # private cluster. It never falls back to a host/fleet DSN.
                subprocess.run(command, env=environment, check=True, close_fds=True)
            finally:
                # Like the reviewed native resource helper, finish owned PG
                # teardown without a second signal interrupting it halfway.
                for sig in handlers:
                    signal.signal(sig, signal.SIG_IGN)
        if socket_directory.exists():
            raise RuntimeError("private PG socket survived teardown")
        if live_process_birth(postmaster_pid) == postmaster_birth:
            raise RuntimeError("owned private PG postmaster survived teardown")
        sys.stdout.write(
            json.dumps({"private_pg_teardown": True, "owned_postmaster_not_live": True})
            + "\n"
        )
    finally:
        for sig, handler in handlers.items():
            signal.signal(sig, handler)
        refusal.cleanup()


if __name__ == "__main__":
    main(sys.argv[1:])
