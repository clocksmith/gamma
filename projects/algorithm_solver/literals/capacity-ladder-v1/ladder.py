#!/usr/bin/env python3
"""The deficit ladder: the defect-space hierarchy of capacity-deficit-v1 at any level, with the subspaces found
by branching on one uncoverable occurrence instead of listing every line. Witness rule (threshold 2, entries of
at most 160 bytes) or the unrestricted rule. Python 3.10+ and numpy; no solver.

Notation as in capacity-deficit-v1/THEOREM.md: rank r, kernel dimension d, phi(t) in F^d for an entry t, and for a
dictionary D the space Phi(D) spanned by its phi-vectors, of dimension at most |D| - r.

Node claim. prove(Phi, j, total) decides, or fails to decide, whether there is a dictionary D with at most `total`
entries, Phi contained in Phi(D), and dim Phi(D) <= dim Phi + j. It is refuted in one of three ways:
  * some occurrence of a character whose phi is outside Phi is covered by no eligible entry with phi in Phi.
    Any D must cover it with an entry e, phi(e) outside Phi, so Phi + <phi(e)> is inside Phi(D): with j = 0 there
    is no such D, and with j > 0 it is enough to refute prove(Phi + <phi(e)>, j - 1) for the entries e through
    that one occurrence;
  * otherwise the fixed-space search refutes every D with Phi(D) = Phi, and with j > 0 every D left has an entry
    with phi outside Phi, so it is enough to refute every Phi + <phi(e)> over all entries (the wide fallback);
  * the fixed-space search itself, for j = 0.
The root call prove(0, j, r + j) for j = 0, 1, 2, ... is the ladder: each refuted level raises the lower bound by
one, and the first dictionary built at r + j is then a minimum one.

Limits make an answer weaker, never wrong: an undecided node stops the climb at the bound already proved.
"""
import sys
import time

import numpy as np

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


class Undecided(Exception):
    """A limit stopped a node; the message says which."""


def analyze(programs, rule='W2', max_level=2, node_limit=60_000, rank_node_limit=400_000, fragment_limit=600_000,
            branch_limit=600, fallback_limit=4_000, seconds=None, trace=None):
    started = time.time()
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
        rows = reduced_rows(block_vectors(prime, base), prime)
        if best is None or len(rows) > len(best[2]):
            best = (prime, base, rows)
    prime, base, rows = best
    rank, d = len(rows), len(letters) - len(rows)
    info = {'rank': rank, 'nullity': d, 'alphabet': len(letters)}
    if d == 0:
        return dict(info, lowerBound=rank, dictionary=None, level=0, note='rank equals the alphabet', nodes=0)
    kernel = []
    for free_col in (j for j in range(len(letters)) if j not in rows):
        z = [0] * len(letters)
        z[free_col] = 1
        for pivot, row in rows.items():
            z[pivot] = (-row[free_col]) % prime
        kernel.append(z)
    phi_char = {c: tuple(z[column[c]] for z in kernel) for c in letters}
    zero = (0,) * d
    free_all = {c for c in letters if phi_char[c] != zero}

    fragments = {}                                    # eligible multi-character entry touching a free character -> phi
    for n, p in enumerate(programs):
        others = [q for m, q in enumerate(programs) if m != n]
        starts = set()
        for q, c in enumerate(p):
            if c in free_all:
                starts.update(range(max(0, q - CAP + 1), q + 1))
        for i in sorted(starts):
            sums, weight, touched = [0] * d, 1, False
            for j in range(i, len(p)):
                pc = phi_char[p[j]]
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
                        return dict(info, lowerBound=rank, dictionary=None, level=None, note='too many fragments', nodes=0)
    names = sorted(fragments)
    values = sorted(set(fragments.values()) | set(phi_char.values()))
    value_index = {f: n for n, f in enumerate(values)}
    value_matrix = np.array(values, dtype=np.int64).reshape(len(values), d)
    members = [[] for _ in values]
    for t in names:
        members[value_index[fragments[t]]].append(t)
    touches = {t: frozenset(c for c in t if c in free_all) for t in names}

    free_blocks = [b for b in blocks if any(c in free_all for c in b)]
    occurrence, occurrence_char, occurrence_at = {}, [], []
    for bi, b in enumerate(free_blocks):
        for pos, c in enumerate(b):
            if c in free_all:
                occurrence[(bi, pos)] = len(occurrence_char)
                occurrence_char.append(c)
                occurrence_at.append((bi, pos))
    place, cover = {}, {}
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
    char_mask = {c: 0 for c in free_all}
    for o, c in enumerate(occurrence_char):
        char_mask[c] |= 1 << o

    # ---- subspaces of F^d in reduced row echelon form: a sorted tuple of (pivot, row)
    def reduce(f, space):
        v = list(f)
        for pivot, row in space:
            if v[pivot]:
                k = v[pivot]
                v = [(a - k * b) % prime for a, b in zip(v, row)]
        return v

    def extend(space, f):
        v = reduce(f, space)
        pivot = next((j for j, x in enumerate(v) if x), None)
        if pivot is None:
            return space
        inverse = pow(v[pivot], prime - 2, prime)
        v = tuple(x * inverse % prime for x in v)
        out = []
        for other, row in space:
            if row[pivot]:
                k = row[pivot]
                row = tuple((a - k * b) % prime for a, b in zip(row, v))
            out.append((other, row))
        out.append((pivot, v))
        return tuple(sorted(out))

    contexts = {}

    def context(space):
        if space in contexts:
            return contexts[space]
        residual = value_matrix.copy()
        for pivot, row in space:
            residual = (residual - residual[:, pivot:pivot + 1] * np.array(row, dtype=np.int64)) % prime
        inside_value = ~residual.any(axis=1)
        single_set = {c for c in letters if inside_value[value_index[phi_char[c]]]}
        free = free_all - single_set
        allowed = [t for n in np.nonzero(inside_value)[0] for t in members[n] if not touches[t].isdisjoint(free)]
        need = 0
        for c in free:
            need |= char_mask[c]
        covered = 0
        for t in allowed:
            covered |= cover[t]
        ctx = {'single_set': single_set, 'free': free, 'allowed': allowed, 'need': need, 'stuck': need & ~covered, 'inside_value': inside_value}
        contexts[space] = ctx
        return ctx

    counters = {'nodes': 0, 'fixed': 0, 'spaces': 0}

    index_of_block = {b: bi for bi, b in enumerate(free_blocks)}

    def fixed(ctx, total, limit_nodes):
        """Dictionaries whose entries all have phi in the space of ctx. Returns (candidate or None, refuted, reason):
        refuted is True when no such dictionary has at most `total` entries; reason is None when the answer is
        decided (a candidate that fits, or a refutation) and says what stopped it otherwise."""
        counters['fixed'] += 1
        single_set, free, allowed, need = ctx['single_set'], ctx['free'], ctx['allowed'], ctx['need']
        singles = sorted(c for c in single_set if c not in whole)
        kept = sorted(single_set)
        kept_column = {c: n for n, c in enumerate(kept)}

        def run_rank(chosen):
            """Entries that avoid the free characters number at least this: the rank of the stretches between free
            characters (or block edges) that no fragment of `chosen` can overlap, so that such entries spell them alone."""
            flags = [[False] * len(b) for b in free_blocks]
            for t in chosen:
                for bi, at in place[t]:
                    for pos in range(at, at + len(t)):
                        flags[bi][pos] = True
            runs = set()
            for b in blocks:
                row = flags[index_of_block[b]] if b in index_of_block else [False] * len(b)
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
            vectors = []
            for run in runs:
                v, weight = [0] * len(kept), 1
                for c in run:
                    v[kept_column[c]] = (v[kept_column[c]] + weight) % prime
                    weight = weight * base % prime
                vectors.append(v)
            return len(reduced_rows(vectors, prime))

        # Restricted rank. With entries limited to this space, a multi-character entry can cross the boundary next to
        # a free character only as part of an allowed fragment. Cut every block at the boundaries no allowed
        # fragment crosses: each piece is then spelled on its own, so a dictionary needs at least the rank of the pieces.
        crossed = [[False] * len(b) for b in free_blocks]              # crossed[bi][i]: some allowed fragment covers i and i + 1
        for t in allowed:
            for bi, at in place[t]:
                for pos in range(at, at + len(t) - 1):
                    crossed[bi][pos] = True
        pieces = set()
        for b in blocks:
            if b not in index_of_block:
                pieces.add(b)
                continue
            row, start = crossed[index_of_block[b]], 0
            for i in range(len(b) - 1):
                if (b[i] in free or b[i + 1] in free) and not row[i]:
                    pieces.add(b[start:i + 1])
                    start = i + 1
            pieces.add(b[start:])
        vectors = []
        for piece in pieces:
            v, weight = [0] * len(letters), 1
            for c in piece:
                v[column[c]] = (v[column[c]] + weight) % prime
                weight = weight * base % prime
            vectors.append(v)
        restricted = len(reduced_rows(vectors, prime))
        counters['restricted'] = counters.get('restricted', 0) + (restricted > total)
        if restricted > total:
            return None, True, None
        avoid_at_least = run_rank(allowed)
        # Cores. An allowed fragment t = u core w, where the core runs from its first free character to its last and
        # u, w hold none. Every allowed fragment has at least two free characters (with one, phi(t) in the space
        # would put that character's phi in the space), so the core is a fragment; phi(core) is in the space
        # because phi(u) and phi(w) are; and wherever t is used, u-singles + core + w-singles spell the same text
        # and cover the same free occurrences. The searches below spell with every allowed single character
        # available, so they need only cores. A core that is not an eligible entry keeps its fragments as they are.
        family = {}
        for t in allowed:
            first = next(n for n, c in enumerate(t) if c in free)
            last = max(n for n, c in enumerate(t) if c in free)
            core = t[first:last + 1]
            family.setdefault(core if core in fragments and last > first else t, []).append(t)
        all_allowed, allowed = allowed, sorted(family)
        relevant = {t: cover[t] & need for t in allowed}
        blocks_here = [b for b in free_blocks if any(c in free for c in b)]
        nodes = [0]

        def table(chosen):
            out = {}
            for e in list(single_set) + chosen:
                out.setdefault(e[0], []).append(e)
            return out

        def tick():
            nodes[0] += 1
            counters['nodes'] += 1
            if nodes[0] > limit_nodes or (seconds is not None and time.time() - started > seconds):
                raise TimeoutError

        def search(remaining, chosen, limit):
            tick()
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

        strict = total - len(singles)                       # with every allowed single character kept
        loose = total - avoid_at_least                      # most entries any dictionary of `total` can spend on free characters
        if trace is not None:
            trace.append({'total': total, 'allowed': len(all_allowed), 'cores': len(allowed), 'freeCharacters': len(free), 'freeOccurrences': bin(need).count('1'),
                          'singles': len(singles), 'restrictedRank': restricted, 'strict': strict, 'loose': loose, 'allowedFragments': sorted(allowed, key=len)[:40], 'free': sorted(free)})
        try:
            found = search(need, [], strict) if strict >= 0 else None
            if found is not None:
                return singles + sorted(found), False, None
            if loose <= strict:
                return None, True, None
            nodes[0] = 0
            wider = search(need, [], loose) if loose >= 0 else None
        except TimeoutError:
            return None, False, 'a fixed-space search hit its node limit'
        if wider is None:
            return None, True, None
        def expand(cores):
            # Longer fragments with the same cores can make single characters unnecessary; pruning sorts that out.
            members = sorted({t for core in cores for t in family[core]})
            return singles + (members if len(members) <= 300 else sorted(cores))

        candidate = expand(wider)
        if len(prune(candidate)) <= total:
            return candidate, False, None

        # Some set of fragments covers within the loose budget but its dictionary is too large. Go through every set F
        # of at most `loose` cores: a dictionary whose free-touching entries have exactly the cores F has at least
        # |F| + run_rank(every fragment with a core in F) entries. Refuted when that exceeds `total` for every F that covers and spells.
        # With few fragments go through the fragments themselves, which gives the sharper bound; otherwise cores.
        small = len(all_allowed) <= 60
        pool = sorted(all_allowed) if small else allowed
        reach = {t: cover[t] & need for t in pool}
        tail = [0] * (len(pool) + 1)
        for n in range(len(pool) - 1, -1, -1):
            tail[n] = tail[n + 1] | reach[pool[n]]
        outcome = {'gap': None, 'best': candidate}

        def every(start, chosen, covered):
            tick()
            if covered == need and all(spells(b, table(chosen)) for b in blocks_here):
                if len(chosen) + run_rank(chosen if small else [t for core in chosen for t in family[core]]) <= total:
                    attempt = singles + sorted(chosen) if small else expand(chosen)
                    size = len(prune(attempt))
                    if size <= total:
                        return attempt
                    if size < len(prune(outcome['best'])):
                        outcome['best'] = attempt
                    outcome['gap'] = size
            if len(chosen) >= loose:
                return None
            for n in range(start, len(pool)):
                if (covered | tail[n]) & need != need:
                    break
                found = every(n + 1, chosen + [pool[n]], covered | reach[pool[n]])
                if found is not None:
                    return found
            return None

        nodes[0] = 0
        try:
            found = every(0, [], 0)
        except TimeoutError:
            return outcome['best'], False, 'a fixed-space search hit its node limit'
        if found is not None:
            return found, False, None
        if outcome['gap'] is None:
            return None, True, None
        return outcome['best'], False, f"a fixed-space search is left with a dictionary of {outcome['gap']} entries against a bound of {total} or fewer"

    def prune(dictionary):
        current = list(dictionary)
        for e in sorted(current, key=lambda x: (len(x) > 1, -len(x), x)):
            rest = [x for x in current if x != e]
            table = {}
            for x in rest:
                table.setdefault(x[0], []).append(x)
            if all(spells(b, table) for b in blocks):
                current = rest
        return current

    state = {'dictionary': None}

    def offer(dictionary):
        if dictionary is None:
            return
        table = {}
        for x in dictionary:
            table.setdefault(x[0], []).append(x)
        if not all(spells(b, table) for b in blocks):
            return
        pruned = prune(dictionary)
        if state['dictionary'] is None or len(pruned) < len(state['dictionary']):
            state['dictionary'] = pruned

    def fits(total):
        return state['dictionary'] is not None and len(state['dictionary']) <= total

    def directions(space, entries_phi):
        out = {}
        for f in entries_phi:
            bigger = extend(space, f)
            if bigger != space:
                out.setdefault(bigger, None)
        return sorted(out)

    memo, through_cache, records = {}, {}, {}

    def through(o):
        if o not in through_cache:
            through_cache[o] = [t for t in names if cover[t] >> o & 1]
        return through_cache[o]

    def prove(space, j, total, root_limit=None):
        """True when refuted (see the module text); False when a dictionary of at most `total` entries was built.
        Raises Undecided when a limit stops it."""
        key = (space, j, total)
        if key in memo:
            if memo[key] is None:
                raise Undecided('a node already found undecided')
            return memo[key]
        memo[key] = None
        if seconds is not None and time.time() - started > seconds:
            raise Undecided('time limit')
        counters['spaces'] += 1
        ctx = context(space)
        if ctx['stuck']:
            if j == 0:
                records[key] = ('stuck', (ctx['stuck'] & -ctx['stuck']).bit_length() - 1, [])
                memo[key] = True
                return True
            stuck, per_char, choice, chosen_at = ctx['stuck'], {}, None, None
            looked = 0
            while stuck and looked < 12:                   # look at a few stuck occurrences, branch on the cheapest
                low = (stuck & -stuck).bit_length() - 1
                stuck &= ~(1 << low)
                c = occurrence_char[low]
                per_char[c] = per_char.get(c, 0) + 1
                if per_char[c] > 2:
                    stuck &= ~char_mask[c]
                    continue
                looked += 1
                phis = {fragments[t] for t in through(low)}
                if c not in whole:
                    phis.add(phi_char[c])
                spaces = directions(space, phis)
                if choice is None or len(spaces) < len(choice):
                    choice, chosen_at = spaces, low
                    if len(choice) <= 1:
                        break
            if len(choice) > branch_limit:
                raise Undecided(f'{len(choice)} branches at one occurrence exceed the limit')
            branches = choice
            records[key] = ('stuck', chosen_at, branches)
        else:
            candidate, refuted, reason = fixed(ctx, total, root_limit or node_limit)
            offer(candidate)
            if fits(total):
                memo[key] = False
                return False
            if not refuted:
                raise Undecided(reason or 'a fixed-space candidate did not replay')
            records[key] = ('search', None, [])
            if j == 0:
                memo[key] = True
                return True
            outside = [values[n] for n in np.nonzero(~ctx['inside_value'])[0]]
            branches = directions(space, outside)
            if len(branches) > fallback_limit:
                raise Undecided(f'{len(branches)} directions in the wide fallback exceed the limit')
        for bigger in branches:
            if not prove(bigger, j - 1, total):
                memo[key] = False
                return False
        memo[key] = True
        return True

    lower, level, note = rank, None, None
    for j in range(max_level + 1):
        total = rank + j
        if fits(total):
            level, note = j, f'rank + {j} attained'
            break
        try:
            refuted = prove((), j, total, rank_node_limit if j == 0 else None)
        except Undecided as reason:
            note = f'level {j} undecided: {reason}'
            break
        if not refuted:
            level, note = j, f'rank + {j} attained' if j else 'rank attained'
            break
        lower = total + 1
    else:
        note = f'no dictionary of rank + {max_level} entries'

    # A certificate for the bound, when every node of the last refuted level was closed by an uncoverable occurrence
    # and no search: the kernel basis and a tree of (space, occurrence, child spaces). check_certificate.py verifies it.
    certificate, proved = None, lower - rank - 1
    if proved >= 0:
        nodes, order, searched, queue = {}, [], False, [((), proved)]
        while queue:
            space, j = queue.pop()
            if (space, j) in nodes:
                continue
            kind, at, children = records[(space, j, rank + proved)]
            if kind != 'stuck':
                searched = True
                break
            bi, pos = occurrence_at[at]
            nodes[(space, j)] = len(order)
            order.append((space, j, free_blocks[bi], pos, children))
            queue.extend((child, j - 1) for child in children)
        if not searched:
            certificate = {'schema': 'bits-defect-tree/v1', 'rule': rule, 'prime': prime, 'base': base, 'letters': letters, 'kernel': kernel,
                           'refutes': rank + proved, 'lowerBound': lower,
                           'nodes': [{'space': [list(row) for _, row in space], 'spare': j, 'block': block, 'position': pos,
                                      'children': [nodes[(child, j - 1)] for child in children]} for space, j, block, pos, children in order]}
    return dict(info, certificate=certificate, boundBy=None if proved < 0 else ('defect tree' if certificate is not None else 'defect tree and search'), lowerBound=lower, dictionary=state['dictionary'], level=level, note=note, nodes=counters['nodes'],
                fixedSearches=counters['fixed'], refutedByRestrictedRank=counters.get('restricted', 0), spaces=counters['spaces'], fragments=len(names), seconds=round(time.time() - started, 3))


if __name__ == '__main__':
    r = analyze(sys.argv[1:], 'W2')
    print({k: v for k, v in r.items()})
