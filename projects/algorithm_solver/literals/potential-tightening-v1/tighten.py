"""Item53 supplied-input fixed-potential tightening; no file loader or optimizer.

Old trie/backward reconstruction and unique-range helpers are adapted from the
frozen item50 prototype. This is an isolated copy, not an import or monkeypatch.
Item33 Index is the shared structural dependency. The separate checker must use
its own occurrence traversal, paths, support classification and scalar sums.
"""
import hashlib
import heapq
import importlib.util
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'potential_tighten_full_index',
    Path(__file__).resolve().parents[1] / 'all-substring-fraction-v1/implicit.py')
full = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(full)


def source_hashes(texts):
    return {pid: hashlib.sha256(t.encode()).hexdigest() for pid, t in texts.items()}


def classes(index):
    prefix = [0] * len(index.positions)
    for i in range(1, len(prefix)):
        prefix[i] = prefix[i-1] + (index.positions[i][0] != index.positions[i-1][0])
    return [1 if prefix[g['hi']-1] == prefix[g['lo']] else 2 for g in index.groups]


class Top:
    """Bounded exact top entries; ties use (group, length) ascending."""
    def __init__(self, capacity):
        self.capacity = capacity
        self.heap = []

    def add(self, weight, gid, length):
        assert type(weight) is int and weight >= 0
        row = (weight, -gid, -length)
        if len(self.heap) < self.capacity:
            heapq.heappush(self.heap, row)
        elif self.capacity and row > self.heap[0]:
            heapq.heapreplace(self.heap, row)

    def entries(self):
        return [(w, -g, -n) for w, g, n in sorted(self.heap, reverse=True)]


class Minimum:
    """Static range minimum of (exact potential, endpoint)."""
    def __init__(self, values):
        self.n = 1
        while self.n < len(values):
            self.n *= 2
        self.tree = [None] * (2*self.n)
        for j, value in enumerate(values):
            self.tree[self.n+j] = (value, j)
        for j in range(self.n-1, 0, -1):
            self.tree[j] = self.merge(self.tree[2*j], self.tree[2*j+1])

    @staticmethod
    def merge(a, b):
        return b if a is None else a if b is None else min(a, b)

    def query(self, lo, hi):
        value = None
        lo += self.n; hi += self.n
        while lo < hi:
            if lo & 1:
                value = self.merge(value, self.tree[lo]); lo += 1
            if hi & 1:
                hi -= 1; value = self.merge(value, self.tree[hi])
            lo //= 2; hi //= 2
        assert value is not None
        return value


class Tighten:
    def __init__(self, texts, banned, old_pool, old_q, seed, alphabet,
                 denominator, *, old_source_hashes, old_banned,
                 expected_occurrence_sha256=None, expected_old_certificate=None):
        if not __debug__:
            raise RuntimeError('checks must remain enabled')
        assert type(denominator) is int and denominator > 0
        assert texts and all(isinstance(pid, str) and text for pid, text in texts.items())
        assert old_source_hashes == source_hashes(texts), 'source identity mismatch'
        assert set(old_banned) == set(banned), 'ban identity mismatch'
        assert old_pool == sorted(set(old_pool)) and all(old_pool)
        assert len(set(seed)) == len(seed) and set(seed) <= set(old_pool)
        assert set(alphabet) <= set(old_pool) and all(len(v) == 1 for v in alphabet)
        assert set(''.join(texts.values())) <= set(alphabet)
        assert not set(old_pool) & set(banned), 'old path edge may be banned'
        assert all(type(q) is int and q >= 0 for q in old_q)
        self.texts, self.D = dict(texts), denominator
        self.expected_old_certificate = expected_old_certificate
        self.old_pool = list(old_pool)
        self.index = full.Index(texts, banned)
        self.support = classes(self.index)
        self.positions = self.index.positions
        ranks = {position: rank for rank, position in enumerate(self.positions)}
        intervals = {(g['lo'], g['hi']): gid for gid, g in enumerate(self.index.groups)}
        trie = {}
        for eid, word in enumerate(old_pool):
            node = trie
            for ch in word:
                node = node.setdefault(ch, {})
            node[None] = eid
        weights = [0] * len(old_pool)
        lows, highs, counts = [len(ranks)]*len(old_pool), [-1]*len(old_pool), [0]*len(old_pool)
        self.rows, self.d = {}, {}
        order = hashlib.sha256()
        cursor = 0
        self.trie_transitions = 0
        for pid, text in sorted(texts.items()):
            rows = [[] for _ in text]
            for start in range(len(text)):
                node = trie
                for end in range(start+1, len(text)+1):
                    self.trie_transitions += 1
                    node = node.get(text[end-1])
                    if node is None:
                        break
                    if None not in node:
                        continue
                    eid = node[None]
                    assert cursor < len(old_q), 'missing old occurrence multiplier'
                    q = old_q[cursor]; cursor += 1
                    order.update((json.dumps([pid, start, end, eid], separators=(',', ':'))+'\n').encode())
                    rows[start].append((end, eid, q))
                    weights[eid] += q
                    rank = ranks[pid, start]
                    lows[eid] = min(lows[eid], rank); highs[eid] = max(highs[eid], rank)
                    counts[eid] += 1
            distance = [None]*len(text)+[0]
            for start in range(len(text)-1, -1, -1):
                distance[start] = min((9 if end-start == 1 else -1)*denominator + q + distance[end]
                                      for end, eid, q in rows[start])
            self.rows[pid], self.d[pid] = rows, distance
        assert cursor == len(old_q), 'extra old occurrence multiplier'
        self.old_occurrences = cursor
        self.occurrence_sha256 = order.hexdigest()
        if expected_occurrence_sha256 is not None:
            assert self.occurrence_sha256 == expected_occurrence_sha256, 'occurrence order mismatch'
        self.old_weights = weights
        self.old_entries = {}
        self.old_entry_ids = {}
        actual_shared = 0
        for eid, word in enumerate(old_pool):
            if not counts[eid]:
                assert word in seed or word in alphabet, 'unsupported absent old entry'
                continue
            lo, hi = lows[eid], highs[eid]+1
            assert counts[eid] == hi-lo
            gid = intervals[lo, hi]
            g = self.index.groups[gid]
            assert g['first'] <= len(word) <= g['last'] and len(word) not in g['excluded_lengths']
            assert (gid, len(word)) not in self.old_entries
            self.old_entries[gid, len(word)] = weights[eid]
            self.old_entry_ids[gid, len(word)] = eid
            shared_learned = self.support[gid] == 2 and len(word) >= 2
            assert shared_learned or word in seed or word in alphabet, 'extra old entry'
            actual_shared += shared_learned
        expected_shared = sum(g['multiplicity'] - int(g['first'] == 1 and 1 not in g['excluded_lengths'])
                              for gid, g in enumerate(self.index.groups) if self.support[gid] == 2)
        assert actual_shared == expected_shared, 'old pool omits an allowed shared substring'
        # Full-pool characters, including support-one characters, are paid old entries.
        for gid, g in enumerate(self.index.groups):
            if g['first'] == 1 and 1 not in g['excluded_lengths']:
                assert (gid, 1) in self.old_entries
        self.path_numerators = {pid: d[0] for pid, d in self.d.items()}
        self.tight_weights = [0]*len(old_pool)
        reduced, reduction, tight_positions = 0, 0, 0
        for pid, rows in self.rows.items():
            d = self.d[pid]
            assert all(type(value) is int for value in d) and d[-1] == 0
            for start, outgoing in enumerate(rows):
                tight = False
                for end, eid, q in outgoing:
                    base = 9 if end-start == 1 else -1
                    value = max(0, d[start]-d[end]-base*self.D)
                    assert 0 <= value <= q
                    assert d[start] <= base*self.D+q+d[end]
                    if d[start] == base*self.D+q+d[end]:
                        assert value == q
                        tight = True
                    self.tight_weights[eid] += value
                    reduced += value < q
                    reduction += q-value
                assert tight, 'every old suffix needs a retained tight continuation'
                tight_positions += 1
        assert tight_positions == sum(map(len, self.texts.values()))
        assert all(a >= b for a, b in zip(weights, self.tight_weights))
        assert sum(weights)-sum(self.tight_weights) == reduction
        self.reductions = {'old_occurrences_reduced': reduced,
                           'old_multiplier_reduction': reduction,
                           'old_entries_reduced': sum(a > b for a, b in zip(weights, self.tight_weights)),
                           'occurring_old_entries': len(self.old_entries),
                           'absent_old_entries': len(old_pool)-len(self.old_entries)}
        self.tight_suffix_positions_checked = tight_positions

    def penalty(self, pid, start, end, *, tighten_old=True):
        """Supplied-input oracle access; caller selects an allowed occurrence."""
        assert type(tighten_old) is bool
        if not tighten_old:
            for old_end, eid, q in self.rows[pid][start]:
                if old_end == end:
                    return q
        base = 9 if end-start == 1 else -1
        return max(0, self.d[pid][start]-self.d[pid][end]-base*self.D)

    def certificate(self, capacity=256):
        """Paired complete50/53 proofs from one new-only aggregation.

        lifted and tightened each contain exactly item50's scientific PROOF_FIELDS.
        Integer support keys serialize as strings; digest() normalizes them.
        New-only class tops remain separate until the two final merges.
        """
        if not __debug__:
            raise RuntimeError('checks must remain enabled')
        assert type(capacity) is int and capacity >= 0
        newtop = {1: Top(capacity), 2: Top(capacity)}
        counts, newcounts = {1: 0, 2: 0}, {1: 0, 2: 0}
        overrides = {}
        for gid, length in self.old_entries:
            overrides.setdefault(gid, set()).add(length)
        minima = {pid: Minimum(d) for pid, d in self.d.items()}
        unique = []
        repeated_work, range_queries = 0, 0

        def add_range(gid, pid, start, first, last):
            nonlocal range_queries
            if first > last:
                return
            assert first >= 2, 'all occurring characters are old'
            value, end = minima[pid].query(start+first, start+last+1)
            range_queries += 1
            weight = max(0, self.d[pid][start]+self.D-value)
            length = end-start if weight else first
            heapq.heappush(unique, (-weight, gid, length, pid, start, first, last))

        for gid, group in enumerate(self.index.groups):
            support = self.support[gid]
            counts[support] += group['multiplicity']
            oldlengths = overrides.get(gid, set())
            assert len(oldlengths) <= group['multiplicity']
            newcounts[support] += group['multiplicity']-len(oldlengths)
            if support == 2:
                assert len(oldlengths) == group['multiplicity'], 'missing old shared entry'
                continue
            if not group['multiplicity']:
                continue
            excluded = set(group['excluded_lengths']) | oldlengths
            if group['hi']-group['lo'] == 1:
                pid, start = self.positions[group['lo']]
                first = group['first']
                for length in sorted(excluded):
                    add_range(gid, pid, start, first, length-1)
                    first = length+1
                add_range(gid, pid, start, first, group['last'])
            else:
                for length in range(group['first'], group['last']+1):
                    if length in excluded:
                        continue
                    assert length >= 2
                    weight = 0
                    for rank in range(group['lo'], group['hi']):
                        pid, start = self.positions[rank]
                        weight += max(0, self.d[pid][start]-self.d[pid][start+length]+self.D)
                        repeated_work += 1
                    newtop[support].add(weight, gid, length)
        extracted = 0
        while unique and extracted < capacity:
            minus, gid, length, pid, start, first, last = heapq.heappop(unique)
            newtop[1].add(-minus, gid, length)
            extracted += 1
            add_range(gid, pid, start, first, length-1)
            add_range(gid, pid, start, length+1, last)
        new_entries = {support: newtop[support].entries() for support in (1, 2)}
        assert newcounts[2] == 0
        assert sum(counts.values()) == self.index.distinct_allowed_entries
        for support in (1, 2):
            assert len(new_entries[support]) == min(capacity, newcounts[support])

        total = sum(self.path_numerators.values())
        old_charge = sum(heapq.nlargest(capacity, self.old_weights))
        common = {'denominator': self.D, 'path_numerators': dict(self.path_numerators),
                  'old_charge': old_charge, 'old_numerator': total-old_charge,
                  'class_counts': counts, 'old_occurrences': self.old_occurrences,
                  'occurrence_sha256': self.occurrence_sha256}
        if self.expected_old_certificate is not None:
            rebuilt = {'denominator': self.D, 'relaxed_paths_numerator': total,
                       'top_capacity_numerator': old_charge, 'numerator': total-old_charge,
                       'integer_lower_bound': -(-(total-old_charge)//self.D),
                       'per_program_path_numerators': [self.path_numerators[pid] for pid in sorted(self.texts)]}
            for key, expected in rebuilt.items():
                actual = self.expected_old_certificate[key]
                assert type(actual) is type(expected)
                if isinstance(expected, list):
                    assert all(type(v) is int for v in actual)
                assert actual == expected, ('old certificate', key)

        proofs = {}
        for name, weights in (('lifted', self.old_weights), ('tightened', self.tight_weights)):
            merged = {1: Top(capacity), 2: Top(capacity)}
            for support, entries in new_entries.items():
                for weight, gid, length in entries:
                    merged[support].add(weight, gid, length)
            for (gid, length), eid in self.old_entry_ids.items():
                merged[self.support[gid]].add(weights[eid], gid, length)
            entries = {support: merged[support].entries() for support in (1, 2)}
            rows = allocations(entries, counts, capacity, total, self.D)
            assert rows[0]['numerator'] >= total-old_charge
            proofs[name] = {**common, 'top_entries': entries, 'rows': rows}
        before, after = proofs['lifted']['rows'], proofs['tightened']['rows']
        deltas = []
        for a, b in zip(before, after):
            assert b['charge'] <= a['charge'] and b['integer_lower_bound'] >= a['integer_lower_bound']
            deltas.append({'k': a['k'], 'charge_reduction': a['charge']-b['charge'],
                           'integer_bound_gain': b['integer_lower_bound']-a['integer_lower_bound']})
        reductions = {**self.reductions,
                      'strict_charge_budgets': sum(row['charge_reduction'] > 0 for row in deltas),
                      'strict_integer_bound_budgets': sum(row['integer_bound_gain'] > 0 for row in deltas)}
        digests = {'potentials_sha256': digest(self.d),
                   'old_weights_sha256': digest(self.old_weights),
                   'tightened_old_weights_sha256': digest(self.tight_weights),
                   'new_only_top_sha256': digest(new_entries)}
        for name, proof in proofs.items():
            digests[name+'_proof_sha256'] = digest(proof)
            digests[name+'_top_entries_sha256'] = digest(proof['top_entries'])
            digests[name+'_rows_sha256'] = digest(proof['rows'])
        return {'schema': 'gamma.potential-tightening.supplied.v1', **proofs,
                'new_only_class_counts': newcounts, 'new_only_top_entries': new_entries,
                'digests': digests, 'reductions': reductions, 'deltas': deltas,
                'work': {'old_trie_transitions': self.trie_transitions,
                         'old_occurrences_tightened': self.old_occurrences,
                         'tight_suffix_positions_checked': self.tight_suffix_positions_checked,
                         'repeated_new_occurrence_contributions': repeated_work,
                         'unique_range_queries': range_queries,
                         'unique_entries_extracted': extracted}}


def digest(value):
    """Match item50 public digest: JSON string keys, sorted, ASCII, no floats."""
    def shape(v):
        if isinstance(v, dict):
            return {str(k): shape(x) for k, x in v.items()}
        if isinstance(v, (list, tuple)):
            return [shape(x) for x in v]
        return v
    return hashlib.sha256(json.dumps(shape(value), sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def allocations(entries, counts, capacity, total, denominator):
    prefixes = {}
    for support in (1, 2):
        assert len(entries[support]) == min(capacity, counts[support])
        prefixes[support] = [0]
        for weight, gid, length in entries[support]:
            prefixes[support].append(prefixes[support][-1]+weight)
    rows = []
    for k in range(capacity+1):
        charge, negative_one, shared = max(
            (prefixes[1][j]+prefixes[2][min(capacity-j, counts[2])],
             -j, min(capacity-j, counts[2]))
            for j in range(min(k, counts[1])+1))
        numerator = total-charge
        rows.append({'k': k, 'charge': charge, 'one_owner_slots': -negative_one,
                     'shared_slots': shared, 'numerator': numerator,
                     'integer_lower_bound': -(-numerator//denominator)})
    assert all(a['charge'] <= b['charge'] for a, b in zip(rows, rows[1:]))
    assert rows[-1]['charge'] == sum(heapq.nlargest(capacity,
        (w for values in entries.values() for w, _, _ in values)))
    return rows
