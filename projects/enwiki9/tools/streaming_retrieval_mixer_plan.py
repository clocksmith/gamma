#!/usr/bin/env python3
"""Generate the lock-safe SRSTC / Streaming Retrieval Mixer plan.

This tool does not run a compressor. It pins the primary novel streaming
self-referential retrieval lane to an explicit algorithm, receipt contract, and
promotion gate so it can be implemented and audited beside the active cmix21
scorer and the backup structural lanes.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import textwrap
from collections import Counter
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT_MD = ROOT / "docs" / "streaming_retrieval_mixer.md"
RESULTS_DIR = ROOT / "results" / "streaming_retrieval_shadow"
AUDIT_JSON = ROOT / "docs" / "streaming_retrieval_receipt_audit.json"

CURRENT_WINNER = 110_793_128
TARGET_SCORE = 109_500_000
BEST_FORECAST = 110_181_114


def fmt_int(value: int) -> str:
    return f"{value:,}"


def as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_receipts() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if RESULTS_DIR.exists():
        for path in sorted(RESULTS_DIR.glob("*.json")):
            try:
                data = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if data.get("receipt_type") != "streaming_retrieval_shadow":
                continue
            rows.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "verdict": str(data.get("verdict") or "incomplete"),
                    "feature_source": str(data.get("feature_source") or "unknown"),
                    "alignment_warning": bool(
                        isinstance(data.get("trace_data_alignment"), dict)
                        and data["trace_data_alignment"].get("warning")
                    ),
                    "encoded_rows": data.get("encoded_rows"),
                    "shadow_saved_bytes": as_float(data.get("shadow_saved_bytes")),
                    "heldout_shadow_saved_bytes": as_float(
                        data.get("heldout_shadow_saved_bytes")
                    ),
                    "net_saved_bytes": as_float(data.get("net_saved_bytes")),
                }
            )
    verdicts = Counter(row["verdict"] for row in rows)
    feature_sources = Counter(row["feature_source"] for row in rows)
    alignment_warning_count = sum(1 for row in rows if row["alignment_warning"])
    heldout = [row for row in rows if row["heldout_shadow_saved_bytes"] is not None]
    best_heldout = max(
        heldout,
        key=lambda row: row["heldout_shadow_saved_bytes"],
        default=None,
    )
    best_net = max(
        [row for row in rows if row["net_saved_bytes"] is not None],
        key=lambda row: row["net_saved_bytes"],
        default=None,
    )
    return {
        "rows": rows,
        "verdicts": dict(sorted(verdicts.items())),
        "feature_sources": dict(sorted(feature_sources.items())),
        "alignment_warning_count": alignment_warning_count,
        "heldout_count": len(heldout),
        "best_heldout": best_heldout,
        "best_net": best_net,
    }


def load_audit() -> dict[str, Any] | None:
    try:
        payload = json.loads(AUDIT_JSON.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def fmt_gap(value: Any) -> str:
    number = as_float(value)
    if number is None:
        return "n/a"
    if number < 0:
        return f"clears by {fmt_int(int(abs(number)))}"
    return fmt_int(int(number))


def evidence_section() -> str:
    evidence = load_receipts()
    rows = evidence["rows"]
    if not rows:
        return textwrap.dedent(
            """\
            ## Current Cached Evidence

            No `streaming_retrieval_shadow` receipt is present yet. The next
            concrete action is to run `tools/streaming_retrieval_shadow.py` on a
            cached residual TSV with true `bit` and `p1` fields.
            """
        ).strip()

    verdict_text = ", ".join(
        f"`{name}`: `{count}`" for name, count in evidence["verdicts"].items()
    )
    source_text = ", ".join(
        f"`{name}`: `{count}`" for name, count in evidence["feature_sources"].items()
    )
    best_heldout = evidence["best_heldout"]
    best_net = evidence["best_net"]
    audit = load_audit()
    if isinstance(audit, dict):
        audit_best = audit.get("best_net_receipt")
        if isinstance(audit_best, dict):
            audit_best_row = {
                "path": audit_best.get("path"),
                "heldout_shadow_saved_bytes": audit_best.get("heldout_shadow_saved_bytes"),
                "net_saved_bytes": audit_best.get("net_saved_bytes"),
            }
            if audit_best_row["heldout_shadow_saved_bytes"] is not None:
                best_heldout = audit_best_row
            if audit_best_row["net_saved_bytes"] is not None:
                best_net = audit_best_row
    best_heldout_line = (
        f"- Best held-out saved bytes: `{best_heldout['heldout_shadow_saved_bytes']}` "
        f"from `{best_heldout['path']}`."
        if best_heldout
        else "- Best held-out saved bytes: `n/a`."
    )
    best_net_line = (
        f"- Best net saved bytes after code/table estimate: `{best_net['net_saved_bytes']}` "
        f"from `{best_net['path']}`."
        if best_net
        else "- Best net saved bytes after code/table estimate: `n/a`."
    )
    best_heldout_value = (
        best_heldout["heldout_shadow_saved_bytes"]
        if best_heldout and best_heldout["heldout_shadow_saved_bytes"] is not None
        else None
    )
    best_net_value = (
        best_net["net_saved_bytes"]
        if best_net and best_net["net_saved_bytes"] is not None
        else None
    )
    if best_net_value is not None and best_net_value > 0:
        interpretation = (
            "Current interpretation: at least one receipt clears the counted "
            "code/table estimate in shadow. That is still not a compressor "
            "claim; the next gate is block-regression audit and packaging the "
            "smallest deterministic paying piece."
        )
    elif best_heldout_value is not None and best_heldout_value > 0:
        interpretation = (
            "Current interpretation: raw byte-aligned SRSTC has a positive "
            "held-out same-coder signal, but the best receipt is still below "
            "the counted code/table estimate. Keep the lane active, scale and "
            "mutate the retrieval key/probability model, and do not promote it "
            "into a compressor package yet."
        )
    else:
        interpretation = (
            "Current interpretation: the tested deterministic sketch-retrieval "
            "coupling is flat or negative. Keep the SRSTC lane, but change the "
            "retrieval key/probability model before promoting anything."
        )
    alignment_note = (
        "Cached trace/data alignment warnings remain only on receipts that "
        "compare raw data bytes to cached `bit` rows; raw byte-aligned "
        "`raw_data` receipts avoid that mismatch."
        if evidence["alignment_warning_count"]
        else "No trace/data alignment warning is present in the current receipts."
    )
    audit_note = ""
    if audit is not None:
        best = audit.get("best_net_receipt")
        blockers = []
        if isinstance(best, dict):
            raw_blockers = best.get("promotion_blockers")
            if isinstance(raw_blockers, list):
                blockers = [str(item) for item in raw_blockers]
        selection = audit.get("objective_selection")
        selection_note = ""
        if isinstance(selection, dict):
            target_closing = selection.get("best_target_closing_receipt")
            ready = selection.get("best_promotion_ready_receipt")
            if isinstance(target_closing, dict) or isinstance(ready, dict):
                target_lines = []
                if isinstance(target_closing, dict):
                    target_lines.extend(
                        [
                            f"- Best target-closing receipt: `{target_closing.get('path')}`",
                            f"- Target-closing net bytes: `{target_closing.get('net_saved_bytes')}`",
                            f"- Forecast gap after target-closing receipt: `{fmt_gap(target_closing.get('forecast_gap_remaining_bytes'))}`",
                            f"- Target-closing blockers: `{', '.join(target_closing.get('promotion_blockers') or ['none'])}`",
                        ]
                    )
                if isinstance(ready, dict):
                    target_lines.extend(
                        [
                            f"- Best promotion-ready fallback: `{ready.get('path')}`",
                            f"- Ready fallback net bytes: `{ready.get('net_saved_bytes')}`",
                            f"- Forecast gap after ready fallback: `{fmt_gap(ready.get('forecast_gap_remaining_bytes'))}`",
                        ]
                    )
                selection_note = "\n".join(
                    [
                        "",
                        "Objective selector:",
                        "",
                        f"- Recommended action: `{selection.get('recommended_action', 'unknown')}`",
                        f"- Reason: `{selection.get('action_reason', 'unknown')}`",
                        *target_lines,
                    ]
                )
        audit_note = textwrap.dedent(
            f"""\

            Receipt audit:

            - Positive net receipts: `{audit.get('positive_net_receipts', 'n/a')}`
            - Promotion-ready shadow receipts: `{audit.get('promotion_ready_shadow_receipts', 'n/a')}`
            - Best receipt promotion blockers: `{', '.join(blockers) if blockers else 'none'}`
            {selection_note}

            The generated receipt audit is `docs/streaming_retrieval_receipt_audit.md`.
            """
        ).rstrip()
    return textwrap.dedent(
        f"""\
        ## Current Cached Evidence

        Current `streaming_retrieval_shadow` receipts are lock-safe shadow
        evidence only. They do not modify the active compressor and do not prove
        `10.95%`.

        - Cached receipts: `{len(rows)}`
        - Receipts with held-out rows: `{evidence['heldout_count']}`
        - Verdict counts: {verdict_text}
        - Feature-source counts: {source_text}
        - Receipts with trace/data alignment warnings: `{evidence['alignment_warning_count']}`
        {best_heldout_line}
        {best_net_line}

        {interpretation}

        {alignment_note}
        {audit_note}
        """
    ).strip()


def render() -> str:
    win_gap = CURRENT_WINNER - TARGET_SCORE
    forecast_gap = BEST_FORECAST - TARGET_SCORE
    forecast_margin = CURRENT_WINNER - BEST_FORECAST
    required_bits = forecast_gap * 8

    body = textwrap.dedent(
        f"""\
            # Streaming Retrieval Mixer

            Working name: `SRSTC`, the Streaming Self-Referential Semantic
            Table Coder.

            This is now the primary novel-algorithm strategy for `enwik9`. The
            active `cmix21` memory-valve ladder remains the serialized proof
            lane and a strong backup substrate, but it is no longer treated as
            the main source of new modeling power. SRSTC targets a different
            byte class: causal semantic and structural recurrence that ordinary
            suffix matches, static transforms, and narrow residual patches do
            not model directly.

            Status: design plus cached shadow-evidence lane. This document is
            generated by `tools/streaming_retrieval_mixer_plan.py`; it is not a
            compression result.

            ## Strategy Pivot

            The project keeps two distinct tracks:

            | Track | Role | Claim boundary |
            |---|---|---|
            | SRSTC / streaming retrieval | Primary novel research lane. Build a streaming self-referential probability model from already-decoded spans, deterministic sketches, patch-copy priors, and causal regret routing. | No score claim until exact shadow receipts show positive held-out net bytes after counted code and table costs. |
            | cmix21 / fx2 backup lanes | Proof infrastructure, baselines, and integration substrates. Continue exact gates, memory brackets, public reproduction, and accounting discipline. | Prefix and guard receipts only prove their measured scope. |

            Backup concepts are retained as components:

            - FX2-SC residual/SSE becomes the calibration layer for SRSTC
              probabilities.
            - Causal schema tries become one SRSTC table family.
            - Embedding teachers remain offline discovery tools for sketch
              features and page-family rules.
            - MWCC/I-SSA remain router or state-coordinate candidates.
            - cmix21/fx2 remain the strongest base predictors and packaging
              references.

            ## Target Pressure

            | Quantity | Bytes |
            |---|---:|
            | Current public-record line used by local ledger | `{fmt_int(CURRENT_WINNER)}` |
            | Internal target | `{fmt_int(TARGET_SCORE)}` |
            | Required improvement versus current winner | `{fmt_int(win_gap)}` |
            | Best local forecast | `{fmt_int(BEST_FORECAST)}` |
            | Forecast margin versus current winner | `{fmt_int(forecast_margin)}` |
            | Forecast gap to target | `{fmt_int(forecast_gap)}` |
            | Forecast gap in bits | `{fmt_int(required_bits)}` |

            The active memory-valve ladder can still produce a constructive
            proof. The research gap is that its algorithmic novelty is low.
            SRSTC is the plan for closing the modeling gap rather than only
            shaving memory around an established context mixer.

            @@EVIDENCE_SECTION@@

            ## Algorithm

            1. Decode bytes normally through the base compressor or a shadow
               byte-probability trace.
            2. Segment only completed history into causal spans: page title,
               heading span, paragraph, template argument, URL span, table cell,
               citation, and fallback byte windows.
            3. For every completed span, compute deterministic sketches:
               byte n-gram SimHash, token minhash, XML/wiki phase, title hash,
               template slot, char-class histogram, and suffix bytes.
            4. Insert the span into bounded self-referential online tables keyed
               by sketch bands. The table entries are history-derived and are
               not shipped in the archive.
            5. Before predicting the current bit, compute the current prefix
               sketch from already-decoded bytes only.
            6. Retrieve a small candidate set from matching sketch bands and
               rank it with integer Hamming/overlap scores that approximate
               cosine similarity.
            7. Read the bytes or bits that followed those prior spans and
               accumulate patch-copy continuation distributions: aligned byte,
               nearby offset, normalized token, schema slot, and escape.
            8. Convert the continuation distribution into a legal next-bit
               probability with smoothing and a hard nonzero floor.
            9. Mix that probability with the base compressor through fixed-point
               outer SSE/APM or a regret router. Do not rewrite the byte stream
               and do not inject the state into primary high-order hashes until
               shadow receipts prove that doing so pays.
            10. Update retrieval tables only after the current byte is known to
                both encoder and decoder.

            ## Probability Model

            SRSTC treats near-certain semantic predictions as sharp soft
            probabilities, never as hidden stochastic state:

            ```text
            P_final(x) =
                a * P_base(x)
              + b * P_local_match(x)
              + c * P_retrieved_patch(x)
              + d * P_schema_table(x)
              + e * P_entity_ref_table(x)
              + floor_escape(x)
            ```

            The coefficients are causal fixed-point weights updated from past
            loss. A wrong high-confidence retrieval costs bits, but it cannot
            desynchronize decoding because every byte keeps nonzero probability
            and every table update is derived from decoded bytes.

            Current raw-shadow implementation note: `tools/streaming_retrieval_raw_shadow.py`
            can now run SRSTC as a probabilistic typed copy channel, not only as
            a sketch hint. Enable it with `--copy-channel-enabled`,
            `--log-odds-mix`, `--expert-mode no_regret_abstain`, and
            `--block-fallback-qbits`. The receipt records typed table value for
            prose, titles, templates, refs, URLs, table rows, infoboxes,
            category/link contexts, and entity-like contexts, plus copy-channel
            rows, selected expert bands, proposed block gain before fallback,
            and exact same-coder bytes after fallback. It also records
            `conditional_attribution`, which separates copy availability from
            router-selected copy and compares typed retrieval, byte prior, and
            copy priors on the same bits. Copy confidence can be made
            type-specific with `--copy-channel-type-blends`, so a weak entity or
            category copy bucket can be suppressed without disabling ref, URL,
            table, or prose continuation.

            ## Why This Is Different

            Existing `hierarchical_retrieval_shadow.py` mostly asks whether a
            parser/retrieval bucket can correct residual bias. SRSTC is
            stronger: it makes causal k-nearest continuation memory a primary
            probability source over the already-decoded stream. The useful
            memory is the corpus prefix itself, not a static embedding model.

            The phrase "cosine similarity" is admissible only after it is
            compiled into deterministic integer sketches. Floating embeddings
            may be teachers, but the final decoder may use only counted code and
            history-derived state.

            The phrase "self-referential table" means decoder-learned state:
            completed spans become future prediction tables after both sides
            have decoded them. It does not mean an archive-side index, a shipped
            embedding table, or a future-derived summary.

            ## Determinism Contract

            The encoder and decoder must compute the same value at every bit:

            ```text
            state_t = f(decoded_bytes_before_t, counted_constants)
            p_retrieval_t = g(state_t, base_probability_t)
            p_final_t = mix(base_probability_t, p_retrieval_t, online_weights_t)
            ```

            Forbidden:

            - stochastic decode choices;
            - unseeded randomness;
            - floating-point similarity in the final arithmetic path;
            - future page summaries;
            - offline cluster IDs unless the exact rule or table is counted;
            - zero-probability masks.

            Allowed:

            - fixed integer random projections;
            - SimHash/minhash sketches with counted constants;
            - bounded online tables rebuilt from decoded history;
            - online regret weights replayed identically by the decoder;
            - soft probability floors.

            ## Shadow-Coder Receipt

            A valid first receipt must contain:

            ```json
            {{
              "receipt_type": "streaming_retrieval_shadow",
              "trace_version": "fx2_shadow_trace_v1",
              "scope_bytes": null,
              "base_trace": "",
              "data_sha256": "",
              "span_schema_hash": "",
              "sketch_schema_hash": "",
              "table_update_rule_hash": "",
              "retrieval_table_cap_entries": null,
              "sketch_schema": {{
                "copy_channel": {{
                  "blend_ppm": null,
                  "type_blends": {{
                    "prose": null,
                    "title": null,
                    "template": null,
                    "ref": null,
                    "url": null,
                    "table": null,
                    "infobox": null,
                    "category_link": null,
                    "entity": null
                  }}
                }}
              }},
              "retrieved_neighbors_per_bit": null,
              "conditional_attribution": {{
                "schema": "conditional_copy_attribution_v1",
                "buckets": {{
                  "typed_retrieval": {{"direct_gain_bytes_vs_copy": null}},
                  "byte_prior": {{"direct_gain_bytes_vs_copy": null}},
                  "copy_available": {{
                    "selected_rows": null,
                    "direct_gain_bytes_vs_typed": null,
                    "direct_gain_bytes_vs_byte_prior": null,
                    "mean_copy_best_sketch_distance": null,
                    "mean_copy_abs_offset": null,
                    "mean_copy_edit_distance": null
                  }},
                  "copy_<span_type>": {{"selected_rows": null}}
                }}
              }},
              "patch_alignment_modes": [],
              "escape_floor": null,
              "base_shadow_bytes": null,
              "candidate_shadow_bytes": null,
              "shadow_saved_bytes": null,
              "heldout_shadow_saved_bytes": null,
              "added_code_bytes_estimate": null,
              "added_static_table_bytes": null,
              "max_online_state_bytes": null,
              "largest_block_regression_bytes": null,
              "net_saved_bytes": null,
              "verdict": "incomplete"
            }}
            ```

            Promotion requires positive held-out `net_saved_bytes`, block-level
            stability, exact finite-precision shadow coding, and a named C++ or
            Python integration point.

            ## Implementation Queue

            | Step | Concrete delta | Proof output |
            |---|---|---|
            | 1 | Add a passive causal span and sketch builder over corpus prefixes and existing residual traces. | JSON summary of span counts, table caps, deterministic schema hash, and max online state. |
            | 2 | Add standalone SRSTC shadow scoring on cached residual rows and raw byte-aligned corpus bits with base, local match, retrieval patch, schema, and entity/ref experts. | Exact shadow bytes for base versus SRSTC-mixed probabilities. |
            | 3 | Add block-level held-out splits and page-family diagnostics. | Winning/losing block table, largest-regression field, and concentrated-gain flag. |
            | 4 | Add fixed-point regret routing over base and SRSTC experts. | Router shadow receipt with counted code/table estimates and replayed weight hashes. |
            | 4a | Add typed copy-channel tables with log-odds mixing, MDL-value eviction, no-regret abstain routing, block fallback, and conditional attribution in the raw shadow scorer. | Raw-shadow receipt fields for `typed_copy_channel`, copy expert bands, `block_fallback`, and `conditional_attribution`. |
            | 5 | Integrate only the smallest winning SRSTC component into the strongest admissible substrate. | Prefix replay result JSON with roundtrip and determinism. |

            ## Kill Gates

            Retire or narrow this lane if:

            - the best held-out shadow row remains below counted code bytes;
            - gains are concentrated in one page family or one prefix;
            - the online table cap grows beyond the memory budget;
            - the retrieval probability only duplicates existing match-model
              behavior;
            - implementation requires shipping an embedding model or index.

            ## Relationship To Active cmix21 Work

            Keep the active `cmix21` scorer serialized and untouched. SRSTC work
            runs beside it on cached traces, corpus-prefix shadow scoring, and
            design receipts. If SRSTC proves positive MDL, it should first enter
            as the smallest paying outer correction or router input to the
            strongest admissible compressor. A standalone custom backend is only
            justified after the shadow receipts show that the primary
            self-referential probability model beats the backup substrates on
            same-scope evidence.

            A `cmix21` probability-trace substrate must be run as its own
            guarded diagnostic lane, not beside an active memory proof gate.
            The diagnostic trace hook is compile-time gated by
            `CMIX_TRACE_ROWS`; even tiny diagnostic inputs allocate the native
            cmix model tables up front, so running it next to the proof lane
            would contaminate RSS evidence. Trace row positions are in the
            cmix preprocessed stream, so any SRSTC-on-cmix receipt must also
            record the exact transformed byte stream used for the trace.
            """
    )
    return body.replace("@@EVIDENCE_SECTION@@", evidence_section()).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rendered = render()
    if args.check:
        existing = OUT_MD.read_text() if OUT_MD.exists() else ""
        if existing != rendered:
            raise SystemExit(f"stale {OUT_MD.relative_to(ROOT)}")
        print(f"up_to_date {OUT_MD}")
        return 0

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(rendered)
    print(f"wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
