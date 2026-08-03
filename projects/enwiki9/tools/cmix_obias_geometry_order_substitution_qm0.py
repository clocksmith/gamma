#!/usr/bin/env python3
"""Exact opening-10M order-only screen on the pinned cmix-obias donor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from typing import Any


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
RSS_GUARD = PROJECT_ROOT / "tools" / "run_with_rss_guard.py"

CANDIDATE_ID = "cmix_obias_geometry_order_substitution_qm0_v1"
SCHEMA = "cmix_obias_geometry_order_substitution_qm0_decision_v1"
DONOR_COMMIT = "51488a0c1228dbeab7c1be837fc90ceaed351728"
SCOPE_BYTES = 10_000_000
SCOPE_SHA256 = "5985c81c39d927ae0e169625790ca4d9e7d1531270c8b09ad73176a375bb3d97"
FULL_INPUT_BYTES = 1_000_000_000
FULL_INPUT_SHA256 = "159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc"

PACKAGED_CMIX_BYTES = 459_989
PACKAGED_CMIX_SHA256 = "eee69c879f4bbd58015efd4d34f55c6dc986ec818fa68c2f32a9ee5ab5568f68"
RAW_CMIX_BYTES = 159_704
RAW_CMIX_SHA256 = "24f52d24e5ff5027fa76ea75864a76b7d627917f75df14c64091f1f37b519ec0"
COMP_DICT_BYTES = 100_598
COMP_DICT_SHA256 = "353caf87f6ea9b3a66b1691c6777ee04b24f0c9b5a1c9c3212652597521ca6f8"
COMP_PUBLIC_ORDER_BYTES = 199_671
COMP_PUBLIC_ORDER_SHA256 = "ebb9015438c52ba5d75276792235994a0e5af5e5ca31f2ed437d19259e0eae37"
RAW_PUBLIC_ORDER_BYTES = 1_094_862
RAW_PUBLIC_ORDER_SHA256 = "eecd462c29319bab185b48229c4d09ab52f16ca9c582e8e32eff9a7c2a7de39e"
HEAD_BYTES = 23_002
HEAD_SHA256 = "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"

PARENT_PAYLOAD_BYTES = 1_599_218
PARENT_ARCHIVE_BYTES = 1_882_538
GROSS_GATE_BYTES = 5_000
ALGORITHMIC_SOURCE_ALLOWANCE = 32_768
EXTERNAL_FULL_TOTAL = 108_492_825
FIXED_ORDER_ASSET_BYTES = 199_671
TARGET_BYTES = 108_000_000
DECIMAL_10GB_KIB = 9_765_625
BINARY_10GIB_KIB = 10_485_760

PAGE_OPEN = b"  <page>\n"
PAGE_CLOSE = b"  </page>\n"
REDIRECT_PREFIXES = (
    b'      <text xml:space="preserve">#REDIRECT',
    b'      <text xml:space="preserve">#redirect',
    b'      <text xml:space="preserve">#Redirect',
    b'      <text xml:space="preserve">#REdirect',
    b'      <text xml:space="preserve">{{softredirect',
)
TITLE_RE = re.compile(rb"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
ID_RE = re.compile(rb"<id>(\d+)</id>", re.IGNORECASE | re.DOTALL)
CATEGORY_RE = re.compile(rb"\[\[Category:([^\]\|\n]{1,100})", re.IGNORECASE)
INFOBOX_RE = re.compile(
    rb"\{\{\s*(infobox[^\|\}\n]{0,80})", re.IGNORECASE | re.DOTALL
)
TEMPLATE_RE = re.compile(rb"\{\{([^\|\}\n]{1,80})", re.IGNORECASE | re.DOTALL)


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: pathlib.Path, size: int, digest: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_size = path.stat().st_size
    actual_digest = sha256_file(path)
    if actual_size != size or actual_digest != digest:
        raise RuntimeError(
            f"asset mismatch: {path} bytes={actual_size} sha256={actual_digest}"
        )


def atomic_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def normalized(value: bytes) -> bytes:
    return re.sub(rb"[^a-z0-9]+", b" ", value.lower()).strip()[:240]


def first_match(pattern: re.Pattern[bytes], page: bytes) -> bytes:
    match = pattern.search(page)
    return match.group(1) if match else b""


def complete_pages(data: bytes) -> list[bytes]:
    pages: list[bytes] = []
    cursor = data.find(PAGE_OPEN)
    while cursor >= 0:
        end = data.find(PAGE_CLOSE, cursor)
        if end < 0:
            break
        end += len(PAGE_CLOSE)
        pages.append(data[cursor:end])
        cursor = data.find(PAGE_OPEN, end)
    if not pages:
        raise RuntimeError("no complete enwik pages found")
    return pages


def is_donor_redirect(page: bytes) -> bool:
    return any(line.startswith(REDIRECT_PREFIXES) for line in page.splitlines())


def geometry_key(page: bytes) -> bytes:
    title = first_match(TITLE_RE, page)
    categories = CATEGORY_RE.findall(page)
    if categories:
        return normalized(b"c " + b" ".join(sorted(categories)) + b" t " + title[:40])
    infobox = first_match(INFOBOX_RE, page)
    if infobox:
        return normalized(b"i " + infobox)
    template = first_match(TEMPLATE_RE, page)
    return normalized(b"x " + (template or title))


def generate_order(data: bytes, mode: str) -> tuple[bytes, dict[str, int]]:
    if mode not in {"geometry", "title"}:
        raise ValueError(mode)
    rows: list[tuple[bytes, int, int, int]] = []
    redirect_count = 0
    nonredirect_ordinal = 0
    pages = complete_pages(data)
    for physical_ordinal, page in enumerate(pages):
        page_id_raw = first_match(ID_RE, page)
        if not page_id_raw:
            raise RuntimeError(f"page {physical_ordinal} has no page id")
        page_id = int(page_id_raw)
        if is_donor_redirect(page):
            redirect_count += 1
            continue
        if mode == "geometry":
            key = geometry_key(page)
        else:
            key = normalized(first_match(TITLE_RE, page))
        rows.append((key, page_id, physical_ordinal, nonredirect_ordinal))
        nonredirect_ordinal += 1
    rows.sort(key=lambda row: (row[0], row[1], row[2]))
    output = b"".join(f"{row[3]}\n".encode("ascii") for row in rows)
    if len({row[3] for row in rows}) != len(rows):
        raise RuntimeError("generated order contains duplicate ordinals")
    return output, {
        "complete_pages": len(pages),
        "redirect_pages": redirect_count,
        "ordered_nonredirect_pages": len(rows),
    }


def run_checked(
    command: list[str],
    *,
    cwd: pathlib.Path,
    env: dict[str, str] | None = None,
) -> None:
    print(json.dumps({"event": "command", "cwd": str(cwd), "command": command}), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def run_guarded(
    command: list[str],
    *,
    cwd: pathlib.Path,
    label: str,
    guard_path: pathlib.Path,
    env: dict[str, str],
) -> dict[str, Any]:
    guard_command = [
        sys.executable,
        str(RSS_GUARD),
        "--limit-kib",
        str(BINARY_10GIB_KIB),
        "--limit-mode",
        "max_single",
        "--official-decimal-limit-kib",
        str(DECIMAL_10GB_KIB),
        "--sample-interval",
        "0.5",
        "--guard-json",
        str(guard_path),
        "--label",
        label,
        "--",
        *command,
    ]
    run_checked(guard_command, cwd=cwd, env=env)
    guard = json.loads(guard_path.read_text())
    if guard.get("status") != "complete" or guard.get("returncode") != 0:
        raise RuntimeError(f"RSS-guarded command failed: {label}: {guard}")
    return guard


def write_prefix(source: pathlib.Path, destination: pathlib.Path) -> None:
    remaining = SCOPE_BYTES
    with source.open("rb") as input_file, destination.open("wb") as output_file:
        while remaining:
            chunk = input_file.read(min(1 << 20, remaining))
            if not chunk:
                raise RuntimeError("full input ended before the frozen scope")
            output_file.write(chunk)
            remaining -= len(chunk)
    if sha256_file(destination) != SCOPE_SHA256:
        raise RuntimeError("opening-10M input hash mismatch")


def donor_paths(donor_root: pathlib.Path) -> dict[str, pathlib.Path]:
    return {
        "packaged": donor_root / "artifacts_asbuilt" / "cmix",
        "comp_dict": donor_root / "artifacts_asbuilt" / "comp_dict",
        "comp_order": donor_root / "artifacts_asbuilt" / "comp_order",
        "raw_order": donor_root
        / "cmix-obias"
        / "src"
        / "readalike_prepr"
        / "data"
        / "new_article_order",
        "head": donor_root
        / "cmix-obias"
        / "models"
        / "bitlstm32"
        / "refit_golden256_fp16.blob",
    }


def verify_donor(donor_root: pathlib.Path) -> tuple[dict[str, pathlib.Path], bytes]:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=donor_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    if commit != DONOR_COMMIT:
        raise RuntimeError(f"donor commit mismatch: {commit}")
    paths = donor_paths(donor_root)
    require_file(paths["packaged"], PACKAGED_CMIX_BYTES, PACKAGED_CMIX_SHA256)
    require_file(paths["comp_dict"], COMP_DICT_BYTES, COMP_DICT_SHA256)
    require_file(paths["comp_order"], COMP_PUBLIC_ORDER_BYTES, COMP_PUBLIC_ORDER_SHA256)
    require_file(paths["raw_order"], RAW_PUBLIC_ORDER_BYTES, RAW_PUBLIC_ORDER_SHA256)
    require_file(paths["head"], HEAD_BYTES, HEAD_SHA256)

    package = paths["packaged"].read_bytes()
    header = struct.unpack("<4i", package[-16:])
    if header != (COMP_DICT_BYTES, COMP_PUBLIC_ORDER_BYTES, 0, 0):
        raise RuntimeError(f"unexpected donor package header: {header}")
    raw = package[:RAW_CMIX_BYTES]
    if hashlib.sha256(raw).hexdigest() != RAW_CMIX_SHA256:
        raise RuntimeError("raw cmix prefix hash mismatch")
    embedded_dict = package[RAW_CMIX_BYTES : RAW_CMIX_BYTES + COMP_DICT_BYTES]
    embedded_order = package[
        RAW_CMIX_BYTES + COMP_DICT_BYTES : RAW_CMIX_BYTES + COMP_DICT_BYTES + COMP_PUBLIC_ORDER_BYTES
    ]
    if hashlib.sha256(embedded_dict).hexdigest() != COMP_DICT_SHA256:
        raise RuntimeError("embedded dictionary mismatch")
    if hashlib.sha256(embedded_order).hexdigest() != COMP_PUBLIC_ORDER_SHA256:
        raise RuntimeError("embedded public order mismatch")
    return paths, raw


def build_package(
    *,
    arm: str,
    workspace: pathlib.Path,
    raw_executable: bytes,
    comp_dict: pathlib.Path,
    raw_order: bytes,
) -> tuple[pathlib.Path, dict[str, Any]]:
    workspace.mkdir(parents=True)
    cmix_orig = workspace / "cmix_orig"
    cmix_orig.write_bytes(raw_executable)
    cmix_orig.chmod(0o755)
    order_path = workspace / "order.txt"
    order_path.write_bytes(raw_order)
    comp_order = workspace / "comp_order"
    run_checked([str(cmix_orig), "-c", str(order_path), str(comp_order)], cwd=workspace)
    (workspace / "ppm.temp").unlink(missing_ok=True)
    run_checked(
        [
            str(cmix_orig),
            "-h",
            str(COMP_DICT_BYTES),
            str(comp_order.stat().st_size),
            "0",
        ],
        cwd=workspace,
    )
    header = workspace / "header.dat"
    header_bytes = header.read_bytes()
    if len(header_bytes) != 16:
        raise RuntimeError(f"{arm} header is not 16 bytes")
    package = workspace / "cmix"
    package.write_bytes(
        raw_executable + comp_dict.read_bytes() + comp_order.read_bytes() + header_bytes
    )
    package.chmod(0o755)
    return package, {
        "raw_order_bytes": len(raw_order),
        "raw_order_sha256": hashlib.sha256(raw_order).hexdigest(),
        "comp_order_bytes": comp_order.stat().st_size,
        "comp_order_sha256": sha256_file(comp_order),
        "packaged_cmix_bytes": package.stat().st_size,
        "packaged_cmix_sha256": sha256_file(package),
    }


def run_arm(
    *,
    arm: str,
    package: pathlib.Path,
    input_path: pathlib.Path,
    head_path: pathlib.Path,
    root: pathlib.Path,
) -> dict[str, Any]:
    print(json.dumps({"event": "arm_start", "arm": arm}), flush=True)
    encode_dir = root / f"encode_{arm}"
    decode_dir = root / f"decode_{arm}"
    encode_dir.mkdir()
    decode_dir.mkdir()
    cmix = encode_dir / "cmix"
    shutil.copyfile(package, cmix)
    cmix.chmod(0o755)
    payload = encode_dir / "out.cmix"
    encode_env = os.environ.copy()
    encode_env["KH_BITLSTM32"] = str(head_path)
    encode_env.pop("CMIX_PPM_RSS_MB", None)
    encode_guard = run_guarded(
        ["./cmix", "-e", str(input_path), str(payload)],
        cwd=encode_dir,
        label=f"{CANDIDATE_ID}_{arm}_encode",
        guard_path=encode_dir / "rss_guard.json",
        env=encode_env,
    )
    archive = encode_dir / "archive9"
    if not payload.is_file() or not archive.is_file():
        raise RuntimeError(f"{arm} did not produce payload and archive9")

    decode_archive = decode_dir / "archive9"
    shutil.copyfile(archive, decode_archive)
    decode_archive.chmod(0o755)
    decode_env = os.environ.copy()
    for name in ("KH_BITLSTM32", "KH_OBIAS", "CMIX_PPM_RSS_MB"):
        decode_env.pop(name, None)
    decode_guard = run_guarded(
        ["./archive9"],
        cwd=decode_dir,
        label=f"{CANDIDATE_ID}_{arm}_decode",
        guard_path=decode_dir / "rss_guard.json",
        env=decode_env,
    )
    restored = decode_dir / "enwik9_uncompressed"
    if not restored.is_file():
        raise RuntimeError(f"{arm} did not produce enwik9_uncompressed")
    restored_size = restored.stat().st_size
    restored_sha256 = sha256_file(restored)
    roundtrip_ok = restored_size == SCOPE_BYTES and restored_sha256 == SCOPE_SHA256
    if not roundtrip_ok:
        raise RuntimeError(
            f"{arm} roundtrip mismatch bytes={restored_size} sha256={restored_sha256}"
        )
    result = {
        "archive9_bytes": archive.stat().st_size,
        "archive9_sha256": sha256_file(archive),
        "bare_decode": True,
        "encode_guard": encode_guard,
        "payload_bytes": payload.stat().st_size,
        "payload_sha256": sha256_file(payload),
        "decode_guard": decode_guard,
        "restored_bytes": restored_size,
        "restored_sha256": restored_sha256,
        "roundtrip_ok": roundtrip_ok,
    }
    print(
        json.dumps(
            {
                "event": "arm_complete",
                "arm": arm,
                "payload_bytes": result["payload_bytes"],
                "archive9_bytes": result["archive9_bytes"],
            }
        ),
        flush=True,
    )
    return result


def repeated_encode(
    *,
    package: pathlib.Path,
    input_path: pathlib.Path,
    head_path: pathlib.Path,
    expected: dict[str, Any],
    root: pathlib.Path,
) -> dict[str, Any]:
    repeat_dir = root / "encode_G0_repeat"
    repeat_dir.mkdir()
    cmix = repeat_dir / "cmix"
    shutil.copyfile(package, cmix)
    cmix.chmod(0o755)
    payload = repeat_dir / "out.cmix"
    env = os.environ.copy()
    env["KH_BITLSTM32"] = str(head_path)
    env.pop("CMIX_PPM_RSS_MB", None)
    guard = run_guarded(
        ["./cmix", "-e", str(input_path), str(payload)],
        cwd=repeat_dir,
        label=f"{CANDIDATE_ID}_G0_repeat_encode",
        guard_path=repeat_dir / "rss_guard.json",
        env=env,
    )
    archive = repeat_dir / "archive9"
    identity = (
        sha256_file(payload) == expected["payload_sha256"]
        and sha256_file(archive) == expected["archive9_sha256"]
    )
    return {
        "guard": guard,
        "payload_bytes": payload.stat().st_size,
        "payload_sha256": sha256_file(payload),
        "archive9_bytes": archive.stat().st_size,
        "archive9_sha256": sha256_file(archive),
        "byte_identical": identity,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    parser.add_argument("--input", type=pathlib.Path, default=PROJECT_ROOT / "data" / "enwik9")
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=PROJECT_ROOT / "results" / CANDIDATE_ID,
    )
    args = parser.parse_args()

    donor_root = args.donor_root.resolve()
    input_path = args.input.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if input_path.stat().st_size != FULL_INPUT_BYTES:
        raise RuntimeError(f"full input size mismatch: {input_path.stat().st_size}")
    if sha256_file(input_path) != FULL_INPUT_SHA256:
        raise RuntimeError("full enwik9 hash mismatch")
    paths, raw_executable = verify_donor(donor_root)

    with tempfile.TemporaryDirectory(prefix=f"{CANDIDATE_ID}_") as temporary_text:
        temporary = pathlib.Path(temporary_text)
        prefix_path = temporary / "enwik7"
        write_prefix(input_path, prefix_path)
        data = prefix_path.read_bytes()

        geometry_order_a, page_counts = generate_order(data, "geometry")
        geometry_order_b, page_counts_b = generate_order(data, "geometry")
        if geometry_order_a != geometry_order_b or page_counts != page_counts_b:
            raise RuntimeError("G0 raw order rebuild is not byte-identical")

        b0_package = paths["packaged"]
        g0_package, g0_package_receipt = build_package(
            arm="G0",
            workspace=temporary / "package_G0",
            raw_executable=raw_executable,
            comp_dict=paths["comp_dict"],
            raw_order=geometry_order_a,
        )

        b0 = run_arm(
            arm="B0",
            package=b0_package,
            input_path=prefix_path,
            head_path=paths["head"],
            root=temporary,
        )
        if b0["payload_bytes"] != PARENT_PAYLOAD_BYTES:
            raise RuntimeError(f"B0 payload size mismatch: {b0['payload_bytes']}")
        if b0["archive9_bytes"] != PARENT_ARCHIVE_BYTES:
            raise RuntimeError(f"B0 archive size mismatch: {b0['archive9_bytes']}")

        g0 = run_arm(
            arm="G0",
            package=g0_package,
            input_path=prefix_path,
            head_path=paths["head"],
            root=temporary,
        )
        gross_gain = b0["archive9_bytes"] - g0["archive9_bytes"]
        t0: dict[str, Any] | None = None
        t0_package_receipt: dict[str, Any] | None = None
        repeat: dict[str, Any] | None = None
        control_pass = False
        determinism_pass = False

        if gross_gain >= GROSS_GATE_BYTES:
            title_order, title_counts = generate_order(data, "title")
            t0_package, t0_package_receipt = build_package(
                arm="T0",
                workspace=temporary / "package_T0",
                raw_executable=raw_executable,
                comp_dict=paths["comp_dict"],
                raw_order=title_order,
            )
            t0_package_receipt["page_counts"] = title_counts
            t0 = run_arm(
                arm="T0",
                package=t0_package,
                input_path=prefix_path,
                head_path=paths["head"],
                root=temporary,
            )
            control_pass = g0["archive9_bytes"] < t0["archive9_bytes"]
            repeat = repeated_encode(
                package=g0_package,
                input_path=prefix_path,
                head_path=paths["head"],
                expected=g0,
                root=temporary,
            )
            determinism_pass = bool(repeat["byte_identical"])

        verdict = (
            "AUTHORIZE_SOURCE_CHILD"
            if gross_gain >= GROSS_GATE_BYTES and control_pass and determinism_pass
            else "REJECT"
        )
        projected_archive_gain_1g = gross_gain * 100
        program_saving = FIXED_ORDER_ASSET_BYTES - ALGORITHMIC_SOURCE_ALLOWANCE
        projected_external_total = (
            EXTERNAL_FULL_TOTAL - program_saving - projected_archive_gain_1g
        )
        decision = {
            "candidate_id": CANDIDATE_ID,
            "schema": SCHEMA,
            "status": "terminal",
            "scope": {
                "bytes": SCOPE_BYTES,
                "sha256": SCOPE_SHA256,
                "population": "canonical opening 10M",
            },
            "inputs": {
                "donor_commit": DONOR_COMMIT,
                "full_input_bytes": FULL_INPUT_BYTES,
                "full_input_sha256": FULL_INPUT_SHA256,
                "packaged_cmix_bytes": PACKAGED_CMIX_BYTES,
                "packaged_cmix_sha256": PACKAGED_CMIX_SHA256,
                "raw_cmix_bytes": RAW_CMIX_BYTES,
                "raw_cmix_sha256": RAW_CMIX_SHA256,
                "comp_dict_bytes": COMP_DICT_BYTES,
                "comp_dict_sha256": COMP_DICT_SHA256,
                "comp_public_order_bytes": COMP_PUBLIC_ORDER_BYTES,
                "comp_public_order_sha256": COMP_PUBLIC_ORDER_SHA256,
                "raw_public_order_bytes": RAW_PUBLIC_ORDER_BYTES,
                "raw_public_order_sha256": RAW_PUBLIC_ORDER_SHA256,
                "head_bytes": HEAD_BYTES,
                "head_sha256": HEAD_SHA256,
            },
            "orders": {
                "geometry": {**g0_package_receipt, "page_counts": page_counts},
                "title": t0_package_receipt,
            },
            "arms": {"B0": b0, "G0": g0, "T0": t0, "G0_repeat": repeat},
            "accounting": {
                "b0_archive_bytes": b0["archive9_bytes"],
                "g0_archive_bytes": g0["archive9_bytes"],
                "gross_archive_gain_10m_bytes": gross_gain,
                "gross_archive_gain_bytes_per_million": gross_gain / 10.0,
                "gross_gate_bytes": GROSS_GATE_BYTES,
                "algorithmic_source_allowance_bytes": ALGORITHMIC_SOURCE_ALLOWANCE,
                "fixed_order_asset_bytes": FIXED_ORDER_ASSET_BYTES,
                "program_saving_ceiling_bytes": program_saving,
                "projected_archive_gain_1g_bytes": projected_archive_gain_1g,
                "projected_external_total_bytes": projected_external_total,
                "standing_target_bytes": TARGET_BYTES,
                "projected_target_margin_bytes": TARGET_BYTES - projected_external_total,
                "projection_score_credit_bytes": 0,
            },
            "gates": {
                "parent_payload_identity": b0["payload_bytes"] == PARENT_PAYLOAD_BYTES,
                "parent_archive_identity": b0["archive9_bytes"] == PARENT_ARCHIVE_BYTES,
                "parent_roundtrip": b0["roundtrip_ok"],
                "geometry_order_rebuild_identity": geometry_order_a == geometry_order_b,
                "geometry_roundtrip": g0["roundtrip_ok"],
                "geometry_gross_gate": gross_gain >= GROSS_GATE_BYTES,
                "geometry_beats_title": control_pass,
                "geometry_repeat_identity": determinism_pass,
            },
            "decision": {
                "verdict": verdict,
                "scientific_valid": True,
                "score_credit_bytes": 0,
                "forecast_change_authorized": False,
                "source_child_authorized": verdict == "AUTHORIZE_SOURCE_CHILD",
                "next_action": (
                    "Materialize only the frozen source-level geometry generator child and one distant replay."
                    if verdict == "AUTHORIZE_SOURCE_CHILD"
                    else "Retire this exact geometry-order substitution on the cmix-obias donor without rescue sweeps."
                ),
            },
        }
        atomic_json(output_dir / "decision.json", decision)
        print(json.dumps(decision, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
