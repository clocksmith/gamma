#!/usr/bin/env python3
"""Unit tests for dual A1AF/A1AD serialization, independent decoding, and negative corruption controls."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / "objective-holdout-v1"
CL = LIT / "closure-holdout-v1"

import headers as H
import independent_decode as ID


def _load_sample_docs(n_docs: int = 12):
    spec = json.loads((OH / "frozen/sets/dev.json").read_text())
    return [(LIT / f["path"]).read_bytes() for f in spec["files"][:n_docs]]


def _load_chain(path: Path, n_total: int):
    out = []
    for line in path.read_text().splitlines():
        if line.startswith("E "):
            out.append(bytes.fromhex(line.split()[5]))
            if len(out) >= n_total:
                break
    return out


def _encode_both(entries, docs, emit_mask=None, merge_ranks=None):
    dag = H.build_dag_spec(entries, emit_mask=emit_mask, merge_ranks=merge_ranks)
    emitted = dag.emitted_entries
    d = H.Dictionary(emitted)
    edges = [d.edges(raw) for raw in docs]
    lengths, _, _, _ = H.fit_table(d, edges)
    parses = [H.parse_bits(e, lengths, d.ESC)[0] for e in edges]
    res = H.serialize_dual_archives(dag, lengths, docs, parses)
    return dag, lengths, res


def test_roundtrip_closed_and_open():
    docs = _load_sample_docs(16)
    closed_entries = _load_chain(CL / "out/exact/exact-closed-s1-whole.txt", 171 + 84)
    open_entries = _load_chain(CL / "out/exact/exact-entry-s1-whole.txt", 171 + 84)

    # 1. Pure-pair closed vocab (A1AF vs A1AD mode=0)
    dag_c, _, res_c = _encode_both(closed_entries, docs, merge_ranks=list(range(84)))
    assert dag_c.mode == H.FLAG_MODE_PAIR
    dec_f = ID.verify_archive_against_sources(res_c["flat_archive"], docs)
    dec_d = ID.verify_archive_against_sources(res_c["dag_archive"], docs)
    assert dec_f["tokens"] == dec_d["tokens"]
    assert dec_f["payload_bytes"] == dec_d["payload_bytes"]
    assert res_c["dag_header_bytes"] < res_c["flat_header_bytes"]
    assert res_c["dag_complete_bits"] == 8 * len(res_c["dag_archive"])
    assert res_c["flat_complete_bits"] == 8 * len(res_c["flat_archive"])

    # 2. Hybrid open vocab (A1AF vs A1AD mode=1)
    dag_o, _, res_o = _encode_both(open_entries, docs)
    assert dag_o.mode == H.FLAG_MODE_HYBRID
    dec_of = ID.verify_archive_against_sources(res_o["flat_archive"], docs)
    dec_od = ID.verify_archive_against_sources(res_o["dag_archive"], docs)
    assert dec_of["tokens"] == dec_od["tokens"]
    assert dec_of["payload_bytes"] == dec_od["payload_bytes"]

    # 3. Storage-only ancestor via emit_mask (disable 10 intermediate fragments for emission)
    emit_mask = [True] * len(closed_entries)
    for idx in range(171, 181):
        emit_mask[idx] = False
    dag_m, _, res_m = _encode_both(closed_entries, docs, emit_mask=emit_mask)
    assert dag_m.emit_mask is not None
    assert res_m["dag_nodes"] == 255
    assert res_m["emitted_entries"] == 245
    dec_mf = ID.verify_archive_against_sources(res_m["flat_archive"], docs)
    dec_md = ID.verify_archive_against_sources(res_m["dag_archive"], docs)
    assert dec_mf["entries"] == 245 and dec_md["entries"] == 245
    assert dec_md["dag_nodes"] == 255
    return {
        "closed_flat_header_bytes": res_c["flat_header_bytes"],
        "closed_dag_header_bytes": res_c["dag_header_bytes"],
        "open_flat_header_bytes": res_o["flat_header_bytes"],
        "open_dag_header_bytes": res_o["dag_header_bytes"],
        "masked_dag_nodes": res_m["dag_nodes"],
        "masked_emitted_entries": res_m["emitted_entries"],
    }


def _expect_fail(fn, label: str):
    try:
        fn()
    except ID.FormatError as exc:
        return f"{label}: rejected ({exc})"
    raise AssertionError(f"negative control FAILED to reject: {label}")


def test_negative_controls():
    docs = _load_sample_docs(8)
    # Build a small deterministic closed DAG where node 5 depends on node 4.
    # Leaves: sorted bytes from docs; pick a guaranteed multi-step chain inside docs[0].
    leaves = sorted({bytes([b]) for d in docs for b in d})
    # Pick 4-byte substring from docs[0]
    sub = docs[0][:4]
    p1 = sub[:2]
    p2 = sub[:3]
    p3 = sub[:4]
    entries = leaves + [p1, p2, p3]
    ranks = [0, 1, 2]
    dag, lengths, res = _encode_both(entries, docs, merge_ranks=ranks)
    ID.verify_archive_against_sources(res["dag_archive"], docs)

    results = []

    # Control 1: Corrupted DAG edge pointing to forward/self index (>= i)
    bad_dag_forward = H.DAGSpec(
        leaves=dag.leaves,
        nodes=dag.nodes,
        defs=[(dag.defs[0][0], (len(leaves), 0))] + dag.defs[1:],  # left == node_i (self-edge)
        mode=dag.mode,
        emit_mask=dag.emit_mask,
        merge_ranks=dag.merge_ranks,
    )
    bad_buf_fwd = H.build_dag_header(bad_dag_forward, lengths) + res["dag_archive"][res["dag_header_bytes"]:]
    results.append(_expect_fail(lambda: ID.verify_archive_against_sources(bad_buf_fwd, docs), "dag_self_edge"))

    # Control 2: Corrupted DAG edge swapped to a different valid earlier leaf (changes decoded bytes)
    orig_l, orig_r = dag.defs[0][1]
    alt_l = (orig_l + 1) % len(leaves)
    bad_dag_swap = H.DAGSpec(
        leaves=dag.leaves,
        nodes=dag.nodes,
        defs=[("pair", (alt_l, orig_r))] + dag.defs[1:],
        mode=dag.mode,
        emit_mask=dag.emit_mask,
        merge_ranks=dag.merge_ranks,
    )
    bad_buf_swap = H.build_dag_header(bad_dag_swap, lengths) + res["dag_archive"][res["dag_header_bytes"]:]
    results.append(_expect_fail(lambda: ID.verify_archive_against_sources(bad_buf_swap, docs), "dag_edge_swap"))

    # Control 3: Corrupted merge rank order (child p1 rank > parent p2 rank)
    bad_dag_rank_inv = H.DAGSpec(
        leaves=dag.leaves,
        nodes=dag.nodes,
        defs=dag.defs,
        mode=dag.mode,
        emit_mask=dag.emit_mask,
        merge_ranks=[1, 0, 2],  # p2 depends on p1, so rank[p1]=1 >= rank[p2]=0 is illegal
    )
    bad_buf_rank_inv = H.build_dag_header(bad_dag_rank_inv, lengths) + res["dag_archive"][res["dag_header_bytes"]:]
    results.append(_expect_fail(lambda: ID.verify_archive_against_sources(bad_buf_rank_inv, docs), "rank_inversion"))

    # Control 4: Corrupted duplicate merge rank
    bad_dag_rank_dup = H.DAGSpec(
        leaves=dag.leaves,
        nodes=dag.nodes,
        defs=dag.defs,
        mode=dag.mode,
        emit_mask=dag.emit_mask,
        merge_ranks=[0, 0, 2],
    )
    bad_buf_rank_dup = H.build_dag_header(bad_dag_rank_dup, lengths) + res["dag_archive"][res["dag_header_bytes"]:]
    results.append(_expect_fail(lambda: ID.verify_archive_against_sources(bad_buf_rank_dup, docs), "rank_duplicate"))

    # Control 5: Corrupted canonical Huffman code length (breaks Kraft sum)
    bad_lengths = list(lengths)
    bad_lengths[0] = max(1, bad_lengths[0] - 1) if bad_lengths[0] > 1 else bad_lengths[0] + 1
    bad_buf_huff = H.build_dag_header(dag, bad_lengths) + res["dag_archive"][res["dag_header_bytes"]:]
    results.append(_expect_fail(lambda: ID.verify_archive_against_sources(bad_buf_huff, docs), "huffman_length_corrupt"))

    # Control 6: Corrupted flat archive entry byte
    flat_mut = bytearray(res["flat_archive"])
    # Flip a byte inside the payload
    flat_mut[-2] ^= 0xFF
    results.append(_expect_fail(lambda: ID.verify_archive_against_sources(bytes(flat_mut), docs), "flat_payload_bitflip"))

    return results


def run_all():
    rt = test_roundtrip_closed_and_open()
    neg = test_negative_controls()
    return {"roundtrip": rt, "negative_controls": neg, "ok": True}


if __name__ == "__main__":
    out = run_all()
    print(json.dumps(out, indent=2))
