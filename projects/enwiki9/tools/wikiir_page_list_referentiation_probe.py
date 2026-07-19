#!/usr/bin/env python3
"""Measure causal page-list referentiation headroom for WikiIR-MDL.

For each complete page, the encoder may choose an earlier page as an explicit
reference and encode the ordered link-target list using COPY intervals plus
literal runs.  This discovery probe charges page-reference, opcode, position,
length, and literal costs.  A deterministic random-prior control distinguishes
actual list overlap from the benefit of merely having a reference channel.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import difflib
import hashlib
import json
from pathlib import Path
from typing import Any


MAX_TARGET_BYTES = 1024


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def varint_bytes(value: int) -> int:
    if value < 0:
        raise ValueError("varint value must be nonnegative")
    width = 1
    while value >= 128:
        value >>= 7
        width += 1
    return width


@dataclass(frozen=True)
class Page:
    ordinal: int
    title: bytes
    targets: tuple[bytes, ...]


def scan_targets(data: bytes) -> tuple[bytes, ...]:
    targets: list[bytes] = []
    position = 0
    while position + 3 < len(data):
        opening = data.find(b"[[", position)
        if opening < 0:
            break
        closing = data.find(b"]]", opening + 2)
        if closing < 0:
            break
        start = opening + 2
        separator = data.find(b"|", start, closing)
        end = separator if separator >= 0 else closing
        target = data[start:end]
        if (
            target
            and len(target) <= MAX_TARGET_BYTES
            and b"\n" not in target
            and b"\r" not in target
        ):
            targets.append(target)
        position = closing + 2
    return tuple(targets)


def scan_pages(raw: bytes) -> list[Page]:
    pages: list[Page] = []
    position = 0
    while True:
        start = raw.find(b"<page>", position)
        if start < 0:
            break
        end = raw.find(b"</page>", start + 6)
        if end < 0:
            break
        end += len(b"</page>")
        page = raw[start:end]
        title_start = page.find(b"<title>")
        title_end = page.find(b"</title>", title_start + 7)
        title = (
            page[title_start + 7 : title_end]
            if title_start >= 0 and title_end >= 0
            else b""
        )
        pages.append(Page(len(pages), title, scan_targets(page)))
        position = end
    return pages


def matching_blocks(prior: tuple[bytes, ...], current: tuple[bytes, ...]) -> list[tuple[int, int, int]]:
    matcher = difflib.SequenceMatcher(a=prior, b=current, autojunk=False)
    return [
        (block.a, block.b, block.size)
        for block in matcher.get_matching_blocks()
        if block.size
    ]


def delta_cost(prior: Page, current: Page) -> dict[str, int]:
    blocks = matching_blocks(prior.targets, current.targets)
    copied = [False] * len(current.targets)
    copy_bytes = 0
    copy_cost = 0
    for source, destination, length in blocks:
        copy_bytes += sum(len(target) for target in current.targets[destination : destination + length])
        copy_cost += 1 + varint_bytes(source) + varint_bytes(length)
        copied[destination : destination + length] = [True] * length
    literal_bytes = 0
    literal_cost = 0
    index = 0
    while index < len(current.targets):
        if copied[index]:
            index += 1
            continue
        end = index
        while end < len(current.targets) and not copied[end]:
            literal_bytes += len(current.targets[end])
            end += 1
        literal_cost += 1 + varint_bytes(end - index)
        index = end
    baseline = 1 + sum(len(target) for target in current.targets)
    encoded = 1 + varint_bytes(current.ordinal - prior.ordinal) + copy_cost + literal_cost + literal_bytes
    return {
        "baseline_target_bytes": baseline,
        "delta_target_bytes": encoded,
        "net_saved_bytes": baseline - encoded,
        "copied_target_bytes": copy_bytes,
        "copy_blocks": len(blocks),
        "literal_target_bytes": literal_bytes,
    }


def candidate_prior_ids(page: Page, postings: dict[bytes, list[int]], limit: int) -> list[int]:
    overlap: Counter[int] = Counter()
    for target in set(page.targets):
        overlap.update(postings.get(target, ()))
    return [
        ordinal
        for ordinal, _count in sorted(
            overlap.items(), key=lambda item: (-item[1], -item[0])
        )[:limit]
    ]


def random_prior_id(ordinal: int) -> int:
    return ((ordinal * 1_103_515_245 + 12_345) & 0x7FFFFFFF) % ordinal


def run(raw: bytes, candidate_limit: int) -> dict[str, Any]:
    pages = scan_pages(raw)
    postings: dict[bytes, list[int]] = defaultdict(list)
    best_total = 0
    random_total = 0
    copied_total = 0
    selected_pages = 0
    candidate_pages = 0
    rows: list[dict[str, Any]] = []
    for page in pages:
        if page.ordinal == 0 or not page.targets:
            for target in set(page.targets):
                postings[target].append(page.ordinal)
            continue
        candidates = candidate_prior_ids(page, postings, candidate_limit)
        if candidates:
            candidate_pages += 1
            choices = [
                (delta_cost(pages[prior], page), prior) for prior in candidates
            ]
            best, prior = max(
                choices, key=lambda item: (item[0]["net_saved_bytes"], item[1])
            )
            if best["net_saved_bytes"] > 0:
                selected_pages += 1
                best_total += best["net_saved_bytes"]
                copied_total += best["copied_target_bytes"]
            rows.append(
                {
                    "page_ordinal": page.ordinal,
                    "title": page.title.decode("utf-8", "replace")[:120],
                    "targets": len(page.targets),
                    "selected_prior": prior,
                    **best,
                }
            )
        random = delta_cost(pages[random_prior_id(page.ordinal)], page)
        if random["net_saved_bytes"] > 0:
            random_total += random["net_saved_bytes"]
        for target in set(page.targets):
            postings[target].append(page.ordinal)
    rows.sort(key=lambda row: int(row["net_saved_bytes"]), reverse=True)
    return {
        "schema": "wikiir_page_list_referentiation_probe_v1",
        "evidence_level": "nonconstructive_reversible_representation_headroom",
        "claim_boundary": (
            "Link-target-list MDL estimate only. It does not yet emit a full "
            "raw-byte IR, count the shared skeleton/position stream, or prove "
            "target-backend compression."
        ),
        "pages": len(pages),
        "pages_with_reference_candidates": candidate_pages,
        "pages_with_positive_delta": selected_pages,
        "best_prior_net_target_bytes": best_total,
        "random_prior_net_target_bytes": random_total,
        "targeted_delta_over_random_bytes": best_total - random_total,
        "copied_target_bytes": copied_total,
        "top_pages": rows[:32],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe causal WikiIR page-list referentiation headroom."
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--scope-bytes", type=int, required=True)
    parser.add_argument("--candidate-limit", type=int, default=16)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.input.read_bytes()[: args.scope_bytes]
    if len(raw) != args.scope_bytes:
        raise ValueError("input is shorter than declared scope")
    payload = run(raw, args.candidate_limit)
    payload["scope_bytes"] = len(raw)
    payload["input_sha256"] = sha256_bytes(raw)
    payload["candidate_limit"] = args.candidate_limit
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
