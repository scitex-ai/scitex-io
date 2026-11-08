"""Real ZIP transactions preserve payloads, metadata and failed-write state."""

import hashlib
import json
import zipfile

import pytest

from scitex_io.bundle import ZipBundle


def _archive(tmp_path):
    path = tmp_path / "owned.zip"
    info = zipfile.ZipInfo("payload/data.csv", (2023, 4, 5, 6, 7, 8))
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100640 << 16
    info.comment = b"owned member comment"
    info.extra = b"\xca\xfe\x02\x00ok"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("spec.json", json.dumps({"note": "old", "custom": {"keep": 1}}))
        archive.writestr(info, b"x,y\n1,2\n")
        archive.writestr("empty/", b"")
        archive.comment = b"owned archive comment"
    return path


def _contents(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_append_without_changes_keeps_every_member(tmp_path):
    # Arrange
    path = _archive(tmp_path)
    before = _contents(path)
    # Act
    with ZipBundle(path, "a"):
        pass
    # Assert
    assert _contents(path) == before


def test_append_updates_spec_without_dropping_research_payload(tmp_path):
    # Arrange
    path = _archive(tmp_path)
    # Act
    with ZipBundle(path, "a") as bundle:
        spec = bundle.read_json()
        spec["note"] = "updated"
        bundle.write_json("spec.json", spec)
    contents = _contents(path)
    # Assert
    assert (contents.get("payload/data.csv"), contents.get("empty/"),
            json.loads(contents["spec.json"])) == (
        b"x,y\n1,2\n", b"", {"note": "updated", "custom": {"keep": 1}}
    )


def test_append_keeps_untouched_member_metadata(tmp_path):
    # Arrange
    path = _archive(tmp_path)
    # Act
    with ZipBundle(path, "a") as bundle:
        bundle.write_json("spec.json", {"note": "updated"})
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo("payload/data.csv")
    # Assert
    assert (info.date_time, info.compress_type, info.create_system,
            info.external_attr, info.comment, info.extra) == (
        (2023, 4, 5, 6, 7, 8), zipfile.ZIP_STORED, 3,
        0o100640 << 16, b"owned member comment", b"\xca\xfe\x02\x00ok"
    )


def test_append_keeps_archive_comment(tmp_path):
    # Arrange
    path = _archive(tmp_path)
    # Act
    with ZipBundle(path, "a") as bundle:
        bundle.write_json("spec.json", {"note": "updated"})
    with zipfile.ZipFile(path) as archive:
        comment = archive.comment
    # Assert
    assert comment == b"owned archive comment"


@pytest.mark.parametrize("mode", ["w", "a"])
def test_repeated_updates_commit_only_the_final_member_value(tmp_path, mode):
    # Arrange
    path = _archive(tmp_path)
    # Act
    with ZipBundle(path, mode) as bundle:
        bundle.write_bytes("spec.json", b"first")
        bundle.write_bytes("spec.json", b"last")
    with zipfile.ZipFile(path) as archive:
        observation = (archive.namelist().count("spec.json"), archive.read("spec.json"))
    # Assert
    assert observation == (1, b"last")


def test_new_legacy_prefix_reads_work_before_commit_without_creating_alias_members(tmp_path):
    # Arrange
    path = tmp_path / "owned.zip"
    # Act
    with ZipBundle(path, "w") as bundle:
        bundle.write_json("old.d/spec.json", {"note": "owned"})
        spec = bundle.read_json("spec.json")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    # Assert
    assert (spec, names) == ({"note": "owned"}, ["old.d/spec.json"])


def test_existing_legacy_prefix_reads_do_not_create_alias_members(tmp_path):
    # Arrange
    path = tmp_path / "owned.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("old.d/spec.json", '{"note":"owned"}')
    # Act
    with ZipBundle(path, "a") as bundle:
        spec = bundle.read_json("spec.json")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    # Assert
    assert (spec, names) == ({"note": "owned"}, ["old.d/spec.json"])


@pytest.mark.parametrize("mode", ["w", "a"])
def test_body_failure_preserves_original_and_removes_pending_archive(tmp_path, mode):
    # Arrange
    path = _archive(tmp_path)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    error = None
    # Act
    try:
        with ZipBundle(path, mode) as bundle:
            bundle.write_json("spec.json", {"note": "uncommitted"})
            pending = bundle._temp_path
            raise ValueError("owned serialization failure")
    except ValueError as caught:
        error = str(caught)
    # Assert
    assert (hashlib.sha256(path.read_bytes()).hexdigest(), pending.exists(),
            bundle._zipfile.fp, error) == (before, False, None, "owned serialization failure")


def test_real_commit_failure_removes_pending_archive_and_preserves_error(tmp_path):
    # Arrange -- the destination parent deliberately does not exist.
    path = tmp_path / "absent" / "owned.zip"
    error = None
    # Act
    try:
        with ZipBundle(path, "w") as bundle:
            bundle.write_bytes("payload.bin", b"owned")
            pending = bundle._temp_path
    except OSError as caught:
        error = caught
    # Assert
    assert (isinstance(error, OSError), pending.exists(), path.exists(),
            path.parent.exists(), bundle._zipfile.fp) == (True, False, False, False, None)


def test_mutable_input_keeps_its_write_time_bytes(tmp_path):
    # Arrange
    path = tmp_path / "owned.zip"
    payload = bytearray(b"original")
    # Act
    with ZipBundle(path, "w") as bundle:
        bundle.write_bytes("payload.bin", payload)
        payload[:] = b"modified"
    # Assert
    assert _contents(path) == {"payload.bin": b"original"}


def test_closed_bundle_rejects_writes_without_changing_committed_data(tmp_path):
    # Arrange
    path = tmp_path / "owned.zip"
    with ZipBundle(path, "w") as bundle:
        bundle.write_bytes("payload.bin", b"committed")
    error = None
    # Act
    try:
        bundle.write_bytes("late.bin", b"must not be silently accepted")
    except ValueError as caught:
        error = str(caught)
    # Assert
    assert (error, _contents(path)) == (
        "Cannot write to a closed bundle", {"payload.bin": b"committed"}
    )


def test_invalid_input_fails_before_commit_and_preserves_original(tmp_path):
    # Arrange
    path = _archive(tmp_path)
    before = path.read_bytes()
    error = None
    # Act
    try:
        with ZipBundle(path, "a") as bundle:
            pending = bundle._temp_path
            bundle.write_bytes("payload.bin", 8)
    except TypeError as caught:
        error = caught
    # Assert
    assert (isinstance(error, TypeError), path.read_bytes(), pending.exists()) == (
        True, before, False
    )


def test_explicit_close_discards_changes_before_context_exit(tmp_path):
    # Arrange
    path = _archive(tmp_path)
    before = path.read_bytes()
    # Act
    with ZipBundle(path, "a") as bundle:
        bundle.write_bytes("payload.bin", b"uncommitted")
        pending = bundle._temp_path
        bundle.close()
    # Assert
    assert (path.read_bytes(), pending.exists()) == (before, False)


def test_reopened_append_context_starts_a_fresh_transaction(tmp_path):
    # Arrange
    path = _archive(tmp_path)
    bundle = ZipBundle(path, "a")
    # Act
    with bundle:
        bundle.write_json("spec.json", {"note": "first"})
    with bundle:
        bundle.write_json("spec.json", {"note": "second"})
    contents = _contents(path)
    # Assert
    assert (contents["payload/data.csv"], json.loads(contents["spec.json"])) == (
        b"x,y\n1,2\n", {"note": "second"}
    )


def test_reopened_reader_observes_current_archive_instead_of_stale_cache(tmp_path):
    # Arrange
    path = _archive(tmp_path)
    reader = ZipBundle(path)
    # Act
    with reader:
        first = reader.read_json()["note"]
    with ZipBundle(path, "a") as writer:
        writer.write_json("spec.json", {"note": "updated"})
    with reader:
        second = reader.read_json()["note"]
    # Assert
    assert (first, second) == ("old", "updated")


def test_nested_context_rejects_reentry_and_cleans_original_transaction(tmp_path):
    # Arrange
    path = _archive(tmp_path)
    before = path.read_bytes()
    bundle = ZipBundle(path, "a")
    error = None
    # Act
    try:
        with bundle:
            pending = bundle._temp_path
            bundle.write_json("spec.json", {"note": "uncommitted"})
            with bundle:
                pass
    except RuntimeError as caught:
        error = str(caught)
    # Assert
    assert (error, path.read_bytes(), pending.exists()) == (
        "Bundle is already opened", before, False
    )
