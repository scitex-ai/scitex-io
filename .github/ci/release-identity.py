#!/usr/bin/env python3
"""Bind a IO release to one tag, source commit and two verified artifacts."""

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

REPOSITORY = "scitex-ai/scitex-io"
TAG = re.compile(r"v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)")
SHA = re.compile(r"[0-9a-f]{40}")
LOGIN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")
PROOF = "release-proof.json"


def _load_control(name, filename):
    """Load only the fixed registered helper; never add checkout dirs to sys.path."""
    import importlib.util
    import sys
    path = Path(__file__).resolve().parent / filename
    if path.is_symlink() or not path.is_file():
        raise ValueError("release helper is not a regular file")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_artifacts = _load_control('_io_release_artifacts', '_release_artifacts.py')
_source = _load_control('_io_release_source', '_release_source.py')
regular_bytes = _artifacts.regular_bytes
wheel_identity = _artifacts.wheel_identity
sdist_identity = _artifacts.sdist_identity
source_payload_identity = _source.source_payload_identity


def api(path, status=200, *, open_url=urllib.request.urlopen):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request("https://api.github.com/" + path, headers=headers)
    with open_url(request, timeout=10) as response:
        if response.status != status:
            raise ValueError("GitHub identity response did not match")
        if status == 204:
            return {"status": 204}
        body = response.read(1048577)
        if len(body) > 1048576:
            raise ValueError("GitHub identity response too large")
        return json.loads(body)


def member_admission(query=api):
    if os.environ.get("GITHUB_REPOSITORY") != REPOSITORY:
        raise ValueError("release repository does not match")
    actors = {
        os.environ.get("GITHUB_ACTOR", ""),
        os.environ.get("GITHUB_TRIGGERING_ACTOR", ""),
    }
    if not actors or any(not LOGIN.fullmatch(actor) for actor in actors):
        raise ValueError("release actor is missing or malformed")
    for actor in actors:
        if query("orgs/scitex-ai/public_members/" + actor, status=204) != {
            "status": 204
        }:
            raise ValueError("organization membership is not confirmed")


def resolve(tag, query=api):
    if not TAG.fullmatch(tag):
        raise ValueError("release requires an existing vX.Y.Z tag")
    prefix = "repos/" + REPOSITORY
    before = query(prefix + "/branches/main")
    if (before.get("name") != "main" or before.get("protected") is not True
        or not SHA.fullmatch(before.get("commit", {}).get("sha", ""))):
        raise ValueError("release main is not protected and qualified")
    main_commit = before["commit"]["sha"]
    ref = query(prefix + "/git/ref/tags/" + tag)
    if ref.get("ref") != "refs/tags/" + tag:
        raise ValueError("returned tag ref differs")
    item = ref["object"]
    seen = set()
    for _ in range(5):
        digest = item.get("sha", "")
        if not SHA.fullmatch(digest) or digest in seen:
            raise ValueError("invalid or cyclic tag object")
        seen.add(digest)
        if item.get("type") == "commit":
            break
        if item.get("type") != "tag":
            raise ValueError("tag does not resolve to a commit")
        item = query(prefix + "/git/tags/" + digest)["object"]
    else:
        raise ValueError("tag annotation depth exceeded")
    commit = item["sha"]
    comparison = query(prefix + "/compare/" + commit + "..." + main_commit)
    if comparison.get("base_commit", {}).get("sha") != commit or comparison.get(
        "status"
    ) not in {"ahead", "identical"}:
        raise ValueError("release source has not been promoted to main")
    content = query(prefix + "/contents/pyproject.toml?ref=" + commit)
    if content.get("encoding") != "base64":
        raise ValueError("unsupported metadata encoding")
    raw = base64.b64decode(content["content"].replace("\n", ""), validate=True)
    if len(raw) > 131072 or hashlib.sha1(
        b"blob " + str(len(raw)).encode() + b"\0" + raw
    ).hexdigest() != content.get("sha"):
        raise ValueError("release metadata Git identity differs")
    project = tomllib.loads(raw.decode())["project"]
    if (
        project["name"].replace("_", "-").lower() != "scitex-io"
        or project["version"] != tag[1:]
    ):
        raise ValueError("tag and project metadata differ")
    after = query(prefix + "/branches/main")
    if (after.get("name") != "main" or after.get("protected") is not True
        or after.get("commit", {}).get("sha") != main_commit):
        raise ValueError("release main changed during source qualification")
    return {"tag": tag, "commit": commit, "version": tag[1:]}


def artifact_proof(directory, tag, commit, run, attempt, source_root=Path(".")):
    if (
        not TAG.fullmatch(tag)
        or not SHA.fullmatch(commit)
        or not run.isdigit()
        or not attempt.isdigit()
    ):
        raise ValueError("release identity is malformed")
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("artifact directory is unsafe")
    files = sorted(path for path in directory.iterdir() if path.name != PROOF)
    if (
        len(files) != 2
        or sum(path.name.endswith(".whl") for path in files) != 1
        or sum(path.name.endswith(".tar.gz") for path in files) != 1
    ):
        raise ValueError("release requires exactly one wheel and one sdist")
    rows = []
    payloads = {}
    for path in files:
        if (
            not path.name.startswith("scitex_io-" + tag[1:] + "-")
            and path.name != "scitex_io-" + tag[1:] + ".tar.gz"
        ):
            raise ValueError("artifact filename version differs")
        raw = regular_bytes(path)
        payloads["wheel" if path.name.endswith(".whl") else "sdist"] = raw
        identity = (
            wheel_identity(raw, tag[1:])
            if path.name.endswith(".whl")
            else sdist_identity(raw, tag[1:])
        )
        rows.append(
            {
                "name": path.name,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                **identity,
            }
        )
    source_identity = source_payload_identity(
        payloads["wheel"], payloads["sdist"], commit, source_root
    )
    return {
        "schema": "scitex-io-release/v1",
        "repository": REPOSITORY,
        "tag": tag,
        "commit": commit,
        "run": run,
        "attempt": attempt,
        "files": rows,
        "source_membership": source_identity,
    }


def main(query=api):
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["resolve", "write-proof", "verify-proof"])
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit")
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--revalidate", action="store_true")
    args = parser.parse_args()
    if args.mode == "resolve":
        member_admission(query)
        identity = resolve(args.tag, query)
        if (
            os.environ.get("GITHUB_EVENT_NAME") == "push"
            and os.environ.get("GITHUB_SHA") != identity["commit"]
        ):
            raise ValueError("push event and tag commit differ")
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            for key, value in identity.items():
                stream.write(key + "=" + value + "\n")
        print(json.dumps(identity))
        return
    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    if actual != args.commit:
        raise ValueError("checkout and release commit differ")
    proof = artifact_proof(
        args.dist,
        args.tag,
        args.commit or "",
        os.environ.get("GITHUB_RUN_ID", ""),
        os.environ.get("GITHUB_RUN_ATTEMPT", ""),
    )
    path = args.dist / PROOF
    if args.mode == "write-proof":
        with os.fdopen(
            os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w"
        ) as stream:
            json.dump(proof, stream, indent=2)
    elif json.loads(regular_bytes(path)) != proof:
        raise ValueError("artifact proof or byte identity differs")
    if args.revalidate:
        member_admission(query)
        if resolve(args.tag, query) != {
            "tag": args.tag,
            "commit": args.commit,
            "version": args.tag[1:],
        }:
            raise ValueError("release tag identity changed")
    print(json.dumps(proof))


if __name__ == "__main__":
    main()
