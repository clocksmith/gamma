#!/usr/bin/env python3
"""Screen a static page-entity roster against the exact joint 10M trace.

The screen is intentionally optimistic.  Roster identities, per-page hit
counts, WRT surface variants, model data, and implementation are free.  It
charges only an enumerative hit-position rank and an enumerative ordering of
the hit lexemes.  A miss therefore rejects this static roster alphabet before
proposal materialization; it is not a constructive codec receipt.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Iterable

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import mobius2_tessera_self_annotation_graph as graph  # noqa: E402
import mobius2_tessera_typed_fiber_ceiling as tessera  # noqa: E402
from wrt_exact import parse_store  # noqa: E402


SCREEN_ID = "mobius2_page_entity_roster_enumerative_screen_v0"
GROSS_GATE_BYTES = 30_000
ROLE_SETS = {
    "prose_word": (graph.ROLE_IDS["PROSE_WORD"],),
    "link_target": (graph.ROLE_IDS["LINK_TARGET"],),
    "link_label": (graph.ROLE_IDS["LINK_LABEL"],),
    "prose_and_links": (
        graph.ROLE_IDS["PROSE_WORD"],
        graph.ROLE_IDS["LINK_TARGET"],
        graph.ROLE_IDS["LINK_LABEL"],
    ),
    "all_lexical_roles": (
        graph.ROLE_IDS["PROSE_WORD"],
        graph.ROLE_IDS["LINK_TARGET"],
        graph.ROLE_IDS["LINK_LABEL"],
        graph.ROLE_IDS["TEMPLATE_VALUE"],
        graph.ROLE_IDS["TABLE_CELL"],
        graph.ROLE_IDS["LIST_ITEM"],
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    return {
        "path": str(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256_file(resolved),
    }


def log2_choose(total: int, selected: int) -> float:
    if selected <= 0 or selected >= total:
        return 0.0
    return (
        math.lgamma(total + 1)
        - math.lgamma(selected + 1)
        - math.lgamma(total - selected + 1)
    ) / math.log(2.0)


def log2_multinomial(counts: Iterable[int]) -> float:
    values = tuple(int(value) for value in counts if value > 0)
    total = sum(values)
    if total <= 1:
        return 0.0
    return (
        math.lgamma(total + 1)
        - sum(math.lgamma(value + 1) for value in values)
    ) / math.log(2.0)


def page_roster(raw_page: bytes, lexeme_ids: dict[str, int]) -> set[int]:
    chunks: list[bytes] = []
    title_match = graph.TITLE_RE.search(raw_page)
    text_match = graph.TEXT_RE.search(raw_page)
    if title_match:
        chunks.append(title_match.group(1))
    text = text_match.group(1) if text_match else b""

    for match in graph.LINK_RE.finditer(text):
        chunks.extend(match.group(1).split(b"|", 1))
    for match in graph.TEMPLATE_RE.finditer(text):
        fields = match.group(1).split(b"|")
        if fields:
            chunks.append(fields[0])
        chunks.extend(
            field.split(b"=", 1)[0] for field in fields[1:] if b"=" in field
        )
    chunks.extend(match.group(1) for match in graph.HEADING_RE.finditer(text))

    return {
        lexeme_ids[word]
        for chunk in chunks
        for word in graph.words(chunk)
        if word in lexeme_ids
    }


def map_page_events(parsed: object, pages: list[object]) -> list[list[int]]:
    result: list[list[int]] = [[] for _ in pages]
    page_index = 0
    for event_index, event in enumerate(parsed.events):
        while page_index < len(pages) and event.start >= pages[page_index].wrt_end:
            page_index += 1
        if page_index >= len(pages):
            break
        page = pages[page_index]
        if page.wrt_start <= event.start and event.end <= page.wrt_end:
            result[page_index].append(event_index)
    return result


def score_role_set(
    role_set: tuple[int, ...],
    split: int,
    parsed: object,
    pages: list[object],
    page_events: list[list[int]],
    roles: np.ndarray,
    model: tessera.TesseraModel,
    joint_byte_qbits: np.ndarray,
) -> dict[str, object]:
    opportunities = 0
    hits = 0
    displaced_qbits = 0
    hit_position_bits = 0.0
    lexeme_order_bits = 0.0
    roster_entries = 0
    roster_pages = 0

    for page, indexes in zip(pages, page_events):
        if page.split != split:
            continue
        roster = page_roster(
            parsed.decoded[page.raw_start : page.raw_end], model.lexeme_ids
        )
        roster_entries += len(roster)
        roster_pages += 1
        page_opportunities = 0
        page_hits = 0
        page_lexemes: Counter[int] = Counter()
        for index in indexes:
            if int(roles[index]) not in role_set:
                continue
            event = parsed.events[index]
            values = model.event_values(event)
            if values is None:
                continue
            page_opportunities += 1
            lexeme_id = values[0]
            if lexeme_id not in roster:
                continue
            page_hits += 1
            page_lexemes[lexeme_id] += 1
            displaced_qbits += int(
                joint_byte_qbits[event.start : event.end].sum()
            )
        opportunities += page_opportunities
        hits += page_hits
        hit_position_bits += log2_choose(page_opportunities, page_hits)
        lexeme_order_bits += log2_multinomial(page_lexemes.values())

    optimistic_side_bits = hit_position_bits + lexeme_order_bits
    displaced_bytes = displaced_qbits / (tessera.QBITS * 8.0)
    optimistic_side_bytes = optimistic_side_bits / 8.0
    return {
        "supported_token_opportunities": opportunities,
        "roster_hits": hits,
        "hit_rate": 0.0 if opportunities == 0 else hits / opportunities,
        "roster_pages": roster_pages,
        "roster_entries": roster_entries,
        "mean_roster_entries": (
            0.0 if roster_pages == 0 else roster_entries / roster_pages
        ),
        "displaced_joint_qbits": displaced_qbits,
        "displaced_joint_bytes": displaced_bytes,
        "free_count_hit_position_bits": hit_position_bits,
        "free_count_lexeme_order_bits": lexeme_order_bits,
        "optimistic_side_bytes": optimistic_side_bytes,
        "optimistic_gain_bytes": displaced_bytes - optimistic_side_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--joint-p1",
        type=Path,
        default=ROOT
        / "results/janus_recurrent_quotient_joint_trace_recovery_q0_v1/joint_candidate.p1",
    )
    parser.add_argument(
        "--wrt-store",
        type=Path,
        default=ROOT
        / "results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin",
    )
    parser.add_argument(
        "--dictionary",
        type=Path,
        default=Path(
            "/home/x/enwiki9-nonproof/results/"
            "cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/"
            "clean-build-b/build/english.dic"
        ),
    )
    parser.add_argument(
        "--tessera-model",
        type=Path,
        default=ROOT
        / "results/mobius2_tessera_typed_fiber_ceiling_qh0_v1/model.tsf0.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / SCREEN_ID / "decision.json",
    )
    args = parser.parse_args()

    required = (args.joint_p1, args.wrt_store, args.dictionary, args.tessera_model)
    if not all(path.is_file() for path in required):
        raise SystemExit("missing joint trace, WRT store, dictionary, or TESSERA model")
    if args.output.exists():
        raise FileExistsError("refusing to overwrite an existing roster screen")

    parsed = parse_store(args.wrt_store, args.dictionary)
    pages = tessera.build_pages(parsed)
    roles, _ = tessera.event_metadata(parsed, pages)
    model = tessera.TesseraModel(args.tessera_model.read_bytes())
    page_events = map_page_events(parsed, pages)

    truth = np.unpackbits(
        np.frombuffer(parsed.stream, dtype=np.uint8), bitorder="big"
    )
    joint_p1 = tessera.read_p1(args.joint_p1, len(truth))
    zero, one = tessera.qbit_tables()
    joint_byte_qbits = tessera.byte_qbits(joint_p1, truth, zero, one)

    splits: dict[str, dict[str, object]] = {}
    for split, split_name in enumerate(tessera.SPLIT_NAMES):
        splits[split_name] = {
            name: score_role_set(
                role_set,
                split,
                parsed,
                pages,
                page_events,
                roles,
                model,
                joint_byte_qbits,
            )
            for name, role_set in ROLE_SETS.items()
        }

    aggregate: dict[str, dict[str, object]] = {}
    for name in ROLE_SETS:
        rows = [splits[split_name][name] for split_name in tessera.SPLIT_NAMES]
        displaced = sum(float(row["displaced_joint_bytes"]) for row in rows)
        side = sum(float(row["optimistic_side_bytes"]) for row in rows)
        aggregate[name] = {
            "displaced_joint_bytes": displaced,
            "optimistic_side_bytes": side,
            "optimistic_gain_bytes": displaced - side,
            "all_split_gains_positive": all(
                float(row["optimistic_gain_bytes"]) > 0.0 for row in rows
            ),
        }

    best_name, best = max(
        aggregate.items(), key=lambda item: (item[1]["optimistic_gain_bytes"], item[0])
    )
    gate_pass = (
        float(best["optimistic_gain_bytes"]) >= GROSS_GATE_BYTES
        and bool(best["all_split_gains_positive"])
    )
    result = {
        "schema": "gamma.mobius2_page_entity_roster_enumerative_screen.v0",
        "screen_id": SCREEN_ID,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PROMOTE_TO_EXACT_QH0" if gate_pass else "REJECT_BEFORE_PROPOSAL",
        "score_credit_bytes": 0,
        "population": {
            "raw_bytes": 10_000_000,
            "wrt_bytes": len(parsed.stream),
            "pages": len(pages),
        },
        "inputs": {
            "joint_p1": artifact(args.joint_p1),
            "wrt_store": artifact(args.wrt_store),
            "dictionary": artifact(args.dictionary),
            "tessera_model": artifact(args.tessera_model),
        },
        "contract": {
            "roster_relations": [
                "page_title",
                "link_target",
                "link_label",
                "template_name",
                "template_key",
                "section_heading",
            ],
            "charged": [
                "enumerative supported-token hit positions",
                "enumerative hit-lexeme order given exact per-page counts",
            ],
            "supplied_free": [
                "roster identities",
                "per-page hit and lexeme counts",
                "morphology and exact WRT surface variants",
                "model and implementation",
                "finite-coder framing and termination",
            ],
            "role_sets": {
                name: [graph.ROLE_NAMES[role] for role in role_set]
                for name, role_set in ROLE_SETS.items()
            },
        },
        "splits": splits,
        "aggregate": aggregate,
        "gate": {
            "gross_required_bytes": GROSS_GATE_BYTES,
            "best_role_set": best_name,
            "best_optimistic_gain_bytes": best["optimistic_gain_bytes"],
            "best_all_split_gains_positive": best["all_split_gains_positive"],
            "pass": gate_pass,
        },
        "decision": {
            "proposal_materialization_authorized": gate_pass,
            "forecast_bytes": 109_389_323,
            "verified_full_1g_score_bytes": None,
            "next_action": (
                "freeze an exact finite roster side coder"
                if gate_pass
                else "retire the static free-count page-entity roster alphabet"
            ),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
