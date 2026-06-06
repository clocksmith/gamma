"""columnar_v1 — Phases 1 + 2A + 4 of the relational-decomposition build.

Phase 4 is the active mode. It keeps the architectural shape from
Phase 2A (typed-artifact extraction with byte-perfect format masks,
hash-validated manifest, conservative-abort discipline) and adds
type-aware dictionary coding to the narrowest-vocab columns:

  - template_names: 228 distinct at 10 MB → 1-byte varint indices
  - template_arg_keys: ~100 distinct (url, title, date, publisher, ...) →
    1-byte varint indices
  - wikilink_targets: 65K distinct of 109K at 10 MB; popular targets
    ("United States" ×386 at 10 MB) collapse to 1-byte indices

Each dict-coded column ships its dictionary in its own channel. Index
stream uses small varints. Format masks are unchanged from Phase 2A —
the rigor of byte-perfect template/wikilink reconstruction is preserved.

Single monolithic xz over the concatenated columns (one pass). Manifest
records channel order, raw_size, sha256 per channel.

Phase 3 (columnar transposition without per-column codecs) is retired
from the active path — it regressed against Phase 2A under raw lzma
because the per-record interleave already exposed enough redundancy for
lzma's match finder. The transposed layout only pays once per-column
type-aware codecs replace lzma — which is what Phase 4 does selectively.

Subsequent phases:
  Phase 5: arithmetic coding + Gibbs mixer on the prose residual
"""

from __future__ import annotations

import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve()))

import archive_manifest as M
import channel_codec as CC
import scaffold_codec as SC
import template_parser as TP
import wikilink_parser as WL
import xml_parser as XP


PHASE4_TEMPLATE_CHANNELS = [
    "template_names_dict",
    "template_keys_dict",
    "template_tuples",
    "template_masks",
]
PHASE4_WIKILINK_CHANNELS = [
    "wikilink_targets_dict",
    "wikilink_tuples",
    "wikilink_masks",
]


def _has_any_sentinel_collision(data: bytes) -> bool:
    if XP.has_sentinel_collision(data):
        return True
    if TP.TEMPLATE_SENTINEL in data:
        return True
    if WL.WIKILINK_SENTINEL in data:
        return True
    return False


def _phase4_wc_compress(data: bytes) -> bytes | None:
    """Phase 4 with wordcode pre-pass on the scaffold channel.

    Architecture: typed-artifact extraction (XML + wikilinks + templates)
    with byte-perfect format masks. Per-channel codec choice:
      - scaffold: wordcode pack (top-K word substitution) → lzma
      - dict-coded columns (template_names, template_keys,
        wikilink_targets): varint indices into shipped dictionary
      - atom channels: lzma
      - mask channels: lzma
    Everything is then concatenated into one big buffer and run through
    a single lzma pass.
    """
    scaffold0, atom_channels = XP.extract_xml_channels(data)
    scaffold1, wikilink_records = WL.extract_wikilinks(scaffold0)
    scaffold2, template_records = TP.extract_templates(scaffold1)

    rebuilt_scaffold1 = TP.reconstruct_scaffold(scaffold2, template_records)
    if rebuilt_scaffold1 != scaffold1:
        return None
    rebuilt_scaffold0 = WL.reconstruct_scaffold(rebuilt_scaffold1, wikilink_records)
    if rebuilt_scaffold0 != scaffold0:
        return None
    if XP.reconstruct(scaffold0, atom_channels) != data:
        return None

    # Apply wordcode pack to the scaffold channel.
    scaffold_packed = SC.pack(scaffold2)
    if SC.unpack(scaffold_packed) != scaffold2:
        # Wordcode roundtrip check; should never fail given construction.
        return None

    bodies: dict[str, bytes] = {"scaffold": scaffold_packed}
    for name in XP.CHANNEL_NAMES:
        bodies[name] = CC.serialize_atoms(atom_channels[name])

    t_names_dict, t_keys_dict, t_tuples, t_masks = (
        TP.serialize_records_dictcoded(template_records)
    )
    bodies["template_names_dict"] = t_names_dict
    bodies["template_keys_dict"] = t_keys_dict
    bodies["template_tuples"] = t_tuples
    bodies["template_masks"] = t_masks

    w_targets_dict, w_tuples, w_masks = WL.serialize_records_dictcoded(
        wikilink_records
    )
    bodies["wikilink_targets_dict"] = w_targets_dict
    bodies["wikilink_tuples"] = w_tuples
    bodies["wikilink_masks"] = w_masks

    return CC.build_archive(
        M.MODE_TYPED_PHASE4_WC,
        bodies,
        total_input_size=len(data),
        total_input_hash=M.hash_hex(data),
    )


def _phase1_wc_compress(data: bytes) -> bytes | None:
    """Phase 1 (XML extraction only) + wordcode-pack on scaffold.

    The scaffold here still contains intact {{templates}} and [[wikilinks]]
    so wordcode sees the full natural-language redundancy of the corpus,
    not just the XML-scaffolding fraction. This is where wordcode pays
    most. The cost: no semantic decomposition of templates/wikilinks
    (their canonical key=value structure is not exposed).
    """
    scaffold, atom_channels = XP.extract_xml_channels(data)
    if XP.reconstruct(scaffold, atom_channels) != data:
        return None
    scaffold_packed = SC.pack(scaffold)
    if SC.unpack(scaffold_packed) != scaffold:
        return None

    bodies: dict[str, bytes] = {"scaffold": scaffold_packed}
    for name in XP.CHANNEL_NAMES:
        bodies[name] = CC.serialize_atoms(atom_channels[name])
    # Phase-4 extraction channels: empty under Phase 1_WC.
    empty_t = TP.serialize_records_dictcoded([])
    bodies["template_names_dict"] = empty_t[0]
    bodies["template_keys_dict"] = empty_t[1]
    bodies["template_tuples"] = empty_t[2]
    bodies["template_masks"] = empty_t[3]
    empty_w = WL.serialize_records_dictcoded([])
    bodies["wikilink_targets_dict"] = empty_w[0]
    bodies["wikilink_tuples"] = empty_w[1]
    bodies["wikilink_masks"] = empty_w[2]
    return CC.build_archive(
        M.MODE_TYPED_PHASE1_WC,
        bodies,
        total_input_size=len(data),
        total_input_hash=M.hash_hex(data),
    )


def _phase1_compress(data: bytes) -> bytes:
    scaffold, atom_channels = XP.extract_xml_channels(data)
    if XP.reconstruct(scaffold, atom_channels) != data:
        raise RuntimeError("strict parse validation failed (phase 1)")
    bodies: dict[str, bytes] = {"scaffold": scaffold}
    for name in XP.CHANNEL_NAMES:
        bodies[name] = CC.serialize_atoms(atom_channels[name])
    # Phase-4 channels are present-but-empty under fallback so the
    # decoder's manifest walk is uniform.
    empty_t = TP.serialize_records_dictcoded([])
    bodies["template_names_dict"] = empty_t[0]
    bodies["template_keys_dict"] = empty_t[1]
    bodies["template_tuples"] = empty_t[2]
    bodies["template_masks"] = empty_t[3]
    empty_w = WL.serialize_records_dictcoded([])
    bodies["wikilink_targets_dict"] = empty_w[0]
    bodies["wikilink_tuples"] = empty_w[1]
    bodies["wikilink_masks"] = empty_w[2]
    return CC.build_archive(
        M.MODE_TYPED_PHASE1,
        bodies,
        total_input_size=len(data),
        total_input_hash=M.hash_hex(data),
    )


def _literal_fallback_compress(data: bytes) -> bytes:
    bodies: dict[str, bytes] = {"scaffold": data}
    for name in XP.CHANNEL_NAMES:
        bodies[name] = CC.serialize_atoms([])
    empty_t = TP.serialize_records_dictcoded([])
    bodies["template_names_dict"] = empty_t[0]
    bodies["template_keys_dict"] = empty_t[1]
    bodies["template_tuples"] = empty_t[2]
    bodies["template_masks"] = empty_t[3]
    empty_w = WL.serialize_records_dictcoded([])
    bodies["wikilink_targets_dict"] = empty_w[0]
    bodies["wikilink_tuples"] = empty_w[1]
    bodies["wikilink_masks"] = empty_w[2]
    return CC.build_archive(
        M.MODE_LITERAL_FALLBACK,
        bodies,
        total_input_size=len(data),
        total_input_hash=M.hash_hex(data),
    )


def compress(data: bytes) -> bytes:
    if _has_any_sentinel_collision(data):
        return _literal_fallback_compress(data)
    try:
        archive = _phase1_wc_compress(data)
        if archive is not None:
            return archive
    except Exception:
        pass
    try:
        return _phase1_compress(data)
    except Exception:
        return _literal_fallback_compress(data)


def decompress(arch: bytes) -> bytes:
    manifest, bodies = CC.open_archive(arch)
    mode = manifest["mode"]
    if mode == M.MODE_TYPED_PHASE1_WC:
        scaffold = SC.unpack(bodies["scaffold"])
        atom_channels = {
            name: CC.parse_atoms(bodies[name]) for name in XP.CHANNEL_NAMES
        }
        out = XP.reconstruct(scaffold, atom_channels)
    elif mode == M.MODE_TYPED_PHASE4_WC:
        scaffold2 = SC.unpack(bodies["scaffold"])
        template_records = TP.parse_records_dictcoded(
            bodies["template_names_dict"],
            bodies["template_keys_dict"],
            bodies["template_tuples"],
            bodies["template_masks"],
        )
        wikilink_records = WL.parse_records_dictcoded(
            bodies["wikilink_targets_dict"],
            bodies["wikilink_tuples"],
            bodies["wikilink_masks"],
        )
        scaffold1 = TP.reconstruct_scaffold(scaffold2, template_records)
        scaffold0 = WL.reconstruct_scaffold(scaffold1, wikilink_records)
        atom_channels = {
            name: CC.parse_atoms(bodies[name]) for name in XP.CHANNEL_NAMES
        }
        out = XP.reconstruct(scaffold0, atom_channels)
    elif mode == M.MODE_TYPED_PHASE1:
        scaffold = bodies["scaffold"]
        atom_channels = {
            name: CC.parse_atoms(bodies[name]) for name in XP.CHANNEL_NAMES
        }
        out = XP.reconstruct(scaffold, atom_channels)
    elif mode == M.MODE_LITERAL_FALLBACK:
        out = bodies["scaffold"]
    else:
        raise ValueError(f"unknown mode: {mode}")

    if len(out) != manifest["total_input_size"]:
        raise ValueError(
            f"size mismatch: got {len(out)} expected {manifest['total_input_size']}"
        )
    if M.hash_hex(out) != manifest["total_input_hash"]:
        raise ValueError("total input hash mismatch")
    return out
