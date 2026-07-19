#!/usr/bin/env python3
"""Measure causal same-template value reuse for a WikiIR prototype delta.

This is a discovery-only MDL probe.  A template value may COPY the same field
from an earlier complete-page occurrence with an identical ordered template
skeleton; otherwise it is emitted as ADD.  The reference and every command
cost are charged.  A deterministic random earlier occurrence with the same
skeleton is the matched control, so template popularity alone cannot look like
prototype reuse.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any


MAX_CANDIDATES = 16


def _varint_bytes(value: int) -> int:
    if value < 0:
        raise ValueError("varint value must be nonnegative")
    width = 1
    while value >= 128:
        width += 1
        value >>= 7
    return width


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_template_module() -> ModuleType:
    program = (
        Path(__file__).resolve().parents[1]
        / "programs"
        / "wikiir_template_grammar_v1"
        / "program.py"
    )
    spec = importlib.util.spec_from_file_location("wikiir_template_grammar_probe", program)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load template parser: {program}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@dataclass(frozen=True)
class Occurrence:
    ordinal: int
    page_ordinal: int
    title: bytes
    signature: tuple[bytes, ...]
    holes: tuple[bytes, ...]


def _pages(raw: bytes) -> tuple[tuple[bytes, bytes], ...]:
    """Yield only complete pages, so every reference precedes its decoder use."""

    rows: list[tuple[bytes, bytes]] = []
    position = 0
    while True:
        start = raw.find(b"<page>", position)
        if start < 0:
            return tuple(rows)
        end = raw.find(b"</page>", start + len(b"<page>"))
        if end < 0:
            return tuple(rows)
        end += len(b"</page>")
        page = raw[start:end]
        title_start = page.find(b"<title>")
        title_end = page.find(b"</title>", title_start + len(b"<title>"))
        title = (
            page[title_start + len(b"<title>") : title_end]
            if title_start >= 0 and title_end >= 0
            else b""
        )
        rows.append((page, title))
        position = end


def _cost(current: Occurrence, prior: Occurrence) -> dict[str, int]:
    if current.signature != prior.signature:
        raise ValueError("template signatures differ")
    baseline = sum(_varint_bytes(len(value)) + len(value) for value in current.holes)
    reference = 1 + _varint_bytes(current.ordinal - prior.ordinal)
    encoded = reference
    copied = 0
    copied_bytes = 0
    literal_bytes = 0
    for current_value, prior_value in zip(current.holes, prior.holes):
        if current_value == prior_value:
            encoded += 1  # COPY same field index; position is implicit.
            copied += 1
            copied_bytes += len(current_value)
        else:
            encoded += 1 + _varint_bytes(len(current_value)) + len(current_value)
            literal_bytes += len(current_value)
    return {
        "baseline_value_bytes": baseline,
        "delta_value_bytes": encoded,
        "net_saved_bytes": baseline - encoded,
        "copied_fields": copied,
        "copied_value_bytes": copied_bytes,
        "literal_value_bytes": literal_bytes,
    }


def _random_prior(occurrences: list[Occurrence], current: Occurrence) -> Occurrence:
    index = ((current.ordinal * 1_103_515_245 + 12_345) & 0x7FFFFFFF) % len(occurrences)
    return occurrences[index]


def run(raw: bytes, candidate_limit: int = MAX_CANDIDATES) -> dict[str, Any]:
    if candidate_limit < 1:
        raise ValueError("candidate_limit must be positive")
    parser = _load_template_module()
    by_signature: dict[tuple[bytes, ...], list[Occurrence]] = defaultdict(list)
    ordinal = 0
    total = 0
    random_total = 0
    copied_fields = 0
    copied_bytes = 0
    candidate_occurrences = 0
    positive_occurrences = 0
    rows: list[dict[str, Any]] = []

    for page_ordinal, (page, title) in enumerate(_pages(raw)):
        current_page: list[Occurrence] = []
        for _start, _end, signature, holes in parser._scan(page):
            current = Occurrence(ordinal, page_ordinal, title, signature, holes)
            ordinal += 1
            previous = by_signature[signature]
            if previous:
                candidate_occurrences += 1
                candidates = previous[-candidate_limit:]
                choices = [(_cost(current, prior), prior) for prior in candidates]
                best, prior = max(
                    choices,
                    key=lambda row: (row[0]["net_saved_bytes"], row[1].ordinal),
                )
                if best["net_saved_bytes"] > 0:
                    total += best["net_saved_bytes"]
                    copied_fields += best["copied_fields"]
                    copied_bytes += best["copied_value_bytes"]
                    positive_occurrences += 1
                random = _cost(current, _random_prior(previous, current))
                if random["net_saved_bytes"] > 0:
                    random_total += random["net_saved_bytes"]
                rows.append(
                    {
                        "page_ordinal": page_ordinal,
                        "title": title.decode("utf-8", "replace")[:120],
                        "prior_page_ordinal": prior.page_ordinal,
                        "template_fields": len(holes),
                        **best,
                    }
                )
            current_page.append(current)
        # A referenced page must already be complete.  Do not let repeated
        # templates earlier in the current page masquerade as page-prototype
        # evidence; append this page only after all of its occurrences score.
        for current in current_page:
            by_signature[current.signature].append(current)
    rows.sort(key=lambda row: int(row["net_saved_bytes"]), reverse=True)
    return {
        "schema": "wikiir_template_value_referentiation_probe_v1",
        "evidence_level": "nonconstructive_reversible_representation_headroom",
        "claim_boundary": (
            "Template-value MDL estimate only. It does not yet emit an exact "
            "full raw-byte IR, charge page/template surface skeleton placement, "
            "or prove target-backend compression."
        ),
        "pages": len(_pages(raw)),
        "template_occurrences": ordinal,
        "occurrences_with_same_skeleton_history": candidate_occurrences,
        "positive_delta_occurrences": positive_occurrences,
        "best_prior_net_value_bytes": total,
        "random_same_skeleton_net_value_bytes": random_total,
        "targeted_delta_over_random_bytes": total - random_total,
        "copied_fields": copied_fields,
        "copied_value_bytes": copied_bytes,
        "top_occurrences": rows[:32],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--candidate-limit", type=int, default=MAX_CANDIDATES)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()[: args.scope_bytes]
    if len(raw) != args.scope_bytes:
        raise ValueError("input is shorter than declared scope")
    result = run(raw, args.candidate_limit)
    result["scope_bytes"] = len(raw)
    result["input_sha256"] = _sha256(raw)
    result["candidate_limit"] = args.candidate_limit
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
