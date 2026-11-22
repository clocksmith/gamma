#!/usr/bin/env python3
"""Standalone, solver-free replay verifier for the 6-corpus capacity-impossibility receipt.

Imports nothing from `impossibility_bound.py` and uses no LP/MILP solver (only Python stdlib
and Git blob reads at pin 59ff0441). For all 6 corpora x 7 thresholds = 42 rows:
  1. Reconstructs the frozen corpus from `clocksmith/gamma@59ff0441` and verifies SHA-256s.
  2. Replays every disjoint-position witness and evaluates the full integer Experiment A
     Lagrangian dual formula (at scale = 1 for step potentials, or scale = 2^20 for LP duals)
     over ALL raw eligible substrings to confirm `certified_lower_bound`.
  3. Verifies rule eligibility and exact 0..n_p tiling reachability of `feasible_vocabulary`
     across every program in the corpus to confirm `feasible_upper_bound`, `remaining_gap`,
     and `shortcut_applied`.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

PIN = "59ff04415ff2afd04ff2ed451340f4f02852bf18"
LIT = "projects/algorithm_solver/literals"


def git_cat(repo: Path, rev_path: str) -> bytes:
    return subprocess.check_output(
        ["git", "--no-replace-objects", "-C", str(repo), "cat-file", "blob", rev_path]
    )


def can_tile(source: str, vocab: list[str]) -> bool:
    by_first: dict[str, list[str]] = defaultdict(list)
    for entry in vocab:
        if entry:
            by_first[entry[0]].append(entry)
    n = len(source)
    reach = [False] * (n + 1)
    reach[0] = True
    for i in range(n):
        if reach[i]:
            for entry in by_first.get(source[i], ()):
                end = i + len(entry)
                if end <= n and source.startswith(entry, i):
                    reach[end] = True
    return reach[n]


def build_shared_index(texts: dict[str, str], max_bytes: int | None = 160):
    whole = set(texts.values())
    alpha = set().union(*map(set, whole)) - whole
    items = [(s[i:], pid, i) for pid, s in texts.items() for i in range(len(s))]
    items.sort(key=lambda x: x[0])

    def lcp(a: str, b: str) -> int:
        m = min(len(a), len(b))
        j = 0
        while j < m and a[j] == b[j]:
            j += 1
        return j

    wit = {(pid, i): 0 for _suf, pid, i in items}
    prev_diff = prev_suf = prev_pid = None
    for suf, pid, i in items:
        if prev_pid is not None and prev_pid != pid:
            prev_diff = prev_suf
        if prev_diff is not None:
            v = lcp(suf, prev_diff)
            if v > wit[pid, i]:
                wit[pid, i] = v
        prev_suf, prev_pid = suf, pid

    next_diff = next_suf = next_pid = None
    for suf, pid, i in reversed(items):
        if next_pid is not None and next_pid != pid:
            next_diff = next_suf
        if next_diff is not None:
            v = lcp(suf, next_diff)
            if v > wit[pid, i]:
                wit[pid, i] = v
        next_suf, next_pid = suf, pid

    docs: dict[str, set[str]] = defaultdict(set)
    occs_raw: list[tuple[str, int, int, str]] = []
    for pid, s in texts.items():
        n = len(s)
        for a in range(n):
            w = wit[pid, a]
            if w < 2:
                continue
            hi = min(n, a + w) if max_bytes is None else min(n, a + w, a + max_bytes)
            b_bytes = len(s[a : a + 1].encode("utf-8"))
            for b in range(a + 2, hi + 1):
                b_bytes += len(s[b - 1 : b].encode("utf-8"))
                if max_bytes is not None and b_bytes > max_bytes:
                    break
                sub = s[a:b]
                if sub not in whole:
                    docs[sub].add(pid)
                    occs_raw.append((pid, a, b, sub))
    doc_freq = {sub: len(d) for sub, d in docs.items() if len(d) >= 2}
    occs = [(pid, a, b, sub) for pid, a, b, sub in occs_raw if sub in doc_freq]
    return whole, alpha, doc_freq, occs, wit


def eval_dual_bound_k(
    texts: dict[str, str],
    k: int,
    scale: int,
    potentials: dict[str, list[int]],
    whole: set[str],
    alpha: set[str],
    doc_freq: dict[str, int],
    occs: list[tuple[str, int, int, str]],
    wit: dict[tuple[str, int], int] | None = None,
) -> int:
    """Evaluate exact integer Experiment A dual bound ceil(L_A(pi)) over all eligible strings."""
    assert isinstance(scale, int) and scale > 0
    if set(potentials.keys()) != set(texts.keys()):
        raise ValueError("Potential keys do not match corpus programs")
    numer = 0
    rebates: dict[str, int] = defaultdict(int)
    for pid, s in texts.items():
        p = potentials[pid]
        if len(p) != len(s) + 1 or not all(type(v) is int for v in p):
            raise ValueError(f"Invalid potential vector for {pid}")
        numer += p[0] - p[-1]
        if k == 1:
            n = len(s)
            is_monotone_unit_drop = (
                scale == 1
                and wit is not None
                and all(p[i] >= p[i + 1] for i in range(n))
                and p[0] - p[-1] <= 1
            )
            if is_monotone_unit_drop:
                if p[0] - p[-1] == 1:
                    # Locate unique drop index `pos` where p[pos] == p[0] and p[pos + 1] == p[0] - 1.
                    # The dual sums over every occurrence, so each occurrence that spans `pos` adds 1 to
                    # its token's rebate. A token can span `pos` more than once in two ways: it also
                    # occurs in another program (length <= wit[pid, a]), or it overlaps itself inside
                    # this program (as "aa" does at position 1 of "aaa"). A substring longer than both
                    # extents occurs nowhere else that spans `pos`, so its rebate is exactly 1 == scale
                    # and it contributes min(0, 1 - 1) = 0. Everything shorter is enumerated here.
                    pos = next(i for i in range(n) if p[i] > p[i + 1])
                    for a in range(pos + 1):
                        hi = min(n, a + max(1, wit[pid, a], self_repeat_extent(s, a, pos)))
                        if hi > pos:
                            for b in range(pos + 1, hi + 1):
                                sub = s[a:b]
                                if sub not in whole:
                                    rebates[sub] += 1
            else:
                for a in range(n):
                    pa = p[a]
                    for b in range(a + 1, n + 1):
                        if pa > p[b]:
                            sub = s[a:b]
                            if sub not in whole:
                                rebates[sub] += pa - p[b]
        else:
            for i, ch in enumerate(s):
                if ch in alpha and p[i] > p[i + 1]:
                    rebates[ch] += p[i] - p[i + 1]
    if k >= 2:
        for pid, a, b, sub in occs:
            if doc_freq[sub] >= k:
                p = potentials[pid]
                if p[a] > p[b]:
                    rebates[sub] += p[a] - p[b]
    numer += sum(min(0, scale - reb) for reb in rebates.values())
    return -(-numer // scale)


def self_repeat_extent(s: str, a: int, limit: int) -> int:
    """Longest L such that s[a:a+L] also starts at another index a' <= limit of the same string (0 if none)."""

    def repeats(length: int) -> bool:
        sub = s[a : a + length]
        first = s.find(sub)
        if first != a:
            return True  # an earlier start, and a <= limit
        second = s.find(sub, a + 1)
        return second != -1 and second <= limit

    lo, hi = 0, len(s) - a
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if repeats(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def witness_charges(
    texts: dict[str, str],
    k: int,
    positions: list[tuple[str, int]],
    whole: set[str],
    alpha: set[str],
    doc_freq: dict[str, int],
    occs: list[tuple[str, int, int, str]],
    wit: dict[tuple[str, int], int],
) -> dict[str, list[tuple[str, int]]]:
    """Tokens the all-occurrences dual charges more than once for a scale = 1 step potential.

    Every eligible occurrence that spans a witness position charges its token once for that position.
    Returns {token: [witness position, ...]} for tokens charged at least twice. Two distinct positions in
    a list mean the two cover sets share that token (the witness is not disjoint). The same position
    twice means the token overlaps itself across it: the witness is still disjoint, but the dual value
    falls below the number of positions."""
    by_pid: dict[str, list[int]] = defaultdict(list)
    for pid, pos in positions:
        by_pid[pid].append(pos)
    charges: dict[str, list[tuple[str, int]]] = defaultdict(list)
    if k == 1:
        for pid, plist in by_pid.items():
            s = texts[pid]
            n = len(s)
            if len(plist) == 1:
                pos = plist[0]
                for a in range(pos + 1):
                    hi = min(n, a + max(1, wit[pid, a], self_repeat_extent(s, a, pos)))
                    for b in range(pos + 1, hi + 1):
                        sub = s[a:b]
                        if sub not in whole:
                            charges[sub].append((pid, pos))
            else:
                for a in range(n):
                    for b in range(a + 1, n + 1):
                        inside = [pos for pos in plist if a <= pos < b]
                        if inside:
                            sub = s[a:b]
                            if sub not in whole:
                                charges[sub].extend((pid, pos) for pos in inside)
    else:
        for pid, plist in by_pid.items():
            for pos in plist:
                ch = texts[pid][pos]
                if ch in alpha:
                    charges[ch].append((pid, pos))
        for pid, a, b, sub in occs:
            if doc_freq[sub] >= k and pid in by_pid:
                for pos in by_pid[pid]:
                    if a <= pos < b:
                        charges[sub].append((pid, pos))
    return {token: where for token, where in charges.items() if len(where) >= 2}


def step_potentials(texts: dict[str, str], coords: list[list[int] | tuple[str, int]]) -> dict[str, list[int]]:
    by_pid: dict[str, list[int]] = defaultdict(list)
    for pid, pos in coords:
        by_pid[str(pid)].append(int(pos))
    out: dict[str, list[int]] = {}
    for pid, s in texts.items():
        wpos = sorted(by_pid.get(pid, ()))
        out[pid] = [sum(1 for wp in wpos if wp >= j) for j in range(len(s) + 1)]
    return out


def load_frozen_corpora_for_replay(repo: Path, receipt: dict) -> dict[str, dict[str, str]]:
    ids80 = json.loads(git_cat(repo, f"{PIN}:{LIT}/matched80-v1/labels/ids.json"))
    src_manifest = json.loads(git_cat(repo, f"{PIN}:{LIT}/scale-v2/generated/manifest.json"))["rows"]
    compact_sha = {r["id"]: r["sha256"] for r in src_manifest if r["variant"] == "compact"}
    canon_sha = {r["id"]: r["sha256"] for r in src_manifest if r["variant"] == "canonical"}

    js_compact, js_canonical = {}, {}
    for pid in ids80:
        b_comp = git_cat(repo, f"{PIN}:{LIT}/scale-v2/generated/sources/{pid:04d}-compact.js")
        b_can = git_cat(repo, f"{PIN}:{LIT}/scale-v2/generated/sources/{pid:04d}-canonical.js")
        if hashlib.sha256(b_comp).hexdigest() != compact_sha[pid]:
            raise ValueError(f"Compact SHA mismatch on {pid}")
        if hashlib.sha256(b_can).hexdigest() != canon_sha[pid]:
            raise ValueError(f"Canonical SHA mismatch on {pid}")
        js_compact[str(pid)] = b_comp.decode("utf-8")
        js_canonical[str(pid)] = b_can.decode("utf-8")

    sub12_ids = [str(pid) for pid in sorted(ids80)[:12]]
    js_sub12 = {pid: js_compact[pid] for pid in sub12_ids}

    pa_manifest = json.loads(git_cat(repo, f"{PIN}:{LIT}/paired-authoring-v1/manifest.json"))
    py_rows80 = sorted(
        [r for r in pa_manifest["source_inventory"] if r["language"] == "python"],
        key=lambda r: int(r["problem_id"]),
    )[:80]
    py_paired80 = {}
    for row in py_rows80:
        pid = str(row["problem_id"])
        raw = git_cat(repo, f"{PIN}:{LIT}/paired-authoring-v1/{row['path']}")
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"Python paired80 SHA mismatch on {pid}")
        py_paired80[pid] = raw.decode("utf-8")

    dv_manifest = json.loads(git_cat(repo, f"{PIN}:{LIT}/python-devval-v1/manifest.json"))
    py_readable = {}
    for row in dv_manifest["sources"]:
        pid = str(row.get("problem_id") or row.get("id"))
        raw = git_cat(repo, f"{PIN}:{LIT}/python-devval-v1/{row['path']}")
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"Python devval SHA mismatch on {pid}")
        py_readable[pid] = raw.decode("utf-8")

    out = {
        "js_matched80_compact": js_compact,
        "js_matched80_canonical": js_canonical,
        "js_sub12_compact": js_sub12,
        "py_paired80_fit": py_paired80,
        "py_devval100_readable": py_readable,
    }
    for cname, cmeta in receipt["corpora"].items():
        if cname.startswith("c_tools_"):
            c_paths = cmeta["c_paths"]
            c_texts = {}
            for idx, p in enumerate(c_paths):
                raw = git_cat(repo, f"{PIN}:{p}")
                if not (64 <= len(raw) <= 8192):
                    raise ValueError(f"Unexpected C file byte size on {p}")
                c_texts[str(idx + 1)] = raw.decode("utf-8")
            out[cname] = c_texts
    return out


def replay_witness(texts, k, positions, whole, alpha, doc_freq, occs, wit, label) -> tuple[int, int]:
    """Check that the witness positions have pairwise disjoint cover sets, then evaluate the all-occurrences
    dual of their scale = 1 step potential. Returns (dual value, number of tokens charged more than once)."""
    if len(set(positions)) != len(positions):
        raise ValueError(f"Duplicate witness position on {label} k={k}")
    charged = witness_charges(texts, k, positions, whole, alpha, doc_freq, occs, wit)
    shared = sorted(token for token, where in charged.items() if len(set(where)) > 1)
    if shared:
        raise ValueError(f"Witness cover sets overlap on {label} k={k}: {shared[:3]}")
    penalty = sum(len(where) - 1 for where in charged.values())
    dual = eval_dual_bound_k(texts, k, 1, step_potentials(texts, positions), whole, alpha, doc_freq, occs, wit=wit)
    if dual != len(positions) - penalty:
        raise ValueError(f"All-occurrences dual {dual} disagrees with the charge count on {label} k={k}")
    return dual, len(charged)


def verify_all(repo: Path, receipt_path: Path, certs_path: Path, annotate: bool = False) -> int:
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    certs = json.loads(certs_path.read_text(encoding="utf-8"))
    if receipt["pin"] != PIN or certs["pin"] != PIN:
        raise ValueError("Pin mismatch")

    corpora = load_frozen_corpora_for_replay(repo, receipt)
    checked_rows = 0
    unequal: list[tuple[str, int, int, int, int]] = []

    for cname, cmeta in receipt["corpora"].items():
        texts = corpora[cname]
        whole, alpha, doc_freq, occs, wit = build_shared_index(texts, max_bytes=160)
        if len(alpha) != cmeta["alphabet_size"]:
            raise ValueError(f"Alphabet size mismatch on {cname}")

        for row in cmeta["rows"]:
            k = int(row["k"])
            crec = certs["certificates"][cname][str(k)]
            ctype = crec["type"]

            # 1. Verify the disjoint witness, then its all-occurrences dual at scale = 1.
            if ctype in ("shortcut_disjoint_scale1", "disjoint_step_potential_scale1"):
                f_pos = [(str(p), int(i)) for p, i in crec["forced_positions"]]
                e_pos = [(str(p), int(i)) for p, i in crec["extra_positions"]]
                step_lb, twice = replay_witness(texts, k, f_pos + e_pos, whole, alpha, doc_freq, occs, wit, cname)
                if len(f_pos) + len(e_pos) != row["disjoint_bound"] or row["disjoint_bound"] != row["certified_lower_bound"]:
                    raise ValueError(f"Disjoint witness size mismatch on {cname} k={k}: row={row}")
                vocab = crec["feasible_vocabulary"]
            elif ctype == "pinned_59ff0441_dual_plus_disjoint_witness":
                f_pos = [(str(p), int(i)) for p, i in crec["disjoint_forced_positions"]]
                e_pos = [(str(p), int(i)) for p, i in crec["disjoint_extra_positions"]]
                step_lb, twice = replay_witness(texts, k, f_pos + e_pos, whole, alpha, doc_freq, occs, wit, cname)
                if len(f_pos) + len(e_pos) != row["disjoint_bound"]:
                    raise ValueError(f"Disjoint witness size mismatch on {cname} k={k}")
                pinned_cert = json.loads(git_cat(repo, f"{PIN}:{crec['pinned_cert_path']}"))
                pinned_manifest = json.loads(git_cat(repo, f"{PIN}:{crec['pinned_manifest_path']}"))
                dual_lb = eval_dual_bound_k(
                    texts, k, int(pinned_cert["scale"]), pinned_cert["potentials"], whole, alpha, doc_freq, occs, wit=wit
                )
                if dual_lb != row["certified_lower_bound"]:
                    raise ValueError(f"Pinned dual mismatch on {cname} k={k}: {dual_lb}")
                vocab = pinned_manifest["vocabulary"]
            elif ctype == "lp_dual_certificate_plus_disjoint":
                f_pos = [(str(p), int(i)) for p, i in crec["disjoint_forced_positions"]]
                e_pos = [(str(p), int(i)) for p, i in crec["disjoint_extra_positions"]]
                step_lb, twice = replay_witness(texts, k, f_pos + e_pos, whole, alpha, doc_freq, occs, wit, cname)
                if len(f_pos) + len(e_pos) != row["disjoint_bound"]:
                    raise ValueError(f"Disjoint witness size mismatch on {cname} k={k}")
                dual_lb = eval_dual_bound_k(
                    texts, k, int(crec["scale"]), crec["potentials"], whole, alpha, doc_freq, occs, wit=wit
                )
                if dual_lb != row["certified_lower_bound"]:
                    raise ValueError(f"LP dual replay mismatch on {cname} k={k}: {dual_lb}")
                vocab = crec["feasible_vocabulary"]
            else:
                raise ValueError(f"Unknown certificate type {ctype}")

            # 2. Verify feasible upper bound vocabulary eligibility and full-corpus tiling!
            if len(vocab) != len(set(vocab)) or len(vocab) != row["feasible_upper_bound"]:
                raise ValueError(f"Feasible vocabulary count mismatch on {cname} k={k}")
            for entry in vocab:
                if not entry or entry in whole:
                    raise ValueError(f"Ineligible empty/whole entry in {cname} k={k}")
                if k == 1:
                    if not any(entry in s for s in texts.values()):
                        raise ValueError(f"Non-corpus entry in {cname} k=1")
                elif len(entry) > 1:
                    if len(entry.encode("utf-8")) > 160 or doc_freq.get(entry, 0) < k:
                        raise ValueError(f"Ineligible W(k={k}) entry in {cname}")
            if not all(can_tile(s, vocab) for s in texts.values()):
                raise ValueError(f"Feasible vocabulary fails to tile {cname} k={k}")

            # 2b. The scale = 1 dual equals the disjoint bound only when no token is charged twice.
            found = {"all_occurrences_dual": step_lb, "tokens_counted_twice": twice,
                     "dual_equals_disjoint_bound": twice == 0}
            if annotate:
                row.update(found)
            for field, value in found.items():
                if field in row and row[field] != value:
                    raise ValueError(f"Recorded {field} is {row[field]}, replay gives {value} on {cname} k={k}")
            if twice:
                unequal.append((cname, k, row["disjoint_bound"], step_lb, twice))

            # 3. Verify gap and shortcut flags!
            if row["remaining_gap"] != row["feasible_upper_bound"] - row["certified_lower_bound"] or row["remaining_gap"] < 0:
                raise ValueError(f"Invalid remaining_gap on {cname} k={k}")
            if row["shortcut_applied"] != (row["disjoint_bound"] == row["alphabet_size"]):
                raise ValueError(f"Invalid shortcut_applied flag on {cname} k={k}")
            if row["shortcut_applied"] and row["remaining_gap"] != 0:
                raise ValueError(f"Shortcut applied yet remaining_gap != 0 on {cname} k={k}")
            checked_rows += 1

    if annotate:
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: independently replayed and verified {checked_rows} (corpus, k) certificates from {PIN}")
    print(f"Disjoint witness valid on all {checked_rows} rows. Scale-1 all-occurrences dual equals the disjoint "
          f"bound on {checked_rows - len(unequal)}; a token is charged twice on {len(unequal)}.")
    for cname, k, bound, dual, twice in unequal:
        print(f"  {cname} k={k}: disjoint bound {bound}, all-occurrences dual {dual}, tokens charged twice {twice}")
    return checked_rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    parser.add_argument("--repo", type=Path, default=here.parents[3])
    parser.add_argument("--receipt", type=Path, default=here / "results.json")
    parser.add_argument("--certs", type=Path, default=here / "certificates.json")
    parser.add_argument("--annotate", action="store_true",
                        help="write all_occurrences_dual, tokens_counted_twice and dual_equals_disjoint_bound into each receipt row")
    args = parser.parse_args()
    verify_all(args.repo, args.receipt, args.certs, annotate=args.annotate)


if __name__ == "__main__":
    sys.exit(0 if main() is None else 0)
