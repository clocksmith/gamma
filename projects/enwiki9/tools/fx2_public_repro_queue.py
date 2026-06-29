#!/usr/bin/env python3
"""Lane 0 public fx2-cmix reproduction helper.

This helper is intentionally full-corpus only. The upstream `cmix -e` path uses
fixed enwik9 split/reorder constants and emits `archive9`, so prefix gates are
not meaningful for reproducing the published Hutter entry.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent.parent
DATA = ROOT / "data" / "enwik9"
SOURCE_ROOT = ROOT / "external" / "fx2-cmix"
ROOT_BINARY = SOURCE_ROOT / "cmix"
SOURCE_DICT = SOURCE_ROOT / "dictionary" / "english.dic"
SOURCE_ORDER = SOURCE_ROOT / "src" / "readalike_prepr" / "data" / "new_article_order"
UPSTREAM_PACKAGE = SOURCE_ROOT / "run" / "cmix"
UPSTREAM_BUILD = SOURCE_ROOT / "build_and_construct_comp.sh"
CANDIDATE_ID = "fx2cmix_public_repro_v1"
CANDIDATE_DIR = ROOT / "programs" / CANDIDATE_ID
CANDIDATE_PACKAGE = CANDIDATE_DIR / "cmix"
RESULTS_DIR = ROOT / "results" / CANDIDATE_ID
RECORD = ROOT / "tools" / "record_driver_result.py"
RSS_GUARD = ROOT / "tools" / "run_with_rss_guard.py"
LOCK = pathlib.Path("/tmp/enwiki9-heavy.lock")
BUSY_CODE = 75

FULL_ENWIK9_BYTES = 1_000_000_000
PUBLIC_TARGET = {
    "program": "fx2-cmix",
    "total_score": 110_793_128,
    "archive_size": 110_351_665,
    "executable_size": 441_463,
    "reported_max_ram_kib": 9_523_660,
}


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(REPO_ROOT).as_posix()


def file_size(path: pathlib.Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def md5_file(path: pathlib.Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def preflight() -> dict[str, Any]:
    data_size = file_size(DATA)
    upstream_size = file_size(UPSTREAM_PACKAGE)
    candidate_size = file_size(CANDIDATE_PACKAGE)
    return {
        "lane": "lane0_fx2_public_repro",
        "candidate_id": CANDIDATE_ID,
        "public_target": PUBLIC_TARGET,
        "full_only": True,
        "full_only_reason": (
            "upstream cmix -e uses fixed enwik9 split/reorder constants and "
            "emits archive9"
        ),
        "data": {
            "path": rel(DATA),
            "exists": DATA.exists(),
            "size": data_size,
            "size_ok": data_size == FULL_ENWIK9_BYTES,
            "sha256": sha256_file(DATA) if DATA.exists() else None,
        },
        "source": {
            "path": rel(SOURCE_ROOT),
            "exists": SOURCE_ROOT.exists(),
            "root_binary": rel(ROOT_BINARY),
            "root_binary_exists": ROOT_BINARY.exists(),
            "root_binary_size": file_size(ROOT_BINARY),
            "dictionary": rel(SOURCE_DICT),
            "dictionary_exists": SOURCE_DICT.exists(),
            "article_order": rel(SOURCE_ORDER),
            "article_order_exists": SOURCE_ORDER.exists(),
            "build_script": rel(SOURCE_ROOT / "build_and_construct_comp.sh"),
            "build_script_exists": (SOURCE_ROOT / "build_and_construct_comp.sh").exists(),
            "upstream_package": rel(UPSTREAM_PACKAGE),
            "upstream_package_exists": UPSTREAM_PACKAGE.exists(),
            "upstream_package_size": upstream_size,
        },
        "candidate_package": {
            "path": rel(CANDIDATE_PACKAGE),
            "exists": CANDIDATE_PACKAGE.exists(),
            "size": candidate_size,
        },
        "build_tools": {
            "clang++-17": command_exists("clang++-17"),
            "llvm-profdata-17": command_exists("llvm-profdata-17"),
            "upx-ucl": command_exists("upx-ucl"),
        },
    }


def concatenate(paths: list[pathlib.Path], output: pathlib.Path) -> None:
    with output.open("wb") as out:
        for path in paths:
            with path.open("rb") as src:
                shutil.copyfileobj(src, out)


def prepare_from_root_binary() -> dict[str, Any]:
    missing = [
        path
        for path in (ROOT_BINARY, SOURCE_DICT, SOURCE_ORDER)
        if not path.exists()
    ]
    if missing:
        raise SystemExit("missing source asset(s): " + ", ".join(rel(path) for path in missing))

    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fx2-public-package-") as td:
        root = pathlib.Path(td)
        cmix_orig = root / "cmix_orig"
        shutil.copy2(ROOT_BINARY, cmix_orig)
        os.chmod(cmix_orig, 0o755)

        comp_dict = root / "comp_dict"
        comp_order = root / "comp_order"
        header = root / "header.dat"
        subprocess.run([str(cmix_orig), "-c", str(SOURCE_DICT), str(comp_dict)], cwd=root, check=True)
        subprocess.run([str(cmix_orig), "-c", str(SOURCE_ORDER), str(comp_order)], cwd=root, check=True)
        subprocess.run(
            [
                str(cmix_orig),
                "-h",
                str(comp_dict.stat().st_size),
                str(comp_order.stat().st_size),
                "0",
            ],
            cwd=root,
            check=True,
        )
        if not header.exists():
            header = root / "header.dat"
        concatenate([cmix_orig, comp_dict, comp_order, header], CANDIDATE_PACKAGE)

    os.chmod(CANDIDATE_PACKAGE, 0o755)
    return {
        "status": "prepared_from_root_binary",
        "candidate_id": CANDIDATE_ID,
        "source_binary": rel(ROOT_BINARY),
        "candidate_package": rel(CANDIDATE_PACKAGE),
        "program_size": CANDIDATE_PACKAGE.stat().st_size,
        "exact_public_executable_match": CANDIDATE_PACKAGE.stat().st_size
        == PUBLIC_TARGET["executable_size"],
    }


def prepare() -> dict[str, Any]:
    if not UPSTREAM_PACKAGE.exists():
        raise SystemExit(
            f"missing {rel(UPSTREAM_PACKAGE)}; build the upstream package with "
            f"{rel(SOURCE_ROOT / 'build_and_construct_comp.sh')} first"
        )
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(UPSTREAM_PACKAGE, CANDIDATE_PACKAGE)
    os.chmod(CANDIDATE_PACKAGE, 0o755)
    return {
        "status": "prepared",
        "candidate_id": CANDIDATE_ID,
        "source_package": rel(UPSTREAM_PACKAGE),
        "candidate_package": rel(CANDIDATE_PACKAGE),
        "program_size": CANDIDATE_PACKAGE.stat().st_size,
    }


def build_upstream() -> dict[str, Any]:
    missing_tools = [
        name
        for name in ("clang++-17", "llvm-profdata-17", "upx-ucl")
        if not command_exists(name)
    ]
    if missing_tools:
        return {
            "status": "blocked",
            "reason": "missing_exact_build_tools",
            "missing_tools": missing_tools,
            "build_script": rel(UPSTREAM_BUILD),
            "upstream_package": rel(UPSTREAM_PACKAGE),
            "upstream_package_exists": UPSTREAM_PACKAGE.exists(),
            "upstream_package_size": file_size(UPSTREAM_PACKAGE),
        }
    if not UPSTREAM_BUILD.exists():
        return {
            "status": "blocked",
            "reason": "missing_build_script",
            "build_script": rel(UPSTREAM_BUILD),
        }

    proc = run_command(["bash", str(UPSTREAM_BUILD)], SOURCE_ROOT)
    return {
        "status": "built" if proc.returncode == 0 and UPSTREAM_PACKAGE.exists() else "failed",
        "returncode": proc.returncode,
        "build_script": rel(UPSTREAM_BUILD),
        "upstream_package": rel(UPSTREAM_PACKAGE),
        "upstream_package_exists": UPSTREAM_PACKAGE.exists(),
        "upstream_package_size": file_size(UPSTREAM_PACKAGE),
        "exact_public_executable_match": file_size(UPSTREAM_PACKAGE)
        == PUBLIC_TARGET["executable_size"],
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def run_command(command: list[str], cwd: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_archive_once(data_path: pathlib.Path, package_path: pathlib.Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="fx2-public-repro-") as td:
        root = pathlib.Path(td)
        shutil.copy2(package_path, root / "cmix")
        os.chmod(root / "cmix", 0o755)

        compress = run_command(["./cmix", "-e", str(data_path), "enwik9.comp"], root)
        if compress.returncode != 0:
            return {
                "ok": False,
                "phase": "compress",
                "returncode": compress.returncode,
                "stdout": compress.stdout[-4000:],
                "stderr": compress.stderr[-4000:],
            }

        archive = root / "archive9"
        if not archive.exists():
            return {"ok": False, "phase": "compress", "reason": "archive9_missing"}

        os.chmod(archive, 0o755)
        restore = run_command(["./archive9"], root)
        if restore.returncode != 0:
            return {
                "ok": False,
                "phase": "decompress",
                "returncode": restore.returncode,
                "archive_size": archive.stat().st_size,
                "archive_sha256": sha256_file(archive),
                "stdout": restore.stdout[-4000:],
                "stderr": restore.stderr[-4000:],
            }

        restored = root / "enwik9_uncompressed"
        if not restored.exists():
            return {
                "ok": False,
                "phase": "decompress",
                "reason": "restored_file_missing",
                "archive_size": archive.stat().st_size,
                "archive_sha256": sha256_file(archive),
            }

        data_sha256 = sha256_file(data_path)
        restored_sha256 = sha256_file(restored)
        archive_size = archive.stat().st_size
        return {
            "ok": restored_sha256 == data_sha256,
            "phase": "complete",
            "archive_size": archive_size,
            "archive_md5": md5_file(archive),
            "archive_sha256": sha256_file(archive),
            "restored_size": restored.stat().st_size,
            "restored_sha256": restored_sha256,
            "data_sha256": data_sha256,
        }


def save_result(result: dict[str, Any]) -> pathlib.Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = str(result["timestamp"]).replace(":", "")
    path = RESULTS_DIR / f"{stamp}.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    return path


def record_result(result_path: pathlib.Path, status: str, verdict: str) -> None:
    command = [
        sys.executable,
        str(RECORD),
        CANDIDATE_ID,
        "--result",
        str(result_path),
        "--label",
        "full_public_repro",
        "--status",
        status,
        "--verdict",
        verdict,
    ]
    proc = run_command(command, REPO_ROOT)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr.strip() or proc.stdout.strip())


def run_full(save: bool, record: bool, check_determinism: bool) -> dict[str, Any]:
    if not DATA.exists() or DATA.stat().st_size != FULL_ENWIK9_BYTES:
        raise SystemExit(f"full enwik9 missing or wrong size: {rel(DATA)}")
    if not CANDIDATE_PACKAGE.exists():
        raise SystemExit(f"candidate package missing: {rel(CANDIDATE_PACKAGE)}")

    program_size = CANDIDATE_PACKAGE.stat().st_size
    first = run_archive_once(DATA, CANDIDATE_PACKAGE)
    compressed_size = int(first.get("archive_size") or 0)
    roundtrip_ok = first.get("ok") is True
    determinism: dict[str, Any] | None = None

    if check_determinism and roundtrip_ok:
        second = run_archive_once(DATA, CANDIDATE_PACKAGE)
        first_sha = first.get("archive_sha256")
        second_sha = second.get("archive_sha256")
        determinism = {
            "single_host_byte_equal": bool(second.get("ok")) and first_sha == second_sha,
            "first_run_sha256": first_sha,
            "second_run_sha256": second_sha,
            "second_archive_size": second.get("archive_size"),
        }

    result = {
        "program_id": CANDIDATE_ID,
        "lane": "lane0_fx2_public_repro",
        "data_path": str(DATA),
        "data_size": FULL_ENWIK9_BYTES,
        "data_md5": md5_file(DATA),
        "data_sha256": first.get("data_sha256") or sha256_file(DATA),
        "compressed_size": compressed_size,
        "compressed_md5": first.get("archive_md5"),
        "compressed_sha256": first.get("archive_sha256"),
        "program_size": program_size,
        "program_files": [["cmix", program_size]],
        "hutter_score": compressed_size + program_size,
        "roundtrip_ok": roundtrip_ok,
        "failure": first if not roundtrip_ok else None,
        "determinism": determinism,
        "public_target": PUBLIC_TARGET,
        "delta_vs_public_total": compressed_size + program_size - PUBLIC_TARGET["total_score"],
        "delta_vs_public_archive": compressed_size - PUBLIC_TARGET["archive_size"],
        "delta_vs_public_executable": program_size - PUBLIC_TARGET["executable_size"],
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
    }
    if save:
        result_path = save_result(result)
        result["result_path"] = rel(result_path)
        if record:
            status = "active" if roundtrip_ok else "measured_negative"
            verdict = (
                "Full public fx2-cmix reproduction completed with exact restored bytes."
                if roundtrip_ok
                else "Full public fx2-cmix reproduction failed before exact restored bytes."
            )
            record_result(result_path, status, verdict)
    return result


def run_guarded(check_determinism: bool) -> int:
    guard_json = RESULTS_DIR / "lane0_full_rss_guard.json"
    command = [
        "flock",
        "-n",
        "-E",
        str(BUSY_CODE),
        str(LOCK),
        sys.executable,
        str(RSS_GUARD),
        "--limit-kib",
        "10485760",
        "--sample-interval",
        "1",
        "--guard-json",
        str(guard_json),
        "--label",
        "lane0_fx2_public_repro_full",
        "--",
        sys.executable,
        str(pathlib.Path(__file__).resolve()),
        "--run-full",
        "--save",
        "--record",
    ]
    if check_determinism:
        command.append("--check-determinism")
    proc = subprocess.run(command, cwd=REPO_ROOT)
    return int(proc.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--build-upstream", action="store_true")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--prepare-from-root-binary", action="store_true")
    parser.add_argument("--run-full", action="store_true")
    parser.add_argument("--run-guarded", action="store_true")
    parser.add_argument("--save", action="store_true")
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--check-determinism", action="store_true")
    args = parser.parse_args()

    selected = sum(
        bool(value)
        for value in (
            args.preflight,
            args.build_upstream,
            args.prepare,
            args.prepare_from_root_binary,
            args.run_full,
            args.run_guarded,
        )
    )
    if selected != 1:
        raise SystemExit(
            "select exactly one of --preflight, --prepare, "
            "--build-upstream, --prepare-from-root-binary, --run-full, "
            "--run-guarded"
        )

    if args.preflight:
        print(json.dumps(preflight(), indent=2))
        return 0
    if args.build_upstream:
        result = build_upstream()
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "built" else 1
    if args.prepare:
        print(json.dumps(prepare(), indent=2))
        return 0
    if args.prepare_from_root_binary:
        print(json.dumps(prepare_from_root_binary(), indent=2))
        return 0
    if args.run_full:
        print(json.dumps(run_full(args.save, args.record, args.check_determinism), indent=2))
        return 0
    return run_guarded(args.check_determinism)


if __name__ == "__main__":
    raise SystemExit(main())
