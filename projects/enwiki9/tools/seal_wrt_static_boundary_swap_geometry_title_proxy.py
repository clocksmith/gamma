#!/usr/bin/env python3
"""Seal matched geometry-title proxy evidence for a static WRT boundary swap."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compressed_size(command: list[str], path: pathlib.Path) -> int:
    completed = subprocess.run(
        [*command, str(path)],
        check=True,
        stdout=subprocess.PIPE,
    )
    return len(completed.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identity-store", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-store", type=pathlib.Path, required=True)
    parser.add_argument("--identity-dictionary", type=pathlib.Path, required=True)
    parser.add_argument("--candidate-dictionary", type=pathlib.Path, required=True)
    parser.add_argument("--transform-receipt", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    transform = json.loads(args.transform_receipt.read_text())
    expected = {
        "store_sha256": sha256(args.identity_store),
        "output_store_sha256": sha256(args.candidate_store),
        "dictionary_sha256": sha256(args.identity_dictionary),
        "output_dictionary_sha256": sha256(args.candidate_dictionary),
    }
    for field, observed in expected.items():
        if transform.get(field) != observed:
            raise SystemExit(
                f"transform receipt mismatch for {field}: "
                f"{transform.get(field)!r} != {observed!r}"
            )
    if not transform.get("inverse_permutation_roundtrip_ok"):
        raise SystemExit("inverse permutation did not pass")
    if not transform.get("raw_roundtrip_ok"):
        raise SystemExit("raw roundtrip did not pass")

    compressors = {
        "xz_9e": ["xz", "-9e", "-c"],
        "gzip_9n": ["gzip", "-9n", "-c"],
    }
    proxy: dict[str, object] = {}
    for name, command in compressors.items():
        identity_store_bytes = compressed_size(command, args.identity_store)
        candidate_store_bytes = compressed_size(command, args.candidate_store)
        identity_dictionary_bytes = compressed_size(command, args.identity_dictionary)
        candidate_dictionary_bytes = compressed_size(command, args.candidate_dictionary)
        identity_total = identity_store_bytes + identity_dictionary_bytes
        candidate_total = candidate_store_bytes + candidate_dictionary_bytes
        proxy[name] = {
            "identity_store_bytes": identity_store_bytes,
            "candidate_store_bytes": candidate_store_bytes,
            "identity_dictionary_bytes": identity_dictionary_bytes,
            "candidate_dictionary_bytes": candidate_dictionary_bytes,
            "identity_total_bytes": identity_total,
            "candidate_total_bytes": candidate_total,
            "saved_bytes": identity_total - candidate_total,
            "saved_bytes_per_1m_raw": (identity_total - candidate_total) / 10.0,
        }

    minimum_proxy_saved = min(row["saved_bytes"] for row in proxy.values())
    dictionary_delta = min(
        row["candidate_dictionary_bytes"] - row["identity_dictionary_bytes"]
        for row in proxy.values()
    )
    receipt = {
        "schema": "wrt_static_boundary_swap_geometry_title_proxy_v1",
        "evidence_level": "matched_reversible_geometry_title_10m_proxy",
        "mechanism": (
            "swap 64 low-frequency two-byte WRT dictionary entries with "
            "high-frequency three-byte entries while preserving stable token identity"
        ),
        "inputs": {
            "identity_store": {
                "path": str(args.identity_store),
                "bytes": args.identity_store.stat().st_size,
                "sha256": expected["store_sha256"],
            },
            "candidate_store": {
                "path": str(args.candidate_store),
                "bytes": args.candidate_store.stat().st_size,
                "sha256": expected["output_store_sha256"],
            },
            "identity_dictionary": {
                "path": str(args.identity_dictionary),
                "bytes": args.identity_dictionary.stat().st_size,
                "sha256": expected["dictionary_sha256"],
            },
            "candidate_dictionary": {
                "path": str(args.candidate_dictionary),
                "bytes": args.candidate_dictionary.stat().st_size,
                "sha256": expected["output_dictionary_sha256"],
            },
            "transform_receipt": {
                "path": str(args.transform_receipt),
                "bytes": args.transform_receipt.stat().st_size,
                "sha256": sha256(args.transform_receipt),
            },
        },
        "transform": {
            "selected_one_two_swaps": transform["selected_one_two_swaps"],
            "selected_two_three_swaps": transform["selected_two_three_swaps"],
            "raw_saved_bytes": transform["raw_saved_bytes"],
            "inverse_permutation_roundtrip_ok": True,
            "raw_roundtrip_ok": True,
            "decoded_raw_bytes": transform["decoded_raw_bytes"],
            "source_raw_sha256": transform["source_raw_sha256"],
            "output_raw_sha256": transform["output_raw_sha256"],
        },
        "matched_proxies": proxy,
        "economics": {
            "conservative_112_plus_80_tail_gap_bytes_per_1m": 22.498,
            "minimum_proxy_saved_bytes": minimum_proxy_saved,
            "minimum_proxy_saved_bytes_per_1m_raw": minimum_proxy_saved / 10.0,
            "minimum_compressed_dictionary_delta_bytes": dictionary_delta,
            "exact_112_plus_80_screen_authorized": (
                minimum_proxy_saved / 10.0 > 22.498
            ),
        },
        "promotion_authorized": False,
        "claim_boundary": (
            "This is reversible matched proxy evidence only. Promotion requires "
            "an exact 112+80 archive comparison, decode, determinism, RSS, runtime, "
            "and counted source-package accounting."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
