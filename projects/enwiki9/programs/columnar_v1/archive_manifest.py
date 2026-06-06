"""archive_manifest — schema, hashes, provenance.

The manifest is the human-auditable description of the archive. Every
channel has its sha256 hash; the total input has its sha256 hash.
Decoder verifies all hashes before releasing bytes — if any verification
fails, the archive is rejected.

Phase boundaries declare schema_version; decoder refuses to open archives
with a schema_version it does not understand.
"""

from __future__ import annotations

import hashlib
import json

SCHEMA_VERSION = 7
MODE_TYPED_PHASE1_WC = "typed_phase1_wc"
MODE_TYPED_PHASE4_WC = "typed_phase4_wc"
MODE_TYPED_PHASE4 = "typed_phase4"
MODE_TYPED_PHASE3 = "typed_phase3"
MODE_TYPED_PHASE2A = "typed_phase2a"
MODE_TYPED_PHASE2 = "typed_phase2"
MODE_TYPED_PHASE1 = "typed_phase1"
MODE_LITERAL_FALLBACK = "literal_fallback"


def hash_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_manifest(
    mode: str,
    total_input_size: int,
    total_input_hash: str,
    channel_entries: list[dict],
    notes: dict | None = None,
) -> dict:
    m: dict = {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "total_input_size": total_input_size,
        "total_input_hash": total_input_hash,
        "channels": channel_entries,
    }
    if notes is not None:
        m["notes"] = notes
    return m


def manifest_to_bytes(manifest: dict) -> bytes:
    return json.dumps(manifest, separators=(",", ":"), sort_keys=True).encode(
        "ascii"
    )


def manifest_from_bytes(data: bytes) -> dict:
    m = json.loads(data)
    if m.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(
            f"unsupported schema_version {m.get('schema_version')}; "
            f"this decoder requires {SCHEMA_VERSION}"
        )
    if m.get("mode") not in (
        MODE_TYPED_PHASE1_WC,
        MODE_TYPED_PHASE4_WC,
        MODE_TYPED_PHASE4,
        MODE_TYPED_PHASE3,
        MODE_TYPED_PHASE2A,
        MODE_TYPED_PHASE2,
        MODE_TYPED_PHASE1,
        MODE_LITERAL_FALLBACK,
    ):
        raise ValueError(f"unsupported mode {m.get('mode')}")
    return m
