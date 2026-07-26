#!/usr/bin/env python3
"""Screen reversible surface-symmetry factorizations with causal MDL codes.

This is a zero-credit feasibility oracle over raw spans corresponding to
WRT-relevant realizations. It compares a causal exact-surface code with a
causal representative-plus-action code. It does not claim endpoint archive
gain and does not authorize a native transform by itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path


CASE_RE = re.compile(rb"[A-Za-z]{2,}")
APOSTROPHE_RE = re.compile(
    rb"[A-Za-z]+(?:'|&apos;|&#39;|&#x27;|\xe2\x80\x99)[A-Za-z]+"
)
HYPHEN_RE = re.compile(rb"[A-Za-z]{2,}(?:[- ][A-Za-z]{2,})+")
NUMERIC_RE = re.compile(rb"[0-9][0-9,._:/-]+[0-9]")
XML_QUOTE_RE = re.compile(
    rb"[A-Za-z_:][-A-Za-z0-9_:.]*=(?:\"[^\"<>]{0,96}\"|'[^'<>]{0,96}')"
)

SPELLING_CLUSTERS = (
    ("color", "colour"),
    ("center", "centre"),
    ("theater", "theatre"),
    ("organization", "organisation"),
    ("organize", "organise"),
    ("analyze", "analyse"),
    ("behavior", "behaviour"),
    ("defense", "defence"),
    ("traveled", "travelled"),
    ("canceled", "cancelled"),
    ("catalog", "catalogue"),
    ("program", "programme"),
    ("aluminum", "aluminium"),
    ("gray", "grey"),
    ("maneuver", "manoeuvre"),
    ("encyclopedia", "encyclopaedia"),
    ("sulfur", "sulphur"),
    ("meter", "metre"),
    ("liter", "litre"),
    ("artifact", "artefact"),
)
SPELLING_MAP = {
    value.encode(): (cluster[0].encode(), index, len(cluster))
    for cluster in SPELLING_CLUSTERS
    for index, value in enumerate(cluster)
}


def gamma_bits(value: int) -> int:
    assert value >= 1
    width = value.bit_length()
    return 2 * width - 1


class StringCode:
    """Dynamic escape code: seen symbol or escaped length-plus-literal."""

    def __init__(self) -> None:
        self.counts: dict[tuple[str, int], dict[bytes, int]] = defaultdict(dict)
        self.totals: dict[tuple[str, int], int] = defaultdict(int)

    def encode(self, context: tuple[str, int], symbol: bytes) -> float:
        counts = self.counts[context]
        total = self.totals[context]
        count = counts.get(symbol, 0)
        if count:
            bits = math.log2((total + 1) / count)
        else:
            bits = math.log2(total + 1) + gamma_bits(len(symbol) + 1) + 8 * len(symbol)
        counts[symbol] = count + 1
        self.totals[context] = total + 1
        return bits


class KnownAlphabetCode:
    """Krichevsky-Trofimov code over a fixed, source-defined alphabet."""

    def __init__(self) -> None:
        self.counts: dict[tuple[str, int, int, int], list[int]] = {}

    def encode(
        self,
        context: tuple[str, int],
        position: int,
        symbol: int,
        alphabet: int,
    ) -> float:
        key = (context[0], context[1], min(position, 15), alphabet)
        counts = self.counts.setdefault(key, [0] * alphabet)
        total = sum(counts)
        bits = -math.log2((counts[symbol] + 0.5) / (total + 0.5 * alphabet))
        counts[symbol] += 1
        return bits


def byte_context(data: bytes, start: int) -> int:
    if start == 0:
        return 0
    value = data[start - 1]
    if value == ord("<"):
        return 1
    if value in b" \t\r\n":
        return 2
    if 65 <= value <= 90 or 97 <= value <= 122:
        return 3
    if 48 <= value <= 57:
        return 4
    return 5


def case_factor(surface: bytes) -> tuple[bytes, list[tuple[int, int]], int]:
    representative = surface.lower()
    if surface == representative:
        return representative, [(0, 4)], 0
    if surface == surface.upper():
        return representative, [(1, 4)], 0
    if surface[:1].isupper() and surface[1:] == surface[1:].lower():
        return representative, [(2, 4)], 0
    mask = 0
    for index, value in enumerate(surface):
        if 65 <= value <= 90:
            mask |= 1 << index
    return representative, [(3, 4)], len(surface)


def case_inverse(representative: bytes, action: list[tuple[int, int]], residual: int, surface: bytes) -> bytes:
    kind = action[0][0]
    if kind == 0:
        return representative
    if kind == 1:
        return representative.upper()
    if kind == 2:
        return representative[:1].upper() + representative[1:]
    return bytes(
        value - 32 if (residual >> index) & 1 else value
        for index, value in enumerate(representative)
    )


def factor_case(surface: bytes):
    representative, action, residual_bits = case_factor(surface)
    mask = 0
    if action[0][0] == 3:
        for index, value in enumerate(surface):
            if 65 <= value <= 90:
                mask |= 1 << index
    assert case_inverse(representative, action, mask, surface) == surface
    return representative, action, float(residual_bits)


APOSTROPHES = (b"'", b"&apos;", b"&#39;", b"&#x27;", b"\xe2\x80\x99")


def factor_apostrophe(surface: bytes):
    for index, spelling in enumerate(APOSTROPHES):
        position = surface.find(spelling)
        if position >= 0:
            representative = surface[:position] + b"'" + surface[position + len(spelling) :]
            rebuilt = representative.replace(b"'", spelling, 1)
            assert rebuilt == surface
            return representative, [(index, len(APOSTROPHES))], 0.0
    raise AssertionError("apostrophe matcher produced no spelling")


def factor_hyphen(surface: bytes):
    pieces = re.split(rb"([- ])", surface)
    representative = b"-".join(pieces[::2])
    actions = [(0 if value == b"-" else 1, 2) for value in pieces[1::2]]
    rebuilt = bytearray(pieces[0])
    for action, piece in zip(actions, pieces[2::2]):
        rebuilt.extend(b"-" if action[0] == 0 else b" ")
        rebuilt.extend(piece)
    assert bytes(rebuilt) == surface
    return representative, actions, 0.0


def factor_numeric(surface: bytes):
    representative = bytes(ord("0") if 48 <= value <= 57 else value for value in surface)
    actions = [(value - 48, 10) for value in surface if 48 <= value <= 57]
    digits = iter(action[0] for action in actions)
    rebuilt = bytes(next(digits) + 48 if value == ord("0") else value for value in representative)
    assert rebuilt == surface
    return representative, actions, 0.0


def factor_xml_quote(surface: bytes):
    equal = surface.index(b"=")
    quote = surface[equal + 1]
    representative = surface[: equal + 1] + b'"' + surface[equal + 2 : -1] + b'"'
    action = 0 if quote == ord('"') else 1
    rebuilt_quote = b'"' if action == 0 else b"'"
    rebuilt = surface[: equal + 1] + rebuilt_quote + surface[equal + 2 : -1] + rebuilt_quote
    assert rebuilt == surface
    return representative, [(action, 2)], 0.0


def spelling_matches(data: bytes):
    for match in CASE_RE.finditer(data):
        surface = match.group()
        lowered = surface.lower()
        if lowered in SPELLING_MAP:
            yield match.start(), match.end(), surface


def factor_spelling(surface: bytes):
    canonical, variant, alphabet = SPELLING_MAP[surface.lower()]
    case_rep, case_action, residual_bits = case_factor(surface)
    del case_rep
    representative = canonical
    actions = [(variant, alphabet)] + case_action
    mask = 0
    if case_action[0][0] == 3:
        for index, value in enumerate(surface):
            if 65 <= value <= 90:
                mask |= 1 << index
    selected = SPELLING_CLUSTERS[[cluster[0] for cluster in SPELLING_CLUSTERS].index(canonical.decode())][variant].encode()
    rebuilt = case_inverse(selected, case_action, mask, surface)
    assert rebuilt == surface
    return representative, actions, float(residual_bits)


FAMILIES = {
    "case": (CASE_RE.finditer, factor_case),
    "apostrophe": (APOSTROPHE_RE.finditer, factor_apostrophe),
    "hyphen_space": (HYPHEN_RE.finditer, factor_hyphen),
    "numeric_format": (NUMERIC_RE.finditer, factor_numeric),
    "xml_quote": (XML_QUOTE_RE.finditer, factor_xml_quote),
    "common_spelling": (spelling_matches, factor_spelling),
}


def iter_matches(data: bytes, matcher):
    for item in matcher(data):
        if hasattr(item, "group"):
            yield item.start(), item.end(), item.group()
        else:
            yield item


def screen_family(data: bytes, family: str, matcher, factor) -> dict:
    baseline = StringCode()
    representatives = StringCode()
    actions = KnownAlphabetCode()
    split_bits = {"train": [0.0, 0.0], "development": [0.0, 0.0], "holdout": [0.0, 0.0]}
    events = 0
    transformed_bytes = 0
    for start, end, surface in iter_matches(data, matcher):
        context = (family, byte_context(data, start))
        representative, action_symbols, residual_bits = factor(surface)
        base_bits = baseline.encode(context, surface)
        factored_bits = representatives.encode(context, representative) + residual_bits
        for position, (symbol, alphabet) in enumerate(action_symbols):
            factored_bits += actions.encode(context, position, symbol, alphabet)
        split = "train" if start < 0.6 * len(data) else "development" if start < 0.8 * len(data) else "holdout"
        split_bits[split][0] += base_bits
        split_bits[split][1] += factored_bits
        events += 1
        transformed_bytes += end - start

    splits = {}
    for name, (base_bits, factored_bits) in split_bits.items():
        gain_bytes = (base_bits - factored_bits) / 8.0
        splits[name] = {
            "baseline_ideal_bits": base_bits,
            "factored_ideal_bits": factored_bits,
            "gain_bytes": gain_bytes,
        }
    holdout_bytes = max(1, len(data) - int(0.8 * len(data)))
    holdout_rate = splits["holdout"]["gain_bytes"] * 1_000_000 / holdout_bytes
    return {
        "events": events,
        "covered_raw_bytes": transformed_bytes,
        "coverage_fraction": transformed_bytes / len(data),
        "splits": splits,
        "holdout_gain_bytes_per_m": holdout_rate,
        "development_positive": splits["development"]["gain_bytes"] > 0,
        "holdout_positive": splits["holdout"]["gain_bytes"] > 0,
    }


def parse_scope(value: str) -> tuple[str, Path]:
    name, path = value.split(":", 1)
    return name, Path(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", action="append", required=True, help="NAME:RAW_PATH")
    parser.add_argument("--output", required=True)
    parser.add_argument("--required-holdout-bytes-per-m", type=float, default=1500.0)
    args = parser.parse_args()

    scopes = {}
    for value in args.scope:
        name, path = parse_scope(value)
        data = path.read_bytes()
        scopes[name] = {
            "input": {
                "path": str(path),
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            },
            "families": {
                family: screen_family(data, family, matcher, factor)
                for family, (matcher, factor) in FAMILIES.items()
            },
        }

    passing_families = []
    for family in FAMILIES:
        if all(
            scope["families"][family]["development_positive"]
            and scope["families"][family]["holdout_positive"]
            and scope["families"][family]["holdout_gain_bytes_per_m"]
            >= args.required_holdout_bytes_per_m
            for scope in scopes.values()
        ):
            passing_families.append(family)

    source_bytes = sum(sum(map(len, cluster)) for cluster in SPELLING_CLUSTERS)
    receipt = {
        "schema": "wrt_symmetry_orbit_oracle_v1",
        "evidence_level": "zero_credit_causal_mdl_feasibility_oracle",
        "claim_boundary": (
            "Raw-span causal MDL bound only. No endpoint probabilities, arithmetic archive, "
            "WRT event integration, source package, runtime, or score credit is claimed."
        ),
        "required_holdout_bytes_per_m_each_scope": args.required_holdout_bytes_per_m,
        "hardcoded_spelling_payload_bytes_uncompressed": source_bytes,
        "scopes": scopes,
        "passing_families": passing_families,
        "decision": "authorize_exact_wrt_shadow" if passing_families else "retire_symmetry_orbits_v1",
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "decision": receipt["decision"],
                "passing_families": passing_families,
                "holdout_bytes_per_m": {
                    scope_name: {
                        family: details["holdout_gain_bytes_per_m"]
                        for family, details in scope["families"].items()
                    }
                    for scope_name, scope in scopes.items()
                },
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
