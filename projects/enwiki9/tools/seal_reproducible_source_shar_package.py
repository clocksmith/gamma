#!/usr/bin/env python3
"""Seal deterministic direct-entry source-package reconstruction evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import tempfile
import zipfile


EXPECTED_ENTRIES = ["Makefile", "source_bundle.sh"]


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: pathlib.Path) -> dict[str, object]:
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def source_names(path: pathlib.Path) -> list[str]:
    names = [line.strip() for line in path.read_text().splitlines() if line.strip()]
    if not names or len(names) != len(set(names)):
        raise ValueError("source list must be nonempty and unique")
    for name in names:
        candidate = pathlib.PurePosixPath(name)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError(f"unsafe source path: {name}")
    return names


ZIP_METHODS = {
    "bzip2": zipfile.ZIP_BZIP2,
    "lzma": zipfile.ZIP_LZMA,
}


def inspect_zip(path: pathlib.Path, *, expected_method: str) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        bad = archive.testzip()
        methods = [info.compress_type for info in archive.infolist()]
        return {
            "entries": names,
            "direct_entries_ok": names == EXPECTED_ENTRIES,
            "integrity_ok": bad is None,
            "all_entries_bzip2": all(
                method == zipfile.ZIP_BZIP2 for method in methods
            ),
            "compression_method": expected_method,
            "all_entries_expected_method": all(
                method == ZIP_METHODS[expected_method] for method in methods
            ),
            "comment_bytes": len(archive.comment),
        }


def verify_reconstruction(
    *, root: pathlib.Path, names: list[str], source_zip: pathlib.Path
) -> tuple[bool, str]:
    with tempfile.TemporaryDirectory(prefix="enwiki9-source-package-") as temporary:
        temporary_root = pathlib.Path(temporary)
        package = temporary_root / "package"
        restored = temporary_root / "restored"
        with zipfile.ZipFile(source_zip) as archive:
            archive.extractall(package)
        subprocess.run(
            ["sh", str(package / "source_bundle.sh"), str(restored)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for name in names:
            if (root / name).read_bytes() != (restored / name).read_bytes():
                return False, name
    return True, ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=pathlib.Path, required=True)
    parser.add_argument("--file-list", type=pathlib.Path, required=True)
    parser.add_argument("--bundle-a", type=pathlib.Path, required=True)
    parser.add_argument("--bundle-b", type=pathlib.Path, required=True)
    parser.add_argument("--zip-a", type=pathlib.Path, required=True)
    parser.add_argument("--zip-b", type=pathlib.Path, required=True)
    parser.add_argument("--dictionary-name", default="english.dic")
    parser.add_argument(
        "--zip-method",
        choices=tuple(ZIP_METHODS),
        default="bzip2",
        help="required compression method for both source ZIPs",
    )
    parser.add_argument("--clean-backend-a", type=pathlib.Path)
    parser.add_argument("--clean-backend-b", type=pathlib.Path)
    parser.add_argument("--clean-program-a", type=pathlib.Path)
    parser.add_argument("--clean-program-b", type=pathlib.Path)
    parser.add_argument("--reference-backend", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    for path in (
        args.root,
        args.file_list,
        args.bundle_a,
        args.bundle_b,
        args.zip_a,
        args.zip_b,
    ):
        if not path.exists():
            raise FileNotFoundError(path)
    names = source_names(args.file_list)
    dictionary = args.root / args.dictionary_name
    if args.dictionary_name not in names or not dictionary.is_file():
        raise ValueError("counted dictionary is absent from the source list")

    bundle_identity = args.bundle_a.read_bytes() == args.bundle_b.read_bytes()
    zip_identity = args.zip_a.read_bytes() == args.zip_b.read_bytes()
    zip_a = inspect_zip(args.zip_a, expected_method=args.zip_method)
    zip_b = inspect_zip(args.zip_b, expected_method=args.zip_method)
    reconstruction_ok, mismatch = verify_reconstruction(
        root=args.root, names=names, source_zip=args.zip_a
    )
    build_paths = (
        args.clean_backend_a,
        args.clean_backend_b,
        args.clean_program_a,
        args.clean_program_b,
        args.reference_backend,
    )
    build_requested = any(path is not None for path in build_paths)
    if build_requested and not all(path is not None for path in build_paths):
        raise ValueError("clean-build arguments must be supplied as a complete set")
    clean_backend_identity = None
    clean_program_identity = None
    reference_backend_identity = None
    build_artifacts: dict[str, object] = {}
    if build_requested:
        for path in build_paths:
            assert path is not None
            if not path.is_file():
                raise FileNotFoundError(path)
        clean_backend_identity = (
            args.clean_backend_a.read_bytes() == args.clean_backend_b.read_bytes()
        )
        clean_program_identity = (
            args.clean_program_a.read_bytes() == args.clean_program_b.read_bytes()
        )
        reference_backend_identity = (
            args.clean_backend_a.read_bytes() == args.reference_backend.read_bytes()
        )
        build_artifacts = {
            "clean_backend_a": artifact(args.clean_backend_a),
            "clean_backend_b": artifact(args.clean_backend_b),
            "clean_program_a": artifact(args.clean_program_a),
            "clean_program_b": artifact(args.clean_program_b),
            "reference_backend": artifact(args.reference_backend),
        }
    clean_build_complete = bool(
        build_requested
        and clean_backend_identity
        and clean_program_identity
        and reference_backend_identity
    )
    proof_complete = bool(
        bundle_identity
        and zip_identity
        and zip_a["direct_entries_ok"]
        and zip_a["integrity_ok"]
        and zip_a["all_entries_expected_method"]
        and zip_a["comment_bytes"] == 0
        and zip_b == zip_a
        and reconstruction_ok
    )
    receipt = {
        "schema": "reproducible_source_shar_package_v1",
        "evidence_level": "deterministic_counted_source_package_reconstruction",
        "artifacts": {
            "source_root": str(args.root.resolve()),
            "file_list": artifact(args.file_list),
            "bundle_a": artifact(args.bundle_a),
            "bundle_b": artifact(args.bundle_b),
            "zip_a": artifact(args.zip_a),
            "zip_b": artifact(args.zip_b),
            "dictionary": artifact(dictionary),
            **build_artifacts,
        },
        "source_files": len(names),
        "zip": zip_a,
        "proof": {
            "bundle_identity": bundle_identity,
            "zip_identity": zip_identity,
            "reconstructed_source_identity": reconstruction_ok,
            "first_mismatched_source": mismatch or None,
            "clean_build_requested": build_requested,
            "clean_backend_identity": clean_backend_identity,
            "clean_program_identity": clean_program_identity,
            "reference_backend_identity": reference_backend_identity,
            "clean_build_complete": clean_build_complete,
            "proof_complete": proof_complete,
        },
        "decision": {
            "clean_build_required": not clean_build_complete,
            "wrapper_replay_required": True,
            "promotion_authorized": False,
        },
        "claim_boundary": (
            "This receipt proves deterministic counted source-package bytes and "
            "verbatim source reconstruction only. A clean build plus exact wrapper "
            "archive identity, roundtrip, determinism, memory, runtime, and full-corpus "
            "accounting remain required."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if proof_complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
