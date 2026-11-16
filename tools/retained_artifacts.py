#!/usr/bin/env python3
"""Retain selected public Gamma Git bytes; no uploads, history rewrite or WORM claim."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import BinaryIO, Iterator
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

SCHEMA = "gamma.retained-artifacts/v1"
REPOSITORY = "clocksmith/gamma"
CHUNK_BYTES = 64 * 1024
GIT_ENV = {**os.environ, "GIT_NO_LAZY_FETCH": "1"}


def relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        raise ValueError("Artifact paths must be repository-relative POSIX file paths")
    if any(part in ("", ".", "..") or part.lower() == ".git" for part in value.split("/")):
        raise ValueError("Artifact path contains an absolute, empty, Git-internal or traversing component")
    return value


def hex_id(value: object, digits: int) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{%d}" % digits, value) is not None


def artifact_url(revision: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{quote(path, safe='/')}"


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "--literal-pathspecs", "-C", str(repo), *args], env=GIT_ENV,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=check)


@contextmanager
def local_blob(repo: Path, row: dict) -> Iterator[BinaryIO]:
    child = subprocess.Popen(["git", "-C", str(repo), "cat-file", "blob", row["gitBlob"]],
                             env=GIT_ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        yield child.stdout
        if child.wait() != 0:
            raise ValueError(f"Git blob unavailable without fetching: {row['path']}")
    finally:
        if child.poll() is None:
            child.kill()
        child.wait()
        child.stdout.close()
        child.stderr.close()


def measure(stream: BinaryIO, row: dict, destination: BinaryIO | None = None) -> tuple[int, str]:
    count = 0
    digest = hashlib.sha256()
    git_digest = hashlib.sha1(f"blob {row['bytes']}\0".encode(), usedforsecurity=False)
    while True:
        chunk = stream.read(min(CHUNK_BYTES, row["bytes"] - count + 1))
        if not chunk:
            break
        count += len(chunk)
        if count > row["bytes"]:
            raise ValueError(f"Artifact exceeds its declared byte count: {row['path']}")
        digest.update(chunk)
        git_digest.update(chunk)
        if destination is not None:
            destination.write(chunk)
    if count != row["bytes"] or git_digest.hexdigest() != row["gitBlob"]:
        raise ValueError(f"Artifact size or Git identity mismatch: {row['path']}")
    if row.get("sha256") and digest.hexdigest() != row["sha256"]:
        raise ValueError(f"Artifact SHA-256 mismatch: {row['path']}")
    return count, digest.hexdigest()


def build_catalog(repo: Path, revision: str, paths: list[str]) -> dict:
    if not hex_id(revision, 40) or not isinstance(paths, list) or not paths:
        raise ValueError("Build requires a full commit SHA and nonempty explicit path array")
    names = [relative_path(path) for path in paths]
    if len(set(names)) != len(names):
        raise ValueError("Duplicate artifact path")
    if git(repo, "cat-file", "-t", revision).stdout.strip() != b"commit":
        raise ValueError("Source revision must identify a commit")
    # A local remote-tracking reference is necessary, not proof of remote retention.
    # The migration must additionally exercise pinned remote restore before removal.
    if git(repo, "merge-base", "--is-ancestor", revision, "refs/remotes/origin/main", check=False).returncode:
        raise ValueError("Source commit is not in origin/main; publish and verify it before retention")
    listing = git(repo, "ls-tree", "-lz", "--full-tree", revision, "--", *names).stdout
    rows = {}
    for entry in listing.split(b"\0"):
        if not entry:
            continue
        metadata, name = entry.split(b"\t", 1)
        mode, kind, blob, size = metadata.decode().split()
        name = name.decode("utf-8")
        if name not in names or kind != "blob" or mode not in ("100644", "100755"):
            raise ValueError("Only explicitly named ordinary files may be retained")
        row = {"path": name, "sourceCommit": revision, "gitBlob": blob, "bytes": int(size),
               "mode": mode, "url": artifact_url(revision, name)}
        with local_blob(repo, row) as stream:
            _, row["sha256"] = measure(stream, row)
        rows[name] = row
    if set(rows) != set(names):
        raise ValueError("Some explicit artifact paths are absent from the source commit")
    files = [rows[name] for name in sorted(rows)]
    return {"schema": SCHEMA, "repository": REPOSITORY, "fileCount": len(files),
            "bytes": sum(row["bytes"] for row in files), "files": files}


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate catalog JSON key: {key}")
        result[key] = value
    return result


def validate_row(row: dict) -> str:
    if not isinstance(row, dict):
        raise ValueError("Catalog entries must be objects")
    name = relative_path(row.get("path"))
    if not hex_id(row.get("sourceCommit"), 40) or not hex_id(row.get("gitBlob"), 40):
        raise ValueError("Invalid Git identity")
    if not hex_id(row.get("sha256"), 64) or type(row.get("bytes")) is not int or not 0 <= row["bytes"] < 2**63:
        raise ValueError("Invalid artifact hash or byte count")
    if row.get("mode") not in ("100644", "100755") or row.get("url") != artifact_url(row["sourceCommit"], name):
        raise ValueError("Invalid mode or noncanonical remote artifact URL")
    return name


def read_catalog(path: Path) -> dict:
    catalog = json.loads(path.read_text(), object_pairs_hook=unique_keys)
    if not isinstance(catalog, dict) or catalog.get("schema") != SCHEMA or catalog.get("repository") != REPOSITORY:
        raise ValueError("Unsupported retained artifact catalog")
    files = catalog.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("Catalog must contain files")
    seen = set()
    for row in files:
        name = validate_row(row)
        if name in seen:
            raise ValueError("Duplicate artifact path")
        seen.add(name)
    if type(catalog.get("fileCount")) is not int or catalog["fileCount"] != len(files) or type(catalog.get("bytes")) is not int or catalog["bytes"] != sum(row["bytes"] for row in files):
        raise ValueError("Catalog totals mismatch")
    return catalog


def selected(catalog: dict, prefix: str | None) -> list[dict]:
    if prefix is None:
        return catalog["files"]
    prefix = relative_path(prefix)
    rows = [row for row in catalog["files"] if row["path"] == prefix or row["path"].startswith(prefix + "/")]
    if not rows:
        raise ValueError("No retained artifacts match that prefix")
    return rows


@contextmanager
def parent_directory(root: Path, path: str, create: bool) -> Iterator[tuple[int, str]]:
    """Use directory descriptors so replacing a parent with a symlink cannot redirect writes."""
    relative_path(path)
    if not hasattr(os, "O_NOFOLLOW") or os.open not in os.supports_dir_fd:
        raise ValueError("Restore/check publication requires POSIX directory descriptors and atomic hard links")
    if create:
        root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("Artifact destination root must not be a symlink")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(root, flags)
    try:
        for part in path.split("/")[:-1]:
            if create:
                try:
                    os.mkdir(part, mode=0o755, dir_fd=descriptor)
                except FileExistsError:
                    pass
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor, path.split("/")[-1]
    finally:
        os.close(descriptor)


def check_at(directory: int, name: str, row: dict) -> None:
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size != row["bytes"]:
            raise ValueError(f"Existing artifact type or size differs: {row['path']}")
        if stat.S_IMODE(info.st_mode) != int(row["mode"][-3:], 8):
            raise ValueError(f"Existing artifact mode differs: {row['path']}")
        measure(stream, row)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        raise HTTPError(request.full_url, code, "Artifact redirects are not permitted", headers, fp)


def open_remote(row: dict):
    return build_opener(NoRedirect()).open(Request(row["url"], headers={"User-Agent": "gamma-retained-artifacts/1"}), timeout=30)


def restore_file(row: dict, root: Path, repo: Path, fetch: bool = False,
                 from_restored: str | None = None) -> Path:
    validate_row(row)
    with parent_directory(root, row["path"], create=True) as (directory, name):
        try:
            check_at(directory, name, row)
            return root / row["path"]
        except FileNotFoundError:
            pass
        temporary = f".{name}.restore-{uuid4().hex}"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        try:
            with os.fdopen(descriptor, "wb") as destination:
                available = git(repo, "cat-file", "-e", row["gitBlob"], check=False).returncode == 0
                if from_restored is not None:
                    # Reuse a previous verified identity without another network
                    # transfer. Copy and rehash; never couple outputs by hard link.
                    with parent_directory(root, from_restored, create=False) as (source_directory, source_name):
                        source_fd = os.open(source_name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                            dir_fd=source_directory)
                        with os.fdopen(source_fd, "rb") as stream:
                            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                                raise ValueError("Restored source must be an ordinary file")
                            measure(stream, row, destination)
                elif available:
                    with local_blob(repo, row) as stream:
                        measure(stream, row, destination)
                elif fetch:
                    with open_remote(row) as response:
                        if response.status != 200 or response.geturl() != row["url"]:
                            raise ValueError("Remote artifact response is not the pinned URL")
                        length = response.headers.get("Content-Length")
                        if length is not None and int(length) != row["bytes"]:
                            raise ValueError("Remote Content-Length differs from catalog byte count")
                        measure(response, row, destination)
                else:
                    raise ValueError(f"Local Git blob absent for {row['path']}; explicit --fetch is required")
                destination.flush()
                os.fchmod(destination.fileno(), int(row["mode"][-3:], 8))
                os.fsync(destination.fileno())
            # link is atomic and refuses an existing destination, even a racing writer.
            os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
            os.fsync(directory)
        finally:
            os.unlink(temporary, dir_fd=directory)
    return root / row["path"]


def restore_files(rows: list[dict], root: Path, repo: Path, fetch: bool = False) -> None:
    restored = {}
    for row in rows:
        identity = (row["gitBlob"], row["sha256"], row["bytes"])
        restore_file(row, root, repo, fetch, from_restored=restored.get(identity))
        restored[identity] = row["path"]


def check_files(rows: list[dict], root: Path) -> None:
    for row in rows:
        with parent_directory(root, row["path"], create=False) as (directory, name):
            check_at(directory, name, row)


def check_boundary(rows: list[dict], repo: Path) -> None:
    repo = Path(git(repo, "rev-parse", "--show-toplevel").stdout.decode().strip())
    tracked = git(repo, "ls-files", "-z", "--", *(row["path"] for row in rows)).stdout
    if tracked:
        raise ValueError("Retained output is still tracked: " + ", ".join(tracked.decode().rstrip("\0").split("\0")))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--revision", required=True)
    build.add_argument("--paths", required=True, help="JSON array of explicit repository-relative files")
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--repo", type=Path, default=Path.cwd())
    for name in ("restore", "check", "check-boundary"):
        command = commands.add_parser(name)
        command.add_argument("--catalog", type=Path, required=True)
        command.add_argument("--root", type=Path, required=True)
        command.add_argument("--prefix")
        if name == "restore":
            command.add_argument("--fetch", action="store_true")
            command.add_argument("--repo", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            catalog = build_catalog(args.repo, args.revision, json.loads(args.paths))
            data = (json.dumps(catalog, indent=2, ensure_ascii=False) + "\n").encode()
            with parent_directory(args.out.parent, args.out.name, create=True) as (directory, name):
                try:
                    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                except FileNotFoundError:
                    descriptor = None
                if descriptor is not None:
                    with os.fdopen(descriptor, "rb") as existing:
                        if not stat.S_ISREG(os.fstat(existing.fileno()).st_mode) or existing.read(len(data) + 1) != data:
                            raise ValueError("Refusing to replace a different existing catalog")
                else:
                    temporary = f".{name}.build-{uuid4().hex}"
                    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644, dir_fd=directory)
                    try:
                        with os.fdopen(descriptor, "wb") as output:
                            output.write(data)
                            output.flush()
                            os.fsync(output.fileno())
                        os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
                        os.fsync(directory)
                    finally:
                        os.unlink(temporary, dir_fd=directory)
            print(f"Cataloged {catalog['fileCount']} explicitly selected files ({catalog['bytes']} bytes)")
        else:
            rows = selected(read_catalog(args.catalog), args.prefix)
            if args.command == "restore":
                restore_files(rows, args.root, args.repo, args.fetch)
            elif args.command == "check":
                check_files(rows, args.root)
            else:
                check_boundary(rows, args.root)
            print(f"{args.command}: verified {len(rows)} retained artifacts")
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"retained-artifacts: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
