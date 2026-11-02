"""Fail-closed store routing shared by local tests and the native PG context."""

from __future__ import annotations

import os
import re
import stat
import tempfile
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


def directory_identity(path):
    info = Path(path).lstat()
    return f"{info.st_dev}:{info.st_ino}:{info.st_uid}:{stat.S_IMODE(info.st_mode)}"


def validate_private_environment(environment):
    """Validate actual owned resources and exact routing, not a marker alone."""
    if environment.get("SCITEX_IO_TEST_PG_REQUIRED") != "1":
        raise RuntimeError("native IO tests require the private PG context")
    dsn = environment.get("SCITEX_IO_TEST_PG_DSN", "")
    if not dsn or any(
        environment.get(key) != dsn for key in ("SCITEX_STORE_DSN", "SCITEX_CARDS_DB")
    ):
        raise RuntimeError("private PG routing does not match its declared context")
    parsed = urlsplit(dsn)
    parameters = parse_qs(parsed.query)
    if (
        parsed.scheme != "postgresql"
        or parsed.hostname is not None
        or parsed.username != "postgres"
        or parsed.password is not None
        or parsed.path != "/postgres"
        or set(parameters) != {"host"}
        or len(parameters["host"]) != 1
    ):
        raise RuntimeError("private PG requires exactly its explicit Unix-socket DSN")
    temporary = Path(environment["TMPDIR"]).resolve()
    root = Path(environment["SCITEX_IO_TEST_PG_ROOT"])
    info = root.lstat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or root.is_symlink()
        or info.st_uid != os.getuid()
        or stat.S_IMODE(info.st_mode) != 0o700
        or root.parent.resolve() != temporary
        or not root.name.startswith("scitex-store-test-")
        or directory_identity(root) != environment.get("SCITEX_IO_TEST_PG_ROOT_ID")
    ):
        raise RuntimeError("private PG root ownership or identity is invalid")
    socket_directory = Path(parameters["host"][0])
    directory = socket_directory.lstat()
    if (
        not socket_directory.is_absolute()
        or socket_directory.is_symlink()
        or socket_directory.parent != root
        or not stat.S_ISDIR(directory.st_mode)
        or directory.st_uid != os.getuid()
    ):
        raise RuntimeError("private PG socket directory is not owned")
    socket_file = socket_directory / ".s.PGSQL.5432"
    socket_info = socket_file.lstat()
    if not stat.S_ISSOCK(socket_info.st_mode) or socket_info.st_uid != os.getuid():
        raise RuntimeError("private PG socket is missing or unowned")
    expected = {
        "PGHOST": str(socket_directory),
        "PGPORT": "5432",
        "PGUSER": "postgres",
        "PGDATABASE": "postgres",
    }
    if any(environment.get(key) != value for key, value in expected.items()):
        raise RuntimeError("private PG process routing is inconsistent")
    allowed = {*expected, "PGPASSFILE"}
    if any(key.startswith("PG") and key not in allowed for key in environment):
        raise RuntimeError("unreviewed inherited PG configuration remains")
    password_file = Path(environment["PGPASSFILE"])
    auth = password_file.lstat()
    if (
        password_file.is_symlink()
        or not stat.S_ISREG(auth.st_mode)
        or auth.st_uid != os.getuid()
        or stat.S_IMODE(auth.st_mode) != 0o600
        or auth.st_size != 0
        or password_file.parent.resolve() != temporary
    ):
        raise RuntimeError("private PG requires its owned empty password file")
    scope = environment.get("SCITEX_IO_TEST_PG_SCOPE", "")
    if (
        not re.fullmatch(r"owned-io-[0-9a-f]{32}", scope)
        or environment.get("SCITEX_CLEW_PROJECT") != scope
    ):
        raise RuntimeError("private PG project scope is inconsistent")


def protect_suite_store(environment):
    """Refuse an invalid required context; otherwise mint a private non-store."""
    if environment.get("SCITEX_IO_TEST_PG_REQUIRED"):
        validate_private_environment(environment)
        return None
    return force_unavailable_store(environment)


def force_unavailable_store(environment):
    """Mint an explicit refusal target before importing store-aware tooling."""
    owned = tempfile.TemporaryDirectory(prefix="io-unavailable-store-")
    root = Path(owned.name)
    for key in tuple(environment):
        if key.startswith("PG") or key.startswith("SCITEX_IO_TEST_PG_"):
            environment.pop(key, None)
    password_file = root / "empty-pgpass"
    password_file.write_text("")
    password_file.chmod(0o600)
    dsn = f"postgresql://io_test@/io_test?host={root / 'unavailable'}"
    environment.update(
        SCITEX_STORE_DSN=dsn,
        SCITEX_CARDS_DB=dsn,
        PGPASSFILE=str(password_file),
        SCITEX_CLEW_PROJECT="owned-io-" + uuid.uuid4().hex,
    )
    return owned
