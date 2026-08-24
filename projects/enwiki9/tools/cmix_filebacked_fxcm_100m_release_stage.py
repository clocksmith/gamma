#!/usr/bin/env python3
"""Run the observer-free q1 opening-100M roundtrip with phase attribution."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time
from typing import Any, Callable

import jsonschema


SCHEMA = "gamma.enwiki9.cmix-filebacked-fxcm-100m-release-stage.v1"
CANDIDATE_ID = "cmix_obias_memory_safe_parent_filebacked_q1_v1"
PREFIX_BYTES = 100_000_000
PREFIX_SHA256 = "2b49720ec4d78c3c9fabaee6e4179a5e997302b3a70029f30f2d582218c024a8"
PHASES = (
    "package_helper_construction",
    "frontend_preprocessing",
    "model_pretraining",
    "arithmetic_payload_encode",
    "archive_assembly",
    "archive_decode",
    "frontend_inverse",
    "cleanup",
)
PROGRESS = re.compile(rb"(pretraining|progress):\s*([0-9]+(?:\.[0-9]+)?)%")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, Any]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)}


def existing_regular(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"{label} has a symlink component: {current}")
    metadata = path.stat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise RuntimeError(f"{label} must be a one-link regular file")
    return path.resolve(strict=True)


def existing_directory(path: Path, label: str) -> Path:
    if not path.is_absolute():
        raise RuntimeError(f"{label} must be absolute")
    current = Path(path.anchor)
    for component in path.parts[1:]:
        current /= component
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(f"{label} has an invalid component: {current}")
    return path.resolve(strict=True)


def write_new(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, sort_keys=True, indent=2).encode("ascii") + b"\n"
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o600,
    )
    try:
        cursor = 0
        while cursor < len(payload):
            written = os.write(descriptor, payload[cursor:])
            if written <= 0:
                raise OSError("short release-stage receipt write")
            cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def marker(path: Path, phase: str, event: str) -> None:
    payload = json.dumps(
        {"event": event, "phase": phase}, sort_keys=True, separators=(",", ":")
    ).encode("ascii") + b"\n"
    descriptor = os.open(
        path, os.O_WRONLY | os.O_APPEND | os.O_CLOEXEC | os.O_NOFOLLOW
    )
    try:
        if os.write(descriptor, payload) != len(payload):
            raise OSError("short phase marker write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def concatenate(parts: tuple[Path, ...], output: Path) -> None:
    descriptor = os.open(
        output,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW,
        0o700,
    )
    try:
        for part in parts:
            with part.open("rb") as source:
                for block in iter(lambda: source.read(8 << 20), b""):
                    cursor = 0
                    while cursor < len(block):
                        written = os.write(descriptor, block[cursor:])
                        if written <= 0:
                            raise OSError("short package concatenation write")
                        cursor += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def scratch_usage(roots: tuple[Path, ...]) -> tuple[int, int]:
    logical = 0
    allocated = 0
    pending = list(roots)
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                metadata = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(metadata.st_mode):
                    raise RuntimeError(f"scratch symlink forbidden: {entry.path}")
                if stat.S_ISDIR(metadata.st_mode):
                    pending.append(Path(entry.path))
                elif stat.S_ISREG(metadata.st_mode):
                    logical += metadata.st_size
                    allocated += metadata.st_blocks * 512
                else:
                    raise RuntimeError(f"unsupported scratch entry: {entry.path}")
    return logical, allocated


def process_memory(pid: int) -> tuple[int, int]:
    rss = 0
    hwm = 0
    try:
        for line in (Path("/proc") / str(pid) / "status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                rss = int(line.split()[1])
            elif line.startswith("VmHWM:"):
                hwm = int(line.split()[1])
    except (FileNotFoundError, ProcessLookupError):
        return 0, 0
    return rss, hwm


def read_int(path: Path) -> int:
    return int(path.read_text(encoding="ascii").strip())


def memory_stat(path: Path) -> dict[str, int]:
    values: dict[str, int] = {}
    for line in path.read_text(encoding="ascii").splitlines():
        name, value = line.split()
        values[name] = int(value)
    return values


class PhaseSampler:
    def __init__(
        self, marker_path: Path, cgroup_path: Path, scratch_roots: tuple[Path, ...]
    ) -> None:
        self.marker_path = marker_path
        self.cgroup_path = cgroup_path
        self.scratch_roots = scratch_roots
        self.active: str | None = None
        self.current: dict[str, int] | None = None
        self.records: list[dict[str, Any]] = []

    def start(self, phase: str) -> None:
        if self.active is not None or phase not in PHASES:
            raise RuntimeError(f"invalid phase start: {phase}")
        self.active = phase
        self.current = {
            "tree_rss_peak_kib": 0,
            "largest_process_vmhwm_kib": 0,
            "cgroup_peak_bytes": 0,
            "anonymous_bytes": 0,
            "file_backed_bytes": 0,
            "shmem_bytes": 0,
            "kernel_bytes": 0,
            "page_table_bytes": 0,
            "scratch_logical_bytes": 0,
            "scratch_allocated_bytes": 0,
        }
        marker(self.marker_path, phase, "start")
        self.observe()

    def observe(self) -> None:
        if self.active is None or self.current is None:
            return
        pids = [
            int(value)
            for value in (self.cgroup_path / "cgroup.procs").read_text().split()
        ]
        process_values = [process_memory(pid) for pid in pids]
        tree_rss = sum(value[0] for value in process_values)
        largest_hwm = max((value[1] for value in process_values), default=0)
        cgroup_current = read_int(self.cgroup_path / "memory.current")
        cgroup_values = memory_stat(self.cgroup_path / "memory.stat")
        logical, allocated = scratch_usage(self.scratch_roots)
        observed = {
            "tree_rss_peak_kib": tree_rss,
            "largest_process_vmhwm_kib": largest_hwm,
            "cgroup_peak_bytes": cgroup_current,
            "anonymous_bytes": cgroup_values.get("anon", 0),
            "file_backed_bytes": max(
                cgroup_values.get("file", 0) - cgroup_values.get("shmem", 0), 0
            ),
            "shmem_bytes": cgroup_values.get("shmem", 0),
            "kernel_bytes": cgroup_values.get("kernel", 0),
            "page_table_bytes": cgroup_values.get("pagetables", 0),
            "scratch_logical_bytes": logical,
            "scratch_allocated_bytes": allocated,
        }
        for name, value in observed.items():
            self.current[name] = max(self.current[name], value)

    def end(self) -> None:
        if self.active is None or self.current is None:
            raise RuntimeError("phase end without active phase")
        self.observe()
        marker(self.marker_path, self.active, "end")
        self.records.append(
            {"phase": self.active, "observed": True, **self.current}
        )
        self.active = None
        self.current = None

    def transition(self, phase: str) -> None:
        self.end()
        self.start(phase)


def run_monitored(
    *,
    argv: list[str],
    cwd: Path,
    environment: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    sampler: PhaseSampler,
    event_handler: Callable[[bytes, float, PhaseSampler], None],
) -> int:
    seen_events = 0
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=environment,
            stdout=stdout,
            stderr=stderr,
        )
        while process.poll() is None:
            sampler.observe()
            content = stderr_path.read_bytes()
            events = PROGRESS.findall(content)
            for kind, raw_value in events[seen_events:]:
                event_handler(kind, float(raw_value), sampler)
            seen_events = len(events)
            time.sleep(0.25)
        return_code = process.wait()
    sampler.observe()
    content = stderr_path.read_bytes()
    events = PROGRESS.findall(content)
    for kind, raw_value in events[seen_events:]:
        event_handler(kind, float(raw_value), sampler)
    return return_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--population", type=Path, required=True)
    parser.add_argument("--raw-binary", type=Path, required=True)
    parser.add_argument("--dictionary-payload", type=Path, required=True)
    parser.add_argument("--article-order-payload", type=Path, required=True)
    parser.add_argument("--package-header", type=Path, required=True)
    parser.add_argument("--head-blob", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--receipt-schema", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    population = existing_regular(args.population, "opening-100M population")
    if population.stat().st_size != PREFIX_BYTES or sha256_file(population) != PREFIX_SHA256:
        raise RuntimeError("opening-100M population identity mismatch")
    raw_binary = existing_regular(args.raw_binary, "q1 release binary")
    dictionary = existing_regular(args.dictionary_payload, "dictionary payload")
    article_order = existing_regular(args.article_order_payload, "article-order payload")
    package_header = existing_regular(args.package_header, "package header")
    head_blob = existing_regular(args.head_blob, "head blob")
    work_root = existing_directory(args.work_root, "release-stage work root")
    result_root = existing_directory(args.result_root, "release-stage result root")
    receipt_schema_path = existing_regular(args.receipt_schema, "release-stage schema")
    receipt_schema = json.loads(receipt_schema_path.read_text())
    jsonschema.Draft202012Validator.check_schema(receipt_schema)
    receipt_path = args.receipt
    if (
        receipt_path.parent.resolve(strict=True) != result_root
        or receipt_path.exists()
        or receipt_path.is_symlink()
    ):
        raise RuntimeError("release-stage receipt must be a new direct result child")
    if next(work_root.iterdir(), None) is not None:
        raise RuntimeError("release-stage work root must begin empty")
    marker_path = existing_regular(
        Path(os.environ.get("GAMMA_RESOURCE_PHASE_MARKERS", "")),
        "resource phase marker",
    )
    cgroup_path = existing_directory(
        Path(os.environ.get("GAMMA_PHASE_CGROUP_PATH", "")),
        "phase cgroup",
    )
    sampler = PhaseSampler(marker_path, cgroup_path, (work_root, result_root))
    inputs = {
        "raw_binary": artifact(raw_binary),
        "dictionary_payload": artifact(dictionary),
        "article_order_payload": artifact(article_order),
        "package_header": artifact(package_header),
        "head_blob": artifact(head_blob),
    }
    outputs: dict[str, dict[str, Any] | None] = {
        "packaged_compressor": None,
        "arithmetic_payload": None,
        "self_extracting_archive": None,
        "raw_inverse": None,
    }
    return_codes: dict[str, int | None] = {
        "encode": None,
        "decode": None,
        "raw_inverse": None,
    }
    errors: list[str] = []
    backing_cleanup = False
    exact_inverse = False
    try:
        encode_root = work_root / "encode"
        encode_root.mkdir(mode=0o700)
        sampler.start("package_helper_construction")
        local_cmix = encode_root / "cmix"
        concatenate((raw_binary, dictionary, article_order, package_header), local_cmix)
        local_head = encode_root / "head.blob"
        shutil.copyfile(head_blob, local_head)
        local_input = encode_root / "enwik9"
        shutil.copyfile(population, local_input)
        retained_package = result_root / "release-cmix"
        shutil.copyfile(local_cmix, retained_package)
        retained_package.chmod(0o700)
        outputs["packaged_compressor"] = artifact(retained_package)
        sampler.end()

        encode_backing = work_root / "encode-backing"
        encode_backing.mkdir(mode=0o700)
        environment = {
            "GAMMA_FXCM_BACKING_DIR": str(encode_backing),
            "KH_BITLSTM32": str(local_head),
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
            "TZ": "UTC",
        }
        encode_state = {"pretraining": False, "pretraining_complete": False}

        def encode_event(kind: bytes, value: float, phases: PhaseSampler) -> None:
            if kind == b"pretraining":
                if not encode_state["pretraining"]:
                    if phases.active != "frontend_preprocessing":
                        raise RuntimeError("pretraining marker arrived in wrong phase")
                    phases.transition("model_pretraining")
                    encode_state["pretraining"] = True
                if value >= 100.0:
                    encode_state["pretraining_complete"] = True
            elif encode_state["pretraining_complete"]:
                if phases.active == "model_pretraining":
                    phases.transition("arithmetic_payload_encode")
                if phases.active == "arithmetic_payload_encode" and value >= 100.0:
                    phases.transition("archive_assembly")

        sampler.start("frontend_preprocessing")
        return_codes["encode"] = run_monitored(
            argv=["./cmix", "-e", "enwik9", "out.cmix"],
            cwd=encode_root,
            environment=environment,
            stdout_path=result_root / "encode.stdout",
            stderr_path=result_root / "encode.stderr",
            sampler=sampler,
            event_handler=encode_event,
        )
        if sampler.active != "archive_assembly":
            raise RuntimeError(f"encode ended in unexpected phase {sampler.active}")
        sampler.end()
        if return_codes["encode"] != 0:
            raise RuntimeError(f"encode return code {return_codes['encode']}")
        payload = existing_regular(encode_root / "out.cmix", "100M arithmetic payload")
        archive = existing_regular(encode_root / "archive9", "100M archive")
        retained_payload = result_root / "out.cmix"
        retained_archive = result_root / "archive9"
        os.replace(payload, retained_payload)
        os.replace(archive, retained_archive)
        outputs["arithmetic_payload"] = artifact(retained_payload)
        outputs["self_extracting_archive"] = artifact(retained_archive)
        encode_cleanup = next(encode_backing.iterdir(), None) is None
        if not encode_cleanup:
            raise RuntimeError("encode backing files survived codec exit")
        encode_backing.rmdir()

        decode_root = work_root / "decode"
        decode_root.mkdir(mode=0o700)
        local_archive = decode_root / "archive9"
        shutil.copyfile(retained_archive, local_archive)
        local_archive.chmod(0o700)
        decode_backing = work_root / "decode-backing"
        decode_backing.mkdir(mode=0o700)
        decode_environment = {
            "GAMMA_FXCM_BACKING_DIR": str(decode_backing),
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
            "TZ": "UTC",
        }
        decode_state = {"progress_complete": False}

        def decode_event(kind: bytes, value: float, phases: PhaseSampler) -> None:
            if kind == b"progress" and value >= 100.0 and not decode_state["progress_complete"]:
                if phases.active != "archive_decode":
                    raise RuntimeError("decode completion marker arrived in wrong phase")
                phases.transition("frontend_inverse")
                decode_state["progress_complete"] = True

        sampler.start("archive_decode")
        return_codes["decode"] = run_monitored(
            argv=["./archive9"],
            cwd=decode_root,
            environment=decode_environment,
            stdout_path=result_root / "decode.stdout",
            stderr_path=result_root / "decode.stderr",
            sampler=sampler,
            event_handler=decode_event,
        )
        if sampler.active != "frontend_inverse":
            raise RuntimeError(f"decode ended in unexpected phase {sampler.active}")
        sampler.end()
        if return_codes["decode"] != 0:
            raise RuntimeError(f"decode return code {return_codes['decode']}")
        restored_options = [
            path
            for path in (decode_root / "enwik9", decode_root / "enwik9_uncompressed")
            if path.is_file() and not path.is_symlink()
        ]
        if len(restored_options) != 1:
            raise RuntimeError("decode did not emit exactly one known inverse path")
        retained_inverse = result_root / "enwik9-restored"
        os.replace(restored_options[0], retained_inverse)
        outputs["raw_inverse"] = artifact(retained_inverse)
        return_codes["raw_inverse"] = 0
        exact_inverse = (
            retained_inverse.stat().st_size == PREFIX_BYTES
            and sha256_file(retained_inverse) == PREFIX_SHA256
        )
        if not exact_inverse:
            return_codes["raw_inverse"] = 1
            raise RuntimeError("opening-100M inverse identity mismatch")
        decode_cleanup = next(decode_backing.iterdir(), None) is None
        if not decode_cleanup:
            raise RuntimeError("decode backing files survived codec exit")
        decode_backing.rmdir()
        backing_cleanup = encode_cleanup and decode_cleanup

        sampler.start("cleanup")
        shutil.rmtree(encode_root)
        shutil.rmtree(decode_root)
        sampler.end()
    except Exception as error:
        errors.append(f"{type(error).__name__}: {error}")
        if sampler.active is not None:
            try:
                sampler.end()
            except Exception as phase_error:
                errors.append(f"phase cleanup: {type(phase_error).__name__}: {phase_error}")

    scratch_after_cleanup, _ = scratch_usage((work_root,))
    phase_order_pass = tuple(item["phase"] for item in sampler.records) == PHASES
    stage_pass = (
        not errors
        and all(value == 0 for value in return_codes.values())
        and all(value is not None for value in outputs.values())
        and phase_order_pass
        and backing_cleanup
        and scratch_after_cleanup == 0
        and exact_inverse
    )
    receipt = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "population": artifact(population),
        "inputs": inputs,
        "outputs": outputs,
        "return_codes": return_codes,
        "phase_measurements": sampler.records,
        "backing_cleanup_pass": backing_cleanup,
        "scratch_after_cleanup_bytes": scratch_after_cleanup,
        "exact_raw_inverse_pass": exact_inverse,
        "errors": errors,
        "stage_pass": stage_pass,
        "claim_authority": "opening_100m_release_roundtrip_and_phase_resources_only",
        "execution_authority": False,
        "gamma_compression_credit_bytes": 0,
        "gamma_score_credit_bytes": 0,
    }
    jsonschema.validate(receipt, receipt_schema)
    write_new(receipt_path, receipt)
    return 0 if stage_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
