#!/usr/bin/env python3
"""Check the exact unrestricted coverage curve for compact matched80. Python 3.8+ and Git; no solver.

Under the unrestricted rule an entry is any non-empty substring of a program that is not a whole program.
With the original trailing newlines the most programs K entries can spell is
  K - 1 for 1 <= K <= 60,   K for 61 <= K <= 67,   K + 1 for 68 <= K <= 79,   80 from 80 on.

This is an independent implementation of the proof posted on the tracker: own elimination, suffix census,
reachability and cover check, run in a prime field of your choice. It checks every step of the upper bound
and replays a dictionary that attains the maximum at every budget from 0 to 79.

    python3 -B check_unrestricted.py /path/to/gamma [PRIME BASE]     (default 1000000007 2)
"""
import json
import subprocess
import sys

REPO = sys.argv[1]
P, B = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (1_000_000_007, 2)
PIN = '59ff04415ff2afd04ff2ed451340f4f02852bf18'
ROOT = 'projects/algorithm_solver/literals/'


def blob(path):
    return subprocess.check_output(['git', '-C', REPO, 'show', f'{PIN}:{ROOT}{path}'])


ids = sorted(json.loads(blob('matched80-v1/labels/ids.json')))
wanted = set(ids)
src = {}
for row in json.loads(blob('scale-v2/generated/manifest.json'))['rows']:
    if row['variant'] == 'compact' and row['id'] in wanted:
        src[row['id']] = blob('scale-v2/generated/' + row['file'])
assert len(src) == 80 and len(set(src.values())) == 80
whole = set(src.values())
facts = {'prime': P, 'base': B, 'pin': PIN}
facts['everySourceHasOneNewlineAtTheEnd'] = all(s.count(b'\n') == 1 and s.endswith(b'\n') for s in src.values())
facts['everySourceEndsWithSemicolonBraceNewline'] = all(s.endswith(b';}\n') for s in src.values())
chars = {c: i for i, c in enumerate(sorted(set(b''.join(src.values()))))}
N = len(chars)


def vec(word):
    out, weight = [0] * N, 1
    for c in word:
        out[chars[c]] = (out[chars[c]] + weight) % P
        weight = weight * B % P
    return out


class Space:
    """Reduced row echelon basis of the given vectors, remembering each basis row as a combination of the inputs."""

    def __init__(self, vectors):
        self.count, self.rows, self.null = len(vectors), [], []
        for i, v in enumerate(vectors):
            v, c = list(v), [int(i == j) for j in range(self.count)]
            for pivot, rv, rc in self.rows:
                if v[pivot]:
                    f = v[pivot]
                    v = [(a - f * b) % P for a, b in zip(v, rv)]
                    c = [(a - f * b) % P for a, b in zip(c, rc)]
            pivot = next((j for j, x in enumerate(v) if x), None)
            if pivot is None:
                self.null.append(c)
                continue
            inv = pow(v[pivot], P - 2, P)
            v, c = [x * inv % P for x in v], [x * inv % P for x in c]
            for k, (pj, rv, rc) in enumerate(self.rows):
                if rv[pivot]:
                    f = rv[pivot]
                    self.rows[k] = (pj, [(a - f * b) % P for a, b in zip(rv, v)], [(a - f * b) % P for a, b in zip(rc, c)])
            self.rows.append((pivot, v, c))

    def solve(self, target):
        v, c = list(target), [0] * self.count
        for pivot, rv, rc in self.rows:
            if v[pivot]:
                f = v[pivot]
                v = [(a - f * b) % P for a, b in zip(v, rv)]
                c = [(a + f * b) % P for a, b in zip(c, rc)]
        return None if any(v) else c


def prefix_cuts(program, members):
    """Positions i such that the first i bytes of the program have a vector in the span of the members."""
    space, raw = Space([vec(src[q]) for q in members]), src[program]
    out, running, weight = [], [0] * N, 1
    for i in range(len(raw) + 1):
        if space.solve(running) is not None:
            out.append(i)
        if i < len(raw):
            running[chars[raw[i]]] = (running[chars[raw[i]]] + weight) % P
            weight = weight * B % P
    return out


# ---- 1. Rank, and the one dependent set.
full = Space([vec(src[p]) for p in ids])
facts['rank'] = len(full.rows)
facts['dependencies'] = len(full.null)
lam = full.null[0]
J = [ids[j] for j, x in enumerate(lam) if x]
facts['dependentSetSize'] = len(J)

# ---- 2. The 67-slot step: members of J with no nonempty proper prefix in the span of J.
blocked = [p for p in J if prefix_cuts(p, J) == [0, len(src[p])]]
facts['membersOfJWithNoLegalFirstCut'] = blocked

# ---- 3. Suffixes shared by two or more sources, whole sources excluded.
owners = {}
for p, s in src.items():
    for i in range(len(s)):
        owners.setdefault(s[i:], set()).add(p)
shared_suffixes = sorted(w for w, who in owners.items() if len(who) >= 2 and w not in whole)
facts['sharedSuffixes'] = len(shared_suffixes)

# ---- 4. Every way to write a shared suffix with at most 60 programs.
support_of = lambda coeff: tuple(ids[j] for j, x in enumerate(coeff) if x)
in_span, sparse = 0, {}
for word in shared_suffixes:
    x = full.solve(vec(word))
    if x is None:
        continue
    in_span += 1
    for j, l in enumerate(lam):
        if l:
            t = x[j] * pow(l, P - 2, P) % P
            support = support_of([(a - t * b) % P for a, b in zip(x, lam)])
            if len(support) <= 60:
                sparse.setdefault(support, set()).add(word)
facts['sharedSuffixesInTheSpan'] = in_span
facts['supportsOfAtMost60'] = len(sparse)
S = list(next(iter(sparse))) if len(sparse) == 1 else []
facts['supportSize'] = len(S)
facts['suffixesWithThatSupport'] = sorted(w.decode('latin-1') for w in next(iter(sparse.values()))) if sparse else []
facts['supportOutsideJ'] = sorted(set(S) - set(J))

# The same set a second way: the smallest dependent set of the sources with the newline removed.
strip_col = chars[ord('\n')]
bodies = Space([[0 if k == strip_col else x for k, x in enumerate(vec(src[p]))] for p in ids])
facts['strippedRank'] = len(bodies.rows)
cands = {support_of(d) for d in bodies.null}
if len(bodies.null) == 2:
    d1, d2 = bodies.null
    for j, x in enumerate(d1):
        if x:
            t = d2[j] * pow(x, P - 2, P) % P
            cands.add(support_of([(b - t * a) % P for a, b in zip(d1, d2)]))
smallest = min(cands, key=len)
facts['smallestStrippedDependentSet'] = len(smallest)
facts['supportEqualsSmallestStrippedDependentSet'] = sorted(smallest) == sorted(S)

# ---- 5. The 60-slot step: can a member of S be cut only at allowed positions into pieces found in another source?
def furthest(program, members):
    raw, allowed = src[program], prefix_cuts(program, members)
    others = [s for q, s in src.items() if q != program]
    reach = [0]
    for right in allowed[1:]:
        if any(any(raw[left:right] in other for other in others) for left in reach):
            reach.append(right)
    return len(allowed), max(reach), len(raw)

if S:
    stuck = {}
    for p in S:
        allowed, far, length = furthest(p, S)
        if far < length:
            stuck[p] = {'allowedBoundaries': allowed, 'boundaries': length + 1, 'furthestReachable': far, 'length': length}
    facts['membersOfSThatCannotBeSpelled'] = stuck

# ---- 6. A dictionary attaining the claimed maximum at every budget.
def eligible(words):
    return all(w and w not in whole and any(w in s for s in whole) for w in words)

def covered(words):
    words, out = sorted(words, key=len, reverse=True), set()
    for p, s in src.items():
        ok = [False] * (len(s) + 1)
        ok[len(s)] = True
        for i in range(len(s) - 1, -1, -1):
            ok[i] = any(s.startswith(w, i) and ok[i + len(w)] for w in words)
        if ok[0]:
            out.add(p)
    return out

def stored(job):
    words = json.loads(blob('sixbit-v1/' + job + '/manifest.json'))['vocabulary']
    assert len(set(words)) == len(words)
    return {w.encode() for w in words}

tail = b';}\n'
heads = [src[p][:-len(tail)] for p in ids]
attained, sizes = {0: 0}, {0: 0}
for k in range(1, 61):
    words = {tail, *heads[:k - 1]}
    assert eligible(words) and len(words) == k
    attained[k], sizes[k] = len(covered(words)), len(words)
b_shared = {w for w in stored('run-jupiter-v1/b-u-compact') if sum(w in s for s in whole) >= 2}
seed = covered(b_shared)
facts['sharedEntriesInTheStored64'] = len(b_shared)
facts['programsThoseEntriesCover'] = len(seed)
extra = [src[p][:-len(tail)] for p in ids if p not in seed]
for k in range(61, 68):
    words = b_shared | set(extra[:k - 61])
    assert eligible(words) and len(words) == k, (k, len(words))
    attained[k], sizes[k] = len(covered(words)), len(words)
a_full = stored('run-v1/a-u-compact')
one_owner = sorted(w for w in a_full if sum(w in s for s in whole) == 1)
facts['storedFullDictionary'] = {'entries': len(a_full), 'oneOwnerEntries': len(one_owner)}
for k in range(68, 80):
    words = a_full - set(one_owner[:79 - k])
    assert eligible(words) and len(words) == k
    attained[k], sizes[k] = len(covered(words)), len(words)
claimed = lambda k: 0 if k == 0 else k - 1 if k <= 60 else k if k <= 67 else k + 1
facts['budgetsWhereTheDictionaryMissesTheClaim'] = [k for k in range(80) if attained[k] != claimed(k)]
facts['attained'] = {k: attained[k] for k in (1, 2, 59, 60, 61, 64, 66, 67, 68, 78, 79)}

# ---- 7. A direct check at two slots: two entries cover two sources only if one source is a suffix of another.
facts['sourcesThatAreSuffixesOfAnother'] = sum(1 for a in whole for b in whole if a != b and b.endswith(a))

# ---- The upper bound that follows, budget by budget.
def upper(k):
    if k == 0:
        return 0
    bound = min(80, k + 1)                                         # rank: any m sources have rank at least m - 1
    if k <= 66:
        bound = min(bound, k)                                      # rank m - 1 needs all of J, so m >= 68
    if k == 67 and blocked:
        bound = min(bound, k)                                      # J is the only candidate and one member cannot start
    if k <= 60 and len(sparse) <= 1 and (not S or (len(S) == 60 and facts['membersOfSThatCannotBeSpelled'])):
        bound = min(bound, k - 1)                                  # no admissible set of k sources
    return bound

facts['budgetsWhereUpperAndAttainedDiffer'] = [k for k in range(80) if upper(k) != attained[k]]


def check(value, message):
    if not value:
        raise SystemExit('FAILED: ' + message)


check(facts['everySourceHasOneNewlineAtTheEnd'], 'a source has a newline elsewhere')
check(facts['rank'] == 79 and facts['dependencies'] == 1 and facts['dependentSetSize'] == 68, 'rank or dependent set')
check(len(blocked) >= 1, 'no member of the dependent set lacks a legal first cut')
check(facts['supportsOfAtMost60'] == 1 and facts['supportSize'] == 60, 'supports of at most 60 programs')
check(len(facts['membersOfSThatCannotBeSpelled']) >= 1, 'every member of the 60-program support can be spelled')
check(facts['sourcesThatAreSuffixesOfAnother'] == 0, 'a source is a suffix of another')
check(facts['budgetsWhereTheDictionaryMissesTheClaim'] == [], 'a replayed dictionary misses the claimed maximum')
check(facts['budgetsWhereUpperAndAttainedDiffer'] == [], 'upper bound and attained value differ')
print(f'Field {P}, base {B}. Rank 79; one dependent set of 68 programs; {len(blocked)} of them have no legal first cut.')
print(f"{facts['sharedSuffixes']} shared suffixes give one support of at most 60 programs, of size 60; "
      f"{len(facts['membersOfSThatCannotBeSpelled'])} of its members cannot be spelled inside its span.")
print('Upper bound equals a replayed dictionary at every budget 0..79: K-1 to 60, K to 67, K+1 to 79, then 80.')
if '--json' in sys.argv:
    print(json.dumps(facts, indent=1))
