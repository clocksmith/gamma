#!/usr/bin/env python3
"""Materialize and count one exact enwiki9 codec dependency closure."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
from typing import Any

import research_contracts


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SUFFIXES = {".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".rs", ".zig"}
BUILD_NAMES = {"makefile", "cmakelists.txt", "build.zig", "build.rs"}
LICENSE_PREFIXES = {"copying", "license", "notice"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def parse_command(value: str, name: str) -> list[str]:
    command = json.loads(value)
    if not isinstance(command, list) or not command or not all(
        isinstance(token, str) and token for token in command
    ):
        raise ValueError(f"{name} must be a non-empty JSON array of strings")
    return command


def role(path: Path, explicit: dict[str, str]) -> str:
    relative = path.as_posix()
    if relative in explicit:
        return explicit[relative]
    name = path.name.lower()
    if any(name.startswith(prefix) for prefix in LICENSE_PREFIXES):
        return "license"
    if name in BUILD_NAMES:
        return "build"
    if path.suffix.lower() in SOURCE_SUFFIXES:
        return "source"
    if path.suffix.lower() in {".json", ".toml", ".yaml", ".yml", ".ini"}:
        return "configuration"
    if path.suffix.lower() in {".bin", ".model", ".weights"}:
        return "model"
    if path.suffix.lower() in {".dict", ".dictionary"}:
        return "dictionary"
    return "other"


def source_files(source_root: Path) -> list[tuple[Path, Path]]:
    files: list[tuple[Path, Path]] = []
    for path in sorted(source_root.rglob("*")):
        relative = path.relative_to(source_root)
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f"dependency closure cannot contain symlink: {relative}")
        if not stat.S_ISREG(mode):
            raise ValueError(f"dependency closure cannot contain special file: {relative}")
        files.append((relative, path))
    if not files:
        raise ValueError("dependency closure source is empty")
    return files


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def materialize(args: argparse.Namespace) -> Path:
    source_root = args.source_root.resolve()
    bundle = args.bundle.resolve()
    if ROOT.resolve() not in source_root.parents or not source_root.is_dir():
        raise ValueError("source root must be an existing enwiki9 project directory")
    release_root = (ROOT / "results" / args.candidate_id / "release").resolve()
    if bundle.parent != release_root or bundle.exists():
        raise ValueError(
            "bundle must be a new results/<candidate>/release/<receipt> directory"
        )

    dependencies = load_json(args.dependencies)
    if not isinstance(dependencies, list):
        raise ValueError("dependencies JSON must contain an array")
    explicit_roles = load_json(args.roles) if args.roles is not None else {}
    if not isinstance(explicit_roles, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in explicit_roles.items()
    ):
        raise ValueError("roles JSON must map relative paths to role names")

    files = source_files(source_root)
    package = bundle / "package"
    package.mkdir(parents=True)
    try:
        records: list[dict[str, Any]] = []
        for relative, source in files:
            destination = package / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
            records.append(
                {
                    "path": relative.as_posix(),
                    "bytes": destination.stat().st_size,
                    "sha256": digest(destination),
                    "role": role(relative, explicit_roles),
                }
            )
        if args.entry_point not in {record["path"] for record in records}:
            raise ValueError("entry point is not present in the staged package")

        missing = sorted(set(args.missing))
        if not args.declare_complete:
            missing.append("operator did not declare dependency closure complete")
        required_options = sorted(set(args.required_option))
        manifest = {
            "schema": "gamma.enwiki9.dependency-closure.v1",
            "objective": research_contracts.objective_binding(),
            "candidateId": args.candidate_id,
            "candidateTreeSha256": research_contracts.candidate_tree_digest(records),
            "candidateTreeDigestAlgorithm": "sha256-canonical-counted-files-v1",
            "candidateRoot": "package",
            "entryPoint": args.entry_point,
            "platform": args.platform,
            "commands": {
                "build": parse_command(args.build_command_json, "build command"),
                "compress": parse_command(
                    args.compress_command_json, "compress command"
                ),
                "decompress": parse_command(
                    args.decompress_command_json, "decompress command"
                ),
            },
            "countedFiles": records,
            "requiredOptions": required_options,
            "requiredOptionBytes": sum(
                len(value.encode("utf-8")) for value in required_options
            ),
            "totalPackageBytes": sum(record["bytes"] for record in records),
            "dependencies": dependencies,
            "complete": args.declare_complete and not missing,
            "missing": missing,
            "generatedUtc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
        }
        manifest_path = bundle / "dependency-closure.json"
        temporary = manifest_path.with_name(f".{manifest_path.name}.{os.getpid()}.tmp")
        temporary.write_text(json.dumps(manifest, indent=2) + "\n")
        os.replace(temporary, manifest_path)
        research_contracts.validate_artifact(manifest_path)
        return manifest_path
    except Exception:
        shutil.rmtree(bundle, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--entry-point", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--build-command-json", required=True)
    parser.add_argument("--compress-command-json", required=True)
    parser.add_argument("--decompress-command-json", required=True)
    parser.add_argument("--dependencies", type=Path, required=True)
    parser.add_argument("--roles", type=Path)
    parser.add_argument("--required-option", action="append", default=[])
    parser.add_argument("--missing", action="append", default=[])
    parser.add_argument("--declare-complete", action="store_true")
    args = parser.parse_args()
    path = materialize(args)
    print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
