#!/usr/bin/env python3
"""Exact side-free title-join screen for the cmix-obias payload tail."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
RSS_GUARD = PROJECT_ROOT / "tools" / "run_with_rss_guard.py"

CANDIDATE_ID = "cmix_obias_title_join_tail_qm0_v1"
SCHEMA = "cmix_obias_title_join_tail_qm0_decision_v1"
DONOR_COMMIT = "51488a0c1228dbeab7c1be837fc90ceaed351728"

ORIGINAL_READY_BYTES = 586_459_321
ORIGINAL_READY_SHA256 = "cb466004e5d76000ba7d44a1a4a47245c203f4e8fbb62ffca7799692c966ff4f"
TRANSFORMED_READY_BYTES = 587_138_826
TRANSFORMED_READY_SHA256 = "7826ff63dedd526c119dda08e6e044be8fa8f6e89a55f3d6b1f3447cdfc5c1ce"
SIDE_BYTES = 679_489
SIDE_SHA256 = "98bae9de75b13b0a4f66f33cd24f1c45b145237eb4f99b363c9cb4e6ef918d95"
MAIN_REORDERED_BYTES = 999_988_851
MAIN_REORDERED_SHA256 = "9284d618f69dfc0adb119c64bfe0326a422d151812844a5406128fdc7a131107"

RAW_CMIX_BYTES = 159_704
RAW_CMIX_SHA256 = "24f52d24e5ff5027fa76ea75864a76b7d627917f75df14c64091f1f37b519ec0"
HEAD_BYTES = 23_002
HEAD_SHA256 = "35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078"

TAIL_START = 541_126_651
REGIME1_START = 13_599_801
REGIME2_START = 30_372_888
REGIME1_ABSOLUTE = TAIL_START + REGIME1_START
REGIME1_LENGTH = REGIME2_START - REGIME1_START
SLICE_BYTES = 250_000
TITLE_ROTATION = 37
EXPECTED_PAGES = 243_425
PUBLIC_ENCODED_SIDE_BYTES = 346_948
PUBLIC_EXTERNAL_TOTAL = 108_492_825
TARGET_BYTES = 108_000_000
ORDER_ASSET_CEILING_BYTES = 166_903
SOURCE_ALLOWANCE_BYTES = 16_384
DECIMAL_10GB_KIB = 9_765_625
BINARY_10GIB_KIB = 10_485_760

PAGE_OPEN = b"  <page>\n"
PAGE_CLOSE = b"  </page>\n"
TITLE_RE = re.compile(rb"<title>(.*?)</title>", re.DOTALL)
ID_RE = re.compile(rb"<id>(\d+)</id>")
BLOCK_MARKER = b"\xdf\x99N\n"
D86_PREFIX = b"\xdf\x86N"


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(8 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_file(path: pathlib.Path, size: int, digest: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(path)
    actual_size = path.stat().st_size
    actual_digest = sha256_file(path)
    if actual_size != size or actual_digest != digest:
        raise RuntimeError(
            f"artifact mismatch: {path} bytes={actual_size} sha256={actual_digest}"
        )


def atomic_json(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temporary.replace(path)


def donor_paths(donor_root: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    packaged = donor_root / "artifacts_asbuilt" / "cmix"
    head = donor_root / "cmix-obias" / "models" / "bitlstm32" / "refit_golden256_fp16.blob"
    if not packaged.is_file():
        raise FileNotFoundError(packaged)
    raw = packaged.read_bytes()[:RAW_CMIX_BYTES]
    if len(raw) != RAW_CMIX_BYTES or sha256_bytes(raw) != RAW_CMIX_SHA256:
        raise RuntimeError("cmix-obias raw executable prefix mismatch")
    require_file(head, HEAD_BYTES, HEAD_SHA256)
    return packaged, head


def parse_pages(path: pathlib.Path) -> tuple[list[bytes], list[int]]:
    titles: list[bytes] = []
    revisions: list[int] = []
    in_page = False
    in_revision = False
    title: bytes | None = None
    revision: int | None = None
    with path.open("rb") as source:
        for line in source:
            if line == PAGE_OPEN:
                if in_page:
                    raise RuntimeError("nested page opener")
                in_page = True
                in_revision = False
                title = None
                revision = None
                continue
            if not in_page:
                continue
            if title is None:
                match = TITLE_RE.search(line)
                if match:
                    title = match.group(1)
            if b"<revision>" in line:
                in_revision = True
            elif in_revision and revision is None:
                match = ID_RE.search(line)
                if match:
                    revision = int(match.group(1))
            if line == PAGE_CLOSE:
                if title is None or revision is None:
                    raise RuntimeError(f"page {len(titles)} lacks title or revision id")
                titles.append(title)
                revisions.append(revision)
                in_page = False
                in_revision = False
    if in_page:
        raise RuntimeError("reordered main ends inside a page")
    return titles, revisions


def body(line: bytes) -> bytes:
    return line.rstrip(b"\r\n")


def is_ascii_number_line(line: bytes) -> bool:
    value = body(line)
    return bool(value) and all(48 <= byte <= 57 or byte == 45 for byte in value)


def parse_regime(data: bytes) -> tuple[list[bytes], list[bytes], list[bytes]]:
    lines = data.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line == BLOCK_MARKER]
    if not starts:
        raise RuntimeError("regime has no D99 metadata blocks")
    prelude = lines[: starts[0]]
    blocks: list[bytes] = []
    cursor = starts[0]
    limit = len(lines)
    for block_index, start in enumerate(starts):
        if start != cursor:
            raise RuntimeError(f"noncanonical block boundary at {block_index}")
        next_start = starts[block_index + 1] if block_index + 1 < len(starts) else limit
        if next_start - start <= 16:
            end = next_start
        else:
            end = min(start + 7, next_start)
            if end < next_start and is_ascii_number_line(lines[end]):
                end += 1
                if end < next_start and lines[end] != BLOCK_MARKER:
                    candidate = body(lines[end])
                    if candidate and len(candidate) <= 16 and candidate[0] >= 0x80:
                        end += 1
        blocks.append(b"".join(lines[start:end]))
        cursor = end
    return prelude, blocks, lines[cursor:]


def block_lines(block: bytes) -> list[bytes]:
    return block.splitlines(keepends=True)


def block_revision(block: bytes) -> int:
    lines = block_lines(block)
    if len(lines) < 2 or lines[0] != BLOCK_MARKER:
        raise RuntimeError("malformed metadata block")
    value = body(lines[1])
    if not value.startswith(D86_PREFIX):
        raise RuntimeError("metadata block lacks first D86a value")
    suffix = value[len(D86_PREFIX) :]
    if not suffix.isdigit():
        raise RuntimeError("metadata block D86a value is not unsigned decimal")
    return int(suffix)


def block_sort_key(block: bytes) -> bytes:
    lines = block_lines(block)
    if len(lines) < 2:
        raise RuntimeError("metadata block is too short")
    return b"".join(lines[2:])


def render_regime(prelude: list[bytes], blocks: list[bytes], suffix: list[bytes], order: list[int]) -> bytes:
    return b"".join([*prelude, *(blocks[index] for index in order), *suffix])


def restore_regime(
    prelude: list[bytes], ordered_blocks: list[bytes], suffix: list[bytes], order: list[int]
) -> bytes:
    restored: list[bytes | None] = [None] * len(ordered_blocks)
    for position, original_index in enumerate(order):
        if original_index >= len(restored) or restored[original_index] is not None:
            raise RuntimeError("order is not a permutation")
        restored[original_index] = ordered_blocks[position]
    if any(block is None for block in restored):
        raise RuntimeError("order omits a metadata block")
    return b"".join([*prelude, *(block for block in restored if block is not None), *suffix])


def run_checked(command: list[str], *, cwd: pathlib.Path, env: dict[str, str]) -> None:
    print(json.dumps({"event": "command", "cwd": str(cwd), "command": command}), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)


def run_guarded(
    command: list[str], *, cwd: pathlib.Path, env: dict[str, str], label: str
) -> dict[str, Any]:
    guard_path = cwd / f"{label}.guard.json"
    run_checked(
        [
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
        ],
        cwd=cwd,
        env=env,
    )
    guard = json.loads(guard_path.read_text())
    if guard.get("status") != "complete" or guard.get("returncode") != 0:
        raise RuntimeError(f"guarded command failed: {label}")
    return guard


def run_slice(
    *,
    raw_executable: bytes,
    head: pathlib.Path,
    data: bytes,
    arm: str,
    slice_index: int,
    root: pathlib.Path,
) -> dict[str, Any]:
    work = root / f"{arm}_{slice_index}"
    work.mkdir(parents=True)
    executable = work / "cmix"
    executable.write_bytes(raw_executable)
    executable.chmod(0o755)
    input_path = work / "input.bin"
    archive_path = work / "payload.cmix"
    restored_path = work / "restored.bin"
    input_path.write_bytes(data)
    env = os.environ.copy()
    env["KH_BITLSTM32"] = str(head)
    env.pop("CMIX_PPM_RSS_MB", None)
    encode_guard = run_guarded(
        ["./cmix", "-n", "input.bin", "payload.cmix"],
        cwd=work,
        env=env,
        label=f"{CANDIDATE_ID}_{arm}_{slice_index}_encode",
    )
    (work / "ppm.temp").unlink(missing_ok=True)
    decode_guard = run_guarded(
        ["./cmix", "-d", "payload.cmix", "restored.bin"],
        cwd=work,
        env=env,
        label=f"{CANDIDATE_ID}_{arm}_{slice_index}_decode",
    )
    (work / "ppm.temp").unlink(missing_ok=True)
    restored = restored_path.read_bytes()
    roundtrip_ok = restored == data
    if not roundtrip_ok:
        raise RuntimeError(f"{arm} slice {slice_index} failed exact decode")
    return {
        "input_bytes": len(data),
        "input_sha256": sha256_bytes(data),
        "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": sha256_file(archive_path),
        "restored_sha256": sha256_bytes(restored),
        "roundtrip_ok": roundtrip_ok,
        "encode_guard": encode_guard,
        "decode_guard": decode_guard,
    }


def repeat_slice(
    *,
    raw_executable: bytes,
    head: pathlib.Path,
    data: bytes,
    slice_index: int,
    expected: dict[str, Any],
    root: pathlib.Path,
) -> dict[str, Any]:
    work = root / f"T0_repeat_{slice_index}"
    work.mkdir(parents=True)
    executable = work / "cmix"
    executable.write_bytes(raw_executable)
    executable.chmod(0o755)
    (work / "input.bin").write_bytes(data)
    env = os.environ.copy()
    env["KH_BITLSTM32"] = str(head)
    env.pop("CMIX_PPM_RSS_MB", None)
    guard = run_guarded(
        ["./cmix", "-n", "input.bin", "payload.cmix"],
        cwd=work,
        env=env,
        label=f"{CANDIDATE_ID}_T0_repeat_{slice_index}_encode",
    )
    (work / "ppm.temp").unlink(missing_ok=True)
    archive = work / "payload.cmix"
    digest = sha256_file(archive)
    identical = (
        archive.stat().st_size == expected["archive_bytes"]
        and digest == expected["archive_sha256"]
    )
    if not identical:
        raise RuntimeError(f"T0 slice {slice_index} repeat differs")
    return {
        "archive_bytes": archive.stat().st_size,
        "archive_sha256": digest,
        "byte_identical": identical,
        "encode_guard": guard,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifact-root",
        type=pathlib.Path,
        default=pathlib.Path(
            "/home/x/enwiki9-nonproof/cmix_lex_payload_gate/"
            "cmix_lex_payload_transfer_v1_retry2"
        ),
    )
    parser.add_argument("--donor-root", type=pathlib.Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=PROJECT_ROOT / "results" / CANDIDATE_ID,
    )
    args = parser.parse_args()

    artifact_root = args.artifact_root.resolve()
    donor_root = args.donor_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    original = artifact_root / "original_ready.bin"
    transformed = artifact_root / "transformed_ready.bin"
    side = artifact_root / "extracted_payload_side.bin"
    main_reordered = artifact_root / "work" / ".main_reordered"
    require_file(original, ORIGINAL_READY_BYTES, ORIGINAL_READY_SHA256)
    require_file(transformed, TRANSFORMED_READY_BYTES, TRANSFORMED_READY_SHA256)
    require_file(side, SIDE_BYTES, SIDE_SHA256)
    require_file(main_reordered, MAIN_REORDERED_BYTES, MAIN_REORDERED_SHA256)

    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=donor_root, text=True
    ).strip()
    if commit != DONOR_COMMIT:
        raise RuntimeError(f"donor commit mismatch: {commit}")
    packaged, head = donor_paths(donor_root)
    raw_executable = packaged.read_bytes()[:RAW_CMIX_BYTES]

    titles, page_revisions = parse_pages(main_reordered)
    if len(titles) != EXPECTED_PAGES or len(page_revisions) != EXPECTED_PAGES:
        raise RuntimeError("unexpected complete-page count")
    unique_titles = len(set(titles))
    if unique_titles != EXPECTED_PAGES:
        raise RuntimeError(f"exact page titles are not unique: {unique_titles}")

    with original.open("rb") as source:
        source.seek(REGIME1_ABSOLUTE)
        original_regime = source.read(REGIME1_LENGTH)
    if len(original_regime) != REGIME1_LENGTH:
        raise RuntimeError("short original regime read")
    with transformed.open("rb") as source:
        source.seek(REGIME1_ABSOLUTE)
        public_regime = source.read(REGIME1_LENGTH)
    if len(public_regime) != REGIME1_LENGTH:
        raise RuntimeError("short transformed regime read")

    prelude, blocks, suffix = parse_regime(original_regime)
    if len(blocks) != EXPECTED_PAGES:
        raise RuntimeError(f"unexpected metadata-block count: {len(blocks)}")
    block_revisions = [block_revision(block) for block in blocks]
    mismatches = [
        index
        for index, (page_revision, metadata_revision) in enumerate(
            zip(page_revisions, block_revisions, strict=True)
        )
        if page_revision != metadata_revision
    ]
    if mismatches:
        raise RuntimeError(f"page/block revision mismatch at {mismatches[:8]}")

    original_order = list(range(EXPECTED_PAGES))
    payload_order = sorted(
        original_order, key=lambda index: (block_sort_key(blocks[index]), index)
    )
    title_order = sorted(
        original_order, key=lambda index: (titles[index], page_revisions[index], index)
    )
    rotated_order = sorted(
        original_order,
        key=lambda index: (
            titles[(index + TITLE_ROTATION) % EXPECTED_PAGES],
            page_revisions[index],
            index,
        ),
    )

    rebuilt_public = render_regime(prelude, blocks, suffix, payload_order)
    public_identity = rebuilt_public == public_regime
    if not public_identity:
        raise RuntimeError("rebuilt public payload-key regime differs")
    title_regime = render_regime(prelude, blocks, suffix, title_order)
    rotated_regime = render_regime(prelude, blocks, suffix, rotated_order)
    title_inverse = restore_regime(
        prelude,
        [blocks[index] for index in title_order],
        suffix,
        title_order,
    ) == original_regime
    rotated_inverse = restore_regime(
        prelude,
        [blocks[index] for index in rotated_order],
        suffix,
        rotated_order,
    ) == original_regime
    if not title_inverse or not rotated_inverse:
        raise RuntimeError("side-free join inverse failed")

    regimes = {
        "O0": original_regime,
        "P0": public_regime,
        "T0": title_regime,
        "TR": rotated_regime,
    }
    starts = [
        0,
        (REGIME1_LENGTH - SLICE_BYTES) // 2,
        REGIME1_LENGTH - SLICE_BYTES,
    ]
    arms: dict[str, list[dict[str, Any]]] = {arm: [] for arm in regimes}
    with tempfile.TemporaryDirectory(prefix=f"{CANDIDATE_ID}_") as temporary_text:
        temporary = pathlib.Path(temporary_text)
        for arm, regime in regimes.items():
            for slice_index, start in enumerate(starts):
                row = run_slice(
                    raw_executable=raw_executable,
                    head=head,
                    data=regime[start : start + SLICE_BYTES],
                    arm=arm,
                    slice_index=slice_index,
                    root=temporary,
                )
                row["relative_start"] = start
                arms[arm].append(row)

        totals = {
            arm: sum(row["archive_bytes"] for row in rows)
            for arm, rows in arms.items()
        }
        t0_no_worse_each_o0 = all(
            title_row["archive_bytes"] <= original_row["archive_bytes"]
            for title_row, original_row in zip(arms["T0"], arms["O0"], strict=True)
        )
        t0_no_larger_p0 = totals["T0"] <= totals["P0"]
        t0_beats_rotated = totals["T0"] < totals["TR"]
        memory_ok = all(
            row[guard_name].get("official_decimal_over_limit_kib", 1) == 0
            for rows in arms.values()
            for row in rows
            for guard_name in ("encode_guard", "decode_guard")
        )
        pre_repeat_pass = (
            t0_no_worse_each_o0
            and t0_no_larger_p0
            and t0_beats_rotated
            and memory_ok
        )
        repeats: list[dict[str, Any]] | None = None
        repeat_identity = False
        if pre_repeat_pass:
            repeats = []
            for slice_index, start in enumerate(starts):
                repeats.append(
                    repeat_slice(
                        raw_executable=raw_executable,
                        head=head,
                        data=title_regime[start : start + SLICE_BYTES],
                        slice_index=slice_index,
                        expected=arms["T0"][slice_index],
                        root=temporary,
                    )
                )
            repeat_identity = all(row["byte_identical"] for row in repeats)

    sampled_delta_vs_public = totals["P0"] - totals["T0"]
    projected_regime_delta = (
        sampled_delta_vs_public * REGIME1_LENGTH / (len(starts) * SLICE_BYTES)
    )
    side_free_ceiling = PUBLIC_ENCODED_SIDE_BYTES + projected_regime_delta
    verdict = (
        "AUTHORIZE_SOURCE_CHILD"
        if pre_repeat_pass and repeat_identity
        else "REJECT"
    )
    decision = {
        "schema": SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "status": "terminal",
        "inputs": {
            "artifact_root": str(artifact_root),
            "original_ready_bytes": ORIGINAL_READY_BYTES,
            "original_ready_sha256": ORIGINAL_READY_SHA256,
            "transformed_ready_bytes": TRANSFORMED_READY_BYTES,
            "transformed_ready_sha256": TRANSFORMED_READY_SHA256,
            "side_bytes": SIDE_BYTES,
            "side_sha256": SIDE_SHA256,
            "main_reordered_bytes": MAIN_REORDERED_BYTES,
            "main_reordered_sha256": MAIN_REORDERED_SHA256,
            "donor_commit": DONOR_COMMIT,
            "raw_cmix_bytes": RAW_CMIX_BYTES,
            "raw_cmix_sha256": RAW_CMIX_SHA256,
            "head_bytes": HEAD_BYTES,
            "head_sha256": HEAD_SHA256,
        },
        "scope": {
            "population": "full-corpus payload_lex regime 1; three frozen reset-state 250K slices",
            "regime_bytes": REGIME1_LENGTH,
            "sampled_bytes": len(starts) * SLICE_BYTES,
            "slice_relative_starts": starts,
        },
        "association": {
            "complete_pages": len(titles),
            "metadata_blocks": len(blocks),
            "unique_exact_titles": unique_titles,
            "revision_id_mismatches": len(mismatches),
            "page_revision_digest": sha256_bytes(
                b"".join(value.to_bytes(8, "little") for value in page_revisions)
            ),
            "title_order_digest": sha256_bytes(
                b"".join(value.to_bytes(4, "little") for value in title_order)
            ),
            "rotated_order_digest": sha256_bytes(
                b"".join(value.to_bytes(4, "little") for value in rotated_order)
            ),
            "payload_order_digest": sha256_bytes(
                b"".join(value.to_bytes(4, "little") for value in payload_order)
            ),
        },
        "representations": {
            "O0_sha256": sha256_bytes(original_regime),
            "P0_sha256": sha256_bytes(public_regime),
            "T0_sha256": sha256_bytes(title_regime),
            "TR_sha256": sha256_bytes(rotated_regime),
            "public_rebuild_identity": public_identity,
            "title_inverse_exact": title_inverse,
            "rotated_inverse_exact": rotated_inverse,
            "raw_side_bytes_T0": 0,
        },
        "arms": arms,
        "totals": totals,
        "repeat": repeats,
        "accounting": {
            "public_external_total_bytes": PUBLIC_EXTERNAL_TOTAL,
            "target_bytes": TARGET_BYTES,
            "external_parent_debt_bytes": PUBLIC_EXTERNAL_TOTAL - TARGET_BYTES,
            "public_encoded_side_bytes": PUBLIC_ENCODED_SIDE_BYTES,
            "sampled_T0_minus_P0_bytes": totals["T0"] - totals["P0"],
            "projected_regime_T0_minus_P0_bytes": -projected_regime_delta,
            "side_free_ceiling_bytes": side_free_ceiling,
            "source_allowance_bytes": SOURCE_ALLOWANCE_BYTES,
            "order_asset_ceiling_bytes": ORDER_ASSET_CEILING_BYTES,
            "joint_optimistic_ceiling_bytes": side_free_ceiling
            + ORDER_ASSET_CEILING_BYTES,
            "full_1g_projection_valid": False,
            "score_credit_bytes": 0,
        },
        "gates": {
            "artifact_identity": True,
            "page_block_alignment": len(mismatches) == 0,
            "titles_unique": unique_titles == EXPECTED_PAGES,
            "public_rebuild_identity": public_identity,
            "title_inverse_exact": title_inverse,
            "rotated_inverse_exact": rotated_inverse,
            "all_slice_roundtrips": all(
                row["roundtrip_ok"] for rows in arms.values() for row in rows
            ),
            "memory_ok": memory_ok,
            "T0_no_larger_than_P0": t0_no_larger_p0,
            "T0_no_worse_than_O0_each_slice": t0_no_worse_each_o0,
            "T0_beats_TR": t0_beats_rotated,
            "T0_repeat_identity": repeat_identity,
        },
        "decision": {
            "verdict": verdict,
            "scientific_valid": True,
            "score_credit_bytes": 0,
            "forecast_change_authorized": False,
            "next_action": (
                "Authorize one paid full-state source child only."
                if verdict == "AUTHORIZE_SOURCE_CHILD"
                else "Retire this exact side-free bytewise-title join without rescue sweeps."
            ),
        },
    }
    atomic_json(output_dir / "decision.json", decision)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
