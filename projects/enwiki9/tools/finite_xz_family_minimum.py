#!/usr/bin/env python3
"""Certify the minimum member of a frozen finite XZ parameter family."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
from pathlib import Path
import subprocess


DICTIONARIES = {
    "768KiB": 768 * 1024,
    "800KiB": 800 * 1024,
    "832KiB": 832 * 1024,
    "896KiB": 896 * 1024,
    "1MiB": 1024 * 1024,
    "1536KiB": 1536 * 1024,
    "2MiB": 2 * 1024 * 1024,
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def descriptor(
    dictionary: str,
    lc: int,
    lp: int,
    pb: int,
    mode: str,
    nice: int,
    match_finder: str,
    depth: int,
) -> str:
    return (
        f"dict={dictionary},lc={lc},lp={lp},pb={pb},mode={mode},"
        f"nice={nice},mf={match_finder},depth={depth}"
    )


def family() -> list[str]:
    members: set[str] = set()
    for lc in range(5):
        for lp in range(5 - lc):
            for pb in range(5):
                members.add(descriptor("1MiB", lc, lp, pb, "normal", 273, "bt4", 0))
    for mode in ("normal", "fast"):
        for match_finder in ("hc3", "hc4", "bt2", "bt3", "bt4"):
            for nice in (32, 64, 128, 192, 273):
                for depth in (0, 32, 64, 128, 256):
                    members.add(
                        descriptor(
                            "1MiB", 4, 0, 0, mode, nice, match_finder, depth
                        )
                    )
    for nice in (80, 96, 112, 128, 144, 160, 176):
        for depth in (128, 192, 256, 320, 384, 448, 512):
            members.add(descriptor("1MiB", 4, 0, 0, "normal", nice, "bt2", depth))
    for dictionary in DICTIONARIES:
        members.add(descriptor(dictionary, 4, 0, 0, "normal", 112, "bt2", 256))
    return sorted(members)


def dictionary_bytes(description: str) -> int:
    name = description.split(",", 1)[0].split("=", 1)[1]
    return DICTIONARIES[name]


def encode(raw: bytes, description: str) -> bytes:
    command = [
        "xz",
        "--threads=1",
        "--format=xz",
        "--x86",
        f"--lzma2={description}",
        "-c",
    ]
    return subprocess.run(
        command,
        input=raw,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--receipt", required=True, type=Path)
    args = parser.parse_args()

    parent = args.input.read_bytes()
    raw = lzma.decompress(parent)
    descriptions = family()
    rows: list[dict[str, object]] = []
    payloads: dict[str, bytes] = {}
    for description in descriptions:
        payload = encode(raw, description)
        decoded = lzma.decompress(payload)
        admissible = decoded == raw
        rows.append(
            {
                "admissible": admissible,
                "decoded_sha256": sha256(decoded),
                "description": description,
                "dictionary_bytes": dictionary_bytes(description),
                "payload_bytes": len(payload),
                "payload_sha256": sha256(payload),
            }
        )
        if admissible:
            payloads[description] = payload

    admissible_rows = [row for row in rows if row["admissible"]]
    if not admissible_rows:
        raise RuntimeError("no admissible finite-family member")
    selected = min(
        admissible_rows,
        key=lambda row: (
            int(row["payload_bytes"]),
            int(row["dictionary_bytes"]),
            str(row["description"]),
        ),
    )
    selected_description = str(selected["description"])
    args.output.write_bytes(payloads[selected_description])

    family_serialization = ("\n".join(descriptions) + "\n").encode("ascii")
    receipt = {
        "family_count": len(descriptions),
        "family_serialization_sha256": sha256(family_serialization),
        "input_payload_bytes": len(parent),
        "input_payload_sha256": sha256(parent),
        "raw_bytes": len(raw),
        "raw_sha256": sha256(raw),
        "rows": rows,
        "schema": "finite_xz_family_minimum_v1",
        "score_credit_bytes": 0,
        "selected": selected,
        "selected_saved_bytes": len(parent) - int(selected["payload_bytes"]),
        "verdict": "exact_global_minimum_over_committed_family",
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                key: receipt[key]
                for key in (
                    "family_count",
                    "family_serialization_sha256",
                    "raw_sha256",
                    "selected",
                    "selected_saved_bytes",
                    "verdict",
                )
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
