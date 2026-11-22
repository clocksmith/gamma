#!/usr/bin/env python3
"""The deficit hierarchy: the rank-tight parsing test extended from "rank" to "rank + 1".
Witness rule (threshold 2, entries of at most 160 bytes) or the unrestricted rule. Python 3.8+; no solver.

Every dictionary D that spells the blocks has a span containing the block space R. Write K for the kernel of
the block matrix (dimension d) and, for an entry t, phi(t) for the vector of products of v(t) with a basis of
K. Then:
  * the vectors phi(t), t in D, span a space Phi(D) of dimension dim span(D) - rank, which is at most |D| - rank;
  * so a dictionary of rank + j entries uses only entries whose phi lies in some space Phi of dimension at most j
    that is spanned by phi-vectors of eligible entries.
Level 0 (Phi = 0) is the original test. Level 1 lets Phi be one line, the line of one entry's phi-vector.
For a fixed Phi the characters whose phi lies in Phi may be single entries; every occurrence of any other
"free" character must be covered by a multi-character entry with phi in Phi. The search below is over those.

analyze(programs) returns a lower bound that is rank, rank + 1 or rank + 2, and the smallest dictionary it
built (verified by the caller). Searches that hit their node limit make the answer weaker, never wrong.
"""
import sys

FIELDS = ((1_000_000_007, 2), (998_244_353, 3))
CAP = 160


def reduced_rows(vectors, prime):
    basis = {}
    for raw in vectors:
        v = list(raw)
        for pivot, row in basis.items():
            if v[pivot]:
                f = v[pivot]
                v = [(a - f * b) % prime for a, b in zip(v, row)]
        pivot = next((j for j, x in enumerate(v) if x), None)
        if pivot is None:
            continue
        inverse = pow(v[pivot], prime - 2, prime)
        v = [x * inverse % prime for x in v]
        for other, row in list(basis.items()):
            if row[pivot]:
                f = row[pivot]
                basis[other] = [(a - f * b) % prime for a, b in zip(row, v)]
        basis[pivot] = v
    return basis


def forced_blocks(programs, rule):
    if rule == 'U':
        return sorted(set(programs))
    owners = {}
    for n, p in enumerate(programs):
        for i in range(len(p) - 1):
            owners.setdefault(p[i:i + 2], set()).add(n)
    blocks = set()
    for p in programs:
        start = 0
        for i in range(len(p) - 1):
            if len(owners[p[i:i + 2]]) < 2:
                blocks.add(p[start:i + 1])
                start = i + 1
        blocks.add(p[start:])
    return sorted(blocks)


def spells(text, table):
    reach = [True] + [False] * len(text)
    for i in range(len(text)):
        if reach[i]:
            for e in table.get(text[i], ()):
                if text.startswith(e, i):
                    reach[i + len(e)] = True
    return reach[len(text)]


def normalise(f, prime):
    lead = next((x for x in f if x), None)
    if lead is None:
        return None
    inverse = pow(lead, prime - 2, prime)
    return tuple(x * inverse % prime for x in f)


def analyze(programs, rule='W2', node_limit=60_000, class_limit=4_000, fragment_limit=600_000, rank_node_limit=400_000):
    letters = sorted(set(''.join(programs)))
    column = {c: n for n, c in enumerate(letters)}
    blocks = forced_blocks(programs, rule)
    whole = set(programs)

    def block_vectors(prime, base):
        out = []
        for b in blocks:
            v, weight = [0] * len(letters), 1
            for c in b:
                v[column[c]] = (v[column[c]] + weight) % prime
                weight = weight * base % prime
            out.append(v)
        return out

    best = None
    for prime, base in FIELDS:                       # one field that attains the larger rank; any single field is sound
        basis = reduced_rows(block_vectors(prime, base), prime)
        if best is None or len(basis) > len(best[2]):
            best = (prime, base, basis)
    prime, base, basis = best
    rank, d = len(basis), len(letters) - len(basis)
    info = {'rank': rank, 'nullity': d, 'alphabet': len(letters)}
    if d == 0:
        return dict(info, lowerBound=rank, dictionary=None, levelOne='not needed', note='rank equals the alphabet')
    kernel = []
    for free_col in (j for j in range(len(letters)) if j not in basis):
        z = [0] * len(letters)
        z[free_col] = 1
        for pivot, row in basis.items():
            z[pivot] = (-row[free_col]) % prime
        kernel.append(z)
    phi_char = {c: tuple(z[column[c]] for z in kernel) for c in letters}
    zero = (0,) * d
    free_all = {c for c in letters if phi_char[c] != zero}

    # Eligible multi-character fragments that touch a free character, each with its phi.
    fragments = {}
    for n, p in enumerate(programs):
        others = [q for m, q in enumerate(programs) if m != n]
        starts = set()
        for q, c in enumerate(p):
            if c in free_all:
                starts.update(range(max(0, q - CAP + 1), q + 1))
        for i in sorted(starts):
            sums, weight, touched = [0] * d, 1, False
            for j in range(i, len(p)):
                c = p[j]
                pc = phi_char[c]
                if pc != zero:
                    touched = True
                    for x in range(d):
                        if pc[x]:
                            sums[x] = (sums[x] + weight * pc[x]) % prime
                weight = weight * base % prime
                if j == i:
                    continue
                s = p[i:j + 1]
                if rule != 'U' and (len(s.encode()) > CAP or not any(s in q for q in others)):
                    break
                if touched and s not in whole and s not in fragments:
                    fragments[s] = tuple(sums)
                    if len(fragments) > fragment_limit:
                        return dict(info, lowerBound=rank, dictionary=None, levelOne='not attempted', note='too many fragments')
    names = sorted(fragments)

    free_blocks = [b for b in blocks if any(c in free_all for c in b)]
    occurrence, occurrence_char = {}, []
    for bi, b in enumerate(free_blocks):
        for pos, c in enumerate(b):
            if c in free_all:
                occurrence[(bi, pos)] = len(occurrence_char)
                occurrence_char.append(c)
    place = {}                                            # fragment -> list of (block index, start)
    cover = {}                                            # fragment -> bitmask of free-character occurrences it can cover
    for t in names:
        spots, mask = [], 0
        for bi, b in enumerate(free_blocks):
            at = b.find(t)
            while at != -1:
                spots.append((bi, at))
                for pos in range(at, at + len(t)):
                    o = occurrence.get((bi, pos))
                    if o is not None:
                        mask |= 1 << o
                at = b.find(t, at + 1)
        place[t], cover[t] = spots, mask

    def level(line, total, limit_nodes=None):
        """One choice of Phi: the zero space (line None) or the line through `line`; `total` is the dictionary size
        being tested. Returns (found dictionary or None, refuted, complete)."""
        def inside(f):
            return f == zero or (line is not None and normalise(f, prime) == line)
        singles = [c for c in letters if inside(phi_char[c]) and c not in whole]
        single_set = set(c for c in letters if inside(phi_char[c]))
        free = free_all - single_set
        allowed = [t for t in names if inside(fragments[t]) and any(c in free for c in t)]
        need = 0
        for o, c in enumerate(occurrence_char):
            if c in free:
                need |= 1 << o
        # Runs that no allowed fragment can cover, bounded by a block edge or a free character: entries avoiding the
        # free characters number at least the rank of those runs.
        flags = [[False] * len(b) for b in free_blocks]
        for t in allowed:
            for bi, at in place[t]:
                for pos in range(at, at + len(t)):
                    flags[bi][pos] = True
        runs = set()
        index = {b: bi for bi, b in enumerate(free_blocks)}
        for b in blocks:
            row = flags[index[b]] if b in index else [False] * len(b)
            i = 0
            while i < len(b):
                if row[i]:
                    i += 1
                    continue
                j = i
                while j < len(b) and not row[j]:
                    j += 1
                if (i == 0 or b[i - 1] in free) and (j == len(b) or b[j] in free) and not any(c in free for c in b[i:j]):
                    runs.add(b[i:j])
                i = j
        kept = sorted(single_set)
        kept_column = {c: n for n, c in enumerate(kept)}
        vectors = []
        for run in runs:
            v, weight = [0] * len(kept), 1
            for c in run:
                v[kept_column[c]] = (v[kept_column[c]] + weight) % prime
                weight = weight * base % prime
            vectors.append(v)
        avoid_at_least = len(reduced_rows(vectors, prime))
        relevant = {t: cover[t] & need for t in allowed}
        blocks_here = [b for b in free_blocks if any(c in free for c in b)]
        nodes = [0]

        def table(chosen):
            out = {}
            for e in list(single_set) + chosen:
                out.setdefault(e[0], []).append(e)
            return out

        def search(remaining, chosen, limit):
            nodes[0] += 1
            if nodes[0] > (limit_nodes or node_limit):
                raise TimeoutError
            if remaining == 0:
                if all(spells(b, table(chosen)) for b in blocks_here):
                    return chosen
                if len(chosen) >= limit:
                    return None
                for t in allowed:
                    if t not in chosen:
                        found = search(0, chosen + [t], limit)
                        if found is not None:
                            return found
                return None
            if len(chosen) >= limit:
                return None
            best_candidates, bit = None, 1
            while bit <= remaining:
                if remaining & bit:
                    candidates = [t for t in allowed if relevant[t] & bit and t not in chosen]
                    if best_candidates is None or len(candidates) < len(best_candidates):
                        best_candidates = candidates
                        if not best_candidates:
                            return None
                bit <<= 1
            for t in best_candidates:
                found = search(remaining & ~relevant[t], chosen + [t], limit)
                if found is not None:
                    return found
            return None

        # First the strict budget: with every allowed single character kept, at most this many fragments fit in `total`.
        strict = total - len(singles)
        loose = total - avoid_at_least                      # most entries any dictionary of `total` can spend on free characters
        try:
            found = search(need, [], strict) if strict >= 0 else None
            if found is not None:
                return sorted(singles) + sorted(found), False, True
            if loose <= strict:
                return None, True, True
            nodes[0] = 0
            wider = search(need, [], loose)
        except TimeoutError:
            return None, False, False
        if wider is None:
            return None, True, True
        return sorted(singles) + sorted(wider), False, True       # a candidate that may exceed `total`; the caller prunes and counts it

    def prune(dictionary):
        """Drop entries the blocks can be spelled without; keeps a dictionary a dictionary."""
        current = list(dictionary)
        for e in sorted(current, key=lambda x: (len(x) > 1, -len(x), x)):
            rest = [x for x in current if x != e]
            table = {}
            for x in rest:
                table.setdefault(x[0], []).append(x)
            if all(spells(b, table) for b in blocks):
                current = rest
        return current

    best_dictionary = None

    def offer(dictionary):
        nonlocal best_dictionary
        if dictionary is None:
            return
        table = {}
        for x in dictionary:
            table.setdefault(x[0], []).append(x)
        if not all(spells(b, table) for b in blocks):
            return
        pruned = prune(dictionary)
        if best_dictionary is None or len(pruned) < len(best_dictionary):
            best_dictionary = pruned

    # Level 0 at exactly rank entries: the original test.
    found, refuted, complete = level(None, rank, rank_node_limit)
    offer(found)
    if best_dictionary is not None and len(best_dictionary) <= rank:
        return dict(info, lowerBound=rank, dictionary=best_dictionary, levelOne='not needed', note='rank attained')
    if not (refuted and complete):
        return dict(info, lowerBound=rank, dictionary=best_dictionary, levelOne='not attempted', note='rank neither built nor ruled out')
    lower = rank + 1
    # Rank + 1 inside the block space (Phi = 0): one spare entry, no new direction.
    found0, refuted0, complete0 = level(None, rank + 1)
    offer(found0)
    if best_dictionary is not None and len(best_dictionary) <= rank + 1:
        return dict(info, lowerBound=lower, dictionary=best_dictionary, levelOne='not needed', note='rank + 1 attained inside the block space')

    # Level 1: every line spanned by the phi of an eligible entry.
    lines = {}
    for c in letters:
        line = normalise(phi_char[c], prime)
        if line is not None and c not in whole:
            lines.setdefault(line, 0)
    for t in names:
        line = normalise(fragments[t], prime)
        if line is not None:
            lines.setdefault(line, 0)
    if len(lines) > class_limit:
        return dict(info, lowerBound=lower, dictionary=best_dictionary, levelOne='not attempted', note=f'{len(lines)} lines exceed the limit', lines=len(lines))
    all_refuted = refuted0 and complete0
    for line in sorted(lines):
        found, refuted, complete = level(line, rank + 1)
        offer(found)
        if best_dictionary is not None and len(best_dictionary) <= rank + 1:
            return dict(info, lowerBound=lower, dictionary=best_dictionary, levelOne='attained', note='rank + 1 attained on one line', lines=len(lines))
        if not (refuted and complete):
            all_refuted = False
    if all_refuted:
        return dict(info, lowerBound=rank + 2, dictionary=best_dictionary, levelOne='ruled out', note='no dictionary of rank + 1 entries', lines=len(lines))
    return dict(info, lowerBound=lower, dictionary=best_dictionary, levelOne='unresolved', note='some line neither built nor refuted rank + 1', lines=len(lines))


if __name__ == '__main__':
    r = analyze(sys.argv[1:], 'W2')
    print({k: v for k, v in r.items()})
