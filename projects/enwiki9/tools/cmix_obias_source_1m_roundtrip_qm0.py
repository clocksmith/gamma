#!/usr/bin/env python3
"""Build cmix-obias from tracked source and prove an exact 1M roundtrip."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_ID = "cmix_obias_source_1m_roundtrip_qm0_v1"
RESULT = ROOT / "results" / CANDIDATE_ID
DONOR = Path("/home/x/enwiki9-nonproof/cmix-obias-donor")
DONOR_SOURCE = DONOR / "cmix-obias"
CANONICAL = Path("/home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9")
COMPILER = Path(
    "/home/x/enwiki9-nonproof/toolchains/clang17/root/usr/bin/clang++-17"
)
TOOLCHAIN_BIN = COMPILER.parent
TOOLCHAIN_LIB = COMPILER.parents[1] / "lib/x86_64-linux-gnu"
DONOR_LLVM_BIN = DONOR_SOURCE / "tools/llvm17-local/bin"
DONOR_COMPAT_LIB = DONOR_SOURCE / "tools/llvm17-compat-lib"
UPX = DONOR_SOURCE / "tools/upx"
RAW_SCOPE = 1_000_000
MAX_PROGRAM_BYTES = 500_000
EXPECTED = {
    "outer_commit": "51488a0c1228dbeab7c1be837fc90ceaed351728",
    "source_tree": "23de249ff899db5ba84dd3514a6a1bb52a83d0f5",
    "canonical": "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc",
    "opening": "369b688978f649681136198fb96db14c1616756260c55fb4b65e9bc049552cad",
    "head": "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078",
    "profile": "5141320933c09c4fd24d7f332da67b1008a3e730dd09c8784ea36769f2fe1e52",
}
DEFINES = (
    "-DSEED=923 -DUPDATE_LIMIT=3000 -DLSTM_NUM_CELLS=256 "
    "-DKH_BITLSTM32 -DKH_OBIAS -DKH_OBIAS_CONST_GATE=0.15f"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}


def command(
    args: list[str],
    *,
    cwd: Path,
    environment: dict[str, str] | None = None,
) -> dict[str, object]:
    started = time.monotonic()
    completed = subprocess.run(
        args,
        cwd=cwd,
        env=environment,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "command": args,
        "cwd": str(cwd),
        "elapsed_seconds_diagnostic": time.monotonic() - started,
        "returncode": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
        "stdout_tail": completed.stdout[-4096:].decode("utf-8", "replace"),
        "stderr_tail": completed.stderr[-4096:].decode("utf-8", "replace"),
    }


def git_value(*args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(DONOR), *args], text=True
    ).strip()


def build_environment() -> dict[str, str]:
    value = os.environ.copy()
    value["PATH"] = (
        f"{DONOR_LLVM_BIN}:{TOOLCHAIN_BIN}:" + value.get("PATH", "")
    )
    value["LD_LIBRARY_PATH"] = (
        f"{TOOLCHAIN_LIB}:{DONOR_COMPAT_LIB}:"
        + value.get("LD_LIBRARY_PATH", "")
    )
    return value


def runtime_environment(head: Path) -> dict[str, str]:
    return {
        "PATH": "/usr/bin:/bin",
        "KH_BITLSTM32": str(head.resolve()),
    }


def scratch_usage(root: Path) -> dict[str, int]:
    logical = 0
    allocated = 0
    for path in root.rglob("*"):
        if path.is_file() and not path.is_symlink():
            stat = path.stat()
            logical += stat.st_size
            allocated += stat.st_blocks * 512
    return {"logical_bytes": logical, "allocated_bytes": allocated}


def clear_ppm(directory: Path) -> None:
    ppm = directory / "ppm.temp"
    if ppm.exists():
        ppm.unlink()


def update_peak(peak: dict[str, int], observed: dict[str, int]) -> None:
    for key, value in observed.items():
        peak[key] = max(peak[key], value)


def package_binary(
    binary: Path, source: Path, directory: Path
) -> tuple[Path, list[dict[str, object]]]:
    directory.mkdir()
    raw = directory / "cmix_orig"
    shutil.copy2(binary, raw)
    raw.chmod(0o755)
    head = source / "models/bitlstm32/refit_golden256_fp16.blob"
    local_head = directory / "head.blob"
    shutil.copy2(head, local_head)
    env = runtime_environment(local_head)
    first = command(
        ["./cmix_orig", "-c", str(source / "dictionary/english.dic"), "comp_dict"],
        cwd=directory,
        environment=env,
    )
    first["scratch_usage_before_cleanup"] = scratch_usage(directory.parent)
    receipts = [first]
    clear_ppm(directory)
    second = command(
        [
            "./cmix_orig",
            "-c",
            str(source / "src/readalike_prepr/data/new_article_order"),
            "comp_order",
        ],
        cwd=directory,
        environment=env,
    )
    second["scratch_usage_before_cleanup"] = scratch_usage(directory.parent)
    receipts.append(second)
    clear_ppm(directory)
    receipts.append(
        command(
            [
                "./cmix_orig",
                "-h",
                str((directory / "comp_dict").stat().st_size),
                str((directory / "comp_order").stat().st_size),
                "0",
            ],
            cwd=directory,
            environment=env,
        )
    )
    packaged = directory / "cmix"
    with packaged.open("wb") as output:
        for name in ("cmix_orig", "comp_dict", "comp_order", "header.dat"):
            with (directory / name).open("rb") as part:
                shutil.copyfileobj(part, output)
    packaged.chmod(0o755)
    return packaged, receipts


def encode(
    packaged: Path, head: Path, source_input: Path, directory: Path
) -> dict[str, object]:
    directory.mkdir()
    shutil.copy2(packaged, directory / "cmix")
    (directory / "cmix").chmod(0o755)
    shutil.copy2(head, directory / "head.blob")
    receipt = command(
        ["./cmix", "-e", str(source_input), "out.cmix"],
        cwd=directory,
        environment=runtime_environment(directory / "head.blob"),
    )
    receipt["payload"] = artifact(directory / "out.cmix")
    receipt["archive"] = artifact(directory / "archive9")
    receipt["scratch_usage_before_cleanup"] = scratch_usage(directory.parent)
    clear_ppm(directory)
    return receipt


def main() -> int:
    required = [
        CANONICAL,
        COMPILER,
        DONOR_LLVM_BIN / "ld.lld",
        DONOR_COMPAT_LIB,
        UPX,
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing source-build inputs: {missing}")
    outer_commit = git_value("rev-parse", "HEAD")
    source_tree = git_value("rev-parse", "HEAD:cmix-obias")
    if outer_commit != EXPECTED["outer_commit"] or source_tree != EXPECTED["source_tree"]:
        raise ValueError("cmix-obias donor revision mismatch")
    if CANONICAL.stat().st_size != 1_000_000_000 or sha256(CANONICAL) != EXPECTED["canonical"]:
        raise ValueError("canonical enwik9 mismatch")
    if RESULT.exists():
        raise FileExistsError(f"refusing to overwrite {RESULT}")
    RESULT.mkdir(parents=True)

    execution: dict[str, object] = {}
    peak_scratch = {"logical_bytes": 0, "allocated_bytes": 0}
    with tempfile.TemporaryDirectory(
        prefix=f"{CANDIDATE_ID}-", dir="/dev/shm"
    ) as temporary:
        scratch = Path(temporary)
        source_tar = scratch / "source.tar"
        source = scratch / "source"
        source.mkdir()
        execution["extract_tracked_source"] = command(
            [
                "git",
                "-C",
                str(DONOR),
                "archive",
                "--format=tar",
                f"--output={source_tar}",
                "HEAD:cmix-obias",
            ],
            cwd=scratch,
        )
        execution["unpack_tracked_source"] = command(
            ["tar", "-xf", str(source_tar), "-C", str(source)], cwd=scratch
        )
        source_tar.unlink()
        head = source / "models/bitlstm32/refit_golden256_fp16.blob"
        profile = source / "pgo_data_asbuilt/default.profdata"
        if sha256(head) != EXPECTED["head"]:
            raise ValueError("neural-head asset mismatch")
        if sha256(profile) != EXPECTED["profile"]:
            raise ValueError("PGO profile mismatch")
        (source / "pgo_data").mkdir(exist_ok=True)
        shutil.copy2(profile, source / "pgo_data/default.profdata")
        execution["build"] = command(
            [
                "make",
                "prof_use",
                f"CC={COMPILER}",
                f"CFLAGS_DEFINES={DEFINES}",
                "KH_BITLSTM32_ARCHIVE=1",
                "-j4",
            ],
            cwd=source,
            environment=build_environment(),
        )
        binary = source / "cmix"
        execution["strip"] = command(
            [str(DONOR_LLVM_BIN / "llvm-strip"), "--strip-all", str(binary)],
            cwd=source,
            environment=build_environment(),
        )
        execution["remove_sections"] = command(
            [
                "objcopy",
                "--remove-section=.comment",
                "--remove-section=.note.gnu.property",
                "--remove-section=.note.gnu.build-id",
                "--remove-section=.note.ABI-tag",
                str(binary),
            ],
            cwd=source,
            environment=build_environment(),
        )
        execution["upx"] = command(
            [str(UPX), "--ultra-brute", str(binary)],
            cwd=source,
            environment=build_environment(),
        )

        packaged, package_receipts = package_binary(binary, source, scratch / "package")
        execution["package"] = package_receipts
        for receipt in package_receipts:
            update_peak(peak_scratch, receipt["scratch_usage_before_cleanup"])
        program_bytes = packaged.stat().st_size + head.stat().st_size
        if program_bytes > MAX_PROGRAM_BYTES:
            raise ValueError("source-built counted program exceeds frozen gate")
        input_path = scratch / "enwik1m"
        with CANONICAL.open("rb") as canonical, input_path.open("wb") as output:
            output.write(canonical.read(RAW_SCOPE))
        if input_path.stat().st_size != RAW_SCOPE or sha256(input_path) != EXPECTED["opening"]:
            raise ValueError("opening population mismatch")

        first_dir = scratch / "encode1"
        second_dir = scratch / "encode2"
        execution["encode1"] = encode(packaged, head, input_path, first_dir)
        execution["encode2"] = encode(packaged, head, input_path, second_dir)
        update_peak(
            peak_scratch,
            execution["encode1"]["scratch_usage_before_cleanup"],
        )
        update_peak(
            peak_scratch,
            execution["encode2"]["scratch_usage_before_cleanup"],
        )
        archive1 = first_dir / "archive9"
        archive2 = second_dir / "archive9"
        payload1 = first_dir / "out.cmix"
        payload2 = second_dir / "out.cmix"
        deterministic = (
            archive1.read_bytes() == archive2.read_bytes()
            and payload1.read_bytes() == payload2.read_bytes()
        )
        if not deterministic:
            raise ValueError("source-built repeat archives differ")

        decode = scratch / "decode"
        decode.mkdir()
        shutil.copy2(archive1, decode / "archive9")
        (decode / "archive9").chmod(0o755)
        execution["bare_decode"] = command(
            ["./archive9"], cwd=decode, environment={}
        )
        restored = decode / "enwik9_uncompressed"
        raw_identity = (
            restored.is_file()
            and restored.stat().st_size == RAW_SCOPE
            and sha256(restored) == EXPECTED["opening"]
        )
        if not raw_identity:
            raise ValueError("source-built bare decode mismatch")
        update_peak(peak_scratch, scratch_usage(scratch))
        clear_ppm(decode)
        shutil.copy2(packaged, RESULT / "cmix")
        shutil.copy2(head, RESULT / "head.blob")
        shutil.copy2(archive1, RESULT / "archive9")
        shutil.copy2(payload1, RESULT / "out.cmix")

    decision = {
        "schema": "enwiki9_cmix_obias_source_1m_roundtrip_qm0_v1",
        "candidate_id": CANDIDATE_ID,
        "status": "AUTHORIZED_SOURCE_BUILT_FULL_REPRODUCTION",
        "verdict": "authorize_source_built_full_corpus_reproduction_ladder",
        "score_credit_bytes": 0,
        "claim_boundary": (
            "Exact clean tracked-source opening-1M build, repeat encode, and bare "
            "decode qualification. It is not a full-corpus archive or score."
        ),
        "population": {
            "raw_bytes": RAW_SCOPE,
            "sha256": EXPECTED["opening"],
        },
        "source": {
            "outer_commit": outer_commit,
            "source_tree": source_tree,
            "tracked_files_only": True,
            "official_source_eligibility_proven": False,
        },
        "program_accounting": {
            "packaged_compressor": artifact(RESULT / "cmix"),
            "neural_head": artifact(RESULT / "head.blob"),
            "total_bytes": (RESULT / "cmix").stat().st_size
            + (RESULT / "head.blob").stat().st_size,
            "maximum_bytes": MAX_PROGRAM_BYTES,
        },
        "archive": artifact(RESULT / "archive9"),
        "payload": artifact(RESULT / "out.cmix"),
        "integrity": {
            "repeat_archive_and_payload_byte_identical": True,
            "bare_environment": {},
            "raw_roundtrip_exact": True,
        },
        "scratch_peak": peak_scratch,
        "execution": execution,
        "decision": {
            "promotion_authorized": True,
            "verified_full_1g_score_bytes": None,
            "target_bytes": 105_000_000,
        },
    }
    (RESULT / "decision.json").write_text(
        json.dumps(decision, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
