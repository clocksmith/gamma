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
    # k >= 2: single characters (not whole) + multi-char substrings <= max_bytes in >= k programs.
    # Use suffix-array adjacent distinct-program LCP to enumerate only actually shared substrings (exact).
    alpha = set().union(*(set(s) for s in programs)) - whole
    items = [(s[i:], pidx, i) for pidx, s in enumerate(programs) for i in range(len(s))]
    items.sort(key=lambda item: item[0])

    def lcp_len(a: str, b: str) -> int:
        m = min(len(a), len(b))
        j = 0
        while j < m and a[j] == b[j]:
            j += 1
        return j

    wit: dict[tuple[int, int], int] = {(pidx, i): 0 for _, pidx, i in items}
    prev_diff = prev_suf = None
    prev_pid = None
    for suf, pidx, i in items:
        if prev_pid is not None and prev_pid != pidx:
            prev_diff = prev_suf
        if prev_diff is not None:
            v = lcp_len(suf, prev_diff)
            if v > wit[pidx, i]:
                wit[pidx, i] = v
        prev_suf, prev_pid = suf, pidx

    next_diff = next_suf = None
    next_pid = None
    for suf, pidx, i in reversed(items):
        if next_pid is not None and next_pid != pidx:
            next_diff = next_suf
        if next_diff is not None:
            v = lcp_len(suf, next_diff)
            if v > wit[pidx, i]:
                wit[pidx, i] = v
        next_suf, next_pid = suf, pidx

    docs: dict[str, set[int]] = defaultdict(set)
    for pidx, s in enumerate(programs):
        n = len(s)
        for a in range(n):
            w = wit[pidx, a]
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
                    docs[sub].add(pidx)
    return alpha | {sub for sub, dset in docs.items() if len(dset) >= k}


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


def is_token_eligible(
    entry: str,
    programs: list[str],
    k: int,
    whole: set[str] | None = None,
    max_bytes: int | None = 160,
) -> bool:
    """Exact single-token eligibility check under U (k=1) or W_k (k>=2) without enumerating all substrings."""
    if not entry:
        return False
    w = set(programs) if whole is None else whole
    if entry in w:
        return False
    if k == 1:
        return any(entry in s for s in programs)
    if len(entry) == 1:
        return any(entry in s for s in programs)
    if max_bytes is not None and len(entry.encode("utf-8")) > max_bytes:
        return False
    count = 0
    for s in programs:
        if entry in s:
            count += 1
            if count >= k:
                return True
    return False


def suffix_shared_lengths(programs: list[str], k: int, max_bytes: int | None = 160) -> list[list[int]]:
    """Exact maximum length L (<= max_bytes UTF-8 bytes) starting at each (pidx, i) that appears in >= k distinct programs.

    Uses a bounded-slice suffix array (O(N log N) time, O(N) memory) so long shared docstrings
    never blow up memory. Exact for all k >= 2.
    """
    if k < 2:
        return [[len(s) - i for i in range(len(s))] for s in programs]
    cap = None if max_bytes is None else max_bytes
    items: list[tuple[str, int, int]] = []
    for pidx, s in enumerate(programs):
        n = len(s)
        if cap is None:
            for i in range(n):
                items.append((s[i:], pidx, i))
        else:
            for i in range(n):
                items.append((s[i : i + cap], pidx, i))
    items.sort(key=lambda item: item[0])
    m = len(items)
    wit = [[0] * len(s) for s in programs]
    if m == 0:
        return wit

    def lcp_len(a: str, b: str) -> int:
        lim = min(len(a), len(b))
        j = 0
        while j < lim and a[j] == b[j]:
            j += 1
        return j

    if k == 2:
        prev_diff = prev_suf = None
        prev_pid = None
        for suf, pidx, i in items:
            if prev_pid is not None and prev_pid != pidx:
                prev_diff = prev_suf
            if prev_diff is not None:
                v = lcp_len(suf, prev_diff)
                if v > wit[pidx][i]:
                    wit[pidx][i] = v
            prev_suf, prev_pid = suf, pidx

        next_diff = next_suf = None
        next_pid = None
        for suf, pidx, i in reversed(items):
            if next_pid is not None and next_pid != pidx:
                next_diff = next_suf
            if next_diff is not None:
                v = lcp_len(suf, next_diff)
                if v > wit[pidx][i]:
                    wit[pidx][i] = v
            next_suf, next_pid = suf, pidx
    else:
        # Exact for all k >= 3 via DSU merging adjacent ranks in descending LCP order
        adj = [(lcp_len(items[j][0], items[j + 1][0]), j) for j in range(m - 1)]
        adj.sort(reverse=True)
        parent = list(range(m))
        p_sets: list[set[int]] = [{items[j][1]} for j in range(m)]
        unstamped: list[list[int]] = [[j] for j in range(m)]

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for lcp, j in adj:
            if lcp == 0:
                break
            ra, rb = find(j), find(j + 1)
            if ra == rb:
                continue
            if len(p_sets[ra]) < len(p_sets[rb]):
                ra, rb = rb, ra
            parent[rb] = ra
            p_sets[ra] |= p_sets[rb]
            p_sets[rb].clear()
            if unstamped[rb]:
                unstamped[ra].extend(unstamped[rb])
                unstamped[rb].clear()
            if len(p_sets[ra]) >= k and unstamped[ra]:
                for r in unstamped[ra]:
                    _, pidx, i = items[r]
                    wit[pidx][i] = lcp
                unstamped[ra].clear()

    # Enforce exact UTF-8 byte cap when non-ASCII characters appear
    if max_bytes is not None:
        for pidx, s in enumerate(programs):
            row = wit[pidx]
            for i, w in enumerate(row):
                if w > 0:
                    sub = s[i : i + w]
                    if len(sub.encode("utf-8")) > max_bytes:
                        b = 0
                        new_w = 0
                        for ch in sub:
                            cb = len(ch.encode("utf-8"))
                            if b + cb > max_bytes:
                                break
                            b += cb
                            new_w += 1
                        row[i] = new_w
    return wit


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
    whole = set(programs)
    for entry in dictionary:
        if tokens is not None:
            ok = entry in tokens
        else:
            ok = is_token_eligible(entry, programs, k, whole=whole, max_bytes=max_bytes)
        if not ok:
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


def _nullspace_basis_and_support(
    basis: list[tuple[int, list[int]]], num_cols: int, prime: int
) -> tuple[list[list[int]], set[int]]:
    pivots = {p for p, _ in basis}
    free_cols = [j for j in range(num_cols) if j not in pivots]
    null_vecs: list[list[int]] = []
    for fc in free_cols:
        z = [0] * num_cols
        z[fc] = 1
        for p, row in basis:
            z[p] = (-row[fc]) % prime
        null_vecs.append(z)
    support = {j for j in range(num_cols) if any(z[j] != 0 for z in null_vecs)}
    return null_vecs, support


def nullspace_kernel_certificate(
    programs: list[str],
    k: int,
    max_bytes: int | None = 160,
    max_nodes: int = 30000,
) -> dict:
    """Exact Nullspace-Kernel Theorem check for rank attainment under U (k=1) or W_k (k>=2).

    Let M_B be the position-weighted forced-block incidence matrix over every rank-attaining
    field F_p, with rank r = |Sigma| - d, nullspace support S_free = union supp(ker M_B),
    determined alphabet S_det = Sigma \\ S_free, and k_free = |S_free| - d.

    Theorem:
      1. (Sufficiency) If all singletons in S_det are eligible and there exists T subset E_span^free
         of size |T| <= k_free such that S_det U T parses every forced block touching S_free, then
         D = S_det U T is an exact optimal dictionary of size r = OPT.
      2. (Necessity) Let B_det* be the forced D_det-segments (maximal runs of forced blocks not
         covered by any occurrence of E_span^free whose left and right boundaries are block edges
         or characters of S_free), with rank r_det* and slack Delta_det* = |S_det| - r_det*.
         Any legal dictionary of size r must contain a subset T subset E_span^free of size
         <= k_free + Delta_det* such that S_det U T parses B_free. Hence if no such T exists,
         OPT >= r + 1 is certified IMPOSSIBLE at budget r.
    """
    blocks = list(programs) if k == 1 else forced_blocks(programs, k, max_bytes=max_bytes)
    chars = alphabet_index(programs)
    idx_to_ch = {i: ch for ch, i in chars.items()}
    num_cols = len(chars)
    whole = set(programs)
    all_singletons_ok = all(ch not in whole for ch in chars)

    field_data = []
    for prime, base in PRIMES:
        basis = rref_basis([pos_vector(b, chars, prime, base) for b in blocks], prime)
        null_vecs, supp = _nullspace_basis_and_support(basis, num_cols, prime)
        field_data.append((prime, base, basis, null_vecs, supp))
    max_rank = max(len(b) for _, _, b, _, _ in field_data)
    attaining = [fd for fd in field_data if len(fd[2]) == max_rank]
    d = num_cols - max_rank
    s_free_idx = set().union(*(fd[4] for fd in attaining)) if d > 0 else set()
    s_free = sorted(idx_to_ch[i] for i in s_free_idx)
    s_free_set = set(s_free)
    s_det = sorted(idx_to_ch[i] for i in range(num_cols) if i not in s_free_idx)
    k_free = len(s_free) - d

    if d == 0:
        return {
            "status": "SATURATED",
            "rank": max_rank,
            "nullity": 0,
            "sFree": [],
            "kFree": 0,
            "deltaDetStar": 0,
            "certifiedLowerBound": max_rank,
            "attainingConstruction": None,
        }

    wit = (
        [[len(s) - i for i in range(len(s))] for s in programs]
        if k == 1
        else suffix_shared_lengths(programs, k, max_bytes=max_bytes)
    )
    seen: set[str] = set()
    span_free: list[str] = []
    for pidx, s in enumerate(programs):
        row = wit[pidx]
        for a, w in enumerate(row):
            if w < 2:
                continue
            vecs = [[0] * num_cols for _ in attaining]
            weights = [1] * len(attaining)
            has_free = False
            for off in range(w):
                ch = s[a + off]
                ci = chars[ch]
                if ci in s_free_idx:
                    has_free = True
                for fi, (prime, base, _, _, _) in enumerate(attaining):
                    vecs[fi][ci] = (vecs[fi][ci] + weights[fi]) % prime
                    weights[fi] = (weights[fi] * base) % prime
                if off >= 1 and has_free:
                    ok = True
                    for fi, (prime, _, _, null_vecs, _) in enumerate(attaining):
                        vf = vecs[fi]
                        for z in null_vecs:
                            if sum(vf[j] * z[j] for j in s_free_idx) % prime != 0:
                                ok = False
                                break
                        if not ok:
                            break
                    if ok:
                        sub = s[a : a + off + 1]
                        if sub not in seen and sub not in whole:
                            seen.add(sub)
                            span_free.append(sub)

    # Airtight forced D_det segments B_det*: runs not covered by any occurrence of E_span^free
    # whose left and right boundaries are block boundaries or characters of S_free.
    by_first: dict[str, list[str]] = defaultdict(list)
    for tok in span_free:
        by_first[tok[0]].append(tok)
    b_det_star: set[str] = set()
    for b in blocks:
        n = len(b)
        covered = [False] * n
        for i in range(n):
            for tok in by_first.get(b[i], ()):
                tlen = len(tok)
                if i + tlen <= n and b.startswith(tok, i):
                    for j in range(i, i + tlen):
                        covered[j] = True
        i = 0
        while i < n:
            if covered[i]:
                i += 1
                continue
            j = i
            while j < n and not covered[j]:
                j += 1
            left_ok = (i == 0) or (b[i - 1] in s_free_set)
            right_ok = (j == n) or (b[j] in s_free_set)
            if left_ok and right_ok:
                b_det_star.add(b[i:j])
            i = j

    det_chars = {ch: i for i, ch in enumerate(s_det)}
    r_det = 0
    if s_det and b_det_star:
        for prime, base in PRIMES:
            vecs = [pos_vector(seg, det_chars, prime, base) for seg in b_det_star if all(ch in det_chars for ch in seg)]
            r_det = max(r_det, len(rref_basis(vecs, prime)))
    delta_det = len(s_det) - r_det
    max_t_for_rank = k_free + delta_det

    b_free = [b for b in blocks if any(ch in s_free_set for ch in b)]
    occ_id: dict[tuple[int, int], int] = {}
    for bi, b in enumerate(b_free):
        for pos, ch in enumerate(b):
            if ch in s_free_set:
                occ_id[(bi, pos)] = len(occ_id)
    full_mask = (1 << len(occ_id)) - 1

    mask_to_toks: dict[int, list[str]] = defaultdict(list)
    for tok in span_free:
        m = 0
        tlen = len(tok)
        for bi, b in enumerate(b_free):
            st = 0
            while True:
                idx = b.find(tok, st)
                if idx == -1:
                    break
                for pos in range(idx, idx + tlen):
                    oid = occ_id.get((bi, pos))
                    if oid is not None:
                        m |= 1 << oid
                st = idx + 1
        if m:
            mask_to_toks[m].append(tok)

    # Exact lossless deduplication: if tok1 is a substring of tok2 (tok2 = u + tok1 + v) such that
    # NEITHER u NOR v contains any character of S_free, then every occurrence of tok2 in any parse
    # can be replaced in-place by singletons(u) + [tok1] + singletons(v) with zero overlap risk.
    def _has_sdet_only_flanks(tok1: str, tok2: str) -> bool:
        start = 0
        t1_len = len(tok1)
        while True:
            idx = tok2.find(tok1, start)
            if idx == -1:
                return False
            if not any(ch in s_free_set for ch in tok2[:idx]) and not any(
                ch in s_free_set for ch in tok2[idx + t1_len :]
            ):
                return True
            start = idx + 1

    items: list[tuple[int, str]] = []
    for m, toks in mask_to_toks.items():
        toks.sort(key=lambda t: (len(t), t))
        kept: list[str] = []
        for t in toks:
            if not any(_has_sdet_only_flanks(prev, t) for prev in kept):
                kept.append(t)
        for t in kept:
            items.append((m, t))
    items.sort(key=lambda kv: (-kv[0].bit_count(), len(kv[1]), kv[1]))

    def find_cover(limit_t: int, relax_whole: bool = False) -> tuple[list[str] | None, bool]:
        found: list[str] | None = None
        nodes = 0
        aborted = False
        s_det_pool = list(s_det) if relax_whole else [ch for ch in s_det if ch not in whole]

        def search(need_mask: int, chosen_idxs: list[int]) -> None:
            nonlocal found, nodes, aborted
            if found is not None or aborted:
                return
            nodes += 1
            if nodes > max_nodes:
                aborted = True
                return
            if need_mask == 0:
                cand_dict = s_det_pool + [items[i][1] for i in chosen_idxs]
                bad_block = next((b for b in b_free if parse_program(b, cand_dict) is None), None)
                if bad_block is None:
                    found = cand_dict
                    return
                # Overlap conflict: all S_free bits were covered, yet bad_block failed non-overlapping parse.
                # Compute DP reachability on bad_block under cand_dict; every valid extension MUST add a
                # frontier token crossing from reach[a]==True to reach[b]==False (100% sound & complete).
                if len(chosen_idxs) >= limit_t:
                    return
                bn = len(bad_block)
                reach = [False] * (bn + 1)
                reach[0] = True
                by_first_c: dict[str, list[str]] = defaultdict(list)
                for tok in cand_dict:
                    if tok:
                        by_first_c[tok[0]].append(tok)
                for pos in range(bn):
                    if not reach[pos]:
                        continue
                    for tok in by_first_c.get(bad_block[pos], ()):
                        end = pos + len(tok)
                        if end <= bn and not reach[end] and bad_block.startswith(tok, pos):
                            reach[end] = True
                chosen_set = set(chosen_idxs)
                for i, (_m, tok) in enumerate(items):
                    if i in chosen_set:
                        continue
                    tlen = len(tok)
                    st = 0
                    crosses_frontier = False
                    while True:
                        idx = bad_block.find(tok, st)
                        if idx == -1:
                            break
                        if reach[idx] and not reach[idx + tlen]:
                            crosses_frontier = True
                            break
                        st = idx + 1
                    if crosses_frontier:
                        search(0, chosen_idxs + [i])
                        if found is not None or aborted:
                            return
                return
            if len(chosen_idxs) >= limit_t:
                return
            best_cands: list[int] | None = None
            tmp = need_mask
            while tmp:
                lsb = tmp & -tmp
                tmp ^= lsb
                cands = [i for i in range(len(items)) if i not in chosen_idxs and (items[i][0] & lsb)]
                if best_cands is None or len(cands) < len(best_cands):
                    best_cands = cands
                    if len(best_cands) == 0:
                        return
            for i in best_cands or ():
                search(need_mask & ~items[i][0], chosen_idxs + [i])
                if found is not None or aborted:
                    return

        search(full_mask, [])
        return found, aborted

    # 1. Exact sufficiency check for size r: |T| <= k_free with S_det singletons
    if all(ch not in whole for ch in s_det):
        found_r, _ = find_cover(k_free, relax_whole=False)
        if found_r is not None:
            verified = verify_construction(programs, found_r, k, max_bytes=max_bytes)
            return {
                "status": "RANK_ATTAINED",
                "rank": max_rank,
                "nullity": d,
                "sFree": s_free,
                "kFree": k_free,
                "deltaDetStar": delta_det,
                "spanFreeTokenCount": len(span_free),
                "uniqueMaskCount": len(items),
                "certifiedLowerBound": max_rank,
                "attainingConstruction": verified,
            }

    # 2. Exact necessity check for size r: can ANY |T| <= k_free + delta_det* parse B_free with S_det?
    found_nec, aborted_nec = find_cover(max_t_for_rank, relax_whole=True)
    if not aborted_nec and found_nec is None:
        return {
            "status": "RANK_UNATTAINABLE",
            "rank": max_rank,
            "nullity": d,
            "sFree": s_free,
            "kFree": k_free,
            "deltaDetStar": delta_det,
            "spanFreeTokenCount": len(span_free),
            "uniqueMaskCount": len(items),
            "certifiedLowerBound": max_rank + 1,
            "attainingConstruction": None,
        }

    return {
        "status": "UNRESOLVED",
        "rank": max_rank,
        "nullity": d,
        "sFree": s_free,
        "kFree": k_free,
        "deltaDetStar": delta_det,
        "spanFreeTokenCount": len(span_free),
        "uniqueMaskCount": len(items),
        "certifiedLowerBound": max_rank,
        "attainingConstruction": None,
    }


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
    """Return [(prog_idx, pos, C_k(prog_idx, pos))] for every character position.

    Uses prefix-length index over `tokens` so only actual token matches are visited (exact).
    """
    by_first: dict[str, list[str]] = defaultdict(list)
    for tok in tokens:
        if tok:
            by_first[tok[0]].append(tok)
    out: list[tuple[int, int, frozenset[str]]] = []
    for pidx, s in enumerate(programs):
        n = len(s)
        covers: list[list[str]] = [[] for _ in range(n)]
        for a in range(n):
            cands = by_first.get(s[a])
            if not cands:
                continue
            for tok in cands:
                tlen = len(tok)
                if a + tlen <= n and s.startswith(tok, a):
                    for pos in range(a, a + tlen):
                        covers[pos].append(tok)
        for pos in range(n):
            out.append((pidx, pos, frozenset(covers[pos])))
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


def verify_disjoint_witness_direct(
    programs: list[str],
    witness: list[tuple[int, int]],
    k: int,
    wit: list[list[int]],
    whole: set[str],
    max_bytes: int | None = 160,
) -> bool:
    """Independently verify witness cover sets using exact suffix shared lengths `wit` (zero full-corpus token enumeration)."""
    used: set[str] = set()
    seen_coords: set[tuple[int, int]] = set()
    for pidx, pos in witness:
        if (pidx, pos) in seen_coords:
            raise ValueError(f"Duplicate witness coordinate {(pidx, pos)}")
        seen_coords.add((pidx, pos))
        s = programs[pidx]
        n = len(s)
        row = wit[pidx]
        cover: set[str] = set()
        if s[pos] not in whole:
            cover.add(s[pos])
        lo = 0 if max_bytes is None else max(0, pos - max_bytes + 1)
        for a in range(lo, pos + 1):
            w = row[a]
            if w < 2 or a + w <= pos:
                continue
            for b in range(max(a + 2, pos + 1), a + w + 1):
                sub = s[a:b]
                if sub not in whole:
                    cover.add(sub)
        if not cover:
            raise ValueError(f"Empty cover set at {(pidx, pos)}")
        overlap = used & cover
        if overlap:
            raise ValueError(f"Witness cover sets share token(s): {sorted(overlap)[:3]}")
        used |= cover
    return True


def disjoint_position_certificate_fast(
    programs: list[str],
    k: int,
    max_bytes: int | None = 160,
    max_cover_size: int = 256,
) -> dict:
    """Bounded-memory verified disjoint-position lower bound for large k>=2 corpora.

    Computes exact suffix shared lengths O(N log N), skips bloated docstring positions (> max_cover_size
    covering tokens) as packing candidates (never omits tokens from any verified cover set), and
    independently verifies pairwise disjointness over ALL eligible tokens <= max_bytes.
    """
    whole = set(programs)
    wit = suffix_shared_lengths(programs, k, max_bytes=max_bytes)

    # First check unspellable positions and compute exact cover-set size upper bound per position via sweep
    # For each position (pidx, pos), count how many (a, b) with a <= pos < b <= a + wit[pidx][a] (b-a >= 2) cover it.
    candidates: list[tuple[int, int, int]] = []  # (approx_cover_size, pidx, pos)
    seen_forced_chars: set[str] = set()
    for pidx, s in enumerate(programs):
        n = len(s)
        row = wit[pidx]
        # Exact O(n) forced-singleton detection via max_reach
        max_reach = 0
        for pos in range(n):
            w = row[pos]
            if w >= 2 and pos + w > max_reach:
                max_reach = pos + w
            has_multi = max_reach > pos
            ch = s[pos]
            if not has_multi:
                if ch in whole:
                    return {
                        "bound": None,
                        "exact": True,
                        "unspellablePosition": {"programIndex": pidx, "pos": pos},
                        "witness": [],
                    }
                if ch not in seen_forced_chars:
                    seen_forced_chars.add(ch)
                    candidates.append((1, pidx, pos))
            else:
                # Compute cheap exact cover count only when local shared span is modest
                lo = 0 if max_bytes is None else max(0, pos - max_bytes + 1)
                est = 1 if ch not in whole else 0
                too_big = False
                for a in range(lo, pos + 1):
                    wa = row[a]
                    if wa >= 2 and a + wa > pos:
                        est += (a + wa) - max(a + 1, pos)
                        if est > max_cover_size:
                            too_big = True
                            break
                if not too_big:
                    candidates.append((est, pidx, pos))

    candidates.sort()
    chosen: list[tuple[int, int]] = []
    used_tokens: set[str] = set()
    for _, pidx, pos in candidates:
        s = programs[pidx]
        row = wit[pidx]
        cover: set[str] = set()
        if s[pos] not in whole:
            cover.add(s[pos])
        lo = 0 if max_bytes is None else max(0, pos - max_bytes + 1)
        conflict = False
        if cover and not used_tokens.isdisjoint(cover):
            continue
        for a in range(lo, pos + 1):
            wa = row[a]
            if wa < 2 or a + wa <= pos:
                continue
            for b in range(max(a + 2, pos + 1), a + wa + 1):
                sub = s[a:b]
                if sub not in whole:
                    if sub in used_tokens:
                        conflict = True
                        break
                    cover.add(sub)
            if conflict:
                break
        if not conflict and cover:
            used_tokens |= cover
            chosen.append((pidx, pos))

    verify_disjoint_witness_direct(programs, chosen, k, wit, whole, max_bytes=max_bytes)
    return {"bound": len(chosen), "exact": False, "witness": chosen}


def fast_constructive_dictionary(
    programs: list[str],
    k: int,
    budget: int,
    lb: int,
    max_bytes: int | None = 160,
    minimize: bool = False,
) -> dict | None:
    """Fast solver-free constructive dictionary search below |Sigma| for k >= 2.

    Identifies exact non-forced characters R = Sigma \\ F_1, extracts compact maximal shared spans
    covering R, and runs iterative net-gain greedy + closure bundle elimination verified by
    exact byte-for-byte parsing. Returns a verified construction of size <= budget, or None.
    """
    if k < 2:
        return None
    whole = set(programs)
    alpha = sorted(set("".join(programs)))
    if not all(ch not in whole for ch in alpha):
        return None
    if len(alpha) <= budget and not minimize:
        return verify_construction(programs, alpha, k, max_bytes=max_bytes)

    wit = suffix_shared_lengths(programs, k, max_bytes=max_bytes)

    # 1. Exact forced singletons F_1 and eliminable characters R = Sigma \ F_1
    forced_chars: set[str] = set()
    char_occs: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for pidx, s in enumerate(programs):
        row = wit[pidx]
        max_reach = 0
        for pos, ch in enumerate(s):
            w = row[pos]
            if w >= 2 and pos + w > max_reach:
                max_reach = pos + w
            if max_reach <= pos:
                forced_chars.add(ch)
            char_occs[ch].append((pidx, pos))

    elim_chars = [ch for ch in alpha if ch not in forced_chars]
    if not elim_chars:
        return None
    elim_set = set(elim_chars)

    # 2. Extract compact candidate multi-char eligible tokens covering R-occurrences
    cand_set: set[str] = set()
    for pidx, s in enumerate(programs):
        n = len(s)
        row = wit[pidx]
        for a, w in enumerate(row):
            if w < 2:
                continue
            # Keep left-maximal shared spans (or spans starting at an R-char)
            is_left_max = (a == 0) or (row[a - 1] < w + 1)
            span = s[a : a + w]
            r_offsets = [off for off, ch in enumerate(span) if ch in elim_set]
            if not r_offsets:
                continue
            if is_left_max and span not in whole:
                cand_set.add(span)
                # Also add tight R-hull inside span (handles overlapping boilerplate headers/guards cleanly)
                lo_off, hi_off = r_offsets[0], r_offsets[-1]
                if lo_off == hi_off:
                    if lo_off > 0:
                        hull = span[lo_off - 1 : hi_off + 1]
                        if hull not in whole:
                            cand_set.add(hull)
                    if hi_off + 1 < w:
                        hull = span[lo_off : hi_off + 2]
                        if hull not in whole:
                            cand_set.add(hull)
                else:
                    hull = span[lo_off : hi_off + 1]
                    if hull not in whole:
                        cand_set.add(hull)
            # For every R-position in this span, add short 2-3 char anchors so overlaps never block elimination
            for off in r_offsets:
                pos = a + off
                if off > 0:
                    t2 = span[off - 1 : off + 1]
                    if t2 not in whole:
                        cand_set.add(t2)
                if off + 1 < w:
                    t2 = span[off : off + 2]
                    if t2 not in whole:
                        cand_set.add(t2)
                if off > 0 and off + 1 < w:
                    t3 = span[off - 1 : off + 2]
                    if t3 not in whole:
                        cand_set.add(t3)

    # Filter to genuinely eligible multi-char tokens (doc_freq >= k, <= max_bytes, not whole)
    candidates: list[str] = []
    for tok in sorted(cand_set, key=lambda t: (-len(t), t)):
        if len(tok) >= 2 and is_token_eligible(tok, programs, k, whole=whole, max_bytes=max_bytes):
            candidates.append(tok)
    if not candidates:
        return None

    # 3. Precompute R-occurrence bitmasks per candidate token
    occ_to_id: dict[tuple[int, int], int] = {}
    char_mask: dict[str, int] = {}
    for ch in elim_chars:
        mask = 0
        for coord in char_occs[ch]:
            oid = occ_to_id.setdefault(coord, len(occ_to_id))
            mask |= 1 << oid
        char_mask[ch] = mask

    tok_mask: dict[str, int] = {}
    tok_chars: dict[str, set[str]] = {}
    char_to_toks: dict[str, list[str]] = defaultdict(list)
    for tok in candidates:
        tlen = len(tok)
        m = 0
        tch: set[str] = set()
        for pidx, s in enumerate(programs):
            start = 0
            while True:
                idx = s.find(tok, start)
                if idx == -1:
                    break
                for pos in range(idx, idx + tlen):
                    coord = (pidx, pos)
                    oid = occ_to_id.get(coord)
                    if oid is not None:
                        m |= 1 << oid
                        tch.add(s[pos])
                start = idx + 1
        if m:
            tok_mask[tok] = m
            tok_chars[tok] = tch
            for ch in tch:
                char_to_toks[ch].append(tok)

    # Deduplicate tokens with identical R-occurrence mask (prefer shorter token to minimize overlap conflicts,
    # while keeping the longest one too in case it merges adjacent spans cleanly)
    mask_groups: dict[int, list[str]] = defaultdict(list)
    for tok, m in tok_mask.items():
        mask_groups[m].append(tok)
    pruned_cands: list[str] = []
    for m, toks in mask_groups.items():
        toks.sort(key=lambda t: (len(t), t))
        pruned_cands.append(toks[0])
        if len(toks[-1]) != len(toks[0]):
            pruned_cands.append(toks[-1])
    pruned_set = set(pruned_cands)
    char_to_toks = {ch: [t for t in toks if t in pruned_set] for ch, toks in char_to_toks.items()}

    # Helper: exact parse check only on programs containing any of `affected_chars`
    char_progs: dict[str, list[int]] = {
        ch: sorted({pidx for pidx, _ in char_occs[ch]}) for ch in elim_chars
    }

    def parses_for_chars(vocab_list: list[str], chars_dropped: set[str]) -> bool:
        pidxs: set[int] = set()
        for ch in chars_dropped:
            pidxs.update(char_progs[ch])
        return all(parse_program(programs[pidx], vocab_list) is not None for pidx in pidxs)

    active_singles: set[str] = set(alpha)
    chosen_multi: list[str] = []
    chosen_set: set[str] = set()
    chosen_mask = 0

    # 4. Iterative net-gain elimination (free drops + single-token + greedy closure bundles)
    while len(active_singles) + len(chosen_multi) > lb:
        if not minimize and len(active_singles) + len(chosen_multi) <= budget:
            break
        rem_r = [ch for ch in elim_chars if ch in active_singles]
        if not rem_r:
            break

        # 4a. Free drops: any remaining R-char already 100% covered by chosen_multi
        dropped_any = False
        for ch in list(rem_r):
            if (char_mask[ch] & ~chosen_mask) == 0:
                trial = sorted(active_singles - {ch}) + chosen_multi
                if parses_for_chars(trial, {ch}):
                    active_singles.remove(ch)
                    dropped_any = True
        if dropped_any:
            continue

        # 4b. Build seed bundles: every candidate touching >= 2 remaining R-chars, plus small-degree R-chars
        rem_r_set = set(rem_r)
        rem_r_mask = 0
        for ch in rem_r:
            rem_r_mask |= char_mask[ch]

        seeds: list[str] = []
        seen_seed: set[str] = set()
        # Rank candidates by how many remaining R-chars they touch
        for tok in pruned_cands:
            if tok in chosen_set:
                continue
            if len(tok_chars[tok] & rem_r_set) >= 2:
                seeds.append(tok)
                seen_seed.add(tok)
        seeds.sort(key=lambda t: (-len(tok_chars[t] & rem_r_set), -(tok_mask[t] & rem_r_mask).bit_count(), len(t), t))
        seeds = seeds[:160]

        best_bundles: list[tuple[int, int, tuple[str, ...], frozenset[str]]] = []
        seen_bundle_keys: set[tuple[str, ...]] = set()

        for seed in seeds:
            bundle = [seed]
            b_set = {seed}
            cov = chosen_mask | tok_mask[seed]
            target_chars = set(tok_chars[seed] & rem_r_set)

            for _ in range(12):
                done = frozenset(ch for ch in rem_r if (char_mask[ch] & ~cov) == 0)
                gain = len(done) - len(bundle)
                if gain >= 1:
                    b_key = tuple(sorted(bundle))
                    if b_key not in seen_bundle_keys:
                        seen_bundle_keys.add(b_key)
                        best_bundles.append((gain, -len(bundle), b_key, done))
                # Expand bundle to finish off partially-covered target_chars
                unfinished = [ch for ch in target_chars if (char_mask[ch] & ~cov) != 0]
                if not unfinished:
                    # Also try pulling in one high-overlap neighbor char
                    break
                # Pick unfinished char with fewest remaining uncovered occurrences
                unfinished.sort(key=lambda ch: ((char_mask[ch] & ~cov).bit_count(), ch))
                focus_ch = unfinished[0]
                focus_need = char_mask[focus_ch] & ~cov
                target_need = 0
                for ch in unfinished:
                    target_need |= char_mask[ch] & ~cov

                best_next = None
                best_score = (-1, -1, -1)
                for cand in char_to_toks.get(focus_ch, ()):
                    if cand in chosen_set or cand in b_set:
                        continue
                    cm = tok_mask[cand]
                    hit_focus = (cm & focus_need).bit_count()
                    if hit_focus == 0:
                        continue
                    hit_target = (cm & target_need).bit_count()
                    finishes = sum(1 for ch in rem_r if (char_mask[ch] & ~cov) != 0 and (char_mask[ch] & ~(cov | cm)) == 0)
                    sc = (finishes, hit_target, hit_focus)
                    if sc > best_score:
                        best_score = sc
                        best_next = cand
                if best_next is None:
                    break
                bundle.append(best_next)
                b_set.add(best_next)
                cov |= tok_mask[best_next]
                target_chars |= (tok_chars[best_next] & rem_r_set)

        if not best_bundles:
            break
        best_bundles.sort(reverse=True)

        committed = False
        for gain, _, b_key, done in best_bundles[:12]:
            b_list = list(b_key)
            trial_vocab = sorted(active_singles - set(done)) + chosen_multi + b_list
            if parses_for_chars(trial_vocab, set(done)):
                active_singles -= set(done)
                chosen_multi.extend(b_list)
                chosen_set.update(b_list)
                for tok in b_list:
                    chosen_mask |= tok_mask[tok]
                committed = True
                break
            # Overlap fallback: greedily drop as many chars in `done` as parse cleanly with `b_list`
            actually_dropped: set[str] = set()
            cur_singles = set(active_singles)
            for ch in sorted(done):
                tv = sorted(cur_singles - {ch}) + chosen_multi + b_list
                if parses_for_chars(tv, actually_dropped | {ch}):
                    cur_singles.remove(ch)
                    actually_dropped.add(ch)
            if len(actually_dropped) > len(b_list):
                active_singles = cur_singles
                chosen_multi.extend(b_list)
                chosen_set.update(b_list)
                for tok in b_list:
                    chosen_mask |= tok_mask[tok]
                committed = True
                break
        if not committed:
            break

    # 5. Final prune of any redundant multi-char tokens or remaining R-singletons
    final_dict = sorted(active_singles) + sorted(chosen_multi)
    for tok in sorted(chosen_multi, key=lambda t: (-len(t), t)):
        rest = [d for d in final_dict if d != tok]
        if all(parse_program(s, rest) is not None for s in programs):
            final_dict = rest
    for ch in sorted(active_singles & elim_set):
        rest = [d for d in final_dict if d != ch]
        if parses_for_chars(rest, {ch}):
            final_dict = rest

    if len(final_dict) <= budget:
        return verify_construction(programs, final_dict, k, max_bytes=max_bytes)
    return None


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

    Lemma: Let r = max_i rank_{F_{p_i}}(M_T). For any field (p_i, b_i) that attains rank r
    (len(basis_i) == r), any legal dictionary D of size r tiling every program must satisfy
    span_{p_i}(D) == span_{p_i}(M_T), so every t in D lies in span_{p_i}(M_T) and {v_{p_i}(t)}
    is linearly independent. Fields with rank < r are NEVER used to filter span tokens.
    """
    chars = alphabet_index(programs)
    tokens = sorted(eligible_tokens(programs, k=1, max_bytes=None), key=lambda t: (len(t), t))
    field_bases = [
        (prime, base, rref_basis([pos_vector(s, chars, prime, base) for s in programs], prime))
        for prime, base in PRIMES
    ]
    rank = max(len(basis) for _, _, basis in field_bases)
    attaining = [(prime, base, basis) for prime, base, basis in field_bases if len(basis) == rank]

    # Necessary condition 1: every program has a proper prefix in span(M_T) for every rank-attaining field
    prefix_cuttable = all(
        any(
            all(in_span(pos_vector(s[:i], chars, p, b), basis, p) for p, b, basis in attaining)
            for i in range(1, len(s))
        )
        for s in programs
    )

    # Necessary condition 2: every program admits a complete non-overlapping parse in E_span
    span_tokens = [
        t for t in tokens
        if all(in_span(pos_vector(t, chars, p, b), basis, p) for p, b, basis in attaining)
    ]
    unparseable_in_span = [s for s in programs if parse_program(s, span_tokens) is None]
    parses_in_span = len(unparseable_in_span) == 0

    result: dict = {
        "programRank": rank,
        "attainingFields": [{"prime": p, "base": b, "rank": len(basis)} for p, b, basis in attaining],
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
            # Must be linearly independent in every rank-attaining field and parse every source
            if not all(
                len(rref_basis([pos_vector(t, chars, p, b) for t in cand], p)) == rank
                for p, b, _ in attaining
            ):
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


# ---------------------------------------------------------------------- construction search (small + fast real-corpus)
def find_verified_construction(
    programs: list[str],
    k: int,
    budget: int,
    tokens: set[str] | None,
    max_bytes: int | None = 160,
    exhaustive_token_limit: int = 24,
    exhaustive_budget_limit: int = 9,
    lb: int = 0,
) -> dict | None:
    """Return a byte-verified eligible dictionary of size <= budget if found, else None."""
    whole = set(programs)
    alpha = sorted(set("".join(programs)))
    all_singletons_eligible = all(ch not in whole for ch in alpha)
    if all_singletons_eligible and len(alpha) <= budget:
        return verify_construction(programs, alpha, k, max_bytes=max_bytes, tokens=tokens)

    # For k >= 2, if every forced block is eligible and their count fits the budget,
    # the forced blocks themselves form an explicit byte-verified tiling dictionary.
    if k >= 2:
        blocks = forced_blocks(programs, k, max_bytes=max_bytes)
        if len(blocks) <= budget and all(
            (b in tokens if tokens is not None else is_token_eligible(b, programs, k, whole=whole, max_bytes=max_bytes))
            for b in blocks
        ):
            return verify_construction(programs, blocks, k, max_bytes=max_bytes, tokens=tokens)
        # Fast net-gain constructive dictionary pass below |Sigma| (verified byte-exact)
        if all_singletons_eligible and budget < len(alpha):
            fast_found = fast_constructive_dictionary(programs, k, budget, lb=lb, max_bytes=max_bytes)
            if fast_found is not None:
                return fast_found

    # For k = 1, check Theorem B span-basis construction when budget >= program rank
    if k == 1:
        tb = theorem_b_span_parse_test(programs)
        if tb.get("rankAttainable") is True and tb["programRank"] <= budget:
            return tb["attainingConstruction"]

    # Exhaustive search on small components (only returns byte-verified dictionaries)
    if tokens is None:
        if sum(len(s) for s in programs) <= 500:
            tokens = eligible_tokens(programs, k, max_bytes=max_bytes)
        else:
            return None
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
    measure_memory: bool = True,
) -> dict:
    """Tri-state full-corpus capacity diagnostic: IMPOSSIBLE, FEASIBLE, or UNRESOLVED.

    Never reports a rank bound or upper bound as a construction.
    """
    if measure_memory:
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
        per_comp_tokens: list[set[str] | None] = []
        per_comp_kernel_constructions: list[dict | None] = []

        for idx, comp in enumerate(components):
            comp_alpha = sorted(set("".join(comp)))
            comp_singletons_ok = all(ch not in set(comp) for ch in comp_alpha)
            comp_chars = sum(len(s) for s in comp)
            rank_cert = certified_rank_bound(comp, k, max_bytes=max_bytes)

            # Fast path for large k>=2 components: compute rank + forced-block rank FIRST without
            # enumerating all eligible substrings. Then apply Nullspace-Kernel Theorem (Theorem 1)
            # whenever nullity d > 0 and budget lies in [rank, |Sigma|-1].
            tokens: set[str] | None = None
            block_subreports = []
            block_split_lb = None
            rank_val = rank_cert["bound"]
            tb_lift = None
            nk_cert: dict | None = None
            nk_construction: dict | None = None

            if k == 1:
                tokens = eligible_tokens(comp, k, max_bytes=max_bytes)
                disj_cert = disjoint_position_certificate(comp, k, tokens, max_bytes=max_bytes)
                if disj_cert["bound"] is not None:
                    tb = theorem_b_span_parse_test(comp)
                    if tb["certifiedLowerBound"] > rank_cert["bound"]:
                        tb_lift = tb
                    rank_val = tb_lift["certifiedLowerBound"] if tb_lift else rank_cert["bound"]
            elif comp_chars <= 500:
                tokens = eligible_tokens(comp, k, max_bytes=max_bytes)
                disj_cert = disjoint_position_certificate(comp, k, tokens, max_bytes=max_bytes)
            else:
                # Large k >= 2 component: check forced-block rank decomposition first (cheap O(L) + RREF)
                fb_comps = forced_block_components(comp, k, max_bytes=max_bytes)
                fb_rank_sum = 0
                if len(fb_comps) > 1:
                    for fb_idx, fb_units in enumerate(fb_comps):
                        fb_rank = certified_rank_bound(comp, k, max_bytes=max_bytes, units=fb_units)
                        fb_rank_sum += fb_rank["bound"]
                        block_subreports.append({
                            "blockComponentIndex": fb_idx,
                            "blocks": fb_units,
                            "alphabetSize": len(set("".join(fb_units))),
                            "blockRank": fb_rank["bound"],
                            "disjointBound": None,
                            "lowerBound": fb_rank["bound"],
                        })
                    if fb_rank_sum > rank_val:
                        block_split_lb = fb_rank_sum
                rank_best = max(rank_val, block_split_lb or 0)
                if comp_singletons_ok and (
                    rank_best > budget
                    or rank_best >= len(comp_alpha)
                    or (len(components) == 1 and len(comp_alpha) <= budget)
                ):
                    disj_cert = {"bound": 0, "exact": False, "skipped": True, "witness": []}
                else:
                    # Try Nullspace-Kernel Theorem BEFORE slow disjoint packing
                    nk_cert = nullspace_kernel_certificate(comp, k, max_bytes=max_bytes)
                    if nk_cert["status"] == "RANK_ATTAINED":
                        nk_construction = nk_cert["attainingConstruction"]
                        disj_cert = {"bound": 0, "exact": False, "skipped": True, "witness": []}
                    elif nk_cert["status"] == "RANK_UNATTAINABLE" and (
                        nk_cert["certifiedLowerBound"] > budget or (comp_singletons_ok and nk_cert["certifiedLowerBound"] >= len(comp_alpha))
                    ):
                        disj_cert = {"bound": 0, "exact": False, "skipped": True, "witness": []}
                    else:
                        disj_cert = disjoint_position_certificate_fast(comp, k, max_bytes=max_bytes)

            per_comp_tokens.append(tokens)

            if disj_cert["bound"] is None:
                unspellable = True
                comp_lb = None
                stronger = "unspellable-position"
            else:
                disj_val = disj_cert["bound"]
                comp_lb = max(rank_val, disj_val, block_split_lb or 0)

                # For small k >= 2 components, run forced-block component decomposition + Nullspace-Kernel Theorem
                if k >= 2 and comp_chars <= 500:
                    fb_comps = forced_block_components(comp, k, max_bytes=max_bytes)
                    if len(fb_comps) > 1:
                        fb_sum = 0
                        fb_ok = True
                        for fb_idx, fb_units in enumerate(fb_comps):
                            fb_chars = set("".join(fb_units))
                            fb_tokens = {t for t in (tokens or set()) if set(t) <= fb_chars}
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
                    if comp_lb < len(comp_alpha) and comp_lb <= budget:
                        nk_cert = nullspace_kernel_certificate(comp, k, max_bytes=max_bytes)
                        if nk_cert["status"] == "RANK_ATTAINED":
                            nk_construction = nk_cert["attainingConstruction"]

                nk_lift = False
                if nk_cert is not None and nk_cert["certifiedLowerBound"] > comp_lb:
                    comp_lb = nk_cert["certifiedLowerBound"]
                    nk_lift = True

                if nk_lift:
                    stronger = "nullspace-kernel-obstruction"
                elif block_split_lb is not None and block_split_lb >= max(rank_val, disj_val):
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

            per_comp_kernel_constructions.append(nk_construction)
            comp_reports.append({
                "componentIndex": idx,
                "programs": comp,
                "alphabetSize": len(comp_alpha),
                "allSingletonsEligible": comp_singletons_ok,
                "rankCertificate": rank_cert,
                "disjointCertificate": disj_cert,
                "nullspaceKernelCertificate": (
                    {k2: v2 for k2, v2 in nk_cert.items() if k2 != "attainingConstruction"}
                    if nk_cert is not None
                    else None
                ),
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
                for comp, report, tokens, nk_found in zip(
                    components, comp_reports, per_comp_tokens, per_comp_kernel_constructions
                ):
                    comp_lb = report["componentLowerBound"]
                    if nk_found is not None and nk_found["dictionarySize"] <= comp_lb + slack:
                        found = nk_found
                    else:
                        found = find_verified_construction(
                            comp, k, comp_lb + slack, tokens, max_bytes=max_bytes, lb=comp_lb
                        )
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
        if measure_memory:
            _, peak_bytes = tracemalloc.get_traced_memory()
            peak_kib = round(peak_bytes / 1024.0, 2)
        else:
            peak_kib = None
        verdict["measuredCost"] = {"elapsedMs": elapsed_ms, "peakAllocKiB": peak_kib}
        return verdict
    finally:
        if measure_memory:
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
