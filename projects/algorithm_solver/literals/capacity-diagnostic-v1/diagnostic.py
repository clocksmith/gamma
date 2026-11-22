#!/usr/bin/env python3
"""Phase 3 tri-state BITS capacity diagnostic with component decomposition,
threshold-monotonicity saturation reuse, Theorem B span-token parse testing,
and separate shared-budget partial-coverage allocation.

Pure Python stdlib, no LP/MILP solver.

Usage:
    python3 -B diagnostic.py --controls      # reproducible run on frozen tiny controls + regressions
    python3 -B diagnostic.py --json          # emit machine-readable JSON for the control suite
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import itertools
import json
import sys
import time
import tracemalloc

PRIMES = ((1_000_000_007, 2), (998_244_353, 3))


# ---------------------------------------------------------------------- rules & parsing
def substrings(s: str, max_bytes: int | None = None) -> set[str]:
    out: set[str] = set()
    n = len(s)
    for a in range(n):
        b_bytes = 0
        for b in range(a + 1, n + 1):
            b_bytes += len(s[b - 1 : b].encode("utf-8"))
            if max_bytes is not None and b_bytes > max_bytes:
                break
            out.add(s[a:b])
    return out


def eligible_tokens(programs: list[str], k: int, max_bytes: int | None = 160) -> set[str]:
    """Eligible dictionary entries under rule U (k = 1) or witness rule W_k (k >= 2)."""
    if k < 1:
        raise ValueError(f"Threshold k must be >= 1, got {k}")
    whole = set(programs)
    if k == 1:
        every: set[str] = set()
        for s in programs:
            every |= substrings(s, max_bytes=None)
        return every - whole
    # k >= 2: single characters (not whole) + multi-char substrings <= max_bytes in >= k programs
    alpha = set().union(*(set(s) for s in programs)) - whole
    doc_freq: dict[str, int] = defaultdict(int)
    for s in programs:
        seen = substrings(s, max_bytes=max_bytes)
        for sub in seen:
            if len(sub) >= 2 and sub not in whole:
                doc_freq[sub] += 1
    return alpha | {sub for sub, df in doc_freq.items() if df >= k}


def parse_program(source: str, vocab: list[str] | set[str]) -> list[str] | None:
    """Find a contiguous non-overlapping parse of `source` using `vocab`, or None."""
    by_first: dict[str, list[str]] = defaultdict(list)
    for tok in vocab:
        if tok:
            by_first[tok[0]].append(tok)
    for ch in by_first:
        by_first[ch].sort(key=lambda t: (-len(t), t))
    n = len(source)
    parent: list[tuple[int, str] | None] = [None] * (n + 1)
    reach = [False] * (n + 1)
    reach[0] = True
    for i in range(n):
        if not reach[i]:
            continue
        for tok in by_first.get(source[i], ()):
            end = i + len(tok)
            if end <= n and not reach[end] and source.startswith(tok, i):
                reach[end] = True
                parent[end] = (i, tok)
    if not reach[n]:
        return None
    parts: list[str] = []
    cur = n
    while cur > 0:
        prev, tok = parent[cur]  # type: ignore[misc]
        parts.append(tok)
        cur = prev
    parts.reverse()
    if "".join(parts) != source:
        raise RuntimeError("Internal parse reconstruction mismatch")
    return parts


def verify_construction(
    programs: list[str],
    dictionary: list[str],
    k: int,
    max_bytes: int | None = 160,
    tokens: set[str] | None = None,
) -> dict:
    """Independently verify dictionary eligibility and byte-exact reconstruction of every program."""
    if len(dictionary) != len(set(dictionary)):
        raise ValueError("Dictionary contains duplicate entries")
    elig = eligible_tokens(programs, k, max_bytes=max_bytes) if tokens is None else tokens
    for entry in dictionary:
        if entry not in elig:
            raise ValueError(f"Ineligible dictionary entry {entry!r} for k={k}")
    parses: list[list[str]] = []
    for s in programs:
        parsed = parse_program(s, dictionary)
        if parsed is None:
            raise ValueError(f"Dictionary fails to parse program {s!r}")
        if "".join(parsed).encode("utf-8") != s.encode("utf-8"):
            raise ValueError(f"Byte-exact reconstruction failed for {s!r}")
        parses.append(parsed)
    return {"dictionarySize": len(dictionary), "dictionary": sorted(dictionary), "parses": parses}


# ---------------------------------------------------------------------- component decomposition
def split_components(programs: list[str]) -> list[list[str]]:
    """Split full-corpus programs into connected components by character cooccurrence."""
    n = len(programs)
    if n == 0:
        return []
    char_sets = [set(s) for s in programs]
    char_to_indices: dict[str, list[int]] = defaultdict(list)
    for idx, cset in enumerate(char_sets):
        for ch in cset:
            char_to_indices[ch].append(idx)
    visited = [False] * n
    components: list[list[str]] = []
    for start in range(n):
        if visited[start]:
            continue
        stack = [start]
        visited[start] = True
        comp_indices: list[int] = []
        while stack:
            u = stack.pop()
            comp_indices.append(u)
            for ch in char_sets[u]:
                for v in char_to_indices[ch]:
                    if not visited[v]:
                        visited[v] = True
                        stack.append(v)
        comp_indices.sort()
        components.append([programs[i] for i in comp_indices])
    return components


# ---------------------------------------------------------------------- linear algebra over F_p
def alphabet_index(programs: list[str]) -> dict[str, int]:
    return {ch: idx for idx, ch in enumerate(sorted(set("".join(programs))))}


def pos_vector(word: str, chars: dict[str, int], prime: int, base: int) -> list[int]:
    vec = [0] * len(chars)
    weight = 1
    for ch in word:
        vec[chars[ch]] = (vec[chars[ch]] + weight) % prime
        weight = (weight * base) % prime
    return vec


def rref_basis(vectors: list[list[int]], prime: int) -> list[tuple[int, list[int]]]:
    basis: list[tuple[int, list[int]]] = []
    for raw in vectors:
        v = list(raw)
        for pivot, row in basis:
            if v[pivot]:
                f = v[pivot]
                v = [(a - f * b) % prime for a, b in zip(v, row)]
        pivot = next((j for j, x in enumerate(v) if x), None)
        if pivot is None:
            continue
        inv = pow(v[pivot], prime - 2, prime)
        v = [(x * inv) % prime for x in v]
        basis = [
            (pj, [(a - row[pivot] * b) % prime for a, b in zip(row, v)] if row[pivot] else row)
            for pj, row in basis
        ]
        basis.append((pivot, v))
    return basis


def in_span(vec: list[int], basis: list[tuple[int, list[int]]], prime: int) -> bool:
    v = list(vec)
    for pivot, row in basis:
        if v[pivot]:
            f = v[pivot]
            v = [(a - f * b) % prime for a, b in zip(v, row)]
    return not any(v)


def forced_blocks(programs: list[str], k: int, max_bytes: int | None = 160) -> list[str]:
    """Mandatory blocks for threshold k >= 2: cut whenever no eligible token can cross (i, i+1)."""
    if k < 2:
        return list(programs)
    bigram_docs: dict[str, set[int]] = defaultdict(set)
    for idx, s in enumerate(programs):
        for i in range(len(s) - 1):
            bg = s[i : i + 2]
            if max_bytes is None or len(bg.encode("utf-8")) <= max_bytes:
                bigram_docs[bg].add(idx)
    blocks: list[str] = []
    for s in programs:
        if not s:
            continue
        start = 0
        for i in range(len(s) - 1):
            bg = s[i : i + 2]
            if len(bigram_docs.get(bg, ())) < k:
                blocks.append(s[start : i + 1])
                start = i + 1
        blocks.append(s[start:])
    return sorted(set(blocks))


def forced_block_components(programs: list[str], k: int, max_bytes: int | None = 160) -> list[list[str]]:
    """Split a corpus's mandatory blocks (k >= 2) into character-cooccurrence connected components."""
    blocks = forced_blocks(programs, k, max_bytes=max_bytes)
    return split_components(blocks)


def certified_rank_bound(programs: list[str], k: int, max_bytes: int | None = 160, units: list[str] | None = None) -> dict:
    """Position-weighted rank lower bound (program rank for k=1, mandatory-block rank for k>=2), checked under two primes."""
    target_units = units if units is not None else (list(programs) if k == 1 else forced_blocks(programs, k, max_bytes=max_bytes))
    chars = alphabet_index(target_units)
    ranks = []
    for prime, base in PRIMES:
        basis = rref_basis([pos_vector(u, chars, prime, base) for u in target_units], prime)
        ranks.append({"prime": prime, "base": base, "rank": len(basis)})
    # Every prime gives a sound lower bound on Z-rank / dictionary size; max is sound and agreement checks no mod drop.
    bound = max(r["rank"] for r in ranks)
    return {
        "kind": "program-rank" if k == 1 else "mandatory-block-rank",
        "bound": bound,
        "distinctBlocks": len(target_units),
        "primesChecked": ranks,
    }


# ---------------------------------------------------------------------- disjoint-position bound
def position_cover_sets(programs: list[str], tokens: set[str], max_bytes: int | None = 160) -> list[tuple[int, int, frozenset[str]]]:
    """Return [(prog_idx, pos, C_k(prog_idx, pos))] for every character position."""
    out: list[tuple[int, int, frozenset[str]]] = []
    for pidx, s in enumerate(programs):
        n = len(s)
        for pos in range(n):
            lo = 0 if max_bytes is None else max(0, pos - max_bytes + 1)
            cover = []
            for a in range(lo, pos + 1):
                hi = n if max_bytes is None else min(n, a + max_bytes)
                for b in range(pos + 1, hi + 1):
                    sub = s[a:b]
                    if sub in tokens:
                        cover.append(sub)
            out.append((pidx, pos, frozenset(cover)))
    return out


def verify_disjoint_witness(
    programs: list[str],
    witness: list[tuple[int, int]],
    tokens: set[str],
    max_bytes: int | None = 160,
) -> bool:
    """Independently verify that witness cover sets are non-empty and share zero token strings."""
    used: set[str] = set()
    seen_coords: set[tuple[int, int]] = set()
    for pidx, pos in witness:
        if (pidx, pos) in seen_coords:
            raise ValueError(f"Duplicate witness coordinate {(pidx, pos)}")
        seen_coords.add((pidx, pos))
        s = programs[pidx]
        n = len(s)
        lo = 0 if max_bytes is None else max(0, pos - max_bytes + 1)
        cover = {
            s[a:b]
            for a in range(lo, pos + 1)
            for b in range(pos + 1, (n if max_bytes is None else min(n, a + max_bytes)) + 1)
            if s[a:b] in tokens
        }
        if not cover:
            raise ValueError(f"Empty cover set at {(pidx, pos)}")
        overlap = used & cover
        if overlap:
            raise ValueError(f"Witness cover sets share token(s): {sorted(overlap)[:3]}")
        used |= cover
    return True


def disjoint_position_certificate(
    programs: list[str],
    k: int,
    tokens: set[str],
    max_bytes: int | None = 160,
    exact_limit: int = 28,
) -> dict:
    """Compute a verified pairwise-disjoint position witness (exact on small components, greedy on larger ones)."""
    limit_bytes = None if k == 1 else max_bytes
    raw = position_cover_sets(programs, tokens, max_bytes=limit_bytes)
    if any(len(cov) == 0 for _, _, cov in raw):
        bad = next((pidx, pos) for pidx, pos, cov in raw if len(cov) == 0)
        return {"bound": None, "exact": True, "unspellablePosition": {"programIndex": bad[0], "pos": bad[1]}, "witness": []}
    # Deduplicate identical cover sets keeping canonical first coordinate
    unique: list[tuple[frozenset[str], tuple[int, int]]] = []
    seen_cov: set[frozenset[str]] = set()
    for pidx, pos, cov in sorted(raw, key=lambda item: (len(item[2]), item[0], item[1])):
        if cov not in seen_cov:
            seen_cov.add(cov)
            unique.append((cov, (pidx, pos)))

    if len(unique) <= exact_limit:
        best_witness: list[tuple[int, int]] = []

        def grow(start: int, used: frozenset[str], chosen: list[tuple[int, int]]) -> None:
            nonlocal best_witness
            if len(chosen) > len(best_witness):
                best_witness = list(chosen)
            if len(chosen) + (len(unique) - start) <= len(best_witness):
                return
            for j in range(start, len(unique)):
                cov, coord = unique[j]
                if used.isdisjoint(cov):
                    chosen.append(coord)
                    grow(j + 1, used | cov, chosen)
                    chosen.pop()

        grow(0, frozenset(), [])
        verify_disjoint_witness(programs, best_witness, tokens, max_bytes=limit_bytes)
        return {"bound": len(best_witness), "exact": True, "witness": best_witness}

    # Greedy min-cover packing (always sound, independently verified)
    chosen_greedy: list[tuple[int, int]] = []
    used_tokens: set[str] = set()
    for cov, coord in unique:
        if used_tokens.isdisjoint(cov):
            used_tokens |= cov
            chosen_greedy.append(coord)
    verify_disjoint_witness(programs, chosen_greedy, tokens, max_bytes=limit_bytes)
    return {"bound": len(chosen_greedy), "exact": False, "witness": chosen_greedy}


# ---------------------------------------------------------------------- Theorem B parsing test (rule U)
def theorem_b_span_parse_test(programs: list[str], exhaustive_basis_limit: int = 24) -> dict:
    """Test whether candidate span-basis tokens admit a complete non-overlapping parse for every source under U.

    Lemma: If a legal dictionary D of size r = rank(M_T) tiles every program in T, then
    every token t in D must lie in E_span = {t in E_U(T) : v(t) in span(M_T)}, their vectors
    must form a basis of span(M_T), and every source must admit a contiguous non-overlapping
    parse over D.
    """
    chars = alphabet_index(programs)
    tokens = sorted(eligible_tokens(programs, k=1, max_bytes=None), key=lambda t: (len(t), t))
    p1, b1 = PRIMES[0]
    p2, b2 = PRIMES[1]
    basis1 = rref_basis([pos_vector(s, chars, p1, b1) for s in programs], p1)
    basis2 = rref_basis([pos_vector(s, chars, p2, b2) for s in programs], p2)
    rank = max(len(basis1), len(basis2))

    # Necessary condition 1: every program has a proper prefix in span(M_T)
    prefix_cuttable = all(
        any(
            in_span(pos_vector(s[:i], chars, p1, b1), basis1, p1)
            and in_span(pos_vector(s[:i], chars, p2, b2), basis2, p2)
            for i in range(1, len(s))
        )
        for s in programs
    )

    # Necessary condition 2: every program admits a complete non-overlapping parse in E_span
    span_tokens = [
        t for t in tokens
        if in_span(pos_vector(t, chars, p1, b1), basis1, p1)
        and in_span(pos_vector(t, chars, p2, b2), basis2, p2)
    ]
    unparseable_in_span = [s for s in programs if parse_program(s, span_tokens) is None]
    parses_in_span = len(unparseable_in_span) == 0

    result: dict = {
        "programRank": rank,
        "everyProgramHasACuttablePrefix": prefix_cuttable,
        "spanTokenCount": len(span_tokens),
        "spanTokens": span_tokens if len(span_tokens) <= 40 else span_tokens[:40],
        "everyProgramParsesInSpan": parses_in_span,
        "unparseableInSpan": unparseable_in_span,
    }
    if not parses_in_span:
        result["rankAttainable"] = False
        result["certifiedLowerBound"] = rank + 1
        result["reason"] = "at least one source admits no complete non-overlapping parse over eligible span tokens"
        return result

    # Exact basis-parse attainability check when E_span is small enough for exhaustive basis test
    if len(span_tokens) <= exhaustive_basis_limit and rank <= 10:
        for cand in itertools.combinations(span_tokens, rank):
            # Must span all programs (linear independence over F_p) and parse every source
            if len(rref_basis([pos_vector(t, chars, p1, b1) for t in cand], p1)) != rank:
                continue
            if all(parse_program(s, cand) is not None for s in programs):
                verified = verify_construction(programs, list(cand), k=1, max_bytes=None, tokens=set(tokens))
                result["rankAttainable"] = True
                result["certifiedLowerBound"] = rank
                result["attainingConstruction"] = verified
                return result
        result["rankAttainable"] = False
        result["certifiedLowerBound"] = rank + 1
        result["reason"] = "no size-rank basis inside E_span admits a complete non-overlapping parse for every source"
        return result

    result["rankAttainable"] = None
    result["certifiedLowerBound"] = rank
    result["reason"] = "E_span exceeds exhaustive basis search limit; left unresolved"
    return result


# ---------------------------------------------------------------------- construction search (small components)
def find_verified_construction(
    programs: list[str],
    k: int,
    budget: int,
    tokens: set[str],
    max_bytes: int | None = 160,
    exhaustive_token_limit: int = 24,
    exhaustive_budget_limit: int = 9,
) -> dict | None:
    """Return a byte-verified eligible dictionary of size <= budget if found, else None."""
    alpha = sorted(set("".join(programs)))
    all_singletons_eligible = all(ch in tokens for ch in alpha)
    if all_singletons_eligible and len(alpha) <= budget:
        return verify_construction(programs, alpha, k, max_bytes=max_bytes, tokens=tokens)

    # For k = 1, check Theorem B span-basis construction when budget >= program rank
    if k == 1:
        tb = theorem_b_span_parse_test(programs)
        if tb.get("rankAttainable") is True and tb["programRank"] <= budget:
            return tb["attainingConstruction"]

    # Exhaustive search on small components (only returns byte-verified dictionaries)
    ordered = sorted(tokens, key=lambda t: (len(t), t))
    if len(ordered) <= exhaustive_token_limit and budget <= exhaustive_budget_limit:
        for size in range(1, min(budget, len(ordered)) + 1):
            for cand in itertools.combinations(ordered, size):
                if all(parse_program(s, cand) is not None for s in programs):
                    return verify_construction(programs, list(cand), k, max_bytes=max_bytes, tokens=tokens)
    return None


# ---------------------------------------------------------------------- partial coverage (kept strictly separate)
def exact_partial_coverage_curve(programs: list[str], k: int, max_budget: int, max_bytes: int | None = 160) -> list[int]:
    """Exact max programs spelled at each budget 0..max_budget for a tiny component."""
    tokens = sorted(eligible_tokens(programs, k, max_bytes=max_bytes), key=lambda t: (len(t), t))
    curve = [0]
    for b in range(1, max_budget + 1):
        best = curve[-1]
        if best < len(programs) and b <= len(tokens):
            for cand in itertools.combinations(tokens, b):
                got = sum(parse_program(s, cand) is not None for s in programs)
                if got > best:
                    best = got
                    if best == len(programs):
                        break
        curve.append(best)
    return curve


def allocate_partial_coverage(component_curves: list[list[int]], shared_budget: int) -> dict:
    """Allocate a shared slot budget across components via exact knapsack DP.

    Never adds partial coverage as though every component received the full budget.
    """
    dp = [0] * (shared_budget + 1)
    choice: list[list[int]] = [[] for _ in range(shared_budget + 1)]
    for curve in component_curves:
        new_dp = [-1] * (shared_budget + 1)
        new_choice: list[list[int]] = [[] for _ in range(shared_budget + 1)]
        for total in range(shared_budget + 1):
            for take in range(min(total, len(curve) - 1) + 1):
                val = dp[total - take] + curve[take]
                if val > new_dp[total]:
                    new_dp[total] = val
                    new_choice[total] = choice[total - take] + [take]
        dp = new_dp
        choice = new_choice
    return {
        "sharedBudget": shared_budget,
        "maxProgramsSpelled": dp[shared_budget],
        "budgetAllocationByComponent": choice[shared_budget],
    }


# ---------------------------------------------------------------------- main tri-state diagnostic
def diagnose_full_corpus(
    programs: list[str],
    k: int,
    budget: int,
    max_bytes: int | None = 160,
    allow_construction_search: bool = True,
) -> dict:
    """Tri-state full-corpus capacity diagnostic: IMPOSSIBLE, FEASIBLE, or UNRESOLVED.

    Never reports a rank bound or upper bound as a construction.
    """
    tracemalloc.start()
    t0 = time.perf_counter()
    try:
        components = split_components(programs)
        whole = set(programs)
        alphabet = sorted(set("".join(programs)))
        all_singletons_eligible = all(ch not in whole for ch in alphabet)

        comp_reports = []
        total_lb = 0
        unspellable = False
        per_comp_tokens: list[set[str]] = []

        for idx, comp in enumerate(components):
            comp_alpha = sorted(set("".join(comp)))
            comp_singletons_ok = all(ch not in set(comp) for ch in comp_alpha)
            tokens = eligible_tokens(comp, k, max_bytes=max_bytes)
            per_comp_tokens.append(tokens)

            rank_cert = certified_rank_bound(comp, k, max_bytes=max_bytes)
            disj_cert = disjoint_position_certificate(comp, k, tokens, max_bytes=max_bytes)
            block_subreports = []
            block_split_lb = None
            if disj_cert["bound"] is None:
                unspellable = True
                comp_lb = None
                stronger = "unspellable-position"
            else:
                # For k = 1, also check Theorem B span-token parseability as a sound +1 lift when E_span fails
                tb_lift = None
                if k == 1:
                    tb = theorem_b_span_parse_test(comp)
                    if tb["certifiedLowerBound"] > rank_cert["bound"]:
                        tb_lift = tb
                rank_val = tb_lift["certifiedLowerBound"] if tb_lift else rank_cert["bound"]
                disj_val = disj_cert["bound"]
                comp_lb = max(rank_val, disj_val)

                # For k >= 2, forced-block character components cannot share any eligible token (no token crosses a forced cut).
                # Filter corpus-wide eligible tokens per block component (preserving true program doc_freq and whole exclusions).
                if k >= 2:
                    fb_comps = forced_block_components(comp, k, max_bytes=max_bytes)
                    if len(fb_comps) > 1:
                        fb_sum = 0
                        fb_ok = True
                        for fb_idx, fb_units in enumerate(fb_comps):
                            fb_chars = set("".join(fb_units))
                            fb_tokens = {t for t in tokens if set(t) <= fb_chars}
                            fb_rank = certified_rank_bound(comp, k, max_bytes=max_bytes, units=fb_units)
                            fb_disj = disjoint_position_certificate(fb_units, k, fb_tokens, max_bytes=max_bytes)
                            if fb_disj["bound"] is None:
                                fb_ok = False
                                break
                            fb_lb = max(fb_rank["bound"], fb_disj["bound"])
                            fb_sum += fb_lb
                            block_subreports.append({
                                "blockComponentIndex": fb_idx,
                                "blocks": fb_units,
                                "alphabetSize": len(fb_chars),
                                "blockRank": fb_rank["bound"],
                                "disjointBound": fb_disj["bound"],
                                "lowerBound": fb_lb,
                            })
                        if fb_ok and fb_sum > comp_lb:
                            block_split_lb = fb_sum
                            comp_lb = fb_sum

                if block_split_lb is not None:
                    stronger = "forced-block-components"
                elif tb_lift and rank_val >= disj_val:
                    stronger = "span-parse-obstruction"
                elif rank_val > disj_val:
                    stronger = rank_cert["kind"]
                elif disj_val > rank_val:
                    stronger = "disjoint-position"
                else:
                    stronger = f"tie({rank_cert['kind']},disjoint-position)"
                total_lb += comp_lb

            comp_reports.append({
                "componentIndex": idx,
                "programs": comp,
                "alphabetSize": len(comp_alpha),
                "allSingletonsEligible": comp_singletons_ok,
                "rankCertificate": rank_cert,
                "disjointCertificate": disj_cert,
                "forcedBlockSubcomponents": block_subreports,
                "componentLowerBound": comp_lb,
                "strongerBound": stronger,
            })

        # Threshold monotonicity reuse certificate: valid ONLY when k >= 2, all singletons eligible, and lb == |Sigma|
        monotone_saturation = None
        if not unspellable and k >= 2 and all_singletons_eligible and total_lb == len(alphabet):
            monotone_saturation = {
                "reusableForAllThresholdsAtLeast": k,
                "exactMinimum": len(alphabet),
                "allSingletonsEligible": True,
                "basis": "increasing k only shrinks eligible tokens and adds forced cuts, so certified lb stays at |Sigma|",
            }

        # Case 1: IMPOSSIBLE
        if unspellable or total_lb > budget:
            verdict = {
                "status": "IMPOSSIBLE",
                "rule": "U" if k == 1 else f"W{k}",
                "budget": budget,
                "alphabetSize": len(alphabet),
                "allSingletonsEligible": all_singletons_eligible,
                "componentCount": len(components),
                "certifiedLowerBound": None if unspellable else total_lb,
                "monotoneSaturation": monotone_saturation,
                "components": comp_reports,
            }
        else:
            # Attempt verified byte-exact construction across components
            verified_dict: list[str] | None = None
            verified_parses: dict[str, list[str]] = {}
            if all_singletons_eligible and len(alphabet) <= budget:
                v = verify_construction(programs, alphabet, k, max_bytes=max_bytes)
                verified_dict = v["dictionary"]
                verified_parses = dict(zip(programs, v["parses"]))
            elif allow_construction_search:
                # Find minimal verified construction per component up to remaining budget slack
                comp_dicts: list[list[str]] = []
                slack = budget - total_lb
                ok_all = True
                for comp, report, tokens in zip(components, comp_reports, per_comp_tokens):
                    comp_lb = report["componentLowerBound"]
                    found = find_verified_construction(comp, k, comp_lb + slack, tokens, max_bytes=max_bytes)
                    if found is None:
                        ok_all = False
                        break
                    comp_dicts.append(found["dictionary"])
                    slack -= len(found["dictionary"]) - comp_lb
                    if slack < 0:
                        ok_all = False
                        break
                if ok_all:
                    combined = sorted(set().union(*comp_dicts))
                    if len(combined) <= budget:
                        v = verify_construction(programs, combined, k, max_bytes=max_bytes)
                        verified_dict = v["dictionary"]
                        verified_parses = dict(zip(programs, v["parses"]))

            if verified_dict is not None:
                verdict = {
                    "status": "FEASIBLE",
                    "rule": "U" if k == 1 else f"W{k}",
                    "budget": budget,
                    "alphabetSize": len(alphabet),
                    "allSingletonsEligible": all_singletons_eligible,
                    "componentCount": len(components),
                    "certifiedLowerBound": total_lb,
                    "construction": {
                        "dictionarySize": len(verified_dict),
                        "dictionary": verified_dict,
                        "parses": verified_parses,
                        "byteExactVerified": True,
                    },
                    "monotoneSaturation": monotone_saturation,
                    "components": comp_reports,
                }
            else:
                ub = len(alphabet) if all_singletons_eligible else None
                verdict = {
                    "status": "UNRESOLVED",
                    "rule": "U" if k == 1 else f"W{k}",
                    "budget": budget,
                    "alphabetSize": len(alphabet),
                    "allSingletonsEligible": all_singletons_eligible,
                    "componentCount": len(components),
                    "certifiedLowerBound": total_lb,
                    "certifiedUpperBound": ub,
                    "interval": [total_lb, ub],
                    "monotoneSaturation": monotone_saturation,
                    "components": comp_reports,
                }

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        _, peak_bytes = tracemalloc.get_traced_memory()
        verdict["measuredCost"] = {"elapsedMs": elapsed_ms, "peakAllocKiB": round(peak_bytes / 1024.0, 2)}
        return verdict
    finally:
        tracemalloc.stop()


# ---------------------------------------------------------------------- reproducible control suite CLI
def run_controls_suite() -> list[dict]:
    cases = [
        ("aligned_repeats_W2_K2", ["abc", "abab"], 2, 2, True),
        ("shifted_repeats_W2_K2", ["abc", "baba"], 2, 2, True),
        ("shifted_repeats_W2_K3", ["abc", "baba"], 2, 3, True),
        ("no_circuit_jump_U_K3", ["ab", "ac", "bc"], 1, 3, True),
        ("grid_2x2_U_K3", ["ax", "ay", "bx", "by"], 1, 3, True),
        ("block_grid_W2_K3", ["axby", "byax", "aybx", "bxay"], 2, 3, True),
        ("block_grid_U_K3", ["axby", "byax", "aybx", "bxay"], 1, 3, True),
        ("overlap_non_tiling_W2_K4", ["abcd", "abce", "fbcd"], 2, 4, True),
        ("seven_program_union_W2_K8", ["abd", "abe", "fbd", "pxqy", "qypx", "pyqx", "qxpy"], 2, 8, True),
        ("seven_program_union_W2_K9", ["abd", "abe", "fbd", "pxqy", "qypx", "pyqx", "qxpy"], 2, 9, True),
        ("connected_bridge_6prog_W2_K7", ["abd", "fbd", "abpxqy", "qypx", "pyqx", "qxpy"], 2, 7, True),
        ("connected_bridge_6prog_W2_K8", ["abd", "fbd", "abpxqy", "qypx", "pyqx", "qxpy"], 2, 8, True),
        ("unresolved_interval_demo_W2_K2", ["abc", "abab"], 2, 2, False),
    ]
    reports = []
    for name, progs, k, budget, allow_search in cases:
        res = diagnose_full_corpus(progs, k, budget, allow_construction_search=allow_search)
        reports.append({"name": name, "programs": progs, "verdict": res})
    return reports


def parse_rule_arg(rule_str: str) -> int:
    text = rule_str.strip().upper()
    if text in ("U", "K1", "1"):
        return 1
    if text.startswith("W") and text[1:].isdigit() and int(text[1:]) >= 2:
        return int(text[1:])
    raise ValueError(f"Unsupported rule {rule_str!r}; use U or W2, W3, ...")


def format_verdict_line(name: str, v: dict) -> str:
    lb = "-" if v["certifiedLowerBound"] is None else str(v["certifiedLowerBound"])
    if v["status"] == "FEASIBLE":
        detail = f"dict={v['construction']['dictionary']} (byte-exact)"
    elif v["status"] == "IMPOSSIBLE":
        reasons = [f"c{c['componentIndex']}:{c['strongerBound']}={c['componentLowerBound']}" for c in v["components"]]
        detail = "cert=" + "+".join(reasons)
    else:
        detail = f"interval={v['interval']} (no construction searched/found)"
    if v.get("monotoneSaturation"):
        detail += f" [sat>=W{v['monotoneSaturation']['reusableForAllThresholdsAtLeast']}]"
    c = v["measuredCost"]
    return (
        f"{name:32s} {v['rule']:4s} {v['budget']:2d} {v['componentCount']:4d} {lb:>3s} "
        f"{v['status']:10s} {c['elapsedMs']:7.2f} {c['peakAllocKiB']:7.1f}  {detail}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="BITS Phase 3 tri-state capacity diagnostic")
    parser.add_argument("--controls", action="store_true", help="Run reproducible control suite (human-readable table)")
    parser.add_argument("--corpus", type=str, default=None, help="JSON file containing a list of program strings or {'programs': [...]}")
    parser.add_argument("--programs", nargs="+", default=None, help="Inline program strings to diagnose")
    parser.add_argument("--rule", type=str, default="W2", help="Eligibility rule: U or W2, W3, ...")
    parser.add_argument("--budget", type=int, default=None, help="Slot budget K (required with --corpus or --programs)")
    parser.add_argument("--no-search", action="store_true", help="Skip exhaustive construction search (still checks singletons and Theorem B span basis)")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    args = parser.parse_args()

    if args.corpus is not None or args.programs is not None:
        if args.budget is None:
            parser.error("--budget K is required with --corpus or --programs")
        if args.corpus is not None:
            raw = json.loads(open(args.corpus, encoding="utf-8").read())
            progs = raw["programs"] if isinstance(raw, dict) else raw
            label = args.corpus
        else:
            progs = args.programs
            label = "inline"
        k = parse_rule_arg(args.rule)
        verdict = diagnose_full_corpus(progs, k, args.budget, allow_construction_search=not args.no_search)
        if args.json:
            print(json.dumps(verdict, indent=2))
        else:
            print(f"{'Case':32s} {'Rule':4s} {'K':>2s} {'Comp':>4s} {'LB':>3s} {'Status':10s} {'ms':>7s} {'KiB':>7s}  Detail")
            print("-" * 110)
            print(format_verdict_line(label[:32], verdict))
        return 0

    reports = run_controls_suite()
    if args.json:
        print(json.dumps(reports, indent=2))
        return 0

    print(f"{'Case':32s} {'Rule':4s} {'K':>2s} {'Comp':>4s} {'LB':>3s} {'Status':10s} {'ms':>7s} {'KiB':>7s}  Detail")
    print("-" * 110)
    for item in reports:
        print(format_verdict_line(item["name"], item["verdict"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
