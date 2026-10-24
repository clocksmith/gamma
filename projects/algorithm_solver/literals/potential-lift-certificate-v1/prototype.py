"""Supplied-input potential lift only; no private loader, optimizer or runner."""
import hashlib
import heapq
import importlib.util
import json
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'potential_lift_full_index',
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


class Lift:
    def __init__(self, texts, banned, old_pool, old_q, seed, alphabet,
                 denominator, *, old_source_hashes, old_banned,
                 expected_occurrence_sha256=None):
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
                    rows[start].append((end, q))
                    weights[eid] += q
                    rank = ranks[pid, start]
                    lows[eid] = min(lows[eid], rank); highs[eid] = max(highs[eid], rank)
                    counts[eid] += 1
            distance = [None]*len(text)+[0]
            for start in range(len(text)-1, -1, -1):
                distance[start] = min((9 if end-start == 1 else -1)*denominator + q + distance[end]
                                      for end, q in rows[start])
            self.rows[pid], self.d[pid] = rows, distance
        assert cursor == len(old_q), 'extra old occurrence multiplier'
        self.old_occurrences = cursor
        self.occurrence_sha256 = order.hexdigest()
        if expected_occurrence_sha256 is not None:
            assert self.occurrence_sha256 == expected_occurrence_sha256, 'occurrence order mismatch'
        self.old_weights = weights
        self.old_entries = {}
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

    def penalty(self, pid, start, end):
        """For proof tests: old q is preserved exactly, even if larger than the lift."""
        for old_end, q in self.rows[pid][start]:
            if old_end == end:
                return q
        base = 9 if end-start == 1 else -1
        return max(0, self.d[pid][start]-self.d[pid][end]-base*self.D)

    def certificate(self, capacity=256):
        assert type(capacity) is int and capacity >= 0
        top = {1: Top(capacity), 2: Top(capacity)}
        counts = {1: 0, 2: 0}
        # All old occurring entries preserve their exact weights. Shared groups
        # have no new entries; old absent entries have weight zero and disappear.
        overrides = {}
        for (gid, length), weight in self.old_entries.items():
            top[self.support[gid]].add(weight, gid, length)
            overrides.setdefault(gid, set()).add(length)
        minima = {pid: Minimum(d) for pid, d in self.d.items()}
        unique = []
        repeated_occurrence_work = 0
        range_queries = 0

        def add_range(gid, pid, start, first, last):
            nonlocal range_queries
            if first > last:
                return
            value, end = minima[pid].query(start+first, start+last+1)
            range_queries += 1
            threshold = self.d[pid][start]+self.D
            weight = max(0, threshold-value)
            # Clamp ties at zero must choose earliest length, not smallest d.
            length = end-start if weight else first
            heapq.heappush(unique, (-weight, gid, length, pid, start, first, last))

        for gid, g in enumerate(self.index.groups):
            support = self.support[gid]
            counts[support] += g['multiplicity']
            if support == 2 or not g['multiplicity']:
                continue
            excluded = set(g['excluded_lengths']) | overrides.get(gid, set())
            if g['hi']-g['lo'] == 1:
                pid, start = self.positions[g['lo']]
                first = g['first']
                for length in sorted(excluded):
                    add_range(gid, pid, start, first, length-1); first = length+1
                add_range(gid, pid, start, first, g['last'])
            else:
                for length in range(g['first'], g['last']+1):
                    if length in excluded:
                        continue
                    assert length >= 2
                    weight = 0
                    for rank in range(g['lo'], g['hi']):
                        pid, start = self.positions[rank]
                        weight += max(0, self.d[pid][start]-self.d[pid][start+length]+self.D)
                        repeated_occurrence_work += 1
                    top[1].add(weight, gid, length)
        # Only top B from the union of unique-occurrence entries can enter a
        # global class top B. Splitting visits no unneeded individual lengths.
        unique_selected = 0
        while unique and unique_selected < capacity:
            minus_weight, gid, length, pid, start, first, last = heapq.heappop(unique)
            top[1].add(-minus_weight, gid, length); unique_selected += 1
            add_range(gid, pid, start, first, length-1)
            add_range(gid, pid, start, length+1, last)
        entries = {s: top[s].entries() for s in (1, 2)}
        prefixes = {}
        for s in (1, 2):
            assert len(entries[s]) == min(capacity, counts[s])
            prefixes[s] = [0]
            for weight, gid, length in entries[s]:
                prefixes[s].append(prefixes[s][-1]+weight)
        total = sum(self.path_numerators.values())
        rows = []
        for k in range(capacity+1):
            charge, neg_one, shared = max(
                (prefixes[1][j]+prefixes[2][min(capacity-j, len(entries[2]))],
                 -j, min(capacity-j, len(entries[2])))
                for j in range(min(k, len(entries[1]))+1))
            numerator = total-charge
            rows.append({'k': k, 'charge': charge, 'one_owner_slots': -neg_one,
                         'shared_slots': shared, 'numerator': numerator,
                         'integer_lower_bound': -(-numerator//self.D)})
        old_charge = sum(sorted(self.old_weights, reverse=True)[:capacity])
        assert rows[0]['numerator'] >= total-old_charge
        assert all(a['numerator'] >= b['numerator'] for a, b in zip(rows, rows[1:]))
        assert rows[-1]['charge'] == sum(sorted([w for s in entries.values() for w, g, n in s], reverse=True)[:capacity])
        return {'denominator': self.D, 'path_numerators': self.path_numerators,
                'old_charge': old_charge, 'old_numerator': total-old_charge,
                'class_counts': counts, 'top_entries': entries, 'rows': rows,
                'repeated_occurrence_work': repeated_occurrence_work,
                'unique_range_queries': range_queries,
                'unique_entries_extracted': unique_selected,
                'old_occurrences': self.old_occurrences,
                'old_trie_transitions': self.trie_transitions,
                'occurrence_sha256': self.occurrence_sha256}
