"""Strict IO wheel/sdist and generated-metadata identity checks."""
import argparse
import base64
import configparser
import csv
import hashlib
import io
import json
import os
import re
import signal
import stat
import subprocess
import tarfile
import tomllib
import urllib.request
import zipfile
from email.parser import BytesParser
from pathlib import Path, PurePosixPath

SHA = re.compile(r"[0-9a-f]{40}")

def regular_bytes(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("artifact must be a regular file")
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 268435456:
            raise ValueError("artifact type or size is invalid")
        raw = stream.read()
        after = os.fstat(stream.fileno())
    if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ) or path.lstat().st_ino != before.st_ino:
        raise ValueError("artifact changed while reading")
    return raw


def safe_member(name):
    path = PurePosixPath(name)
    if (
        "\\" in name
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in name.rstrip("/").split("/"))
    ):
        raise ValueError("unsafe archive member")


def metadata_identity(raw, version):
    message = BytesParser().parsebytes(raw)
    if message.get_all("Name") != ["scitex-io"] and message.get_all("Name") != [
        "scitex_io"
    ]:
        raise ValueError("artifact distribution differs")
    if message.get_all("Version") != [version]:
        raise ValueError("artifact version differs")


def wheel_identity(raw, version):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or len(names) > 20000:
            raise ValueError("duplicate or excessive wheel members")
        for item in archive.infolist():
            safe_member(item.filename)
            mode = stat.S_IFMT(item.external_attr >> 16)
            if mode not in {0, stat.S_IFREG, stat.S_IFDIR} or item.file_size > 67108864:
                raise ValueError("unsupported wheel member")
        if sum(item.file_size for item in archive.infolist()) > 1073741824:
            raise ValueError("wheel expanded size exceeded")
        metadata = [name for name in names if name.endswith(".dist-info/METADATA")]
        records = [name for name in names if name.endswith(".dist-info/RECORD")]
        if len(metadata) != 1 or len(records) != 1:
            raise ValueError("wheel metadata identity is ambiguous")
        metadata_identity(archive.read(metadata[0]), version)
        record = records[0]
        owner = "scitex_io-" + version + ".dist-info"
        if metadata[0] != owner + "/METADATA" or record != owner + "/RECORD":
            raise ValueError("wheel metadata and RECORD owners differ")
        seen = set()
        for name, digest, size in csv.reader(
            io.StringIO(archive.read(record).decode())
        ):
            if name in seen or name not in names:
                raise ValueError("wheel RECORD membership differs")
            seen.add(name)
            if name == record:
                if digest or size:
                    raise ValueError("wheel RECORD self entry differs")
                continue
            body = archive.read(name)
            expected = "sha256=" + base64.urlsafe_b64encode(
                hashlib.sha256(body).digest()
            ).decode().rstrip("=")
            if digest != expected or size != str(len(body)):
                raise ValueError("wheel RECORD hash or size differs")
        if seen != set(names):
            raise ValueError("wheel has unrecorded members")
        key = "scitex_io/_save_modules/_yaml.py"
        if (
            key not in names
            or "scitex_io/_observers/__init__.py" not in names
        ):
            raise ValueError("wheel lost required public payload")
        return {"members": len(names), "record_members": len(seen)}


def sdist_identity(raw, version):
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        entries = archive.getmembers()
        names = [item.name for item in entries]
        if len(names) != len(set(names)) or len(names) > 20000:
            raise ValueError("duplicate or excessive sdist members")
        for item in entries:
            safe_member(item.name)
            if not (item.isfile() or item.isdir()) or item.size > 67108864:
                raise ValueError("unsupported sdist member")
        if sum(item.size for item in entries) > 1073741824:
            raise ValueError("sdist expanded size exceeded")
        roots = {PurePosixPath(name).parts[0] for name in names}
        if len(roots) != 1:
            raise ValueError("sdist has multiple roots")
        root = next(iter(roots))
        required = {
            root + "/src/scitex_io/_observers/__init__.py",
            root + "/src/scitex_io/_save_modules/_yaml.py",
            root + "/PKG-INFO",
            root + "/pyproject.toml",
        }
        if not required.issubset(names) or any(
            not archive.getmember(name).isfile() for name in required
        ):
            raise ValueError("sdist lost required public payload")
        metadata_identity(archive.extractfile(root + "/PKG-INFO").read(), version)
        project = tomllib.loads(
            archive.extractfile(root + "/pyproject.toml").read().decode()
        )["project"]
        if (
            project["version"] != version
            or project["name"].replace("_", "-").lower() != "scitex-io"
        ):
            raise ValueError("sdist project identity differs")
        return {"members": len(entries)}


def normalized_name(value):
    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?", value):
        raise ValueError("unsupported dependency name")
    return re.sub(r"[-_.]+", "-", value).lower()


def specifier_identity(value):
    value = value.strip()
    if value.startswith("(") and value.endswith(")"):
        value = value[1:-1].strip()
    if not value:
        return ()
    parts = [part.strip().lower() for part in value.split(",")]
    if any(
        not re.fullmatch(r"(?:===|==|!=|~=|<=|>=|<|>)\s*[a-z0-9.*+!_-]+", part)
        for part in parts
    ):
        raise ValueError("unsupported dependency version constraint")
    return tuple(sorted({re.sub(r"\s+", "", part) for part in parts}))


def marker_identity(value):
    if not value:
        return ()
    token = re.compile(
        r"""\s*("[^"\\]*"|'[^'\\]*'|===|==|!=|~=|<=|>=|[<>()]|[A-Za-z_][A-Za-z0-9_]*)"""
    )
    tokens = []
    position = 0
    while position < len(value):
        match = token.match(value, position)
        if not match:
            if value[position:].strip():
                raise ValueError("unsupported dependency marker")
            break
        tokens.append(match[1])
        position = match.end()
    if len(tokens) > 128:
        raise ValueError("dependency marker is excessive")
    position = 0
    variables = {
        "python_version",
        "python_full_version",
        "os_name",
        "sys_platform",
        "platform_release",
        "platform_system",
        "platform_version",
        "platform_machine",
        "platform_python_implementation",
        "implementation_name",
        "implementation_version",
        "extra",
    }

    def operand():
        nonlocal position
        if position >= len(tokens):
            raise ValueError("incomplete dependency marker")
        item = tokens[position]
        position += 1
        if item[:1] in {"'", '"'}:
            return ("literal", item[1:-1])
        if item not in variables:
            raise ValueError("unknown dependency marker variable")
        return ("variable", item)

    def atom(depth):
        nonlocal position
        if depth > 16 or position >= len(tokens):
            raise ValueError("incomplete dependency marker")
        if tokens[position] == "(":
            position += 1
            result = expression(depth + 1)
            if position >= len(tokens) or tokens[position] != ")":
                raise ValueError("unclosed dependency marker")
            position += 1
            return result
        left = operand()
        if position >= len(tokens):
            raise ValueError("incomplete dependency marker")
        operator = tokens[position]
        position += 1
        if operator == "not":
            if position >= len(tokens) or tokens[position] != "in":
                raise ValueError("unsupported dependency marker operator")
            position += 1
            operator = "not in"
        if operator not in {
            "===",
            "==",
            "!=",
            "~=",
            "<=",
            ">=",
            "<",
            ">",
            "in",
            "not in",
        }:
            raise ValueError("unsupported dependency marker operator")
        right = operand()
        if left == ("variable", "extra") and right[0] == "literal":
            right = ("literal", normalized_name(right[1]))
        if right == ("variable", "extra") and left[0] == "literal":
            left = ("literal", normalized_name(left[1]))
        return ("compare", left, operator, right)

    def combine(operator, values):
        flat = []
        for item in values:
            flat.extend(item[1:] if item[0] == operator else [item])
        return flat[0] if len(flat) == 1 else (operator, *sorted(set(flat)))

    def conjunction(depth):
        nonlocal position
        values = [atom(depth)]
        while position < len(tokens) and tokens[position] == "and":
            position += 1
            values.append(atom(depth))
        return combine("and", values)

    def expression(depth):
        nonlocal position
        values = [conjunction(depth)]
        while position < len(tokens) and tokens[position] == "or":
            position += 1
            values.append(conjunction(depth))
        return combine("or", values)

    result = expression(0)
    if position != len(tokens):
        raise ValueError("unsupported dependency marker suffix")
    return result


def requirement_identity(value):
    requirement, separator, marker = value.partition(";")
    match = re.fullmatch(
        r"\s*([A-Za-z0-9][A-Za-z0-9_.-]*)(?:\[([^]]+)\])?\s*(.*?)\s*", requirement
    )
    if not match or "@" in requirement:
        raise ValueError("unsupported dependency requirement")
    extras = tuple(
        sorted(
            {
                normalized_name(x.strip())
                for x in (match[2] or "").split(",")
                if x.strip()
            }
        )
    )
    return (
        normalized_name(match[1]),
        extras,
        specifier_identity(match[3]),
        marker_identity(marker if separator else ""),
    )


def declared_metadata(project):
    """Follow the reviewed Hatch static metadata and recursive-extra contract."""
    if project.get("dynamic"):
        raise ValueError("dynamic release metadata is not qualified")
    core = {requirement_identity(value) for value in project.get("dependencies", [])}
    groups = {}
    inherited = {}
    for name, requirements in project.get("optional-dependencies", {}).items():
        name = normalized_name(name)
        if name in groups:
            raise ValueError("ambiguous source extra")
        groups[name] = set()
        inherited[name] = set()
        for value in requirements:
            row = requirement_identity(value)
            if row[0] == normalized_name(project["name"]):
                if row[2] or row[3]:
                    raise ValueError("conditional self-extra is not qualified")
                inherited[name].update(row[1])
            else:
                groups[name].add(row)
    resolved = set()

    def resolve_group(name, active):
        if name not in groups or name in active:
            raise ValueError("unknown or cyclic source extra")
        if name not in resolved:
            for child in inherited[name]:
                resolve_group(child, active | {name})
                groups[name].update(groups[child])
            resolved.add(name)

    for name in groups:
        resolve_group(name, set())
    expected = set(core)
    for extra, requirements in groups.items():
        extra_marker = marker_identity("extra == '" + extra + "'")
        for name, extras, specifier, marker in requirements:
            if marker:
                parts = list(marker[1:]) if marker[0] == "and" else [marker]
                marker = ("and", *sorted(set([*parts, extra_marker])))
            else:
                marker = extra_marker
            expected.add((name, extras, specifier, marker))
    entries = {
        group: dict(values) for group, values in project.get("entry-points", {}).items()
    }
    for key, group in (("scripts", "console_scripts"), ("gui-scripts", "gui_scripts")):
        if project.get(key):
            if group in entries:
                raise ValueError("ambiguous source entry-point group")
            entries[group] = dict(project[key])
    return {
        "requires_python": specifier_identity(project.get("requires-python", "")),
        "extras": set(groups),
        "requirements": expected,
        "entries": entries,
    }


def metadata_source_identity(wheel_raw, sdist_raw, entry_points, project):
    if any(key in project for key in ("import-names", "import-namespaces")):
        raise ValueError("source import declarations are not qualified")
    expected = declared_metadata(project)
    for raw in (wheel_raw, sdist_raw):
        headers = BytesParser().parsebytes(raw)
        if headers.get_all("Metadata-Version") not in [
            [x] for x in ("2.1", "2.2", "2.3", "2.4", "2.5")
        ]:
            raise ValueError("unsupported generated metadata version")
        if any(
            headers.get_all(key) is not None
            for key in ("Import-Name", "Import-Namespace")
        ):
            raise ValueError("generated import declarations are not qualified")
        python = headers.get_all("Requires-Python", [])
        if len(python) != (1 if expected["requires_python"] else 0) or (
            python and specifier_identity(python[0]) != expected["requires_python"]
        ):
            raise ValueError("source Requires-Python differs")
        extras = headers.get_all("Provides-Extra", [])
        if (
            len(extras) != len({normalized_name(x) for x in extras})
            or {normalized_name(x) for x in extras} != expected["extras"]
        ):
            raise ValueError("source extras differ")
        requirements = [
            requirement_identity(x) for x in headers.get_all("Requires-Dist", [])
        ]
        if (
            len(requirements) != len(set(requirements))
            or set(requirements) != expected["requirements"]
        ):
            raise ValueError("source runtime requirements differ")
        if headers.get_all("License-File", []) != ["LICENSE"]:
            raise ValueError("source license declaration differs")
        if headers.get_all("Dynamic"):
            raise ValueError("dynamic artifact metadata is not qualified")
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.optionxform = str
    try:
        parser.read_string(
            entry_points.decode("utf-8") if entry_points is not None else ""
        )
    except (UnicodeDecodeError, configparser.Error) as error:
        raise ValueError("invalid entry-point metadata") from error
    actual = {name: dict(parser.items(name, raw=True)) for name in parser.sections()}
    if parser.defaults() or actual != expected["entries"]:
        raise ValueError("source entry points differ")
    return {
        "runtime_requirements": len(expected["requirements"]),
        "extras": len(expected["extras"]),
        "entry_point_groups": len(expected["entries"]),
    }


