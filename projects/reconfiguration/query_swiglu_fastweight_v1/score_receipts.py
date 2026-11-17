"""Independent post-hoc scorer for query_swiglu_fastweight_v1 and v2 receipts.

Preserves sealed generation receipts (`raw_exact` field `correct`) completely unchanged,
and publishes symmetric canonical scoring alongside them with explicit handling for:
1. Trailing sentence/clause punctuation (`.`, `,`, `;`) applied symmetrically to both
   model output and expected target string (fixing asymmetric `.` stripping on prose tasks).
2. Surrounding whitespace, multi-line continuation trimming (first non-empty line),
   markdown inline code fences (`` `...` ``), and internal whitespace collapsing.
3. Strict non-equivalence preservation: distinct delimiters inside structured identifiers
   (e.g. `nd_209/mi-66` vs `nd_209 : mi-66`), distinct units/magnitudes (`15mg` vs `10mg`),
   and distinct keys/syllables never falsely match.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import comb
from pathlib import Path
from typing import Any


def canonicalize_answer(text: str) -> str:
    """Symmetric canonicalizer for single-line factual/structured completions."""
    if text is None:
        return ""
    lines = str(text).strip().splitlines()
    first = lines[0].strip() if lines else ""
    # Iteratively strip trailing sentence punctuation and balanced outer quotes/backticks
    changed = True
    while changed and first:
        prev = first
        first = first.rstrip(".,;").strip()
        if len(first) >= 2 and (
            (first[0] == "`" and first[-1] == "`")
            or (first[0] == '"' and first[-1] == '"')
            or (first[0] == "'" and first[-1] == "'")
        ):
            first = first[1:-1].strip()
        changed = first != prev
    first = first.rstrip("`.,;")
    return " ".join(first.split())


def is_equivalent_output(output: str, expected: str) -> bool:
    return canonicalize_answer(output) == canonicalize_answer(expected)


def exact_mcnemar_two_sided_p(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    tail = sum(comb(n, j) for j in range(k + 1)) / float(2 ** n)
    return min(1.0, 2.0 * tail)


def score_subset(rows: list[dict[str, Any]], mode: str = "symmetric") -> dict[str, Any]:
    assert mode in ("raw", "symmetric")
    arm_order = [
        "base",
        "zero_fastweight",
        "focal_fastweight",
        "wrong_context_fastweight",
        "random_fastweight",
        "matched_compute_split2pass",
        "matched_compute_full2pass",
    ]
    present = [a for a in arm_order if any(r["arm"] == a for r in rows)]
    for r in rows:
        if r["arm"] not in present:
            present.append(r["arm"])

    def judge(r: dict[str, Any]) -> bool:
        if mode == "raw":
            return bool(r["correct"])
        return is_equivalent_output(r["output"], r["expected"])

    base_rows = [r for r in rows if r["arm"] == "base"]
    base_ms = sum(r["total_ms"] for r in base_rows) / max(1, len(base_rows))
    focal_map = {r["id"]: judge(r) for r in rows if r["arm"] == "focal_fastweight"}

    arms_summary: dict[str, Any] = {}
    for arm in present:
        ar = [r for r in rows if r["arm"] == arm]
        ok_cnt = sum(1 for r in ar if judge(r))
        m_set = sum(r.get("setup_ms", 0.0) for r in ar) / len(ar)
        m_don = sum(r.get("donor_setup_ms", 0.0) for r in ar) / len(ar)
        m_ft = sum(r["first_token_ms"] for r in ar) / len(ar)
        m_dec = sum(r["decode_ms"] for r in ar) / len(ar)
        m_tot = sum(r["total_ms"] for r in ar) / len(ar)
        m_bytes = sum(r.get("logical_bytes", 0) for r in ar) / len(ar)
        by_dom = {
            d: {
                "correct": sum(1 for r in ar if r["domain"] == d and judge(r)),
                "total": sum(1 for r in ar if r["domain"] == d),
            }
            for d in sorted({r["domain"] for r in ar})
        }
        arms_summary[arm] = {
            "correct": ok_cnt,
            "total": len(ar),
            "accuracy": ok_cnt / len(ar),
            "by_domain": by_dom,
            "mean_setup_ms": m_set,
            "mean_donor_setup_ms": m_don,
            "setup_pct_of_base": 100.0 * m_set / base_ms,
            "mean_first_token_ms": m_ft,
            "mean_decode_ms": m_dec,
            "mean_total_ms": m_tot,
            "total_overhead_pct": 100.0 * (m_tot - base_ms) / base_ms,
            "mean_logical_bytes": m_bytes,
        }

    paired_tests: dict[str, Any] = {}
    if focal_map:
        for ctrl in present:
            if ctrl in ("focal_fastweight", "zero_fastweight"):
                continue
            c_map = {r["id"]: judge(r) for r in rows if r["arm"] == ctrl}
            wins = sum(1 for tid, fv in focal_map.items() if fv and not c_map[tid])
            losses = sum(1 for tid, fv in focal_map.items() if (not fv) and c_map[tid])
            # Also record per-domain net wins/losses vs base for regression transparency
            dom_deltas = {}
            for d in sorted({r["domain"] for r in rows}):
                d_ids = [r["id"] for r in rows if r["arm"] == "focal_fastweight" and r["domain"] == d]
                dw = sum(1 for tid in d_ids if focal_map[tid] and not c_map[tid])
                dl = sum(1 for tid in d_ids if (not focal_map[tid]) and c_map[tid])
                dom_deltas[d] = {"wins": dw, "losses": dl, "net": dw - dl}
            paired_tests[f"focal_vs_{ctrl}"] = {
                "focal_wins": wins,
                "control_wins": losses,
                "net_wins": wins - losses,
                "mcnemar_two_sided_p": exact_mcnemar_two_sided_p(wins, losses),
                "by_domain": dom_deltas,
            }
    return {"arms": arms_summary, "paired_tests": paired_tests}


def score_receipt_file(path: Path) -> dict[str, Any]:
    raw_bytes = path.read_bytes()
    receipt_sha = sha256(raw_bytes).hexdigest()
    data = json.loads(raw_bytes.decode("utf-8"))
    rows = data["rows"]
    groups = sorted({r.get("group", "all") for r in rows})

    result: dict[str, Any] = {
        "receipt_file": path.name,
        "receipt_sha256": receipt_sha,
        "schema": data.get("schema"),
        "model": data.get("modelId") or data.get("model_path"),
        "raw_original": {"pooled": score_subset(rows, mode="raw")},
        "symmetric_canonical": {"pooled": score_subset(rows, mode="symmetric")},
    }
    if len(groups) > 1 or (groups and groups[0] != "all"):
        for g in groups:
            sub = [r for r in rows if r.get("group", "all") == g]
            result["raw_original"][g] = score_subset(sub, mode="raw")
            result["symmetric_canonical"][g] = score_subset(sub, mode="symmetric")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("receipts", nargs="+", type=Path)
    ap.add_argument("--output-json", type=Path, default=None)
    args = ap.parse_args()

    bundle = {}
    for p in args.receipts:
        if not p.exists():
            continue
        res = score_receipt_file(p)
        bundle[p.name] = res
        raw_p = res["raw_original"]["pooled"]["arms"]
        sym_p = res["symmetric_canonical"]["pooled"]["arms"]
        print(f"=== {p.name} (sha256={res['receipt_sha256'][:12]}...) ===")
        for arm in sym_p:
            sr = sym_p[arm]
            rr = raw_p[arm]
            dom_compact = {d: v["correct"] for d, v in sr["by_domain"].items()}
            print(
                f"  {arm:28s} | raw={rr['correct']:3d}/{rr['total']} | sym={sr['correct']:3d}/{sr['total']} ({100*sr['accuracy']:5.1f}%) | "
                f"setup={sr['mean_setup_ms']:5.1f}ms ({sr['setup_pct_of_base']:4.2f}%) | "
                f"tot={sr['mean_total_ms']:6.1f}ms ({sr['total_overhead_pct']:+5.2f}%) | {dom_compact}"
            )
        for k, tv in res["symmetric_canonical"]["pooled"]["paired_tests"].items():
            print(f"    [sym {k}] +{tv['focal_wins']}/-{tv['control_wins']} (net {tv['net_wins']:+d}, p={tv['mcnemar_two_sided_p']:.4g})")

    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(bundle, indent=2))


if __name__ == "__main__":
    main()
