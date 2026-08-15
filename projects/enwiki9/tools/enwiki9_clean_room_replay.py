#!/usr/bin/env python3
"""Replay a full enwik9 package in independent sealed single-core sandboxes."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import socket
import subprocess
import sys
from typing import Any

import research_contracts


ROOT = Path(__file__).resolve().parents[1]
BWRAP = Path("/usr/bin/bwrap")
TASKSET = Path("/usr/bin/taskset")
GUARD = ROOT / "tools" / "run_with_rss_guard.py"
PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")
ENVIRONMENT = {
    "LC_ALL": "C",
    "PATH": "/usr/bin:/bin",
    "SOURCE_DATE_EPOCH": "0",
    "TZ": "UTC",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            value.update(chunk)
    return value.hexdigest()


def artifact(receipt_path: Path, path: Path) -> dict[str, Any]:
    return {
        "path": os.path.relpath(path.resolve(), receipt_path.parent.resolve()),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }


def reference(receipt_path: Path, path: Path) -> dict[str, str]:
    return {
        "path": os.path.relpath(path.resolve(), receipt_path.parent.resolve()),
        "sha256": f"sha256:{digest(path)}",
    }


def command_text(command: list[str]) -> str:
    return "\0".join(command)


def validate_command_contract(manifest: dict[str, Any]) -> None:
    commands = manifest["commands"]
    build_text = command_text(commands["build"])
    compress_text = command_text(commands["compress"])
    decompress_text = command_text(commands["decompress"])
    if "{corpus}" in build_text:
        raise ValueError("build command cannot access the canonical corpus")
    if "{corpus}" in decompress_text:
        raise ValueError("decompress command cannot access the canonical corpus")
    for placeholder, text, name in (
        ("{corpus}", compress_text, "compress"),
        ("{archive}", compress_text, "compress"),
        ("{archive}", decompress_text, "decompress"),
        ("{restored}", decompress_text, "decompress"),
    ):
        if placeholder not in text:
            raise ValueError(f"{name} command must contain {placeholder}")
    all_text = "\0".join((build_text, compress_text, decompress_text))
    if (
        "{entry_point}" not in all_text
        and manifest["entryPoint"] not in all_text
    ):
        raise ValueError("declared commands never invoke the counted entry point")


def expand_command(
    command: list[str],
    manifest: dict[str, Any],
    archive_name: str,
) -> list[str]:
    values = {
        "archive": f"/work/{archive_name}",
        "corpus": "/input/enwik9",
        "entry_point": f"/work/package/{manifest['entryPoint']}",
        "package": "/work/package",
        "restored": "/work/restored.enwik9",
        "scratch": "/work/tmp",
    }
    expanded: list[str] = []
    for token in command:
        unknown = sorted(set(PLACEHOLDER.findall(token)) - set(values))
        if unknown:
            raise ValueError(f"unknown command placeholders: {', '.join(unknown)}")
        for name, value in values.items():
            token = token.replace(f"{{{name}}}", value)
        expanded.append(token)
    return expanded


def sandbox_prefix(work: Path, corpus: Path | None) -> list[str]:
    command = [
        str(BWRAP),
        "--unshare-all",
        "--die-with-parent",
        "--new-session",
        "--hostname",
        "gamma-clean-room",
        "--ro-bind",
        "/usr",
        "/usr",
        "--symlink",
        "usr/bin",
        "/bin",
        "--symlink",
        "usr/lib",
        "/lib",
        "--symlink",
        "usr/lib64",
        "/lib64",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
        "--dir",
        "/input",
        "--bind",
        str(work),
        "/work",
    ]
    if corpus is not None:
        command.extend(("--ro-bind", str(corpus), "/input/enwik9"))
    command.extend(("--chdir", "/work/package", "--clearenv"))
    for name, value in sorted(ENVIRONMENT.items()):
        command.extend(("--setenv", name, value))
    command.append("--")
    return command


def verify_package_copy(
    package: Path,
    counted_files: list[dict[str, Any]],
) -> None:
    actual = sorted(
        path.relative_to(package).as_posix()
        for path in package.rglob("*")
        if path.is_file() and not path.is_symlink()
    )
    expected = sorted(record["path"] for record in counted_files)
    if actual != expected:
        raise ValueError("fresh package copy differs from the counted manifest")
    for record in counted_files:
        path = package / record["path"]
        if path.stat().st_size != record["bytes"] or digest(path) != record["sha256"]:
            raise ValueError(f"fresh package copy identity differs: {record['path']}")


def fresh_work(
    work_root: Path,
    name: str,
    package: Path,
    manifest: dict[str, Any],
) -> Path:
    work = work_root / name
    work.mkdir(parents=True)
    shutil.copytree(package, work / "package")
    (work / "tmp").mkdir()
    verify_package_copy(work / "package", manifest["countedFiles"])
    return work


def run_command(command: list[str], log_path: Path) -> int:
    with log_path.open("wb") as log:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env={},
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    return completed.returncode


def guarded_command(
    args: argparse.Namespace,
    label: str,
    phase: str,
    work: Path,
    sandbox_command: list[str],
    guard_path: Path,
    log_path: Path,
) -> tuple[list[str], int]:
    cpu = min(os.sched_getaffinity(0))
    objective = research_contracts.validate_objective()
    resources = objective["resources"]
    command = [
        sys.executable,
        str(GUARD),
        "--limit-kib",
        str(resources["memory"]["linuxGuardKiB"]),
        "--limit-mode",
        "tree",
        "--official-decimal-limit-kib",
        str(resources["memory"]["linuxGuardKiB"]),
        "--guard-json",
        str(guard_path),
        "--label",
        label,
        "--phase",
        phase,
        "--geekbench5-single-core-score",
        str(args.geekbench5_single_core_score),
        "--scratch-path",
        str(work),
        "--temporary-disk-limit-bytes",
        str(resources["temporaryDisk"]["maximumBytes"]),
        "--max-logical-cpus",
        "1",
        "--sample-interval",
        str(args.sample_interval_seconds),
        "--",
        str(TASKSET),
        "--cpu-list",
        str(cpu),
        *sandbox_command,
    ]
    return command, run_command(command, log_path)


def probe_sandbox(work: Path) -> dict[str, Any]:
    device_inner = ["/usr/bin/find", "/dev", "-maxdepth", "2", "-printf", "%p\n"]
    network_inner = ["/usr/bin/cat", "/proc/net/dev"]
    device = subprocess.run(
        sandbox_prefix(work, None) + device_inner,
        env={},
        capture_output=True,
        text=True,
        check=False,
    )
    network = subprocess.run(
        sandbox_prefix(work, None) + network_inner,
        env={},
        capture_output=True,
        text=True,
        check=False,
    )
    interfaces = sorted(
        line.split(":", 1)[0].strip()
        for line in network.stdout.splitlines()
        if ":" in line
    )
    return {
        "deviceCommand": device_inner,
        "deviceReturncode": device.returncode,
        "devicePaths": sorted(set(device.stdout.splitlines())),
        "networkCommand": network_inner,
        "networkReturncode": network.returncode,
        "networkInterfaces": interfaces,
    }


def guard_reference(
    clean_path: Path,
    guard_path: Path,
) -> dict[str, str]:
    research_contracts.validate_artifact(guard_path)
    return reference(clean_path, guard_path)


def guard_summary(paths: list[Path]) -> tuple[dict[str, bool], bool]:
    results = [research_contracts.validate_artifact(path)["checks"] for path in paths]
    summary = {
        "wallTimePass": all(result["wallTime"] for result in results),
        "memoryPass": all(result["memory"] for result in results),
        "temporaryDiskPass": all(result["temporaryDisk"] for result in results),
        "singleCorePass": all(result["singleCore"] for result in results),
    }
    complete = all(summary.values()) and all(result["command"] for result in results)
    return summary, complete


def host_identity() -> str:
    return "|".join((socket.gethostname(), platform.machine(), platform.release()))


def peer_identity_ok(
    peer: dict[str, Any] | None,
    manifest: dict[str, Any],
    archive_record: dict[str, Any],
) -> bool:
    return bool(
        peer is not None
        and peer["candidateId"] == manifest["candidateId"]
        and peer["candidateTreeSha256"] == manifest["candidateTreeSha256"]
        and peer["archive"]["bytes"] == archive_record["bytes"]
        and peer["archive"]["sha256"] == archive_record["sha256"]
        and peer["correctness"]["roundtripOk"]
        and peer["correctness"]["determinismOk"]
        and peer["verification"]["host"] != host_identity()
    )


def replay(args: argparse.Namespace) -> Path:
    manifest_path = args.manifest.resolve()
    manifest = load_json(manifest_path)
    research_contracts.validate_artifact(manifest_path)
    validate_command_contract(manifest)
    bundle = manifest_path.parent
    package = bundle / manifest["candidateRoot"]
    replay_root = bundle / "replay"
    receipt_path = bundle / "run-receipt.json"
    if replay_root.exists() or receipt_path.exists():
        raise FileExistsError("replay output already exists; use a new dependency bundle")
    if not BWRAP.is_file() or not TASKSET.is_file() or not GUARD.is_file():
        raise FileNotFoundError("bubblewrap, taskset, or resource guard is missing")

    corpus = args.corpus.resolve()
    binding = research_contracts.objective_binding()
    if (
        not corpus.is_file()
        or corpus.stat().st_size != binding["corpusBytes"]
        or digest(corpus) != binding["corpusSha256"]
    ):
        raise ValueError("corpus does not match the canonical full enwik9 identity")

    peer: dict[str, Any] | None = None
    peer_path: Path | None = None
    if args.peer_receipt is not None:
        peer_path = args.peer_receipt.resolve()
        research_contracts.validate_artifact(peer_path)
        peer = load_json(peer_path)
        if peer["verification"]["peerReceipt"] is not None:
            raise ValueError("peer receipt must be a non-recursive primary receipt")

    replay_root.mkdir(parents=True)
    clean_path = replay_root / "clean-room-replay.json"
    work_root = replay_root / "work"
    work_root.mkdir()
    executions: list[dict[str, Any]] = []
    retained: dict[str, Path] = {}
    error: str | None = None
    try:
        probe_work = work_root / "probe"
        (probe_work / "package").mkdir(parents=True)
        probe = probe_sandbox(probe_work)
        if probe["deviceReturncode"] != 0 or probe["networkReturncode"] != 0:
            raise RuntimeError("clean-room isolation probe failed")

        phase_specs = (
            ("first", "build-first", "compression", "archive.first"),
            ("replay", "build-replay", "compression-replay", "archive.replay"),
        )
        guard_paths: list[Path] = []
        for work_name, build_phase, run_phase, archive_name in phase_specs:
            work = fresh_work(work_root, work_name, package, manifest)
            build = sandbox_prefix(work, None) + expand_command(
                manifest["commands"]["build"], manifest, archive_name
            )
            build_log = replay_root / f"{build_phase}.log"
            build_returncode = run_command(build, build_log)
            executions.append(
                {
                    "phase": build_phase,
                    "command": build,
                    "returncode": build_returncode,
                    "guard": None,
                    "log": artifact(clean_path, build_log),
                }
            )
            if build_returncode != 0:
                raise RuntimeError(f"{build_phase} failed")

            compression = sandbox_prefix(work, corpus) + expand_command(
                manifest["commands"]["compress"], manifest, archive_name
            )
            guard_path = replay_root / f"{run_phase}.guard.json"
            run_log = replay_root / f"{run_phase}.log"
            outer, returncode = guarded_command(
                args,
                f"{manifest['candidateId']}:{run_phase}",
                "compression",
                work,
                compression,
                guard_path,
                run_log,
            )
            executions.append(
                {
                    "phase": run_phase,
                    "command": outer,
                    "returncode": returncode,
                    "guard": None,
                    "log": artifact(clean_path, run_log),
                }
            )
            if returncode != 0:
                raise RuntimeError(f"{run_phase} failed or crossed a resource guard")
            archive = work / archive_name
            if not archive.is_file() or archive.stat().st_size == 0:
                raise RuntimeError(f"{run_phase} did not produce an archive")
            retained_archive = replay_root / archive_name
            shutil.copy2(archive, retained_archive)
            retained[run_phase] = retained_archive
            guard_paths.append(guard_path)

        decode_work = fresh_work(work_root, "decode", package, manifest)
        decode_archive = decode_work / "archive.first"
        shutil.copy2(retained["compression"], decode_archive)
        build_decode = sandbox_prefix(decode_work, None) + expand_command(
            manifest["commands"]["build"], manifest, "archive.first"
        )
        build_decode_log = replay_root / "build-decode.log"
        build_decode_returncode = run_command(build_decode, build_decode_log)
        executions.append(
            {
                "phase": "build-decode",
                "command": build_decode,
                "returncode": build_decode_returncode,
                "guard": None,
                "log": artifact(clean_path, build_decode_log),
            }
        )
        if build_decode_returncode != 0:
            raise RuntimeError("build-decode failed")

        decompression = sandbox_prefix(decode_work, None) + expand_command(
            manifest["commands"]["decompress"], manifest, "archive.first"
        )
        decompression_guard = replay_root / "decompression.guard.json"
        decompression_log = replay_root / "decompression.log"
        outer, decompression_returncode = guarded_command(
            args,
            f"{manifest['candidateId']}:decompression",
            "decompression",
            decode_work,
            decompression,
            decompression_guard,
            decompression_log,
        )
        executions.append(
            {
                "phase": "decompression",
                "command": outer,
                "returncode": decompression_returncode,
                "guard": None,
                "log": artifact(clean_path, decompression_log),
            }
        )
        if decompression_returncode != 0:
            raise RuntimeError("decompression failed or crossed a resource guard")
        restored = decode_work / "restored.enwik9"
        if not restored.is_file():
            raise RuntimeError("decompression did not produce the restored corpus")
        retained_restored = replay_root / "restored.enwik9"
        shutil.copy2(restored, retained_restored)
        retained["restored"] = retained_restored
        guard_paths.append(decompression_guard)

        shutil.rmtree(work_root)
        guard_by_phase = {
            "compression": replay_root / "compression.guard.json",
            "compression-replay": replay_root / "compression-replay.guard.json",
            "decompression": decompression_guard,
        }
        for execution in executions:
            guard_path = guard_by_phase.get(execution["phase"])
            if guard_path is not None:
                execution["guard"] = guard_reference(clean_path, guard_path)
        clean_receipt = {
            "schema": "gamma.enwiki9.clean-room-replay.v1",
            "objective": binding,
            "candidateId": manifest["candidateId"],
            "candidateTreeSha256": manifest["candidateTreeSha256"],
            "sandbox": {
                "implementation": "bubblewrap",
                "version": subprocess.run(
                    [str(BWRAP), "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip(),
                "allNamespacesUnshared": True,
                "networkNamespaceUnshared": True,
                "newSession": True,
                "clearEnvironment": True,
                "minimalDeviceFilesystem": True,
                "readOnlySystemRoots": ["/usr"],
                "writableRoots": ["/dev", "/tmp", "/work"],
                "environment": ENVIRONMENT,
                "hostDataPathsVisible": False,
            },
            "probe": probe,
            "executions": executions,
            "packageCopiesVerified": 3,
            "decodeCorpusExposed": False,
            "scratchCleaned": not work_root.exists(),
            "licenseAudit": research_contracts.dependency_license_audit(manifest),
            "allCommandsSucceeded": all(
                execution["returncode"] == 0 for execution in executions
            ),
            "generatedUtc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
        }
        write_json(clean_path, clean_receipt)
        clean_result = research_contracts.validate_artifact(clean_path)

        first_record = artifact(receipt_path, retained["compression"])
        replay_record = artifact(receipt_path, retained["compression-replay"])
        restored_record = artifact(receipt_path, retained["restored"])
        roundtrip_ok = (
            restored_record["bytes"] == binding["corpusBytes"]
            and restored_record["sha256"] == binding["corpusSha256"]
        )
        if not roundtrip_ok:
            raise ValueError("restored corpus differs from canonical enwik9")
        determinism_ok = (
            first_record["bytes"] == replay_record["bytes"]
            and first_record["sha256"] == replay_record["sha256"]
        )
        guard_checks, resources_complete = guard_summary(guard_paths)
        official_score = (
            manifest["totalPackageBytes"]
            + first_record["bytes"]
            + manifest["requiredOptionBytes"]
        )
        license_ok = clean_result["licenseAudit"]["approved"]
        self_contained = bool(
            manifest["complete"]
            and clean_result["cleanRoomReplayOk"]
            and not clean_result["networkUsed"]
            and not clean_result["gpuUsed"]
            and not clean_result["hiddenInputs"]
        )
        cross_host_ok = peer_identity_ok(peer, manifest, first_record)
        objective_pass = all(
            (
                manifest["complete"],
                official_score <= binding["targetScoreBytes"],
                roundtrip_ok,
                determinism_ok,
                clean_result["independentDecodeOk"],
                resources_complete,
                self_contained,
                license_ok,
                cross_host_ok,
            )
        )
        promote = all(
            (
                manifest["complete"],
                roundtrip_ok,
                determinism_ok,
                clean_result["independentDecodeOk"],
                resources_complete,
                self_contained,
                license_ok,
            )
        )
        verifier_digest = digest(Path(__file__))
        receipt = {
            "schema": "gamma.enwiki9.run-receipt.v1",
            "objective": binding,
            "receiptId": args.receipt_id,
            "candidateId": manifest["candidateId"],
            "candidateTreeSha256": manifest["candidateTreeSha256"],
            "corpus": artifact(receipt_path, corpus),
            "archive": first_record,
            "package": {
                "manifestPath": os.path.relpath(manifest_path, bundle),
                "manifestSha256": f"sha256:{digest(manifest_path)}",
                "bytes": manifest["totalPackageBytes"],
                "dependencyClosureComplete": manifest["complete"],
            },
            "accounting": {
                "packageBytes": manifest["totalPackageBytes"],
                "archiveBytes": first_record["bytes"],
                "requiredOptionBytes": manifest["requiredOptionBytes"],
                "officialScoreBytes": official_score,
                "targetDebtBytes": official_score - binding["targetScoreBytes"],
                "complete": manifest["complete"],
            },
            "correctness": {
                "roundtripOk": roundtrip_ok,
                "determinismOk": determinism_ok,
                "deterministicReplayArchive": replay_record,
                "restored": restored_record,
                "independentDecodeOk": clean_result["independentDecodeOk"],
            },
            "resources": {
                "compressionGuard": reference(
                    receipt_path, replay_root / "compression.guard.json"
                ),
                "replayCompressionGuard": reference(
                    receipt_path, replay_root / "compression-replay.guard.json"
                ),
                "decompressionGuard": reference(
                    receipt_path, decompression_guard
                ),
                **guard_checks,
                "complete": resources_complete,
            },
            "distribution": {
                "cleanRoomReceipt": reference(receipt_path, clean_path),
                "selfContained": self_contained,
                "cleanRoomReplayOk": clean_result["cleanRoomReplayOk"],
                "networkUsed": clean_result["networkUsed"],
                "gpuUsed": clean_result["gpuUsed"],
                "hiddenInputs": clean_result["hiddenInputs"],
                "licenseAuditOk": license_ok,
            },
            "commands": {
                **manifest["commands"],
                "independentVerify": [
                    "python3",
                    "tools/research_contracts.py",
                    os.path.relpath(receipt_path, ROOT),
                ],
            },
            "verification": {
                "host": host_identity(),
                "verifier": (
                    "tools/enwiki9_clean_room_replay.py@sha256:" + verifier_digest
                ),
                "peerReceipt": (
                    reference(receipt_path, peer_path)
                    if peer_path is not None
                    else None
                ),
                "crossHostArchiveIdentityOk": cross_host_ok,
            },
            "verdict": (
                "objective-achieved"
                if objective_pass
                else "promote"
                if promote
                else "reject"
            ),
            "generatedUtc": dt.datetime.now(dt.timezone.utc)
            .replace(microsecond=0)
            .isoformat(),
        }
        write_json(receipt_path, receipt)
        research_contracts.validate_artifact(receipt_path)
        return receipt_path
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        if work_root.exists():
            shutil.rmtree(work_root)
        if error is not None:
            write_json(
                replay_root / "attempt.json",
                {
                    "schema": "gamma.enwiki9.clean-room-attempt.diagnostic.v1",
                    "candidateId": manifest["candidateId"],
                    "candidateTreeSha256": manifest["candidateTreeSha256"],
                    "error": error,
                    "executions": executions,
                    "scratchCleaned": not work_root.exists(),
                    "generatedUtc": dt.datetime.now(dt.timezone.utc)
                    .replace(microsecond=0)
                    .isoformat(),
                },
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--geekbench5-single-core-score", type=float, required=True)
    parser.add_argument("--peer-receipt", type=Path)
    parser.add_argument("--receipt-id", required=True)
    parser.add_argument("--sample-interval-seconds", type=float, default=1.0)
    args = parser.parse_args()
    if args.geekbench5_single_core_score <= 0:
        raise SystemExit("--geekbench5-single-core-score must be positive")
    if args.sample_interval_seconds <= 0:
        raise SystemExit("--sample-interval-seconds must be positive")
    path = replay(args)
    print(path.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
